# app/models.py
# -*- coding: utf-8 -*-

from app import db
from datetime import datetime
from typing import Optional, Dict, Any, List
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.types import Date, Text
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import validates
import re
import json

# Монгол цаг
from app.utils.datetime import now_local as now_mn

# Float тооны харьцуулалтын хязгаар (epsilon)
FLOAT_EPSILON = 1e-9


# -------------------------
# ХЭРЭГЛЭГЧ
# -------------------------
class User(UserMixin, db.Model):
    """
    Хэрэглэгчийн модел (ISO 17025 compliance).

    Системд нэвтрэх эрхтэй хэрэглэгчдийн мэдээллийг хадгална.
    Flask-Login-тэй нэгдсэн, роль дээр суурилсан эрх олгох.

    Attributes:
        id (int): Primary key
        username (str): Нэвтрэх нэр (өвөрмөц)
        password_hash (str): Hash-ласан нууц үг (Werkzeug)
        role (str): Эрх ('prep', 'chemist', 'senior', 'manager', 'admin')

    Roles:
        - prep: Дээж бэлтгэх (Sample Preparation)
        - chemist: Шинжилгээ хийх (Chemist)
        - senior: Үр дүн шалгах, баталгаажуулах (Senior Chemist)
        - manager: Лабораторийн менежер (Manager)
        - admin: Системийн админ (бүх эрх)
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(64), index=True, default="prep")

    # Мульти-лаборатори эрх
    allowed_labs = db.Column(db.JSON, default=['coal'])  # ['coal', 'petrography', 'water']

    # Хувийн мэдээлэл (Email signature-д ашиглана)
    full_name = db.Column(db.String(100))  # Бүтэн нэр
    email = db.Column(db.String(120))  # Ажлын имэйл
    phone = db.Column(db.String(20))  # Утасны дугаар
    position = db.Column(db.String(100))  # Албан тушаал

    def has_lab_access(self, lab_key: str) -> bool:
        """Хэрэглэгч тухайн лабд нэвтрэх эрхтэй эсэх."""
        if self.role == 'admin':
            return True
        labs = self.allowed_labs or ['coal']
        return lab_key in labs

    def set_password(self, password: str) -> None:
        """
        Нууц үг тохируулах. Нууц үгний бодлого шалгаж, hash хийнэ.

        Args:
            password (str): Шинэ нууц үг

        Raises:
            ValueError: Нууц үг бодлогыг хангахгүй бол

        Example:
            >>> user = User(username='john')
            >>> user.set_password('weak')
            ValueError: Нууц үгний шаардлага: ...
            >>> user.set_password('Strong123')
            # Амжилттай

        Security:
            - Нууц үг бодлого validate_password()-ээр шалгагдана
            - Hash нь Werkzeug.security.generate_password_hash ашиглана
            - Анхны нууц үг хаана ч хадгалагдахгүй
        """
        errors = self.validate_password(password)
        if errors:
            raise ValueError(f"Нууц үгний шаардлага: {', '.join(errors)}")
        self.password_hash = generate_password_hash(password)

    @staticmethod
    def validate_password(password: str) -> list[str]:
        """
        Нууц үгний бодлого шалгах.

        Шаардлага:
            - Хамгийн багадаа 8 тэмдэгт
            - Том үсэг (A-Z)
            - Жижиг үсэг (a-z)
            - Тоо (0-9)

        Args:
            password (str): Шалгах нууц үг

        Returns:
            list[str]: Алдааны мессежүүдийн жагсаалт.
                      Хоосон жагсаалт = бүх шаардлага хангасан.

        Example:
            >>> User.validate_password('abc')
            ['хамгийн багадаа 8 тэмдэгт байх ёстой', 'том үсэг агуулах ёстой', ...]
            >>> User.validate_password('Strong123')
            []

        Notes:
            Static method учраас object үүсгэхгүйгээр дуудаж болно.
        """
        errors = []
        if len(password) < 8:
            errors.append("хамгийн багадаа 8 тэмдэгт байх ёстой")
        if not any(c.isupper() for c in password):
            errors.append("том үсэг агуулах ёстой")
        if not any(c.islower() for c in password):
            errors.append("жижиг үсэг агуулах ёстой")
        if not any(c.isdigit() for c in password):
            errors.append("тоо агуулах ёстой")
        return errors

    def check_password(self, password: str) -> bool:
        """
        Нууц үг зөв эсэхийг шалгах.

        Args:
            password (str): Шалгах нууц үг (туулалттай текст)

        Returns:
            bool: Зөв бол True, буруу бол False

        Example:
            >>> user.check_password('wrong_password')
            False
            >>> user.check_password('correct_password')
            True

        Security:
            Werkzeug constant-time comparison ашиглана (timing attack сэргийлэх).
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


# -------------------------
# ДЭЭЖ
# -------------------------
class Sample(db.Model):
    """
    Дээжний үндсэн модель (ISO 17025 compliance).

    Лабораторид хүлээн авсан дээжний бүх мэдээлэл, төлөв байдал,
    шинжилгээний үр дүнг хадгална. Нүүрс/ашигт малтмалын шинжилгээнд зориулсан.

    Attributes:
        id (int): Primary key
        sample_code (str): Дээжний өвөрмөц код (жишээ: "CHPP-250101-001")
        received_date (datetime): Хүлээн авсан огноо/цаг (Монгол цагаар)
        user_id (int): Foreign key → User (бэлтгэсэн хэрэглэгч)
        status (str): Төлөв байдал ('new', 'prepared', 'analysis', 'completed')
        sample_date (date): Дээжний огноо
        sample_condition (str): Дээжний нөхцөл байдал
        client_name (str): Захиалагчийн нэр (CHPP, UHG-Geo, BN-Geo, QC, WTL, Proc, LAB)
        sample_type (str): Дээжний төрөл (ж: "2 hourly", "4 hourly", "Daily")
        analyses_to_perform (str): Хийх шинжилгээний жагсаалт (зайгаар тусгаарлагдсан)
        notes (str): Тэмдэглэл
        weight (float): Жин (грамм)
        return_sample (bool): Дээж буцаах эсэх
        delivered_by (str): Хүргэгч
        prepared_by (str): Бэлтгэсэн ажилтан
        prepared_date (date): Бэлтгэсэн огноо
        location (str): Байршил
        hourly_system (str): Цагийн систем
        shift_time (str): Ээлжийн цаг
        product (str): Бүтээгдэхүүн
        mass_ready (bool): Mass gate-д бэлэн эсэх
        mass_ready_at (datetime): Бэлэн болсон огноо
        mass_ready_by_id (int): Бэлэн болгосон хэрэглэгч

    Relationships:
        results: One-to-many → AnalysisResult (шинжилгээний үр дүнгүүд)

    Table Constraints:
        - client_name CHECK constraint: ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB')
        - sample_code UNIQUE index
        - received_date, status indices

    Example:
        >>> sample = Sample(
        ...     sample_code='CHPP-250124-001',
        ...     client_name='CHPP',
        ...     sample_type='2 hourly',
        ...     weight=50.5
        ... )
        >>> db.session.add(sample)
        >>> db.session.commit()
    """
    id = db.Column(db.Integer, primary_key=True)
    sample_code = db.Column(db.String(100), index=True, unique=True)

    # UTC биш, Монгол
    received_date = db.Column(db.DateTime, index=True, default=now_mn)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id", name="fk_sample_user_id"), index=True)

    status = db.Column(db.String(64), default="new", index=True)
    lab_type = db.Column(db.String(20), default='coal', index=True)  # 'coal', 'petrography', 'water'
    sample_date = db.Column(Date, default=lambda: now_mn().date())

    sample_condition = db.Column(db.String(100))
    client_name = db.Column(db.String(200))
    sample_type = db.Column(db.String(100))
    analyses_to_perform = db.Column(db.String(500))
    notes = db.Column(Text)
    weight = db.Column(db.Float)
    return_sample = db.Column(db.Boolean, default=False)
    delivered_by = db.Column(db.String(200))
    prepared_by = db.Column(db.String(200))
    prepared_date = db.Column(Date)
    location = db.Column(db.String(100))
    hourly_system = db.Column(db.String(50))
    shift_time = db.Column(db.String(50))
    product = db.Column(db.String(100))

    # 🛑 Mass gate талбарууд
    mass_ready = db.Column(db.Boolean, nullable=False, default=False, index=True)
    mass_ready_at = db.Column(db.DateTime, nullable=True)
    mass_ready_by_id = db.Column(db.Integer, nullable=True)

    # Усны лабын тусдаа дугаарууд
    chem_lab_id = db.Column(db.String(20), nullable=True, index=True)   # "1_05" = batch 1, сорьц 5
    micro_lab_id = db.Column(db.String(20), nullable=True, index=True)  # "01_05" = өдөр 1, дэс 5

    # 🆕 ISO 17025: Chain of Custody & Sample Retention
    sampled_by = db.Column(db.String(100))  # Хэн авсан
    sampling_date = db.Column(db.DateTime)  # Хэзээ авсан
    sampling_location = db.Column(db.String(200))  # Хаанаас авсан
    sampling_method = db.Column(db.String(100))  # Аргачлал (SOP reference)
    custody_log = db.Column(db.Text)  # JSON: Хариуцлага шилжүүлсэн түүх
    retention_date = db.Column(Date)  # Хадгалах дуусах хугацаа
    disposal_date = db.Column(Date)  # Устгах огноо
    disposal_method = db.Column(db.String(100))  # Яаж устгасан

    # ✅ CHECK CONSTRAINT (Нүүрс + Усны эх үүсвэр)
    __table_args__ = (
        CheckConstraint(
            "client_name IN ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB',"
            "'uutsb','negdsen_office','tsagaan_khad','tsetsii',"
            "'naymant','naimdai','malchdyn_hudag',"
            "'hyanalт','tsf','uarp','shine_camp','busad',"
            "'dotood_air','dotood_swab',"
            "'naimdain','maiga','sum','uurhaichin','gallerey','sbutsb')",
            name="ck_sample_client_name",
        ),
    )

    results = db.relationship(
        "AnalysisResult",
        backref="sample",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @property
    def is_mass_ready(self) -> bool:
        """
        Mass gate-д бэлэн эсэхийг буцаана.

        Returns:
            bool: mass_ready талбарын boolean утга
        """
        return bool(self.mass_ready)

    def get_calculations(self) -> 'SampleCalculations':
        """
        Дээжний тооцооллын объект буцаана (lazy loading).

        SampleCalculations объектыг cache хийж хадгална, давтан
        үүсгэхээс сэргийлнэ.

        Returns:
            SampleCalculations: Тооцооллын объект (CV_ar, Ash_dry гэх мэт)

        Example:
            >>> calc = sample.get_calculations()
            >>> ash_dry = calc.ash_dry
            >>> cv_ar = calc.cv_ar
        """
        if not hasattr(self, "_calculations_cache"):
            self._calculations_cache = SampleCalculations(self)
        return self._calculations_cache

    @validates('sample_code')
    def validate_sample_code(self, key, value):
        """
        Sample code-г нормализаци хийх.
        - Нүүрс/Петрограф: Latin үсэг, тоо, тусгай тэмдэгт (uppercase)
        - Ус/Микробиологи: Кирилл + Latin + тоо + тусгай тэмдэгт (хэвээр)
        """
        if value is None:
            return value

        value = str(value).strip()

        # Усны/микробиологийн дээж → Кирилл зөвшөөрнө
        # Кирилл үсэг агуулж байвал усны дээж гэж үзнэ (lab_type тохируулагдаагүй байж болно)
        has_cyrillic = bool(re.search(r'[\u0400-\u04FF]', value))
        if has_cyrillic or (hasattr(self, 'lab_type') and self.lab_type in ('water', 'microbiology')):
            # Кирилл, Latin, тоо, тусгай тэмдэгт зөвшөөрнө
            if not re.match(r'^[\w\u0400-\u04FF\s/.,+\-\"""()³]+$', value):
                invalid_chars = re.findall(r'[^\w\u0400-\u04FF\s/.,+\-\"""()³]', value)
                raise ValueError(
                    f"Дээжний нэрэнд зөвшөөрөгдөөгүй тэмдэгт: {', '.join(set(invalid_chars))}"
                )
            return value

        # Нүүрс/Петрограф → Latin only, uppercase
        value = value.upper()
        if not re.match(r'^[A-Z0-9_\-/.,+ ]+$', value):
            invalid_chars = re.findall(r'[^A-Z0-9_\-/.,+ ]', value)
            raise ValueError(
                f"Дээжний код зөвхөн Latin үсэг агуулах ёстой. "
                f"Буруу тэмдэгт: {', '.join(set(invalid_chars))}"
            )

        return value

    def __repr__(self) -> str:
        return f"<Sample {self.sample_code}>"


# -------------------------
# ҮР ДҮН
# -------------------------
class AnalysisResult(db.Model):
    """
    Шинжилгээний үр дүнгийн модель (ISO 17025 compliance).

    Нэг дээжний нэг шинжилгээний үр дүн, анхны өгөгдөл, статус,
    буцаалтын мэдээллийг хадгална. Audit trail-тэй.

    Attributes:
        id (int): Primary key
        sample_id (int): Foreign key → Sample
        user_id (int): Foreign key → User (шинжилгээ хийсэн хүн)
        analysis_code (str): Шинжилгээний код (ж: "Mad", "Aad", "CV")
        final_result (float): Эцсийн үр дүн (тоон утга)
        raw_data (str): Анхны өгөгдөл (JSON string)
        reason (str): Тайлбар, шалтгаан
        status (str): Төлөв ('pending_review', 'approved', 'rejected', 'reanalysis')
        rejection_category (str): Буцаалтын ангилал (ISO 17025)
        rejection_subcategory (str): Буцаалтын дэд ангилал
        rejection_comment (str): Буцаалтын тайлбар
        error_reason (str): Алдааны шалтгаан (KPI шинжилгээнд)
        created_at (datetime): Үүсгэсэн огноо (Монгол цаг)
        updated_at (datetime): Сүүлд засварласан огноо (Монгол цаг)

    Relationships:
        sample: Many-to-one → Sample (backref)
        logs: One-to-many → AnalysisResultLog (audit trail)

    Status values:
        - pending_review: Шалгалт хүлээж байна
        - approved: Баталгаажсан
        - rejected: Буцаагдсан
        - reanalysis: Дахин шинжилгээ хийх

    Example:
        >>> result = AnalysisResult(
        ...     sample_id=1,
        ...     analysis_code='Mad',
        ...     final_result=8.5,
        ...     status='pending_review'
        ... )
        >>> result.set_raw_data({'m1': 50.0, 'm2': 45.9})
    """
    __tablename__ = "analysis_result"

    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.Integer, db.ForeignKey("sample.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    analysis_code = db.Column(db.String(50), index=True, nullable=False)
    final_result = db.Column(db.Float)
    raw_data = db.Column(db.Text)
    reason = db.Column(db.Text, nullable=True)  # Тайлбар

    status = db.Column(
        db.String(50),
        server_default="pending_review",
        index=True,
        nullable=False,
    )

    # ISO буцаалт
    rejection_category = db.Column(db.String(100))
    rejection_subcategory = db.Column(db.String(100))
    rejection_comment = db.Column(db.String(255))

    # 🛑 KPI Алдааны шалтгаан
    error_reason = db.Column(db.String(50), nullable=True)

    # Монгол цаг
    created_at = db.Column(db.DateTime, index=True, default=now_mn)
    updated_at = db.Column(db.DateTime, default=now_mn, onupdate=now_mn)

    # Composite indexes - түгээмэл query-уудыг хурдасгах
    __table_args__ = (
        db.Index('ix_analysis_result_sample_code', 'sample_id', 'analysis_code'),
        db.Index('ix_analysis_result_sample_status', 'sample_id', 'status'),
        db.Index('ix_analysis_result_code_status', 'analysis_code', 'status'),
        db.Index('ix_analysis_result_user_code', 'user_id', 'analysis_code'),
    )

    logs = db.relationship(
        "AnalysisResultLog",
        back_populates="result",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="desc(AnalysisResultLog.timestamp)",
    )

    # User relationship (шинжилгээ хийсэн хүн)
    user = db.relationship("User", foreign_keys=[user_id], backref="analysis_results")

    # Note: sample relationship нь Sample.results backref-ээс ирнэ

    def set_raw_data(self, data_dict: Dict[str, Any]) -> None:
        """
        Анхны өгөгдлийг JSON болгож хадгална.

        Args:
            data_dict (dict): Анхны өгөгдөл (жишээ: {'m1': 50.0, 'm2': 45.9})

        Example:
            >>> result.set_raw_data({'m1': 50.0, 'm2': 45.9, 'm_dry': 8.5})
        """
        self.raw_data = json.dumps(data_dict)

    def get_raw_data(self) -> Dict[str, Any]:
        """
        JSON string-ийг Python dict болгож буцаана.

        Returns:
            dict: Анхны өгөгдөл. Алдаа гарвал хоосон dict {}.

        Example:
            >>> data = result.get_raw_data()
            >>> m1 = data.get('m1')
        """
        if self.raw_data:
            try:
                return json.loads(self.raw_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def __repr__(self) -> str:
        return f"<AnalysisResult {self.id}>"


# -------------------------
# ШИНЖИЛГЭЭНИЙ ТӨРӨЛ
# -------------------------
class AnalysisType(db.Model):
    """
    Шинжилгээний төрлүүдийн бүртгэл.

    Системд ашиглагдах шинжилгээнүүдийн жагсаалт, дараалал,
    шаардагдах эрхийг хадгална.

    Attributes:
        id (int): Primary key
        code (str): Шинжилгээний өвөрмөц код (ж: "Mad", "Aad", "CV")
        name (str): Шинжилгээний нэр (ж: "Чийг (агаарын)")
        order_num (int): Жагсаалт дахь дараалал (default: 100)
        required_role (str): Шаардлагатай эрх (default: "chemist")

    Example:
        >>> analysis = AnalysisType(
        ...     code='Mad',
        ...     name='Чийг (агаарын)',
        ...     order_num=10,
        ...     required_role='chemist'
        ... )
    """
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    order_num = db.Column(db.Integer, default=100)
    required_role = db.Column(
        db.String(64), default="chemist", index=True, nullable=False
    )
    lab_type = db.Column(db.String(20), default='coal', index=True)  # 'coal', 'petrography', 'water'

    def __repr__(self) -> str:
        return f"<AnalysisType {self.name}>"


# -------------------------
# ПРОФАЙЛ (simple / pattern)
# -------------------------
class AnalysisProfile(db.Model):
    """
    Шинжилгээний профайл (автомат шинжилгээ сонгох).

    Дээжний client_name + sample_type эсвэл sample_code pattern-аар
    автоматаар шинжилгээ сонгох тохиргоо.

    Attributes:
        id (int): Primary key
        profile_type (str): Төрөл ('simple' эсвэл 'pattern')
        client_name (str): Захиалагч (simple тохиргоонд)
        sample_type (str): Дээжний төрөл (simple тохиргоонд)
        pattern (str): Regex загвар (pattern тохиргоонд, ж: "^CC_.*")
        analyses_json (str): Шинжилгээний жагсаалт (JSON string)
        priority (int): Эрэмбэлэх ач холбогдол (default: 50)
        match_rule (str): Давхцах дүрэм ('merge' эсвэл 'replace')

    Profile Types:
        - simple: Client name + Sample type таарах (ж: CHPP + 2 hourly)
        - pattern: Regex sample_code-той таарах (ж: ^CC_.* → CC дээжнүүд)

    Match Rules:
        - merge: Одоо байгаа шинжилгээнүүдтэй нэмж нэгтгэх
        - replace: Бүрэн солих

    Example:
        >>> # Simple profile
        >>> profile = AnalysisProfile(
        ...     profile_type='simple',
        ...     client_name='CHPP',
        ...     sample_type='2 hourly',
        ...     match_rule='replace'
        ... )
        >>> profile.set_analyses(['Mad', 'Aad', 'Vad', 'CV'])
        >>>
        >>> # Pattern profile
        >>> profile2 = AnalysisProfile(
        ...     profile_type='pattern',
        ...     pattern='^CC_.*',
        ...     priority=100
        ... )
    """
    __tablename__ = "analysis_profiles"

    id = db.Column(db.Integer, primary_key=True)

    # Төрөл: 'simple' (Энгийн матриц) эсвэл 'pattern' (Regex)
    profile_type = db.Column(
        db.String(50), nullable=False, index=True, default="simple"
    )

    # Simple тохиргоонд ашиглана
    client_name = db.Column(db.String(200), index=True, nullable=True)
    sample_type = db.Column(db.String(100), index=True, nullable=True)

    # Pattern тохиргоонд ашиглана
    pattern = db.Column(db.String(255), index=True, nullable=True)

    # ✅ analyses_json
    analyses_json = db.Column(db.Text, default="[]")

    priority = db.Column(db.Integer, nullable=True, default=50)

    # match_rule: 'merge' (нэмэх) эсвэл 'replace' (солих)
    match_rule = db.Column(db.String(50), nullable=True, default="merge")

    def set_analyses(self, analysis_codes: List[str]) -> None:
        """
        List-ийг JSON болгож хадгалах.

        Args:
            analysis_codes (list): Шинжилгээний кодуудын жагсаалт
        """
        if isinstance(analysis_codes, list):
            self.analyses_json = json.dumps(analysis_codes)
        else:
            self.analyses_json = "[]"

    def get_analyses(self) -> List[str]:
        """
        JSON string-ийг Python list болгож буцаана.

        Returns:
            list: Шинжилгээний кодуудын жагсаалт
        """
        if not self.analyses_json:
            return []
        try:
            return json.loads(self.analyses_json)
        except (json.JSONDecodeError, TypeError):
            return []

    def get_tokens_as_dict(self) -> Dict[str, List[str]]:
        """
        UI дээр Pattern-ийг гоё харуулах туслах функц.

        Returns:
            dict: Pattern-ийн бүрэлдэхүүн хэсгүүд
        """
        groups = {}
        raw = self.pattern or ""
        try:
            if raw.startswith("^CC_"):
                groups["Prefix"] = ["CC_"]
                others = raw.replace("^CC_", "").replace("$", "")
                groups["Suffix"] = [others] if others else []
            elif "_Dry_" in raw:
                groups["Contains"] = ["_Dry_"]
            elif raw.startswith("^("):
                groups["Complex Start"] = [raw[0:10] + "..."]
            else:
                groups["General"] = [raw]
            return groups
        except (AttributeError, TypeError):
            return {}

    def __repr__(self) -> str:
        if self.profile_type == "simple":
            return f"<Profile Simple: {self.client_name} - {self.sample_type}>"
        else:
            return f"<Profile Pattern: {self.pattern}>"

# =========================================================
# 🛑 ТОНОГ ТӨХӨӨРӨМЖИЙН УДИРДЛАГА (ISO 17025 - 6.4)
# =========================================================


class Equipment(db.Model):
    """
    Тоног төхөөрөмжийн бүртгэл (ISO 17025 - Section 6.4).

    Лабораторийн тоног төхөөрөмжийн бүртгэл, хянах баталгаажуулалт,
    засвар үйлчилгээний мэдээллийг хадгална.

    Attributes:
        id (int): Primary key
        name (str): Багаж, тоног төхөөрөмжийн нэр
        manufacturer (str): Үйлдвэрлэгчийн нэр
        model (str): Марк / модель
        serial_number (str): Албан ёсны сериал дугаар
        lab_code (str): Дотоод лабораторийн дугаар
        quantity (int): Тоо хэмжээ
        location (str): Лаб (ж: Нүүрс лаб, Төв лаб)
        room_number (str): Өрөөний дугаар
        related_analysis (str): Хамааралтай шинжилгээ (ж: "Aad,Mad,Gi")
        status (str): Ашиглалтын байдал
        category (str): Категори (furnace, prep, analysis, balance, water, micro, wtl, other)
        calibration_date (date): Сүүлд баталгаажсан огноо
        calibration_cycle_days (int): Давтамж (хоног)
        next_calibration_date (date): Дараагийн хугацаа
        calibration_note (str): Шалгалт тохируулгын тэмдэглэл
        manufactured_info (str): Үйлдвэрлэсэн огноо (текст)
        commissioned_info (str): Ашиглалтад орсон огноо
        initial_price (float): Анхны үнэ (₮)
        residual_price (float): Үлдэгдэл үнэ (₮)
        remark (str): Бусад тайлбар

    Relationships:
        logs: One-to-many → MaintenanceLog (Засвар үйлчилгээний түүх)
        usages: One-to-many → UsageLog (Ашиглалтын бүртгэл)

    Status values:
        - normal: Хэвийн
        - broken: Эвдэрсэн
        - needs_spare: Сэлбэг хэрэгтэй
        - maintenance: Засварт
        - retired: Ашиглалтаас гарсан / OUT OF SERVICE

    Category values:
        - furnace: Зуух (ж: Муфель зуух)
        - prep: Дээж бэлтгэх (ж: Бутлуур, элгэвч)
        - analysis: Шинжилгээний багаж (ж: XRF, ICP)
        - balance: Жин (ж: Аналитик жин)
        - water: Усны шинжилгээ
        - micro: Микроскоп
        - wtl: WTL лабын багаж
        - other: Бусад

    Example:
        >>> equipment = Equipment(
        ...     name='Муфель зуух',
        ...     manufacturer='Nabertherm',
        ...     model='LT 9/11/P330',
        ...     serial_number='123456',
        ...     category='furnace',
        ...     status='normal'
        ... )
    """
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)

    # Үндсэн мэдээлэл
    name = db.Column(db.String(150), nullable=False)          # Багаж, тоног төхөөрөмжийн нэр
    manufacturer = db.Column(db.String(100))                  # Үйлдвэрлэгчийн нэр
    model = db.Column(db.String(100))                         # Марк / модель
    serial_number = db.Column(db.String(100))                 # Албан ёсны сериал №
    lab_code = db.Column(db.String(50))                       # Дотоод лабораторийн дугаар (Лаб №)
    quantity = db.Column(db.Integer, default=1)               # Тоо хэмжээ

    # Байршил / хэрэглээ
    location = db.Column(db.String(50))                       # Лаб (ж: Нүүрс лаб, Төв/лаб)
    room_number = db.Column(db.String(50))                    # Өрөөний дугаар (ж: 201)
    related_analysis = db.Column(db.String(200))              # Хамааралтай шинжилгээ (Aad,Mad,Gi ...)

    # Ашиглалтын байдал (Excel-ийн 3 багана)
    # normal       -> Хэвийн
    # broken       -> Эвдэрсэн
    # needs_spare  -> Сэлбэг хэрэгтэй
    # maintenance  -> Засварт
    # retired      -> Ашиглалтаас гарсан / OUT OF SERVICE
    status = db.Column(db.String(20), default='normal', index=True)

    # Шалгалт тохируулга / баталгаажуулалт
    calibration_date = db.Column(db.Date)                     # Сүүлд баталгаажсан огноо
    calibration_cycle_days = db.Column(db.Integer, default=365)  # Давтамж (хоног)
    next_calibration_date = db.Column(db.Date)                # Дараагийн хугацаа
    calibration_note = db.Column(db.String(200))              # Шалгалт тохируулгын товч тэмдэглэл (Excel мөр)
    # ✅ ШИНЭ: Категори сонгох багана
    # Values: 'furnace', 'prep', 'analysis', 'water', 'micro', 'wtl', 'balance', 'other'
    category = db.Column(db.String(50), default='other', index=True)

    # Excel дээрх нэмэлт мэдээлэл
    manufactured_info = db.Column(db.String(20))              # Үйлдвэрлэсэн огноо (текст)
    commissioned_info = db.Column(db.String(20))              # Ашиглалтад орсон огноо (текст)
    initial_price = db.Column(db.Float)                       # Анхны үнэ (₮)
    residual_price = db.Column(db.Float)                      # Үлдэгдэл үнэ (₮)
    remark = db.Column(db.String(255))                        # Бусад тайлбар

    # Бүртгэлийн төрөл (7 тусгай бүртгэл + үндсэн)
    # 'main', 'measurement', 'glassware', 'internal_check', 'new_equipment', 'out_of_service', 'spares', 'balances'
    register_type = db.Column(db.String(30), default='main', index=True)
    extra_data = db.Column(db.JSON)                           # Бүртгэл бүрийн тусгай field-үүд

    # Timestamps (audit trail)
    created_at = db.Column(db.DateTime, default=now_mn)
    updated_at = db.Column(db.DateTime, default=now_mn, onupdate=now_mn)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Холбоосууд
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    logs = db.relationship(
        'MaintenanceLog',
        backref='equipment',
        lazy=True,
        order_by="desc(MaintenanceLog.action_date)"
    )
    usages = db.relationship(
        'UsageLog',
        backref='equipment',
        lazy=True
    )


class MaintenanceLog(db.Model):
    """
    Засвар үйлчилгээний түүх (ISO 17025 - Equipment maintenance).

    Тоног төхөөрөмжийн хянах баталгаажуулалт, засвар үйлчилгээ,
    өдөр тутмын шалгалтын бүртгэл.

    Attributes:
        id (int): Primary key
        equipment_id (int): Foreign key → Equipment
        action_date (datetime): Үйлдэл хийсэн огноо/цаг
        action_type (str): Үйлдлийн төрөл (Calibration, Repair, Maintenance, Daily Check)
        description (str): Юу хийсэн, ямар солисон, тэмдэглэл
        performed_by (str): Гүйцэтгэсэн хүн/байгууллага
        certificate_no (str): Гэрчилгээний дугаар
        result (str): Үр дүн (Pass, Fail, Warning)
        file_path (str): Гэрчилгээ хавсралтын зам (optional)

    Example:
        >>> log = MaintenanceLog(
        ...     equipment_id=1,
        ...     action_type='Calibration',
        ...     description='Температур шалгалт хийв',
        ...     performed_by='Гэрчилгээжүүлэх төв',
        ...     result='Pass'
        ... )
    """
    __tablename__ = 'maintenance_logs'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), index=True)

    # Үйлдэл
    action_date = db.Column(db.DateTime, default=now_mn, index=True)
    action_type = db.Column(db.String(50))    # 'Calibration', 'Repair', 'Maintenance', 'Daily Check' ...
    description = db.Column(db.Text)          # Юу хийсэн, ямар солисон, тэмдэглэл
    performed_by = db.Column(db.String(50))   # Гүйцэтгэсэн хүн / байгууллага (гадны)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)  # Дотоод хэрэглэгч
    certificate_no = db.Column(db.String(50)) # Гэрчилгээний № (хэрэв байгаа бол)
    result = db.Column(db.String(20))         # 'Pass', 'Fail', 'Warning' ...

    # Файл хадгалах зам (Гэрчилгээ хавсаргахад зориулав)
    file_path = db.Column(db.String(256), nullable=True)

    # Audit timestamps
    created_at = db.Column(db.DateTime, default=now_mn)  # Системд бүртгэсэн огноо

    # Холбоос
    performed_by_user = db.relationship('User', foreign_keys=[performed_by_id])


class UsageLog(db.Model):
    """
    Багаж ашиглалтын хугацааг бүртгэх.

    Тоног төхөөрөмж хэдэн минут ажилласныг бүртгэж,
    ашиглалтын статистик гаргахад ашиглана.

    Attributes:
        id (int): Primary key
        equipment_id (int): Foreign key → Equipment
        sample_id (int): Foreign key → Sample (optional - аль дээжинд ашигласан)
        start_time (datetime): Эхэлсэн цаг
        end_time (datetime): Дууссан цаг
        duration_minutes (int): Нийт ажилласан минут

    Example:
        >>> usage = UsageLog(
        ...     equipment_id=1,
        ...     sample_id=123,
        ...     start_time=datetime.now(),
        ...     duration_minutes=45
        ... )
    """
    __tablename__ = 'usage_logs'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), index=True)
    # Аль дээжинд ашигласан (optional)
    sample_id = db.Column(
        db.Integer, db.ForeignKey('sample.id', ondelete="SET NULL"),
        nullable=True, index=True
    )

    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)   # Нийт ажилласан минут
    used_by = db.Column(db.String(100), nullable=True)  # Хэрэглэгчийн нэр (хуучин, backward compat)
    used_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)  # Дотоод хэрэглэгч
    purpose = db.Column(db.String(255), nullable=True)  # Ашигласан зорилго

    # Audit timestamp
    created_at = db.Column(db.DateTime, default=now_mn)

    # Холбоос
    used_by_user = db.relationship('User', foreign_keys=[used_by_id])


# -------------------------
# СЭЛБЭГ ХЭРЭГСЭЛ (Spare Parts Inventory)
# -------------------------


class SparePartCategory(db.Model):
    """
    Сэлбэг хэрэгслийн категори - тоног төхөөрөмжөөр ангилал.

    Админ хэрэглэгч нэмж, хасч, засварлах боломжтой.
    """
    __tablename__ = 'spare_part_category'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    name_en = db.Column(db.String(150))
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_mn)

    # Equipment холбоос (optional)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id', ondelete='SET NULL'))
    equipment = db.relationship('Equipment', foreign_keys=[equipment_id])

    def __repr__(self):
        return f"<SparePartCategory {self.code}: {self.name}>"


class SparePart(db.Model):
    """
    Сэлбэг хэрэгслийн бүртгэл - нөөцийн удирдлага.

    Химийн бодисын загвараар хийгдсэн - нөөц, зарцуулалт,
    автомат хасалт, low stock анхааруулга.

    Attributes:
        id (int): Primary key
        name (str): Сэлбэгийн нэр
        name_en (str): Англи нэр
        part_number (str): Part number / Catalog number
        manufacturer (str): Үйлдвэрлэгч
        supplier (str): Нийлүүлэгч
        quantity (float): Одоогийн нөөц
        unit (str): Нэгж (pcs, set, box, roll)
        reorder_level (float): Дахин захиалах түвшин
        unit_price (float): Нэгж үнэ
        storage_location (str): Хадгалах байршил
        compatible_equipment (str): Тохирох тоног төхөөрөмж
        usage_life_months (int): Ашиглалтын хугацаа (сар)
        status (str): Төлөв (active, low_stock, out_of_stock)
    """
    __tablename__ = 'spare_part'

    id = db.Column(db.Integer, primary_key=True)

    # Үндсэн мэдээлэл
    name = db.Column(db.String(200), nullable=False, index=True)
    name_en = db.Column(db.String(200))  # Англи нэр
    part_number = db.Column(db.String(100), index=True)  # Part number
    description = db.Column(db.Text)  # Тайлбар

    # Нийлүүлэгч
    manufacturer = db.Column(db.String(150))
    supplier = db.Column(db.String(150))

    # Нөөц
    quantity = db.Column(db.Float, default=0)
    unit = db.Column(db.String(20), default='pcs')  # pcs, set, box, roll, m, pack
    reorder_level = db.Column(db.Float, default=1)
    unit_price = db.Column(db.Float)  # Нэгж үнэ

    # Хадгалалт
    storage_location = db.Column(db.String(150))

    # Зураг
    image_path = db.Column(db.String(255))  # uploads/spare_parts/filename.jpg

    # Тоног төхөөрөмжтэй холбоос
    compatible_equipment = db.Column(db.Text)  # Тохирох төхөөрөмжүүд (text)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id', ondelete='SET NULL'), index=True)

    # Ашиглалт
    usage_life_months = db.Column(db.Integer)  # Нэг ширхэгийн ашиглалтын хугацаа

    # Огноо
    received_date = db.Column(db.Date)  # Сүүлд авсан огноо
    last_used_date = db.Column(db.Date)  # Сүүлд ашигласан огноо

    # Категори
    category = db.Column(db.String(50), default='general', index=True)
    # general, filter, belt, lamp, fuse, bearing, seal, tube, sensor, other

    # Төлөв
    status = db.Column(db.String(20), default='active', index=True)
    # active, low_stock, out_of_stock

    # Аудит
    created_at = db.Column(db.DateTime, default=now_mn)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    equipment = db.relationship('Equipment', foreign_keys=[equipment_id])
    usages = db.relationship('SparePartUsage', backref='spare_part', lazy='dynamic')
    logs = db.relationship('SparePartLog', backref='spare_part', lazy='dynamic')

    def update_status(self):
        """Нөөцөнд үндэслэн төлөв автоматаар шинэчлэх."""
        if self.quantity <= 0:
            self.status = 'out_of_stock'
        elif self.reorder_level and self.quantity <= self.reorder_level:
            self.status = 'low_stock'
        else:
            self.status = 'active'

    def __repr__(self):
        return f"<SparePart {self.name} ({self.quantity} {self.unit})>"


class SparePartUsage(db.Model):
    """
    Сэлбэг хэрэгслийн зарцуулалт - хэзээ, хаана, хэдийг ашигласан.

    Attributes:
        id (int): Primary key
        spare_part_id (int): Foreign key → SparePart
        equipment_id (int): Аль төхөөрөмжид ашигласан
        maintenance_log_id (int): Аль засварт ашигласан
        quantity_used (float): Ашигласан тоо
        used_by_id (int): Хэн ашигласан
        used_at (datetime): Хэзээ
        purpose (str): Зорилго
        quantity_before (float): Өмнөх нөөц
        quantity_after (float): Дараах нөөц
    """
    __tablename__ = 'spare_part_usage'

    id = db.Column(db.Integer, primary_key=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id', ondelete='CASCADE'),
                              nullable=False, index=True)

    # Хаана ашигласан
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id', ondelete='SET NULL'), index=True)
    maintenance_log_id = db.Column(db.Integer, db.ForeignKey('maintenance_logs.id', ondelete='SET NULL'))

    # Зарцуулалт
    quantity_used = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))

    # Зорилго
    purpose = db.Column(db.String(255))  # Засвар, солих, урьдчилан сэргийлэх г.м.

    # Хэн, хэзээ
    used_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    used_at = db.Column(db.DateTime, default=now_mn)

    # Нөөцийн өөрчлөлт
    quantity_before = db.Column(db.Float)
    quantity_after = db.Column(db.Float)

    # Тэмдэглэл
    notes = db.Column(db.Text)

    # Relationships
    used_by = db.relationship('User', foreign_keys=[used_by_id])
    equipment = db.relationship('Equipment', foreign_keys=[equipment_id])
    maintenance_log = db.relationship('MaintenanceLog', foreign_keys=[maintenance_log_id])

    def __repr__(self):
        return f"<SparePartUsage {self.spare_part_id}: {self.quantity_used}>"


class SparePartLog(db.Model):
    """
    Сэлбэг хэрэгслийн аудит лог - бүх өөрчлөлтийн түүх.

    Attributes:
        id (int): Primary key
        spare_part_id (int): Foreign key → SparePart
        action (str): Үйлдэл (created, received, consumed, adjusted, disposed)
        quantity_change (float): Өөрчлөлтийн хэмжээ (+/-)
        quantity_before (float): Өмнөх нөөц
        quantity_after (float): Дараах нөөц
        user_id (int): Хэн хийсэн
        timestamp (datetime): Хэзээ
        details (str): Нэмэлт мэдээлэл
    """
    __tablename__ = 'spare_part_log'

    id = db.Column(db.Integer, primary_key=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id', ondelete='CASCADE'),
                              nullable=False, index=True)

    # Үйлдэл
    action = db.Column(db.String(30), nullable=False, index=True)
    # created, updated, received, consumed, adjusted, disposed

    # Тоо хэмжээ
    quantity_change = db.Column(db.Float)  # +/- өөрчлөлт
    quantity_before = db.Column(db.Float)
    quantity_after = db.Column(db.Float)

    # Хэн, хэзээ
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    timestamp = db.Column(db.DateTime, default=now_mn, index=True)

    # Нэмэлт
    details = db.Column(db.Text)

    # Relationship
    user = db.relationship('User', foreign_keys=[user_id])

    def __repr__(self):
        return f"<SparePartLog {self.spare_part_id} {self.action}>"


# -------------------------
# ТООЦООЛОЛ
# -------------------------


class SampleCalculations:
    """
    Нүүрсний шинжилгээний тооцоолол хийх класс.

    Дээжний үр дүнгүүдээс (MT, Mad, Aad гэх мэт) өөр өөр нөхцлийн
    үзүүлэлтүүдийг тооцоолно:
    - Air-dried (ad) → Dry basis (d)
    - Air-dried (ad) → As-received (ar)
    - Dry basis (d) → Dry ash-free (daf)

    Parameters:
        sample (Sample): Тооцоолол хийх дээж

    Attributes:
        inputs (dict): {analysis_code: final_result} dictionary
        mt (float): Total moisture (Нийт чийг)
        mad (float): Moisture air-dried (Агаарын чийг)
        aad (float): Ash air-dried (Үнс air-dried)
        vad (float): Volatile matter air-dried
        cv_ad (float): Calorific value air-dried (Дулааны чанар)
        ts_ad (float): Total sulfur air-dried (Нийт хүхэр)
        trd_ad (float): True relative density
        p_ad (float): Phosphorus (Фосфор)
        csn (float): Crucible swelling number
        gi (float): Gray-King index
        x (float), y (float): Нэмэлт үзүүлэлт
        h_ad (float): Hydrogen (Устөрөгч)

    Methods:
        Олон @property методууд:
        - ash_dry, ash_ar: Үнс (dry/ar)
        - volatiles_dry, volatiles_ar, volatiles_daf: Дэгдэмхий бодис
        - fc_ad, fc_dry, fc_ar: Fixed carbon (Баттай нүүрстөрөгч)
        - cv_dry, cv_ar, cv_daf: Calorific value
        - ts_dry, ts_ar: Total sulfur
        - trd_dry, trd_ar: True relative density
        - p_dry, p_ar: Phosphorus

    Example:
        >>> calc = sample.get_calculations()
        >>> ash_dry = calc.ash_dry  # Үнс (dry basis)
        >>> cv_ar = calc.cv_ar      # Дулааны чанар (as-received)
        >>> fc_dry = calc.fc_dry    # Fixed carbon (dry)

    Notes:
        - FLOAT_EPSILON ашиглан нарийвчлалтай харьцуулалт хийнэ
        - Тооцоолол боломжгүй бол None буцаана
        - Lazy loading: sample.get_calculations() ашиглан дуудна
    """

    def __init__(self, sample):
        self.inputs = {res.analysis_code: res.final_result for res in sample.results}
        self.mt = self.inputs.get("MT")
        self.mad = self.inputs.get("Mad")
        self.aad = self.inputs.get("Aad")
        self.vad = self.inputs.get("Vad")
        self.cv_ad = self.inputs.get("CV")
        self.ts_ad = self.inputs.get("TS")
        self.trd_ad = self.inputs.get("TRD")
        self.p_ad = self.inputs.get("P")
        self.csn = self.inputs.get("CSN")
        self.gi = self.inputs.get("Gi")
        self.x = self.inputs.get("X")
        self.y = self.inputs.get("Y")
        self.h_ad = self.inputs.get("Had")
        self.fm = self.inputs.get("FM")

    def _calculate_conversion(self, param_code: str, conversion_type: str) -> Optional[float]:
        """
        Нөхцлийн хувиргалт хийх (ad → dry, ad → ar).

        Args:
            param_code (str): Параметрийн код (Aad, Vad, CV, TS, TRD, P)
            conversion_type (str): Хувиргалтын төрөл ('dry' эсвэл 'ar')

        Returns:
            float, optional: Хувиргасан утга. Тооцоолох боломжгүй бол None.
        """
        param_value_map = {
            "Aad": self.aad,
            "Vad": self.vad,
            "CV": self.cv_ad,
            "TS": self.ts_ad,
            "TRD": self.trd_ad,
            "P": self.p_ad,
        }
        param_ad = param_value_map.get(param_code)
        if param_ad is None or self.mad is None:
            return None
        if conversion_type == "dry":
            if abs(100 - self.mad) < FLOAT_EPSILON:
                return None
            return param_ad * (100 / (100 - self.mad))
        if conversion_type == "ar":
            if self.mt is None:
                return None
            if abs(100 - self.mad) < FLOAT_EPSILON:
                return None
            return param_ad * ((100 - self.mt) / (100 - self.mad))
        return None

    @property
    def ash_dry(self):
        return self._calculate_conversion("Aad", "dry")

    @property
    def ash_ar(self):
        return self._calculate_conversion("Aad", "ar")

    @property
    def volatiles_dry(self):
        return self._calculate_conversion("Vad", "dry")

    @property
    def volatiles_ar(self):
        return self._calculate_conversion("Vad", "ar")

    @property
    def volatiles_daf(self):
        v_dry = self.volatiles_dry
        a_dry = self.ash_dry
        if v_dry is None or a_dry is None:
            return None
        if abs(100 - a_dry) < FLOAT_EPSILON:
            return None
        return v_dry * (100 / (100 - a_dry))

    @property
    def fc_ad(self):
        if self.aad is None or self.vad is None:
            return None
        return 100 - self.aad - self.vad

    @property
    def fc_dry(self):
        a_dry = self.ash_dry
        v_dry = self.volatiles_dry
        if a_dry is None or v_dry is None:
            return None
        return 100 - a_dry - v_dry

    @property
    def fc_ar(self):
        if self.mt is None or self.ash_ar is None or self.volatiles_ar is None:
            return None
        return 100 - self.mt - self.ash_ar - self.volatiles_ar

    @property
    def cv_dry(self):
        return self._calculate_conversion("CV", "dry")

    @property
    def cv_ar(self):
        return self._calculate_conversion("CV", "ar")

    @property
    def cv_daf(self):
        cv_dry_val = self.cv_dry
        ash_dry_val = self.ash_dry
        if cv_dry_val is None or ash_dry_val is None:
            return None
        if abs(100 - ash_dry_val) < FLOAT_EPSILON:
            return None
        return cv_dry_val * (100 / (100 - ash_dry_val))

    @property
    def qnet_ar(self):
        return None

    @property
    def ts_dry(self):
        return self._calculate_conversion("TS", "dry")

    @property
    def ts_ar(self):
        return self._calculate_conversion("TS", "ar")

    @property
    def trd_dry(self):
        return self._calculate_conversion("TRD", "dry")

    @property
    def trd_ar(self):
        return self._calculate_conversion("TRD", "ar")

    @property
    def p_dry(self):
        return self._calculate_conversion("P", "dry")

    @property
    def p_ar(self):
        return self._calculate_conversion("P", "ar")


# -------------------------
# ҮР ДҮН – ЛОГ (Audit)
# -------------------------
class AnalysisResultLog(db.Model):
    """
    Шинжилгээний үр дүнгийн түүх/лог (Audit trail - ISO 17025).

    Үр дүн өөрчлөгдөх бүрийн түүх, хэн юу хийсэн, хэзээ хийсэн,
    буцаалтын шалтгааныг бүртгэнэ. Өөрчлөлтийг буцаах боломжгүй.

    Attributes:
        id (int): Primary key
        timestamp (datetime): Үйлдэл хийсэн огноо/цаг (Монгол цаг)
        user_id (int): Foreign key → User (хэн хийсэн)
        sample_id (int): Foreign key → Sample
        analysis_result_id (int): Foreign key → AnalysisResult
        analysis_code (str): Шинжилгээний код
        action (str): Үйлдэл ('created', 'updated', 'approved', 'rejected', 'reanalysis')
        raw_data_snapshot (str): Анхны өгөгдлийн snapshot (JSON)
        final_result_snapshot (float): Үр дүнгийн snapshot
        rejection_category (str): Буцаалтын ангилал
        rejection_subcategory (str): Буцаалтын дэд ангилал
        reason (str): Шалтгаан, тайлбар
        error_reason (str): Алдааны шалтгаан (KPI)

    Relationships:
        user: Many-to-one → User
        result: Many-to-one → AnalysisResult

    Action values:
        - created: Шинээр үүсгэсэн
        - updated: Засварласан
        - approved: Баталгаажуулсан
        - rejected: Буцаасан
        - reanalysis: Дахин шинжилгээ

    Example:
        >>> log = AnalysisResultLog(
        ...     user_id=current_user.id,
        ...     sample_id=sample.id,
        ...     analysis_result_id=result.id,
        ...     analysis_code='Mad',
        ...     action='approved'
        ... )

    Security:
        - Бүртгэл устгах, засах боломжгүй (audit trail)
        - SET NULL: Sample эсвэл Result устахад log үлдэнэ (sample_id, analysis_result_id = NULL)
        - Hash checksum: Өөрчлөгдсөн эсэхийг шалгах боломжтой
    """
    __tablename__ = "analysis_result_log"

    id = db.Column(db.Integer, primary_key=True)

    # Монгол цаг
    timestamp = db.Column(db.DateTime, index=True, default=now_mn, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("logs", lazy="dynamic"))

    # ✅ SET NULL: Sample устахад log үлдэнэ
    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("sample.id", ondelete="SET NULL"),
        index=True,
        nullable=True,  # NULL болох боломжтой
    )
    # ✅ SET NULL: Result устахад log үлдэнэ
    analysis_result_id = db.Column(
        db.Integer,
        db.ForeignKey("analysis_result.id", ondelete="SET NULL"),
        index=True,
        nullable=True,  # NULL болох боломжтой
    )
    analysis_code = db.Column(db.String(50), index=True, nullable=False)

    # ✅ ШИНЭ: Анхны хадгалсан химичийн ID (хэзээ ч өөрчлөгдөхгүй)
    original_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    original_user = db.relationship("User", foreign_keys=[original_user_id])

    # ✅ ШИНЭ: Анхны хадгалсан цаг (хэзээ ч өөрчлөгдөхгүй)
    original_timestamp = db.Column(db.DateTime, nullable=True)

    # ✅ ШИНЭ: Дээжний код хадгалах (sample устсан ч харагдах)
    sample_code_snapshot = db.Column(db.String(100), nullable=True)

    # ✅ ШИНЭ: Hash checksum (өөрчлөгдсөн эсэхийг шалгах)
    data_hash = db.Column(db.String(64), nullable=True)  # SHA-256

    result = db.relationship(
        "AnalysisResult",
        back_populates="logs",
        foreign_keys=[analysis_result_id],
    )

    action = db.Column(db.String(50), index=True, nullable=False)
    raw_data_snapshot = db.Column(db.Text)
    final_result_snapshot = db.Column(db.Float, nullable=True)

    rejection_category = db.Column(db.String(100))
    rejection_subcategory = db.Column(db.String(100))
    reason = db.Column(db.String(255), nullable=True)

    # 🛑 ШИНЭ: Алдаа гарч байсан хэсэг
    error_reason = db.Column(db.String(50), nullable=True)

    # Composite indexes - audit log query-уудыг хурдасгах
    __table_args__ = (
        db.Index('ix_result_log_code_timestamp', 'analysis_code', 'timestamp'),
        db.Index('ix_result_log_sample_timestamp', 'sample_id', 'timestamp'),
        db.Index('ix_result_log_user_timestamp', 'user_id', 'timestamp'),
    )

    def compute_hash(self) -> str:
        """
        Бүртгэлийн hash-ийг тооцоолох (өөрчлөгдсөн эсэхийг шалгахад ашиглана).
        """
        import hashlib
        data = (
            f"{self.sample_id}|{self.analysis_code}|{self.action}|"
            f"{self.raw_data_snapshot}|{self.final_result_snapshot}|{self.timestamp}"
        )
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def verify_hash(self) -> bool:
        """
        Hash зөв эсэхийг шалгах (өөрчлөгдсөн эсэх).
        """
        if not self.data_hash:
            return True  # Hash байхгүй бол шалгахгүй
        return self.data_hash == self.compute_hash()

    def __repr__(self) -> str:
        return f"<AnalysisResultLog {self.id}: {self.action}>"


# -------------------------
# БОРТОГО / ТОГТМОЛ
# -------------------------
class Bottle(db.Model):
    """
    Бортогын (пикнометр) бүртгэл.

    Нүүрсний үнэн нягтыг тодорхойлоход ашиглагдах бортогын
    бүртгэл, тогтмолын түүх.

    Attributes:
        id (int): Primary key
        serial_no (str): Сериал дугаар (өвөрмөц)
        label (str): Шошго, нэр
        is_active (bool): Идэвхтэй эсэх
        created_by_id (int): Foreign key → User (бүртгэсэн хүн)
        created_at (datetime): Бүртгэсэн огноо

    Relationships:
        constants: One-to-many → BottleConstant (тогтмолын түүх)

    Example:
        >>> bottle = Bottle(
        ...     serial_no='PKN-001',
        ...     label='Бортого #1',
        ...     is_active=True
        ... )
    """
    __tablename__ = "bottle"

    id = db.Column(db.Integer, primary_key=True)
    serial_no = db.Column(db.String(64), unique=True, index=True, nullable=False)
    label = db.Column(db.String(64))
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_by_id = db.Column(
        db.Integer, db.ForeignKey("user.id", name="fk_bottle_created_by_id"), index=True
    )
    created_at = db.Column(db.DateTime, nullable=False, default=now_mn)

    constants = db.relationship(
        "BottleConstant",
        backref="bottle",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )


class BottleConstant(db.Model):
    """
    Бортогын тогтмол (пикнометрийн тогтмол).

    Нэг бортогын тодорхой хугацааны тогтмол утга.
    3 туршилтын дундаж, баталгаажуулалттай.

    Attributes:
        id (int): Primary key
        bottle_id (int): Foreign key → Bottle
        trial_1 (float): 1-р туршилт
        trial_2 (float): 2-р туршилт
        trial_3 (float): 3-р туршилт (optional)
        avg_value (float): Дундаж утга (тогтмол)
        temperature_c (float): Температур (°C, default: 20)
        effective_from (datetime): Хүчинтэй эхлэх огноо
        effective_to (datetime): Хүчинтэй дуусах огноо (optional)
        remarks (str): Тайлбар
        approved_by_id (int): Foreign key → User (баталсан хүн)
        approved_at (datetime): Баталсан огноо
        created_by_id (int): Foreign key → User (үүсгэсэн хүн)
        created_at (datetime): Үүсгэсэн огноо

    Methods:
        is_active_now(ref): Өгөгдсөн огноонд идэвхтэй эсэхийг буцаана

    Example:
        >>> constant = BottleConstant(
        ...     bottle_id=1,
        ...     trial_1=25.1234,
        ...     trial_2=25.1238,
        ...     trial_3=25.1236,
        ...     avg_value=25.1236,
        ...     temperature_c=20.0
        ... )
        >>> constant.is_active_now()
        True

    Notes:
        - MNS 656:2019 стандартын дагуу
        - Tolerance: ±0.0015 (app.constants.BOTTLE_TOLERANCE)
        - Баталгаажаагүй тогтмол ашиглагдахгүй
    """
    __tablename__ = "bottle_constant"

    id = db.Column(db.Integer, primary_key=True)
    bottle_id = db.Column(
        db.Integer, db.ForeignKey("bottle.id"), index=True, nullable=False
    )

    trial_1 = db.Column(db.Float, nullable=False)
    trial_2 = db.Column(db.Float, nullable=False)
    trial_3 = db.Column(db.Float, nullable=True)
    avg_value = db.Column(db.Float, nullable=False, index=True)

    temperature_c = db.Column(db.Float, nullable=False, server_default="20")
    effective_from = db.Column(db.DateTime, nullable=False, default=now_mn)
    effective_to = db.Column(db.DateTime)

    remarks = db.Column(db.String(255))
    approved_by_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_bottle_constant_approved_by_id"),
        index=True,
    )
    approved_at = db.Column(db.DateTime)

    created_by_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_bottle_constant_created_by_id"),
        index=True,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=now_mn)

    def is_active_now(self, ref: Optional[datetime] = None) -> bool:
        """
        Өгөгдсөн огноонд тогтмол идэвхтэй эсэхийг шалгана.

        Args:
            ref (datetime, optional): Шалгах огноо. Default: одоогийн цаг.

        Returns:
            bool: Идэвхтэй бол True, үгүй бол False.
        """
        from datetime import datetime as _dt

        ref = ref or _dt.utcnow()
        if self.effective_to is not None and ref >= self.effective_to:
            return False
        return self.effective_from <= ref and self.approved_at is not None

    def __repr__(self) -> str:
        return (
            f"<BottleConst b#{self.bottle_id} "
            f"avg={self.avg_value:.5f} @ {self.temperature_c}°C>"
        )


# -------------------------
# СИСТЕМИЙН ТОХИРГОО
# -------------------------
class SystemSetting(db.Model):
    """
    Системийн тохиргоо (key-value store).

    Бүх төрлийн системийн тохиргоог уян хатан хадгалах модель.
    Category-оор ангилж, key-value хос хадгална.

    Attributes:
        id (int): Primary key
        category (str): Ангилал (error_reason, unit_abbr, sample_type, гэх мэт)
        key (str): Түлхүүр
        value (str): Утга (JSON string байж болно)
        description (str): Тайлбар (optional)
        is_active (bool): Идэвхтэй эсэх (default: True)
        sort_order (int): Эрэмбэлэх дараалал (default: 0)
        created_at (datetime): Үүсгэсэн огноо
        updated_at (datetime): Сүүлд засварласан огноо
        updated_by_id (int): Foreign key → User (засварласан хүн)

    Table Constraints:
        - UNIQUE constraint: (category, key) хос давхцахгүй

    Example usage:
        >>> # Алдааны шалтгаан
        >>> setting1 = SystemSetting(
        ...     category='error_reason',
        ...     key='sample_prep',
        ...     value='1. Дээж бэлтгэлийн алдаа',
        ...     sort_order=1
        ... )
        >>>
        >>> # Захиалагчийн товчлол
        >>> setting2 = SystemSetting(
        ...     category='unit_abbr',
        ...     key='UHG-Geo',
        ...     value='U'
        ... )
        >>>
        >>> # Дээжний төрөл (JSON array)
        >>> setting3 = SystemSetting(
        ...     category='sample_type',
        ...     key='CHPP',
        ...     value='["2 hourly", "4 hourly", "Daily", "Composite"]'
        ... )

    Common categories:
        - error_reason: KPI алдааны шалтгаан
        - unit_abbr: Захиалагчийн товчлол
        - sample_type: Дээжний төрлүүд (client-ээр)
        - rejection_category: Буцаалтын ангилал
        - rejection_subcategory: Буцаалтын дэд ангилал

    Notes:
        - value талбарт JSON string хадгалж болно
        - is_active=False тохиргоо харагдахгүй (админ удирдана)
        - sort_order-оор жагсаалтын дараалал тохируулна
    """
    __tablename__ = "system_setting"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(64), nullable=False, index=True)  # error_reason, sample_type, гэх мэт
    key = db.Column(db.String(128), nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(256))  # Тайлбар (опционал)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)  # Эрэмбэлэх дараалал

    created_at = db.Column(db.DateTime, nullable=False, default=now_mn)
    updated_at = db.Column(db.DateTime, default=now_mn, onupdate=now_mn)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)

    # Unique constraint: (category, key) хослол давхцахгүй
    __table_args__ = (
        db.UniqueConstraint('category', 'key', name='uq_system_setting_category_key'),
    )

    def __repr__(self) -> str:
        return f"<SystemSetting [{self.category}] {self.key}={self.value[:50]}>"

# -------------------------
# : ХЯНАЛТЫН СТАНДАРТ
# -------------------------


class ControlStandard(db.Model):
    __tablename__ = 'control_standards'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Жнь: CM-2025-Q4
    created_at = db.Column(db.DateTime, default=now_mn) # Хэрэв now_local байхгүй бол datetime.now ашиглана
    is_active = db.Column(db.Boolean, default=False)  # Одоо ашиглагдаж байгаа эсэх

    # Энд бүх параметрийн Mean, SD-г JSON-оор хадгална
    # Жишээ: { "Aad": {"mean": 24.22, "sd": 0.22}, "Mad": {"mean": 10.5, "sd": 0.1} }
    targets = db.Column(db.JSON, default={})

    def __repr__(self):
        return f"<ControlStandard {self.name}>"

# -------------------------
# : GBW СТАНДАРТ
# -------------------------


class GbwStandard(db.Model):
    __tablename__ = 'gbw_standards'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False) # GBW Дугаар (Batch No)
    targets = db.Column(db.JSON, nullable=False)    # { 'Mad': {'mean': 1.2, 'sd': 0.1}, ... }
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<GBW {self.name}>'


# -------------------------
# AUDIT LOG
# -------------------------
class AuditLog(db.Model):
    """
    Аудитын лог - бүх чухал үйлдлүүдийг бүртгэнэ.

    Бүртгэх үйлдлүүд:
    - Нэвтрэх/гарах (login, logout)
    - Дээж устгах (delete_sample)
    - Хэрэглэгч үүсгэх/устгах (create_user, delete_user)
    - Тохиргоо өөрчлөх (update_settings)
    - Үр дүн баталгаажуулах/буцаах (approve_result, reject_result)

    ISO 17025 compliance:
    - Бүх үйлдлийг мөрдөн шалгах боломжтой
    - Хэн, хэзээ, юу хийсэн эсэх бүртгэгдэнэ
    """
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=now_mn, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    action = db.Column(db.String(50), nullable=False, index=True)  # login, logout, delete_sample, etc
    resource_type = db.Column(db.String(50), index=True)  # Sample, User, Equipment, AnalysisResult
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON хэлбэрээр дэлгэрэнгүй мэдээлэл
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(200))

    # Relationship
    user = db.relationship("User", backref="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by user_id={self.user_id} at {self.timestamp}>"


# -------------------------
# ЗАСВАР АРГА ХЭМЖЭЭ (CAPA)
# -------------------------
class CorrectiveAction(db.Model):
    """
    Засвар арга хэмжээ (Corrective and Preventive Actions).

    ISO 17025 - Clause 8.7: Бүх зөрчил, гомдол, дотоод хяналтын үр дүнд
    засвар арга хэмжээ авах шаардлагатай.
    """
    __tablename__ = "corrective_action"

    id = db.Column(db.Integer, primary_key=True)
    ca_number = db.Column(db.String(50), unique=True, nullable=False, index=True)  # CA-2025-001

    # Асуудлын мэдээлэл
    issue_date = db.Column(db.Date, nullable=False, default=now_mn)
    issue_source = db.Column(db.String(100))  # Internal audit, Customer complaint, PT, Equipment
    issue_description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='Minor')  # Critical, Major, Minor

    # Шалтгааны шинжилгээ
    root_cause = db.Column(db.Text)  # 5 Why, Fishbone analysis
    root_cause_method = db.Column(db.String(100))  # 5 Whys, Fishbone, Pareto

    # Арга хэмжээ
    corrective_action = db.Column(db.Text)  # Засах үйлдэл
    preventive_action = db.Column(db.Text)  # Урьдчилан сэргийлэх
    responsible_person_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    target_date = db.Column(db.Date)
    completion_date = db.Column(db.Date)

    # Баталгаажуулалт
    verification_method = db.Column(db.Text)
    verification_date = db.Column(db.Date)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    effectiveness = db.Column(db.String(20))  # Effective, Not effective, Pending

    # Төлөв
    status = db.Column(db.String(20), default='open', index=True)  # open, in_progress, closed
    notes = db.Column(db.Text)

    # Relationships
    responsible_person = db.relationship('User', foreign_keys=[responsible_person_id], backref='assigned_capas')
    verified_by = db.relationship('User', foreign_keys=[verified_by_id], backref='verified_capas')

    def __repr__(self):
        return f"<CorrectiveAction {self.ca_number} - {self.status}>"


# -------------------------
# ЧАДАМЖИЙН ШАЛГАЛТ (Proficiency Testing)
# -------------------------
class ProficiencyTest(db.Model):
    """
    Чадамжийн шалгалт (Proficiency Testing).

    ISO 17025 - Clause 7.7.2: Лаборатори PT программд оролцож,
    үр дүнгээ гадны байгууллагатай харьцуулж чадвараа батлах.
    """
    __tablename__ = "proficiency_test"

    id = db.Column(db.Integer, primary_key=True)

    # PT мэдээлэл
    pt_provider = db.Column(db.String(150))  # ASTM, ISO LEAP, NIST
    pt_program = db.Column(db.String(100))  # Coal PT-2025
    round_number = db.Column(db.String(50))
    sample_code = db.Column(db.String(100))  # PT дээжний код

    # Үр дүн
    analysis_code = db.Column(db.String(50), index=True)
    our_result = db.Column(db.Float)
    assigned_value = db.Column(db.Float)  # Зөвт утга
    uncertainty = db.Column(db.Float)
    z_score = db.Column(db.Float)  # Performance indicator

    # Үнэлгээ
    performance = db.Column(db.String(30))  # satisfactory, questionable, unsatisfactory

    # Огноо
    received_date = db.Column(db.Date)
    test_date = db.Column(db.Date, index=True)
    report_date = db.Column(db.Date)

    # Хавсралт
    certificate_file = db.Column(db.String(255))
    notes = db.Column(db.Text)

    # Хэн шинжилсэн
    tested_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tested_by = db.relationship('User', backref='pt_tests')

    def __repr__(self):
        return f"<PT {self.pt_program} - {self.analysis_code} Z={self.z_score}>"


# -------------------------
# ОРЧНЫ НӨХЦЛИЙН ХЯНАЛТ
# -------------------------
class EnvironmentalLog(db.Model):
    """
    Орчны нөхцлийн бүртгэл (Environmental Monitoring).

    ISO 17025 - Clause 6.3.3: Лабораторийн орчны нөхцөл
    (температур, чийг) үр дүнд нөлөөлж болох тул хянах.
    """
    __tablename__ = "environmental_log"

    id = db.Column(db.Integer, primary_key=True)
    log_date = db.Column(db.DateTime, default=now_mn, index=True)

    # Байршил
    location = db.Column(db.String(100))  # Sample storage, Analysis room, Furnace room

    # Хэмжилт
    temperature = db.Column(db.Float)  # °C
    humidity = db.Column(db.Float)  # %
    pressure = db.Column(db.Float)  # kPa (optional)

    # Хэвийн хязгаар
    temp_min = db.Column(db.Float)  # Доод хязгаар
    temp_max = db.Column(db.Float)  # Дээд хязгаар
    humidity_min = db.Column(db.Float)
    humidity_max = db.Column(db.Float)

    # Хэвийн эсэх
    within_limits = db.Column(db.Boolean, default=True)

    # Бүртгэсэн хүн
    recorded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recorded_by = db.relationship('User', backref='env_logs')

    notes = db.Column(db.Text)

    def __repr__(self):
        return f"<EnvLog {self.location} T={self.temperature}°C RH={self.humidity}%>"


# -------------------------
# ЧАНАРЫН ХЯНАЛТЫН ГРАФИК (Control Chart)
# -------------------------
class QCControlChart(db.Model):
    """
    Чанарын хяналтын график өгөгдөл.

    ISO 17025 - Clause 7.7.1: QC дээж тогтмол шинжлэж,
    control chart-аар системийн чанарыг хянах.
    """
    __tablename__ = "qc_control_chart"

    id = db.Column(db.Integer, primary_key=True)

    # QC дээж
    analysis_code = db.Column(db.String(50), index=True)
    qc_sample_name = db.Column(db.String(100))  # QC Coal Standard A

    # Хяналтын хязгаар
    target_value = db.Column(db.Float)  # Зорилтот утга
    ucl = db.Column(db.Float)  # Upper control limit (target + 2*sd)
    lcl = db.Column(db.Float)  # Lower control limit (target - 2*sd)
    usl = db.Column(db.Float)  # Upper spec limit (optional)
    lsl = db.Column(db.Float)  # Lower spec limit

    # Хэмжилт
    measurement_date = db.Column(db.Date, index=True)
    measured_value = db.Column(db.Float)
    in_control = db.Column(db.Boolean, default=True)  # UCL/LCL дотор уу?

    # Operator
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    operator = db.relationship('User', backref='qc_measurements')

    # Тэмдэглэл
    notes = db.Column(db.Text)

    def __repr__(self):
        return f"<QC {self.analysis_code} - {self.qc_sample_name} = {self.measured_value}>"


# -------------------------
# ҮЙЛЧЛҮҮЛЭГЧИЙН ГОМДОЛ
# -------------------------
class CustomerComplaint(db.Model):
    """
    Үйлчлүүлэгчийн гомдол (Customer Complaints).

    ISO 17025 - Clause 8.9: Бүх гомдлыг бүртгэж, шалтгааныг
    олж, шийдвэрлэх ёстой.
    """
    __tablename__ = "customer_complaint"

    id = db.Column(db.Integer, primary_key=True)
    complaint_no = db.Column(db.String(50), unique=True, index=True)  # COMP-2025-001

    # Үйлчлүүлэгч
    client_name = db.Column(db.String(200))
    contact_person = db.Column(db.String(100))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(50))

    # Гомдол
    complaint_date = db.Column(db.Date, nullable=False, default=now_mn)
    complaint_type = db.Column(db.String(100))  # Turnaround time, Result accuracy, Service quality
    description = db.Column(db.Text, nullable=False)
    related_sample_id = db.Column(db.Integer, db.ForeignKey('sample.id', ondelete="SET NULL"))

    # Шийдвэрлэлт
    investigated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    investigation_findings = db.Column(db.Text)
    resolution = db.Column(db.Text)
    resolution_date = db.Column(db.Date)

    # Үйлчлүүлэгчийн хариу
    customer_notified = db.Column(db.Boolean, default=False)
    customer_satisfied = db.Column(db.Boolean)
    capa_created = db.Column(db.Boolean, default=False)  # CAPA үүссэн үү
    capa_id = db.Column(db.Integer, db.ForeignKey('corrective_action.id'))

    # Төлөв
    status = db.Column(db.String(20), default='received', index=True)  # received, investigating, resolved, closed

    # Relationships
    related_sample = db.relationship('Sample', backref='complaints')
    investigated_by = db.relationship('User', backref='investigated_complaints')
    related_capa = db.relationship('CorrectiveAction', backref='source_complaints')

    def __repr__(self):
        return f"<Complaint {self.complaint_no} - {self.status}>"


# -------------------------
# САРЫН ТӨЛӨВЛӨГӨӨ (Monthly Plan)
# -------------------------
class MonthlyPlan(db.Model):
    """
    Лабораторийн сарын төлөвлөгөө.

    Ахлах химич долоо хоног бүрийн төлөвлөгөөг оруулж,
    гүйцэтгэлтэй харьцуулах боломжтой.

    Attributes:
        year (int): Он
        month (int): Сар (1-12)
        week (int): Долоо хоног (1-5)
        client_name (str): Нэгж (CONSIGNOR)
        sample_type (str): Дээжийн төрөл
        planned_count (int): Төлөвлөсөн тоо
        created_by_id (int): Үүсгэсэн хэрэглэгч
        created_at (datetime): Үүсгэсэн огноо
        updated_at (datetime): Шинэчилсэн огноо
    """
    __tablename__ = "monthly_plan"

    id = db.Column(db.Integer, primary_key=True)

    # Хугацаа
    year = db.Column(db.Integer, nullable=False, index=True)
    month = db.Column(db.Integer, nullable=False, index=True)  # 1-12
    week = db.Column(db.Integer, nullable=False)  # 1-5

    # Нэгж ба төрөл
    client_name = db.Column(db.String(50), nullable=False, index=True)  # CONSIGNOR
    sample_type = db.Column(db.String(100), nullable=False)  # SAMPLE TYPE

    # Төлөвлөгөө
    planned_count = db.Column(db.Integer, default=0)

    # Audit
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=now_mn)
    updated_at = db.Column(db.DateTime, default=now_mn, onupdate=now_mn)

    # Relationship
    created_by = db.relationship('User', backref='monthly_plans')

    # Unique constraint: нэг долоо хоногт нэг нэгж+төрлийн төлөвлөгөө
    __table_args__ = (
        db.UniqueConstraint('year', 'month', 'week', 'client_name', 'sample_type',
                           name='uq_monthly_plan_entry'),
    )

    def __repr__(self):
        return (
            f"<MonthlyPlan {self.year}-{self.month} W{self.week} "
            f"{self.client_name}/{self.sample_type}: {self.planned_count}>"
        )


class StaffSettings(db.Model):
    """
    Ажилтны тооны тохиргоо (сараар).
    Дээж бэлтгэгч, химичийн тоог хадгална.
    """
    __tablename__ = "staff_settings"

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    preparers = db.Column(db.Integer, default=6)  # Дээж бэлтгэгчийн тоо
    chemists = db.Column(db.Integer, default=10)  # Химичийн тоо
    updated_at = db.Column(db.DateTime, default=now_mn, onupdate=now_mn)

    __table_args__ = (
        db.UniqueConstraint('year', 'month', name='uq_staff_settings_month'),
    )


# -------------------------
# ЧАТ СИСТЕМ
# -------------------------
class ChatMessage(db.Model):
    """
    Химич ↔ Ахлах чат мессеж.
    Real-time харилцааны түүхийг хадгална.
    """
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)  # null = broadcast
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=now_mn, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    message_type = db.Column(db.String(20), default='text')  # text, image, file, sample, urgent

    # Файл хавсралт
    file_url = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)  # bytes

    # Яаралтай мессеж
    is_urgent = db.Column(db.Boolean, default=False)

    # Дээж/Шинжилгээ холбох
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id', ondelete="SET NULL"), nullable=True)

    # Устгах (soft delete)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Broadcast мессеж
    is_broadcast = db.Column(db.Boolean, default=False)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    sample = db.relationship('Sample', backref='chat_messages')

    def __repr__(self):
        return f"<ChatMessage {self.id}: {self.sender_id} → {self.receiver_id}>"

    def to_dict(self):
        """JSON serialization"""
        result = {
            'id': self.id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.username if self.sender else None,
            'receiver_id': self.receiver_id,
            'receiver_name': self.receiver.username if self.receiver else None,
            'message': self.message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'is_read': self.read_at is not None,
            'message_type': self.message_type,
            'is_urgent': self.is_urgent,
            'is_broadcast': self.is_broadcast,
            'is_deleted': self.is_deleted,
            # Файл талбарууд (top-level for JS)
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'sample_id': self.sample_id
        }
        # Файл мэдээлэл (nested object)
        if self.file_url:
            result['file'] = {
                'url': self.file_url,
                'name': self.file_name,
                'size': self.file_size
            }
        # Дээж мэдээлэл
        if self.sample_id and self.sample:
            result['sample'] = {
                'id': self.sample.id,
                'code': self.sample.sample_code,
                'type': self.sample.sample_type
            }
        return result


class UserOnlineStatus(db.Model):
    """
    Хэрэглэгчийн онлайн статус.
    WebSocket холболттой үед шинэчлэгдэнэ.
    """
    __tablename__ = "user_online_status"

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=now_mn)
    socket_id = db.Column(db.String(100), nullable=True)  # Current socket session ID

    # Relationship
    user = db.relationship('User', backref=db.backref('online_status', uselist=False))

    def __repr__(self):
        status = "online" if self.is_online else "offline"
        return f"<UserOnlineStatus {self.user_id}: {status}>"
# -------------------------
# ЛИЦЕНЗ (License Protection)
# -------------------------


class SystemLicense(db.Model):
    """
    Системийн лиценз.
    Програмыг хамгаалж, хугацаа, hardware-д холбоно.
    """
    __tablename__ = 'system_license'

    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(128), unique=True, nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    company_code = db.Column(db.String(50))

    # Хугацаа
    issued_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=False)

    # Хязгаарлалт
    max_users = db.Column(db.Integer, default=10)
    max_samples_per_month = db.Column(db.Integer, default=10000)

    # Hardware binding
    hardware_id = db.Column(db.String(128))
    allowed_hardware_ids = db.Column(db.Text)  # JSON array

    # Төлөв
    is_active = db.Column(db.Boolean, default=True)
    is_trial = db.Column(db.Boolean, default=False)

    # Шалгалт
    last_check = db.Column(db.DateTime)
    check_count = db.Column(db.Integer, default=0)
    tampering_detected = db.Column(db.Boolean, default=False)
    tampering_details = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_valid(self):
        """Лиценз хүчинтэй эсэх"""
        if not self.is_active:
            return False
        if self.tampering_detected:
            return False
        if datetime.utcnow() > self.expiry_date:
            return False
        return True

    @property
    def days_remaining(self):
        """Үлдсэн хоног"""
        if datetime.utcnow() > self.expiry_date:
            return 0
        delta = self.expiry_date - datetime.utcnow()
        return max(0, delta.days)

    @property
    def is_expiring_soon(self):
        """30 хоногоос бага үлдсэн эсэх"""
        return 0 < self.days_remaining <= 30

    def __repr__(self):
        return f'<License {self.company_name} - expires {self.expiry_date}>'


class LicenseLog(db.Model):
    """Лицензийн лог - бүх үйлдлийг бүртгэх"""
    __tablename__ = 'license_log'

    id = db.Column(db.Integer, primary_key=True)
    license_id = db.Column(db.Integer, db.ForeignKey('system_license.id'))

    event_type = db.Column(db.String(50))
    event_details = db.Column(db.Text)
    hardware_id = db.Column(db.String(128))
    ip_address = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    license = db.relationship('SystemLicense', backref='logs')


# -------------------------
# WASHABILITY / THEORETICAL YIELD
# -------------------------
class WashabilityTest(db.Model):
    """
    Баяжигдах чанарын шинжилгээ (Washability Test / Float-Sink Analysis).

    Нүүрсний баяжуулах үйлдвэрийн theoretical yield тооцоолоход ашиглана.
    Float-sink аргаар өөр өөр нягттай фракцуудад хуваан шинжилнэ.

    Excel импортоос болон LIMS WTL нэгжээс дата авна.
    """
    __tablename__ = "washability_test"

    id = db.Column(db.Integer, primary_key=True)

    # Дээжийн мэдээлэл
    lab_number = db.Column(db.String(50), index=True)  # #25_45
    sample_name = db.Column(db.String(100), index=True)  # PR12_B23_ST129_4A
    sample_date = db.Column(db.Date, index=True)
    report_date = db.Column(db.Date)
    consignor = db.Column(db.String(100))  # Process engineers team

    # Анхны нүүрсний шинжилгээ (Raw Coal)
    initial_mass_kg = db.Column(db.Float)
    raw_tm = db.Column(db.Float)  # Total Moisture %
    raw_im = db.Column(db.Float)  # Inherent Moisture %
    raw_ash = db.Column(db.Float)  # Ash ad %
    raw_vol = db.Column(db.Float)  # Volatiles ad %
    raw_sulphur = db.Column(db.Float)  # Sulphur ad %
    raw_csn = db.Column(db.Float)  # CSN
    raw_gi = db.Column(db.Float)  # G index
    raw_trd = db.Column(db.Float)  # TRD

    # LIMS холбоос (хэрвээ WTL нэгжээс ирсэн бол)
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id', ondelete='SET NULL'))
    sample = db.relationship('Sample', backref='washability_tests')

    # Импорт мэдээлэл
    source = db.Column(db.String(50), default='excel')  # 'excel', 'lims'
    excel_filename = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=now_mn)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User', backref='washability_tests')

    # Relationships
    fractions = db.relationship('WashabilityFraction', back_populates='test',
                                cascade='all, delete-orphan', lazy='dynamic')
    yields = db.relationship('TheoreticalYield', back_populates='test',
                             cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f"<WashabilityTest {self.lab_number} - {self.sample_name}>"


class WashabilityFraction(db.Model):
    """
    Float-sink фракцийн дата.

    Size fraction + Density fraction = Individual data
    Жишээ: -50+16mm, density 1.3-1.325 -> Mass, Ash, Vol, etc.
    """
    __tablename__ = "washability_fraction"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('washability_test.id', ondelete='CASCADE'),
                        nullable=False, index=True)

    # Size fraction
    size_fraction = db.Column(db.String(20))  # -50+16, -16+8, -8+2, -2+0.5, -0.5+0.25
    size_upper = db.Column(db.Float)  # 50
    size_lower = db.Column(db.Float)  # 16
    size_mass_kg = db.Column(db.Float)  # Энэ size fraction-ийн нийт жин

    # Density fraction
    density_sink = db.Column(db.Float)  # 1.25
    density_float = db.Column(db.Float)  # 1.3

    # Individual data
    mass_gram = db.Column(db.Float)
    mass_percent = db.Column(db.Float)  # Энэ size fraction дотор эзлэх %
    im_percent = db.Column(db.Float)  # Inherent Moisture
    ash_ad = db.Column(db.Float)  # Ash, ad %
    vol_ad = db.Column(db.Float)  # Volatiles, ad %
    sulphur_ad = db.Column(db.Float)  # Sulphur, ad %
    csn = db.Column(db.Float)  # CSN

    # Cumulative values (тооцоологдсон)
    cumulative_yield = db.Column(db.Float)  # Нийт гарц хүртэл
    cumulative_ash = db.Column(db.Float)  # Нийлмэл үнслэг

    test = db.relationship('WashabilityTest', back_populates='fractions')

    def __repr__(self):
        return f"<Fraction {self.size_fraction} F{self.density_float} Y={self.mass_percent}%>"


class TheoreticalYield(db.Model):
    """
    Онолын гарц тооцоолол (Theoretical Yield).

    Тодорхой зорилтот үнслэгт (target ash) хүрэхэд хэдэн % гарц гарахыг тооцоолно.
    Washability муруйгаас interpolation хийж олно.
    """
    __tablename__ = "theoretical_yield"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('washability_test.id', ondelete='CASCADE'),
                        nullable=False, index=True)

    # Тооцооллын параметрүүд
    target_ash = db.Column(db.Float, nullable=False)  # Зорилтот үнслэг (жишээ: 10.5%)
    size_fraction = db.Column(db.String(20))  # Аль size fraction-д? (эсвэл 'all' бүгдэд)

    # Үр дүн
    theoretical_yield = db.Column(db.Float)  # Онолын гарц %
    actual_yield = db.Column(db.Float)  # Үйлдвэрийн бодит гарц (хэрвээ байвал)
    recovery_efficiency = db.Column(db.Float)  # actual / theoretical * 100

    # NGM (Near Gravity Material) - баяжуулахад хэцүү хэсэг
    ngm_plus_01 = db.Column(db.Float)  # ±0.1 density дахь %
    ngm_plus_02 = db.Column(db.Float)  # ±0.2 density дахь %

    # Separation density
    separation_density = db.Column(db.Float)  # Ялгаралтын нягт (target ash-д хүрэх)

    calculated_at = db.Column(db.DateTime, default=now_mn)
    notes = db.Column(db.Text)

    test = db.relationship('WashabilityTest', back_populates='yields')

    def __repr__(self):
        return f"<TheoreticalYield Ash={self.target_ash}% -> Yield={self.theoretical_yield}%>"


class PlantYield(db.Model):
    """
    Үйлдвэрийн бодит гарц (Plant Actual Yield).

    Онолын гарцтай харьцуулахад ашиглана.
    """
    __tablename__ = "plant_yield"

    id = db.Column(db.Integer, primary_key=True)

    # Огноо/хугацаа
    production_date = db.Column(db.Date, nullable=False, index=True)
    shift = db.Column(db.String(20))  # Day, Night, etc.

    # Нүүрсний төрөл/эх үүсвэр
    coal_source = db.Column(db.String(100))  # Pit, Seam
    product_type = db.Column(db.String(50))  # HCC, SSCC, MASHCC

    # Оролт/Гаралт
    feed_tonnes = db.Column(db.Float)  # Оролтын хэмжээ (тонн)
    product_tonnes = db.Column(db.Float)  # Гаралтын хэмжээ (тонн)
    actual_yield = db.Column(db.Float)  # product / feed * 100

    # Чанарын үзүүлэлт
    feed_ash = db.Column(db.Float)  # Оролтын үнслэг
    product_ash = db.Column(db.Float)  # Гаралтын үнслэг

    # Washability тесттэй холбох (хэрвээ байвал)
    washability_test_id = db.Column(db.Integer, db.ForeignKey('washability_test.id', ondelete='SET NULL'))
    washability_test = db.relationship('WashabilityTest', backref='plant_yields')

    # Харьцуулалт
    theoretical_yield = db.Column(db.Float)  # Онолын гарц (washability-ээс)
    recovery_efficiency = db.Column(db.Float)  # actual / theoretical * 100

    created_at = db.Column(db.DateTime, default=now_mn)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f"<PlantYield {self.production_date} {self.product_type} = {self.actual_yield}%>"


# -------------------------
# ХИМИЙН БОДИС
# -------------------------
class Chemical(db.Model):
    """
    Химийн бодисын бүртгэл (ISO 17025 - Reagent Management).

    Лабораторид ашиглагдах химийн бодис, урвалж, индикатор,
    стандартуудын бүртгэл, нөөц, хугацааны хяналт.

    Attributes:
        id (int): Primary key
        name (str): Химийн бодисын нэр
        cas_number (str): CAS дугаар (Chemical Abstracts Service)
        formula (str): Химийн томъёо
        manufacturer (str): Үйлдвэрлэгч
        supplier (str): Нийлүүлэгч
        catalog_number (str): Каталогийн дугаар
        lot_number (str): Багц дугаар (Lot/Batch)
        grade (str): Зэрэг (AR, CP, HPLC, ACS гэх мэт)
        quantity (float): Одоогийн тоо хэмжээ
        unit (str): Хэмжих нэгж (mL, g, L, kg)
        reorder_level (float): Дахин захиалах түвшин
        received_date (date): Хүлээн авсан огноо
        expiry_date (date): Дуусах хугацаа
        opened_date (date): Нээсэн огноо
        storage_location (str): Хадгалах байршил
        storage_conditions (str): Хадгалах нөхцөл
        hazard_class (str): Аюулын ангилал
        sds_file_path (str): SDS файлын зам
        lab_type (str): Лабын төрөл (coal, water, microbiology, petrography, all)
        category (str): Ангилал (acid, base, solvent, indicator, standard, media, other)
        status (str): Төлөв (active, low_stock, expired, empty, disposed)

    Status values:
        - active: Хэвийн ашиглагдаж буй
        - low_stock: Бага нөөцтэй
        - expired: Хугацаа дууссан
        - empty: Дууссан
        - disposed: Устгагдсан

    Category values:
        - acid: Хүчил
        - base: Суурь
        - solvent: Уусгагч
        - indicator: Индикатор
        - standard: Стандарт уусмал
        - media: Орчин (микробиологид)
        - buffer: Буфер уусмал
        - salt: Давс
        - other: Бусад

    Example:
        >>> chemical = Chemical(
        ...     name='Hydrochloric Acid',
        ...     formula='HCl',
        ...     cas_number='7647-01-0',
        ...     quantity=2500,
        ...     unit='mL',
        ...     category='acid',
        ...     lab_type='coal'
        ... )
    """
    __tablename__ = 'chemical'

    id = db.Column(db.Integer, primary_key=True)

    # Үндсэн мэдээлэл
    name = db.Column(db.String(200), nullable=False, index=True)
    cas_number = db.Column(db.String(50))                       # CAS Registry Number
    formula = db.Column(db.String(100))                         # Химийн томъёо

    # Нийлүүлэлтийн мэдээлэл
    manufacturer = db.Column(db.String(150))                    # Үйлдвэрлэгч
    supplier = db.Column(db.String(150))                        # Нийлүүлэгч
    catalog_number = db.Column(db.String(100))                  # Каталогийн №
    lot_number = db.Column(db.String(100))                      # Багц № (Lot/Batch)
    grade = db.Column(db.String(50))                            # AR, CP, HPLC, ACS

    # Тоо хэмжээ
    quantity = db.Column(db.Float, default=0)                   # Одоогийн тоо хэмжээ
    unit = db.Column(db.String(20), default='mL')               # mL, g, L, kg, pcs
    reorder_level = db.Column(db.Float)                         # Дахин захиалах түвшин

    # Огноо
    received_date = db.Column(db.Date)                          # Хүлээн авсан огноо
    expiry_date = db.Column(db.Date, index=True)                # Дуусах хугацаа
    opened_date = db.Column(db.Date)                            # Нээсэн огноо

    # Хадгалалт
    storage_location = db.Column(db.String(100))                # Байршил (шүүгээ, тавиур)
    storage_conditions = db.Column(db.String(200))              # Нөхцөл (температур, гэх мэт)

    # Аюулгүй байдал
    hazard_class = db.Column(db.String(100))                    # Аюулын ангилал
    sds_file_path = db.Column(db.String(255))                   # Safety Data Sheet файл

    # Ангилал
    lab_type = db.Column(db.String(30), default='all', index=True)  # coal, water, microbiology, petrography, all
    category = db.Column(db.String(30), default='other', index=True)  # acid, base, solvent, indicator, standard, media, other

    # Төлөв
    status = db.Column(db.String(20), default='active', index=True)  # active, low_stock, expired, empty, disposed

    # Тэмдэглэл
    notes = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=now_mn)
    updated_at = db.Column(db.DateTime, default=now_mn, onupdate=now_mn)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    # Relationships
    usages = db.relationship('ChemicalUsage', backref='chemical', lazy='dynamic',
                             cascade='all, delete-orphan')
    logs = db.relationship('ChemicalLog', backref='chemical', lazy='dynamic',
                           cascade='all, delete-orphan')
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def update_status(self):
        """Нөөц болон хугацаанд үндэслэн төлөвийг автоматаар шинэчлэх."""
        from datetime import date
        today = date.today()

        if self.status == 'disposed':
            return  # Устгагдсан бол өөрчлөхгүй

        if self.quantity <= 0:
            self.status = 'empty'
        elif self.expiry_date and self.expiry_date < today:
            self.status = 'expired'
        elif self.reorder_level and self.quantity <= self.reorder_level:
            self.status = 'low_stock'
        else:
            self.status = 'active'

    def __repr__(self):
        return f"<Chemical {self.name} ({self.quantity} {self.unit})>"


class ChemicalUsage(db.Model):
    """
    Химийн бодисын хэрэглээний бүртгэл.

    Хэрэглэсэн тоо хэмжээ, зорилго, шинжилгээтэй холбох.

    Attributes:
        id (int): Primary key
        chemical_id (int): Foreign key → Chemical
        quantity_used (float): Хэрэглэсэн тоо хэмжээ
        unit (str): Нэгж
        sample_id (int): Foreign key → Sample (optional)
        analysis_code (str): Шинжилгээний код (optional)
        purpose (str): Зорилго
        used_by_id (int): Foreign key → User
        used_at (datetime): Хэрэглэсэн огноо/цаг
        quantity_before (float): Хэрэглэхээс өмнөх тоо хэмжээ
        quantity_after (float): Хэрэглэсний дараах тоо хэмжээ

    Example:
        >>> usage = ChemicalUsage(
        ...     chemical_id=1,
        ...     quantity_used=50,
        ...     unit='mL',
        ...     purpose='Aad шинжилгээ',
        ...     used_by_id=current_user.id
        ... )
    """
    __tablename__ = 'chemical_usage'

    id = db.Column(db.Integer, primary_key=True)
    chemical_id = db.Column(db.Integer, db.ForeignKey('chemical.id'), nullable=False, index=True)

    # Хэрэглээний мэдээлэл
    quantity_used = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))

    # Шинжилгээтэй холбох (optional)
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id', ondelete='SET NULL'))
    analysis_code = db.Column(db.String(50))

    # Зорилго, тайлбар
    purpose = db.Column(db.String(255))

    # Хэрэглэгч
    used_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    used_at = db.Column(db.DateTime, default=now_mn, index=True)

    # Нөөцийн өөрчлөлт
    quantity_before = db.Column(db.Float)
    quantity_after = db.Column(db.Float)

    # Relationships
    used_by = db.relationship('User', foreign_keys=[used_by_id])
    sample = db.relationship('Sample', foreign_keys=[sample_id])

    def __repr__(self):
        return f"<ChemicalUsage {self.quantity_used} {self.unit} at {self.used_at}>"


class ChemicalLog(db.Model):
    """
    Химийн бодисын аудит түүх (Audit Trail).

    Бүх өөрчлөлтийн түүхийг хадгална.

    Attributes:
        id (int): Primary key
        chemical_id (int): Foreign key → Chemical
        timestamp (datetime): Үйлдлийн цаг
        user_id (int): Foreign key → User
        action (str): Үйлдлийн төрөл
        quantity_change (float): Тоо хэмжээний өөрчлөлт (+ эсвэл -)
        quantity_before (float): Өмнөх тоо хэмжээ
        quantity_after (float): Дараах тоо хэмжээ
        details (str): Дэлгэрэнгүй тайлбар (JSON)

    Action values:
        - created: Шинээр бүртгэсэн
        - updated: Засварласан
        - received: Нөөц нэмсэн
        - consumed: Хэрэглэсэн
        - disposed: Устгасан
        - adjusted: Тоо хэмжээ засварласан (инвентор)

    Example:
        >>> log = ChemicalLog(
        ...     chemical_id=1,
        ...     user_id=current_user.id,
        ...     action='received',
        ...     quantity_change=2500,
        ...     quantity_before=0,
        ...     quantity_after=2500,
        ...     details='Шинэ багц хүлээн авав'
        ... )
    """
    __tablename__ = 'chemical_log'

    id = db.Column(db.Integer, primary_key=True)
    chemical_id = db.Column(db.Integer, db.ForeignKey('chemical.id'), nullable=False, index=True)

    # Цаг хугацаа
    timestamp = db.Column(db.DateTime, default=now_mn, index=True)

    # Хэрэглэгч
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    # Үйлдэл
    action = db.Column(db.String(30), nullable=False, index=True)
    # 'created', 'updated', 'received', 'consumed', 'disposed', 'adjusted'

    # Тоо хэмжээний өөрчлөлт
    quantity_change = db.Column(db.Float)       # + нэмэгдсэн, - хасагдсан
    quantity_before = db.Column(db.Float)
    quantity_after = db.Column(db.Float)

    # Дэлгэрэнгүй
    details = db.Column(db.Text)                # JSON эсвэл текст

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        db.Index('ix_chemical_log_chemical_timestamp', 'chemical_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<ChemicalLog {self.action} at {self.timestamp}>"


# -------------------------
# ХОГ ХАЯГДЛЫН БҮРТГЭЛ (Chemical Waste)
# -------------------------
class ChemicalWaste(db.Model):
    """
    Химийн хорт болон аюултай хог хаягдлын бүртгэл.

    Лабораторийн хог хаягдал, сав баглаа, шинжилгээний хаягдал зэргийг
    бүртгэж, сар бүрийн хэмжээг хянах.

    Attributes:
        id (int): Primary key
        name_mn (str): Хог хаягдлын монгол нэр
        name_en (str): Хог хаягдлын олон улсын нэр
        monthly_amount (float): Сард гардаг хэмжээ (дундаж)
        unit (str): Хэмжих нэгж (л, кг, ш)
        disposal_method (str): Хаягдах арга (sewer, evaporate, special, incinerate)
        disposal_location (str): Хаягдах газар
        is_hazardous (bool): Аюултай эсэх
        hazard_type (str): Аюулын төрөл
        lab_type (str): Лабын төрөл
        is_active (bool): Идэвхтэй эсэх
        notes (str): Тэмдэглэл
        created_at (datetime): Үүсгэсэн огноо
    """
    __tablename__ = 'chemical_waste'

    id = db.Column(db.Integer, primary_key=True)

    # Нэршил
    name_mn = db.Column(db.String(255), nullable=False)
    name_en = db.Column(db.String(255))

    # Хэмжээ
    monthly_amount = db.Column(db.Float)  # Сард гардаг дундаж хэмжээ
    unit = db.Column(db.String(20), default='л')  # л, кг, ш, мл

    # Хаягдах мэдээлэл
    disposal_method = db.Column(db.String(50))
    # sewer: бохирын шугам, evaporate: ууршина, special: тусгай сав, incinerate: шатаах
    disposal_location = db.Column(db.String(255))

    # Аюултай ангилал
    is_hazardous = db.Column(db.Boolean, default=True)
    hazard_type = db.Column(db.String(100))  # corrosive, toxic, flammable, etc.

    # Лаб
    lab_type = db.Column(db.String(30), default='all')

    # Төлөв
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=now_mn)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    records = db.relationship('ChemicalWasteRecord', back_populates='waste', lazy='dynamic')

    def __repr__(self):
        return f"<ChemicalWaste {self.name_mn}>"


class ChemicalWasteRecord(db.Model):
    """
    Хог хаягдлын сарын бүртгэл.

    Сар бүрийн хаягдсан хэмжээ, үлдэгдэл бүртгэл.

    Attributes:
        id (int): Primary key
        waste_id (int): Foreign key → ChemicalWaste
        year (int): Жил
        month (int): Сар (1-12)
        quantity (float): Хаягдсан хэмжээ
        starting_balance (float): Эхний үлдэгдэл
        ending_balance (float): Эцсийн үлдэгдэл
        notes (str): Тэмдэглэл
        recorded_at (datetime): Бүртгэсэн огноо
        recorded_by_id (int): Бүртгэсэн хэрэглэгч
    """
    __tablename__ = 'chemical_waste_record'

    id = db.Column(db.Integer, primary_key=True)
    waste_id = db.Column(db.Integer, db.ForeignKey('chemical_waste.id'), nullable=False, index=True)

    # Огноо
    year = db.Column(db.Integer, nullable=False, index=True)
    month = db.Column(db.Integer, nullable=False, index=True)  # 1-12

    # Хэмжээ
    quantity = db.Column(db.Float, default=0)  # Тухайн сард хаягдсан хэмжээ
    starting_balance = db.Column(db.Float, default=0)  # Эхний үлдэгдэл
    ending_balance = db.Column(db.Float, default=0)  # Эцсийн үлдэгдэл

    notes = db.Column(db.Text)

    # Бүртгэсэн
    recorded_at = db.Column(db.DateTime, default=now_mn)
    recorded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    waste = db.relationship('ChemicalWaste', back_populates='records')
    recorded_by = db.relationship('User', foreign_keys=[recorded_by_id])

    __table_args__ = (
        db.UniqueConstraint('waste_id', 'year', 'month', name='uq_waste_year_month'),
        db.Index('ix_waste_record_year_month', 'year', 'month'),
    )

    def __repr__(self):
        return f"<WasteRecord {self.year}-{self.month}: {self.quantity}>"


# -------------------------
# ТАЙЛАНГИЙН СИСТЕМ (Report Generation)
# -------------------------
class ReportSignature(db.Model):
    """
    Гарын үсэг, тамганы зураг хадгалах.

    Чанарын менежер, шинжээч нарын гарын үсэг болон
    лабораторийн тамганы зургийг хадгална.

    Attributes:
        id (int): Primary key
        name (str): Нэр (жишээ: "Ц.Бэхцэцэг - Ахлах менежер")
        signature_type (str): Төрөл (signature, stamp)
        image_path (str): Зургийн зам
        user_id (int): Холбоотой хэрэглэгч (optional)
        lab_type (str): Лаб төрөл
        is_active (bool): Идэвхтэй эсэх
        position (str): Албан тушаал
    """
    __tablename__ = 'report_signature'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    signature_type = db.Column(db.String(20), nullable=False)  # 'signature', 'stamp'
    image_path = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    lab_type = db.Column(db.String(30), default='all')
    is_active = db.Column(db.Boolean, default=True)
    position = db.Column(db.String(100))  # Албан тушаал

    created_at = db.Column(db.DateTime, default=now_mn)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])

    def __repr__(self):
        return f"<ReportSignature {self.name} ({self.signature_type})>"


class LabReport(db.Model):
    """
    Лабораторийн тайлангийн бүртгэл.

    Нэгтгэлээс үүсгэсэн PDF тайлангуудыг хадгалах,
    баталгаажуулах, имэйлээр илгээх.

    Attributes:
        id (int): Primary key
        report_number (str): Тайлангийн дугаар (жишээ: 2026_15)
        lab_type (str): Лаб төрөл (coal, water, microbiology, petrography)
        report_type (str): Тайлангийн төрөл (analysis, summary, certificate)
        title (str): Гарчиг
        status (str): Төлөв (draft, pending_approval, approved, sent)

        # Дээжийн мэдээлэл
        sample_ids (JSON): Холбоотой дээжийн ID-ууд
        date_from (date): Эхлэх огноо
        date_to (date): Дуусах огноо

        # Файл
        pdf_path (str): PDF файлын зам

        # Гарын үсэг
        analyst_signature_id (int): Шинжээчийн гарын үсэг
        manager_signature_id (int): Менежерийн гарын үсэг
        stamp_id (int): Тамга

        # Баталгаажуулалт
        approved_by_id (int): Баталгаажуулсан хүн
        approved_at (datetime): Баталгаажуулсан огноо

        # Имэйл
        email_sent (bool): Илгээсэн эсэх
        email_sent_at (datetime): Илгээсэн огноо
        email_recipients (str): Хүлээн авагчид

        # Мета
        created_by_id (int): Үүсгэсэн хүн
        created_at (datetime): Үүсгэсэн огноо
    """
    __tablename__ = 'lab_report'

    id = db.Column(db.Integer, primary_key=True)
    report_number = db.Column(db.String(50), unique=True, nullable=False)
    lab_type = db.Column(db.String(30), nullable=False, index=True)
    report_type = db.Column(db.String(30), default='analysis')
    title = db.Column(db.String(255))
    status = db.Column(db.String(20), default='draft', index=True)
    # draft, pending_approval, approved, sent

    # Дээжийн мэдээлэл
    sample_ids = db.Column(db.JSON)  # [1, 2, 3, ...]
    date_from = db.Column(db.Date)
    date_to = db.Column(db.Date)

    # Тайлангийн агуулга (JSON)
    report_data = db.Column(db.JSON)

    # PDF файл
    pdf_path = db.Column(db.String(255))

    # Гарын үсэг, тамга
    analyst_signature_id = db.Column(db.Integer, db.ForeignKey('report_signature.id'))
    manager_signature_id = db.Column(db.Integer, db.ForeignKey('report_signature.id'))
    stamp_id = db.Column(db.Integer, db.ForeignKey('report_signature.id'))

    # Баталгаажуулалт
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)

    # Имэйл
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime)
    email_recipients = db.Column(db.Text)  # comma-separated

    # Мета
    notes = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=now_mn)
    updated_at = db.Column(db.DateTime, default=now_mn, onupdate=now_mn)

    # Relationships
    analyst_signature = db.relationship('ReportSignature', foreign_keys=[analyst_signature_id])
    manager_signature = db.relationship('ReportSignature', foreign_keys=[manager_signature_id])
    stamp = db.relationship('ReportSignature', foreign_keys=[stamp_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    __table_args__ = (
        db.Index('ix_lab_report_lab_status', 'lab_type', 'status'),
    )

    def __repr__(self):
        return f"<LabReport {self.report_number} ({self.status})>"

    def get_status_display(self):
        status_map = {
            'draft': 'Ноорог',
            'pending_approval': 'Хүлээгдэж буй',
            'approved': 'Баталгаажсан',
            'sent': 'Илгээсэн',
        }
        return status_map.get(self.status, self.status)


# -------------------------
# УУСМАЛ БЭЛДЭХ ДЭВТЭР (Усны хими)
# -------------------------
class SolutionPreparation(db.Model):
    """
    Уусмал бэлдэх дэвтэр (Усны химийн лаб).

    Стандарт уусмал бэлдэх, титр тогтоох бүртгэл.

    Attributes:
        id (int): Primary key
        solution_name (str): Уусмалын нэр
        concentration (float): Концентраци (мг/л)
        volume_ml (float): Эзэлхүүн (мл)
        chemical_used_mg (float): Зарцуулсан бодис (мг)
        prepared_date (date): Огноо
        v1 (float): Титрийн V1 хэмжилт
        v2 (float): Титрийн V2 хэмжилт
        v_avg (float): Vд - дундаж
        titer_coefficient (float): Титрийн коэффициент
        preparation_notes (str): Уусмал бэлдэх явц / заалт
        prepared_by_id (int): Foreign key → User
        chemical_id (int): Foreign key → Chemical (optional)

    Example:
        >>> solution = SolutionPreparation(
        ...     solution_name='HCl 0.1N',
        ...     concentration=0.1,
        ...     volume_ml=1000,
        ...     chemical_used_mg=3650,
        ...     titer_coefficient=0.9985
        ... )
    """
    __tablename__ = 'solution_preparation'

    id = db.Column(db.Integer, primary_key=True)

    # Үндсэн мэдээлэл
    solution_name = db.Column(db.String(200), nullable=False, index=True)
    concentration = db.Column(db.Float)                     # Концентраци (мг/л, mol/L, N)
    concentration_unit = db.Column(db.String(20), default='mg/L')  # mg/L, mol/L, N, %
    volume_ml = db.Column(db.Float)                         # Эзэлхүүн (мл)

    # Зарцуулсан бодис
    chemical_used_mg = db.Column(db.Float)                  # Зарцуулсан бодис (мг)
    chemical_id = db.Column(db.Integer, db.ForeignKey('chemical.id', ondelete='SET NULL'))

    # Жортой холбоос (шинэ)
    recipe_id = db.Column(db.Integer, db.ForeignKey('solution_recipe.id', ondelete='SET NULL'), index=True)

    # Огноо
    prepared_date = db.Column(db.Date, nullable=False, index=True)
    expiry_date = db.Column(db.Date)                        # Хүчинтэй хугацаа

    # Титр тогтоолт
    v1 = db.Column(db.Float)                                # V1 хэмжилт
    v2 = db.Column(db.Float)                                # V2 хэмжилт
    v3 = db.Column(db.Float)                                # V3 хэмжилт (optional)
    v_avg = db.Column(db.Float)                             # Vд - дундаж
    titer_coefficient = db.Column(db.Float)                 # Титрийн коэффициент (K)

    # Уусмал бэлдэх явц
    preparation_notes = db.Column(db.Text)                  # Бэлдэх заавар / тэмдэглэл

    # Төлөв
    status = db.Column(db.String(20), default='active', index=True)  # active, expired, empty

    # Хэрэглэгч
    prepared_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    created_at = db.Column(db.DateTime, default=now_mn)

    # Relationships
    prepared_by = db.relationship('User', foreign_keys=[prepared_by_id])
    chemical = db.relationship('Chemical', foreign_keys=[chemical_id])

    def calculate_v_avg(self):
        """Дундаж V тооцоолох."""
        values = [v for v in [self.v1, self.v2, self.v3] if v is not None]
        if values:
            self.v_avg = sum(values) / len(values)
        return self.v_avg

    def __repr__(self):
        return f"<SolutionPreparation {self.solution_name} ({self.prepared_date})>"


class SolutionRecipe(db.Model):
    """
    Уусмалын жор (Recipe) - урьдчилан тодорхойлсон уусмал бэлдэх заавар.

    Жишээ нь: Трилон Б 0.05N, HCl 0.1N, NaOH 0.1M гэх мэт.
    Тус бүрдээ ямар химийн бодис, хэр хэмжээгээр орох вэ гэдгийг тодорхойлно.

    Attributes:
        id (int): Primary key
        name (str): Уусмалын нэр (жнь: "Трилон Б 0.05N")
        concentration (float): Зорилтот концентраци
        concentration_unit (str): Нэгж (N, M, %, mg/L)
        standard_volume_ml (float): Жорын стандарт эзэлхүүн (жнь: 1000мл)
        preparation_notes (str): Уусмал бэлдэх дэлгэрэнгүй заавар
        lab_type (str): Лабын төрөл (water, coal, micro, petro)
        is_active (bool): Идэвхтэй эсэх
    """
    __tablename__ = 'solution_recipe'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    concentration = db.Column(db.Float)
    concentration_unit = db.Column(db.String(20), default='N')  # N, M, %, mg/L
    standard_volume_ml = db.Column(db.Float, default=1000)  # Стандарт эзэлхүүн

    # Бэлдэх заавар
    preparation_notes = db.Column(db.Text)  # Дэлгэрэнгүй заавар

    # Категори
    lab_type = db.Column(db.String(20), default='water', index=True)  # water, coal, micro, petro
    category = db.Column(db.String(50))  # titrant, buffer, indicator, standard, reagent

    # Төлөв
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_mn)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    ingredients = db.relationship('SolutionRecipeIngredient', backref='recipe', lazy='dynamic',
                                  cascade='all, delete-orphan')
    preparations = db.relationship('SolutionPreparation', backref='recipe', lazy='dynamic')

    def calculate_ingredients(self, target_volume_ml):
        """
        Зорилтот эзэлхүүнд шаардагдах бодисын хэмжээг тооцоолох.

        Args:
            target_volume_ml: Бэлдэх эзэлхүүн (мл)

        Returns:
            list: [{'chemical': Chemical, 'amount': float, 'unit': str}, ...]
        """
        ratio = target_volume_ml / self.standard_volume_ml if self.standard_volume_ml else 1
        result = []
        for ing in self.ingredients:
            result.append({
                'chemical': ing.chemical,
                'chemical_id': ing.chemical_id,
                'amount': ing.amount * ratio,
                'unit': ing.unit,
                'ingredient_id': ing.id
            })
        return result

    def __repr__(self):
        return f"<SolutionRecipe {self.name}>"


class SolutionRecipeIngredient(db.Model):
    """
    Уусмалын жорын найрлага (орц) - нэг жорт хэд хэдэн химийн бодис орж болно.

    Attributes:
        id (int): Primary key
        recipe_id (int): Foreign key → SolutionRecipe
        chemical_id (int): Foreign key → Chemical
        amount (float): Хэмжээ (стандарт эзэлхүүнд)
        unit (str): Нэгж (g, mg, mL)
    """
    __tablename__ = 'solution_recipe_ingredient'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('solution_recipe.id', ondelete='CASCADE'), nullable=False)
    chemical_id = db.Column(db.Integer, db.ForeignKey('chemical.id', ondelete='SET NULL'))
    amount = db.Column(db.Float, nullable=False)  # Стандарт эзэлхүүнд орох хэмжээ
    unit = db.Column(db.String(20), default='g')  # g, mg, mL

    # Relationship
    chemical = db.relationship('Chemical')

    def __repr__(self):
        return f"<SolutionRecipeIngredient {self.chemical.name if self.chemical else 'Unknown'}: {self.amount} {self.unit}>"
