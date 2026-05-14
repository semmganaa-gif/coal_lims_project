# -*- coding: utf-8 -*-
"""
Chemical-related models.

Separated from models.py for maintainability.
"""

from sqlalchemy import CheckConstraint
from app import db
from app.constants import ChemicalStatus
from app.models.mixins import HashableMixin
from app.utils.datetime import now_local as now_mn


# -------------------------
# ХИМИЙН БОДИС
# -------------------------
class Chemical(db.Model):
    """
    Химийн бодисын бүртгэл (ISO 17025 - Reagent Management).
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

    # Нээсний дараах хугацаа (зарим урвалж нээсний дараа богино хугацаатай)
    shelf_life_after_opening_days = db.Column(db.Integer)       # Нээсний дараах хоног
    opened_expiry_date = db.Column(db.Date)                     # Нээсний дараах дуусах хугацаа (автомат)

    # Хадгалалт
    storage_location = db.Column(db.String(100))                # Байршил (шүүгээ, тавиур)
    storage_conditions = db.Column(db.String(200))              # Нөхцөл (температур, гэх мэт)

    # Аюулгүй байдал
    hazard_class = db.Column(db.String(100))                    # Аюулын ангилал (текст)
    sds_file_path = db.Column(db.String(255))                   # Safety Data Sheet файл
    ghs_pictograms = db.Column(db.JSON)                         # GHS тэмдэгүүд ['GHS01','GHS06',...]
    ghs_signal_word = db.Column(db.String(10))                  # 'Danger' эсвэл 'Warning'
    sds_version = db.Column(db.String(20))                      # SDS хувилбар
    sds_revision_date = db.Column(db.Date)                      # SDS хянасан огноо

    # Урьдчилсан анхааруулга
    days_alert_before_expiry = db.Column(db.Integer, default=30)  # Дуусахаас хэдэн хоногийн өмнө анхааруулах
    prevent_use_if_expired = db.Column(db.Boolean, default=True)  # Дуусвал хаах

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

    __table_args__ = (
        CheckConstraint(
            ChemicalStatus.check_constraint("status"),
            name="ck_chemical_status",
        ),
    )

    # Relationships
    usages = db.relationship('ChemicalUsage', backref='chemical', lazy='dynamic',
                             cascade='all, delete-orphan')
    logs = db.relationship('ChemicalLog', backref='chemical', lazy='dynamic',
                           cascade='all, delete-orphan')
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def update_status(self):
        """Нөөц болон хугацаанд үндэслэн төлөвийг автоматаар шинэчлэх."""
        from datetime import date, timedelta
        today = date.today()

        if self.status == 'disposed':
            return  # Устгагдсан бол өөрчлөхгүй

        # Нээсний дараах дуусах хугацааг автомат тооцоолох
        if self.opened_date and self.shelf_life_after_opening_days:
            self.opened_expiry_date = self.opened_date + timedelta(days=self.shelf_life_after_opening_days)

        # Нэн эрт дуусах хугацааг тодорхойлох (expiry_date vs opened_expiry_date)
        effective_expiry = self.expiry_date
        if self.opened_expiry_date:
            if effective_expiry is None or self.opened_expiry_date < effective_expiry:
                effective_expiry = self.opened_expiry_date

        if self.quantity <= 0:
            self.status = 'empty'
        elif effective_expiry and effective_expiry < today:
            self.status = 'expired'
        elif self.reorder_level and self.quantity <= self.reorder_level:
            self.status = 'low_stock'
        else:
            self.status = 'active'

    def days_until_expiry(self):
        """Дуусах хүртэлх хоногийн тоо (эрт дуусах хугацаагаар)."""
        from datetime import date
        today = date.today()
        effective_expiry = self.expiry_date
        if self.opened_expiry_date:
            if effective_expiry is None or self.opened_expiry_date < effective_expiry:
                effective_expiry = self.opened_expiry_date
        if effective_expiry is None:
            return None
        return (effective_expiry - today).days

    def is_expiring_soon(self):
        """Анхааруулах хугацаанд орсон эсэх."""
        days = self.days_until_expiry()
        if days is None:
            return False
        threshold = self.days_alert_before_expiry or 30
        return 0 <= days <= threshold

    def __repr__(self):
        return f"<Chemical {self.name} ({self.quantity} {self.unit})>"


class ChemicalUsage(db.Model):
    """
    Химийн бодисын хэрэглээний бүртгэл.
    """
    __tablename__ = 'chemical_usage'

    id = db.Column(db.Integer, primary_key=True)
    # Chemical устгахад usage record устгана (тус бодис байхгүй бол хэрэглээ
    # утгагүй). Chemical.usages-ийн ORM cascade-тэй synced.
    chemical_id = db.Column(
        db.Integer,
        db.ForeignKey('chemical.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )

    # Хэрэглээний мэдээлэл
    quantity_used = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))

    # Шинжилгээтэй холбох (optional)
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id', ondelete='SET NULL'), index=True)
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


class ChemicalLog(HashableMixin, db.Model):
    """
    Химийн бодисын аудит түүх (Audit Trail).
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

    # Тоо хэмжээний өөрчлөлт
    quantity_change = db.Column(db.Float)       # + нэмэгдсэн, - хасагдсан
    quantity_before = db.Column(db.Float)
    quantity_after = db.Column(db.Float)

    # Дэлгэрэнгүй
    details = db.Column(db.Text)                # JSON эсвэл текст

    # ISO 17025: Audit log hash (өөрчлөгдсөн эсэхийг шалгах)
    data_hash = db.Column(db.String(64), nullable=True)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        db.Index('ix_chemical_log_chemical_timestamp', 'chemical_id', 'timestamp'),
    )

    def _get_hash_data(self) -> str:
        """HashableMixin: Return data string for hashing."""
        return (
            f"{self.chemical_id}|{self.action}|{self.quantity_change}|"
            f"{self.quantity_before}|{self.quantity_after}|{self.user_id}|"
            f"{self.timestamp}|{self.details}"
        )

    def __repr__(self):
        return f"<ChemicalLog {self.action} at {self.timestamp}>"


# -------------------------
# ХОГ ХАЯГДЛЫН БҮРТГЭЛ (Chemical Waste)
# -------------------------
class ChemicalWaste(db.Model):
    """
    Химийн хорт болон аюултай хог хаягдлын бүртгэл.
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
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    records = db.relationship('ChemicalWasteRecord', back_populates='waste', lazy='dynamic')

    def __repr__(self):
        return f"<ChemicalWaste {self.name_mn}>"


class ChemicalWasteRecord(db.Model):
    """
    Хог хаягдлын сарын бүртгэл.
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
    recorded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    # Relationships
    waste = db.relationship('ChemicalWaste', back_populates='records')
    recorded_by = db.relationship('User', foreign_keys=[recorded_by_id])

    __table_args__ = (
        db.UniqueConstraint('waste_id', 'year', 'month', name='uq_waste_year_month'),
        db.Index('ix_waste_record_year_month', 'year', 'month'),
    )

    def __repr__(self):
        return f"<WasteRecord {self.year}-{self.month}: {self.quantity}>"
