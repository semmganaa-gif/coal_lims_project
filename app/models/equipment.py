# -*- coding: utf-8 -*-
"""
Equipment-related models.

Separated from models.py for maintainability.
"""

from app import db
from app.utils.datetime import now_local as now_mn


# =========================================================
# 🛑 ТОНОГ ТӨХӨӨРӨМЖИЙН УДИРДЛАГА (ISO 17025 - 6.4)
# =========================================================


class Equipment(db.Model):
    """
    Тоног төхөөрөмжийн бүртгэл (ISO 17025 - Section 6.4).

    Лабораторийн тоног төхөөрөмжийн бүртгэл, хянах баталгаажуулалт,
    засвар үйлчилгээний мэдээллийг хадгална.
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

    # Ашиглалтын байдал
    status = db.Column(db.String(20), default='normal', index=True)

    # Шалгалт тохируулга / баталгаажуулалт
    calibration_date = db.Column(db.Date)                     # Сүүлд баталгаажсан огноо
    calibration_cycle_days = db.Column(db.Integer, default=365)  # Давтамж (хоног)
    next_calibration_date = db.Column(db.Date)                # Дараагийн хугацаа
    calibration_note = db.Column(db.String(200))              # Шалгалт тохируулгын товч тэмдэглэл
    category = db.Column(db.String(50), default='other', index=True)

    # Excel дээрх нэмэлт мэдээлэл
    manufactured_info = db.Column(db.String(20))              # Үйлдвэрлэсэн огноо (текст)
    commissioned_info = db.Column(db.String(20))              # Ашиглалтад орсон огноо (текст)
    initial_price = db.Column(db.Float)                       # Анхны үнэ (₮)
    residual_price = db.Column(db.Float)                      # Үлдэгдэл үнэ (₮)
    remark = db.Column(db.String(255))                        # Бусад тайлбар

    # Бүртгэлийн төрөл
    register_type = db.Column(db.String(30), default='main', index=True)
    extra_data = db.Column(db.JSON)                           # Бүртгэл бүрийн тусгай field-үүд

    # Timestamps (audit trail)
    created_at = db.Column(db.DateTime, default=now_mn)
    updated_at = db.Column(db.DateTime, default=now_mn, onupdate=now_mn)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)

    # H-9: Composite indexes
    __table_args__ = (
        db.Index('ix_equipment_category_status', 'category', 'status'),
    )

    # Холбоосууд
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    logs = db.relationship(
        'MaintenanceLog',
        backref='equipment',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by="desc(MaintenanceLog.action_date)"
    )
    usages = db.relationship(
        'UsageLog',
        backref='equipment',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )


class MaintenanceLog(db.Model):
    """
    Засвар үйлчилгээний түүх (ISO 17025 - Equipment maintenance).
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
