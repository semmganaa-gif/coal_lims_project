# -*- coding: utf-8 -*-
"""
Bottle (pycnometer) models for TRD analysis.
"""

from datetime import datetime
from typing import Optional

from app import db
from app.utils.datetime import now_local as now_mn

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
        lazy="select",
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
        ref = ref or now_mn()
        if self.effective_to is not None and ref >= self.effective_to:
            return False
        return self.effective_from <= ref and self.approved_at is not None

    def __repr__(self) -> str:
        return (
            f"<BottleConst b#{self.bottle_id} "
            f"avg={self.avg_value:.5f} @ {self.temperature_c}°C>"
        )
