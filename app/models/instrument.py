# app/models/instrument.py
# -*- coding: utf-8 -*-
"""
Instrument data integration models.

Багажаас автоматаар уншсан өгөгдлийг хадгалах, review хийх.
"""

from app import db
from app.utils.datetime import now_local as now_mn


class InstrumentReading(db.Model):
    """
    Багажаас уншсан нэг хэмжилтийн бүртгэл.

    Workflow: pending → approved/rejected
    - pending: Багажаас автоматаар уншигдсан, химич шалгаагүй
    - approved: Химич баталгаажуулсан → AnalysisResult-д хадгалагдсан
    - rejected: Химич татгалзсан (алдаатай хэмжилт)
    """
    __tablename__ = "instrument_reading"

    id = db.Column(db.Integer, primary_key=True)

    # Багажийн мэдээлэл
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment.id"), nullable=True, index=True)
    instrument_name = db.Column(db.String(100), nullable=False)  # "TGA-701", "5E-C5500"
    instrument_type = db.Column(db.String(50), nullable=False)   # "tga", "bomb_cal", "elemental", "karl_fischer"

    # Файлын мэдээлэл
    source_file = db.Column(db.String(500), nullable=False)  # Файлын зам
    file_hash = db.Column(db.String(64))  # SHA-256 (давхардал шалгах)

    # Дээж холбоос
    sample_id = db.Column(db.Integer, db.ForeignKey("sample.id", ondelete="SET NULL"), nullable=True, index=True)
    sample_code = db.Column(db.String(100), index=True)  # Файлаас уншсан дээжний код
    analysis_code = db.Column(db.String(20), index=True)  # "Mad", "Aad", "Qgr,ad" гэх мэт

    # Хэмжилтийн өгөгдөл
    raw_data = db.Column(db.JSON)       # Файлаас уншсан бүх өгөгдөл
    parsed_value = db.Column(db.Float)  # Тооцоолсон эцсийн үр дүн
    unit = db.Column(db.String(20))     # "%" , "J/g", "g"

    # Workflow
    status = db.Column(db.String(20), default="pending", index=True)  # pending, approved, rejected
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reject_reason = db.Column(db.String(200), nullable=True)

    # AnalysisResult-д хадгалагдсан бол
    analysis_result_id = db.Column(db.Integer, db.ForeignKey("analysis_result.id", ondelete="SET NULL"), nullable=True)

    # Timestamps
    read_at = db.Column(db.DateTime, default=now_mn, index=True)  # Файлаас уншсан цаг
    created_at = db.Column(db.DateTime, default=now_mn)

    # Relationships
    equipment = db.relationship("Equipment", backref="instrument_readings")
    sample = db.relationship("Sample", backref="instrument_readings")
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])

    __table_args__ = (
        db.Index("ix_instr_reading_status_read_at", "status", "read_at"),
    )

    def __repr__(self):
        return f"<InstrumentReading {self.instrument_name} {self.sample_code} {self.analysis_code}={self.parsed_value}>"
