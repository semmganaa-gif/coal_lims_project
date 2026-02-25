# -*- coding: utf-8 -*-
"""
Planning models.
"""

from app import db
from app.utils.datetime import now_local as now_mn

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
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
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
