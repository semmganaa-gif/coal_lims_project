# -*- coding: utf-8 -*-
"""
System audit log model.

Системийн бүх чухал үйлдлүүдийг бүртгэх (ISO 17025).
Login, logout, дээж устгах, хэрэглэгч үүсгэх зэрэг.
"""

from app import db
from app.models.mixins import HashableMixin
from app.utils.datetime import now_local as now_mn


class AuditLog(HashableMixin, db.Model):
    """
    Аудитын лог - бүх чухал үйлдлүүдийг бүртгэнэ.

    Бүртгэх үйлдлүүд:
    - Нэвтрэх/гарах (login, logout)
    - Дээж устгах (delete_sample)
    - Хэрэглэгч үүсгэх/устгах (create_user, delete_user)
    - Тохиргоо өөрчлөх (update_settings)
    - Үр дүн баталгаажуулах/буцаах (approve_result, reject_result)

    ISO 17025 compliance:
    - Бүх үйлдлийг мөрдөн шалгах боломжтой
    - Хэн, хэзээ, юу хийсэн эсэх бүртгэгдэнэ
    """
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=now_mn, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    action = db.Column(db.String(50), nullable=False, index=True)  # login, logout, delete_sample, etc
    resource_type = db.Column(db.String(50), index=True)  # Sample, User, Equipment, AnalysisResult
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON хэлбэрээр дэлгэрэнгүй мэдээлэл
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(200))

    # ISO 17025: Audit log integrity hash
    data_hash = db.Column(db.String(64), nullable=True)

    # Relationship
    user = db.relationship("User", backref="audit_logs")

    def _get_hash_data(self) -> str:
        """HashableMixin: Return data string for hashing."""
        return (
            f"{self.user_id}|{self.action}|{self.resource_type}|"
            f"{self.resource_id}|{self.timestamp}|{self.details}|{self.ip_address}"
        )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by user_id={self.user_id} at {self.timestamp}>"
