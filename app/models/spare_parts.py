# -*- coding: utf-8 -*-
"""
Spare parts models.
"""

from app import db
from app.models.mixins import HashableMixin
from app.utils.datetime import now_local as now_mn

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
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id', ondelete='SET NULL'), index=True)
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
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

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
    maintenance_log_id = db.Column(db.Integer, db.ForeignKey('maintenance_logs.id', ondelete='SET NULL'), index=True)

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


class SparePartLog(HashableMixin, db.Model):
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

    # ISO 17025: Audit log hash (өөрчлөгдсөн эсэхийг шалгах)
    data_hash = db.Column(db.String(64), nullable=True)

    # Relationship
    user = db.relationship('User', foreign_keys=[user_id])

    def _get_hash_data(self) -> str:
        """HashableMixin: Return data string for hashing."""
        return (
            f"{self.spare_part_id}|{self.action}|{self.quantity_change}|"
            f"{self.quantity_before}|{self.quantity_after}|{self.user_id}|"
            f"{self.timestamp}|{self.details}"
        )

    def __repr__(self):
        return f"<SparePartLog {self.spare_part_id} {self.action}>"


# -------------------------
# ТООЦООЛОЛ
# -------------------------


