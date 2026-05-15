# -*- coding: utf-8 -*-
"""
Report-related models.

Separated from models.py for maintainability.
"""

from app import db
from app.utils.datetime import now_local as now_mn


# -------------------------
# ТАЙЛАНГИЙН СИСТЕМ (Report Generation)
# -------------------------
class ReportSignature(db.Model):
    """
    Гарын үсэг, тамганы зураг хадгалах.

    Чанарын менежер, шинжээч нарын гарын үсэг болон
    лабораторийн тамганы зургийг хадгална.

    Attributes:
        id (int): Primary key
        name (str): Нэр (жишээ: "Ц.Бэхцэцэг - Ахлах менежер")
        signature_type (str): Төрөл (signature, stamp)
        image_path (str): Зургийн зам
        user_id (int): Холбоотой хэрэглэгч (optional)
        lab_type (str): Лаб төрөл
        is_active (bool): Идэвхтэй эсэх
        position (str): Албан тушаал
    """
    __tablename__ = 'report_signature'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    signature_type = db.Column(db.String(20), nullable=False)  # 'signature', 'stamp'
    image_path = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), index=True)
    lab_type = db.Column(db.String(30), default='all')
    is_active = db.Column(db.Boolean, default=True)
    position = db.Column(db.String(100))  # Албан тушаал

    created_at = db.Column(db.DateTime, default=now_mn)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])

    def __repr__(self):
        return f"<ReportSignature {self.name} ({self.signature_type})>"


class LabReport(db.Model):
    """
    Лабораторийн тайлангийн бүртгэл.

    Нэгтгэлээс үүсгэсэн PDF тайлангуудыг хадгалах,
    баталгаажуулах, имэйлээр илгээх.

    Attributes:
        id (int): Primary key
        report_number (str): Тайлангийн дугаар (жишээ: 2026_15)
        lab_type (str): Лаб төрөл (coal, water, microbiology, petrography)
        report_type (str): Тайлангийн төрөл (analysis, summary, certificate)
        title (str): Гарчиг
        status (str): Төлөв (draft, pending_approval, approved, sent)

        # Дээжийн мэдээлэл
        sample_ids (JSON): Холбоотой дээжийн ID-ууд
        date_from (date): Эхлэх огноо
        date_to (date): Дуусах огноо

        # Файл
        pdf_path (str): PDF файлын зам

        # Гарын үсэг
        analyst_signature_id (int): Шинжээчийн гарын үсэг
        manager_signature_id (int): Менежерийн гарын үсэг
        stamp_id (int): Тамга

        # Баталгаажуулалт
        approved_by_id (int): Баталгаажуулсан хүн
        approved_at (datetime): Баталгаажуулсан огноо

        # Имэйл
        email_sent (bool): Илгээсэн эсэх
        email_sent_at (datetime): Илгээсэн огноо
        email_recipients (str): Хүлээн авагчид

        # Мета
        created_by_id (int): Үүсгэсэн хүн
        created_at (datetime): Үүсгэсэн огноо
    """
    __tablename__ = 'lab_report'

    id = db.Column(db.Integer, primary_key=True)
    report_number = db.Column(db.String(50), unique=True, nullable=False)
    lab_type = db.Column(db.String(30), nullable=False, index=True)
    report_type = db.Column(db.String(30), default='analysis')
    title = db.Column(db.String(255))
    status = db.Column(db.String(20), default='draft', index=True)
    # draft, pending_approval, approved, sent

    # Дээжийн мэдээлэл
    sample_ids = db.Column(db.JSON)  # [1, 2, 3, ...]
    date_from = db.Column(db.Date)
    date_to = db.Column(db.Date)

    # Тайлангийн агуулга (JSON)
    report_data = db.Column(db.JSON)

    # PDF файл
    pdf_path = db.Column(db.String(255))

    # Гарын үсэг, тамга
    analyst_signature_id = db.Column(db.Integer, db.ForeignKey('report_signature.id'), index=True)
    manager_signature_id = db.Column(db.Integer, db.ForeignKey('report_signature.id'), index=True)
    stamp_id = db.Column(db.Integer, db.ForeignKey('report_signature.id'), index=True)

    # Баталгаажуулалт
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), index=True)
    approved_at = db.Column(db.DateTime)

    # Имэйл
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime)
    email_recipients = db.Column(db.Text)  # comma-separated

    # Мета
    notes = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), index=True)
    created_at = db.Column(db.DateTime, default=now_mn)
    updated_at = db.Column(db.DateTime, default=now_mn, onupdate=now_mn)

    # Relationships
    analyst_signature = db.relationship('ReportSignature', foreign_keys=[analyst_signature_id])
    manager_signature = db.relationship('ReportSignature', foreign_keys=[manager_signature_id])
    stamp = db.relationship('ReportSignature', foreign_keys=[stamp_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    __table_args__ = (
        db.Index('ix_lab_report_lab_status', 'lab_type', 'status'),
    )

    def __repr__(self):
        return f"<LabReport {self.report_number} ({self.status})>"

    def get_status_display(self):
        status_map = {
            'draft': 'Ноорог',
            'pending_approval': 'Хүлээгдэж буй',
            'approved': 'Баталгаажсан',
            'sent': 'Илгээсэн',
        }
        return status_map.get(self.status, self.status)
