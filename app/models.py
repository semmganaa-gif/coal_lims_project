# app/models.py
# -*- coding: utf-8 -*-

from app import db
from datetime import datetime
from typing import Optional, Dict, Any, List
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.types import Date, Text
from sqlalchemy import CheckConstraint
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
        role (str): Эрх ('beltgegch', 'himich', 'ahlah', 'admin')

    Roles:
        - beltgegch: Дээж бэлтгэх
        - himich: Шинжилгээ хийх
        - ahlah: Үр дүн шалгах, баталгаажуулах
        - admin: Системийн админ (бүх эрх)
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(64), index=True, default="beltgegch")

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

    # 🆕 ISO 17025: Chain of Custody & Sample Retention
    sampled_by = db.Column(db.String(100))  # Хэн авсан
    sampling_date = db.Column(db.DateTime)  # Хэзээ авсан
    sampling_location = db.Column(db.String(200))  # Хаанаас авсан
    sampling_method = db.Column(db.String(100))  # Аргачлал (SOP reference)
    custody_log = db.Column(db.Text)  # JSON: Хариуцлага шилжүүлсэн түүх
    retention_date = db.Column(Date)  # Хадгалах дуусах хугацаа
    disposal_date = db.Column(Date)  # Устгах огноо
    disposal_method = db.Column(db.String(100))  # Яаж устгасан

    # ✅ CHECK CONSTRAINT
    __table_args__ = (
        CheckConstraint(
            "client_name IN ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB')",
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

    logs = db.relationship(
        "AnalysisResultLog",
        back_populates="result",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="desc(AnalysisResultLog.timestamp)",
    )

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
        required_role (str): Шаардлагатай эрх (default: "himich")

    Example:
        >>> analysis = AnalysisType(
        ...     code='Mad',
        ...     name='Чийг (агаарын)',
        ...     order_num=10,
        ...     required_role='himich'
        ... )
    """
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    order_num = db.Column(db.Integer, default=100)
    required_role = db.Column(
        db.String(64), default="himich", index=True, nullable=False
    )

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
        except Exception:
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
        except Exception:
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

    # Холбоосууд
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
    performed_by = db.Column(db.String(50))   # Гүйцэтгэсэн хүн / байгууллага
    certificate_no = db.Column(db.String(50)) # Гэрчилгээний № (хэрэв байгаа бол)
    result = db.Column(db.String(20))         # 'Pass', 'Fail', 'Warning' ...

    # ✅ ШИНЭ: Файл хадгалах зам (Гэрчилгээ хавсаргахад зориулав)
    file_path = db.Column(db.String(256), nullable=True)


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
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'), nullable=True, index=True)  # Аль дээжинд ашигласан (optional)

    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)   # Нийт ажилласан минут
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
        - Cascade delete: Sample эсвэл Result устахад л устана
    """
    __tablename__ = "analysis_result_log"

    id = db.Column(db.Integer, primary_key=True)

    # Монгол цаг
    timestamp = db.Column(db.DateTime, index=True, default=now_mn, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    user = db.relationship("User", backref=db.backref("logs", lazy="dynamic"))

    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("sample.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    analysis_result_id = db.Column(
        db.Integer,
        db.ForeignKey("analysis_result.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    analysis_code = db.Column(db.String(50), index=True, nullable=False)

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
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.text("1"))

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
    related_sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'))

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
