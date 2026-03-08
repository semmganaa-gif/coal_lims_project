# -*- coding: utf-8 -*-
"""
Settings models.
"""

from app import db
from app.utils.datetime import now_local as now_mn

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

