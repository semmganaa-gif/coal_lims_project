# -*- coding: utf-8 -*-
"""
Quality standards models.
"""

from app import db
from app.utils.datetime import now_local as now_mn


class ControlStandard(db.Model):
    """
    Хяналтын стандарт дээж (QC Control Chart).

    Шинжилгээний параметр бүрийн mean, SD утгуудыг JSON-оор хадгалж,
    QC chart-д зорилтот утга, хяналтын хязгаарт ашиглана.
    """
    __tablename__ = 'control_standards'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Жнь: CM-2025-Q4
    created_at = db.Column(db.DateTime, default=now_mn)
    is_active = db.Column(db.Boolean, default=False)  # Одоо ашиглагдаж байгаа эсэх

    # Жишээ: { "Aad": {"mean": 24.22, "sd": 0.22}, "Mad": {"mean": 10.5, "sd": 0.1} }
    targets = db.Column(db.JSON, default=lambda: {})

    def __repr__(self):
        return f"<ControlStandard {self.name}>"


class GbwStandard(db.Model):
    """
    GBW стандарт лавлагааны материал.

    Хятадын GBW стандарт дээжний сертификат утгууд.
    QC шалгалтад ашиглана.
    """
    __tablename__ = 'gbw_standards'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # GBW Дугаар (Batch No)
    targets = db.Column(db.JSON, nullable=False)  # { 'Mad': {'mean': 1.2, 'sd': 0.1}, ... }
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now_mn)

    def __repr__(self):
        return f'<GBW {self.name}>'
