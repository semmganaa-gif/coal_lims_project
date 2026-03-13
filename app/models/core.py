# -*- coding: utf-8 -*-
"""
User and sample models.
"""

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from app.utils.datetime import now_local as now_mn
import re
import json
from sqlalchemy.types import Date, Text
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import validates

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
    allowed_labs = db.Column(db.JSON, default=lambda: ['coal'])  # ['coal', 'petrography', 'water']

    # Хэлний тохиргоо (i18n)
    language = db.Column(db.String(5), default='en')  # 'en' or 'mn'

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
            - Хамгийн багадаа 10 тэмдэгт
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
        if len(password) < 10:
            errors.append("хамгийн багадаа 10 тэмдэгт байх ёстой")
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
    weight = db.Column(db.Numeric(12, 4))
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
    mass_ready_by_id = db.Column(db.Integer, db.ForeignKey("user.id", name="fk_sample_mass_ready_by_id"), nullable=True)

    # SLA / Turnaround tracking
    sla_hours = db.Column(db.Integer, nullable=True)  # SLA хугацаа (цагаар, жишээ: 72 = 3 хоног)
    due_date = db.Column(db.DateTime, nullable=True, index=True)  # Хариу өгөх эцсийн хугацаа
    priority = db.Column(db.String(20), nullable=True, default='normal')  # normal, urgent, rush
    completed_at = db.Column(db.DateTime, nullable=True)  # Бүх шинжилгээ дуусах огноо

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
        CheckConstraint(
            "status IN ('new','in_progress','analysis','completed','archived')",
            name="ck_sample_status",
        ),
        # H-9: Composite indexes — dashboard болон workspace query-уудыг хурдасгах
        db.Index('ix_sample_lab_type_status', 'lab_type', 'status'),
        db.Index('ix_sample_received_date_lab_type', 'received_date', 'lab_type'),
        db.Index('ix_sample_client_name_sample_type', 'client_name', 'sample_type'),
    )

    results = db.relationship(
        "AnalysisResult",
        backref="sample",
        lazy="select",
        cascade="all, delete-orphan",
    )

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
            from app.models.analysis import SampleCalculations
            self._calculations_cache = SampleCalculations(self)
        return self._calculations_cache

    @validates('sample_code')
    def validate_sample_code(self, key, value):
        """
        Sample code-г нормализаци хийх.
        - Нүүрс/Петрограф: Latin үсэг, тоо, тусгай тэмдэгт (uppercase)
        - WTL: Latin mixed case зөвшөөрнө (Dry, Wet гэх мэт)
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

        # WTL → mixed case хэвээр хадгална (Dry, Wet гэх мэт)
        if getattr(self, 'client_name', None) == 'WTL':
            if not re.match(r'^[A-Za-z0-9_\-/.,+ ]+$', value):
                invalid_chars = re.findall(r'[^A-Za-z0-9_\-/.,+ ]', value)
                raise ValueError(
                    f"Дээжний код зөвхөн Latin үсэг агуулах ёстой. "
                    f"Буруу тэмдэгт: {', '.join(set(invalid_chars))}"
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
