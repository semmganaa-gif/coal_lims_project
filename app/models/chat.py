# -*- coding: utf-8 -*-
"""
Chat models.
"""

from app import db
from app.utils.datetime import now_local as now_mn

class ChatMessage(db.Model):
    """
    Химич ↔ Ахлах чат мессеж.
    Real-time харилцааны түүхийг хадгална.
    """
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True, index=True)  # null = broadcast
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=now_mn, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    message_type = db.Column(db.String(20), default='text')  # text, image, file, sample, urgent

    # Файл хавсралт
    file_url = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)  # bytes

    # Яаралтай мессеж
    is_urgent = db.Column(db.Boolean, default=False)

    # Дээж/Шинжилгээ холбох
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id', ondelete="SET NULL"), nullable=True, index=True)

    # Устгах (soft delete)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Broadcast мессеж
    is_broadcast = db.Column(db.Boolean, default=False)

    # Composite indexes — чат query-уудыг хурдасгах
    __table_args__ = (
        db.Index('ix_chat_receiver_read', 'receiver_id', 'read_at'),
        db.Index('ix_chat_sender_receiver', 'sender_id', 'receiver_id'),
    )

    # Relationships
    sender = db.relationship(
        'User', foreign_keys=[sender_id],
        backref=db.backref('sent_messages', passive_deletes=True),
    )
    receiver = db.relationship(
        'User', foreign_keys=[receiver_id],
        backref=db.backref('received_messages', passive_deletes=True),
    )
    sample = db.relationship('Sample', backref='chat_messages')

    def __repr__(self):
        return f"<ChatMessage {self.id}: {self.sender_id} → {self.receiver_id}>"

    def to_dict(self):
        """JSON serialization"""
        result = {
            'id': self.id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.username if self.sender else None,
            'receiver_id': self.receiver_id,
            'receiver_name': self.receiver.username if self.receiver else None,
            'message': self.message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'is_read': self.read_at is not None,
            'message_type': self.message_type,
            'is_urgent': self.is_urgent,
            'is_broadcast': self.is_broadcast,
            'is_deleted': self.is_deleted,
            # Файл талбарууд (top-level for JS)
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'sample_id': self.sample_id
        }
        # Файл мэдээлэл (nested object)
        if self.file_url:
            result['file'] = {
                'url': self.file_url,
                'name': self.file_name,
                'size': self.file_size
            }
        # Дээж мэдээлэл
        if self.sample_id and self.sample:
            result['sample'] = {
                'id': self.sample.id,
                'code': self.sample.sample_code,
                'type': self.sample.sample_type
            }
        return result


class UserOnlineStatus(db.Model):
    """
    Хэрэглэгчийн онлайн статус.
    WebSocket холболттой үед шинэчлэгдэнэ.
    """
    __tablename__ = "user_online_status"

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=now_mn)
    socket_id = db.Column(db.String(100), nullable=True)  # Current socket session ID

    # Relationship
    user = db.relationship(
        'User',
        backref=db.backref('online_status', uselist=False, passive_deletes=True),
    )

    def __repr__(self):
        status = "online" if self.is_online else "offline"
        return f"<UserOnlineStatus {self.user_id}: {status}>"
