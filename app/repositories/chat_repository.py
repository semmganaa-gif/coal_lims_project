# app/repositories/chat_repository.py
# -*- coding: utf-8 -*-
"""Chat Repository - Чат мессежийн database operations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import or_, select

from app import db
from app.models import ChatMessage, UserOnlineStatus


class ChatMessageRepository:
    """ChatMessage model-ийн database operations."""

    @staticmethod
    def get_by_id(message_id: int) -> Optional[ChatMessage]:
        return db.session.get(ChatMessage, message_id)

    @staticmethod
    def get_conversation(user1_id: int, user2_id: int, limit: int = 50) -> list[ChatMessage]:
        return (
            ChatMessage.query
            .filter(
                ChatMessage.is_deleted.is_(False),
                or_(
                    db.and_(
                        ChatMessage.sender_id == user1_id,
                        ChatMessage.receiver_id == user2_id,
                    ),
                    db.and_(
                        ChatMessage.sender_id == user2_id,
                        ChatMessage.receiver_id == user1_id,
                    ),
                ),
            )
            .order_by(ChatMessage.sent_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_broadcasts(limit: int = 50) -> list[ChatMessage]:
        return (
            ChatMessage.query
            .filter_by(is_broadcast=True, is_deleted=False)
            .order_by(ChatMessage.sent_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        return (
            ChatMessage.query
            .filter(
                ChatMessage.receiver_id == user_id,
                ChatMessage.read_at.is_(None),
                ChatMessage.is_deleted.is_(False),
            )
            .count()
        )

    @staticmethod
    def mark_as_read(message_ids: list[int], commit: bool = False) -> int:
        from app.utils.datetime import now_local as now_mn
        count = (
            ChatMessage.query
            .filter(
                ChatMessage.id.in_(message_ids),
                ChatMessage.read_at.is_(None),
            )
            .update({ChatMessage.read_at: now_mn()}, synchronize_session=False)
        )
        if commit:
            db.session.commit()
        return count

    @staticmethod
    def save(message: ChatMessage, commit: bool = False) -> ChatMessage:
        db.session.add(message)
        if commit:
            db.session.commit()
        return message

    @staticmethod
    def soft_delete(message: ChatMessage, commit: bool = False) -> bool:
        from app.utils.datetime import now_local as now_mn
        message.is_deleted = True
        message.deleted_at = now_mn()
        if commit:
            db.session.commit()
        return True


class UserOnlineStatusRepository:
    """UserOnlineStatus model-ийн database operations."""

    @staticmethod
    def get_by_user_id(user_id: int) -> Optional[UserOnlineStatus]:
        return db.session.get(UserOnlineStatus, user_id)

    @staticmethod
    def get_online_users() -> list[UserOnlineStatus]:
        stmt = select(UserOnlineStatus).where(UserOnlineStatus.is_online.is_(True))
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def set_online(user_id: int, socket_id: str, commit: bool = False) -> UserOnlineStatus:
        status = db.session.get(UserOnlineStatus, user_id)
        if not status:
            status = UserOnlineStatus(user_id=user_id)
            db.session.add(status)
        status.is_online = True
        status.socket_id = socket_id
        from app.utils.datetime import now_local as now_mn
        status.last_seen = now_mn()
        if commit:
            db.session.commit()
        return status

    @staticmethod
    def set_offline(user_id: int, commit: bool = False) -> Optional[UserOnlineStatus]:
        status = db.session.get(UserOnlineStatus, user_id)
        if status:
            status.is_online = False
            from app.utils.datetime import now_local as now_mn
            status.last_seen = now_mn()
            if commit:
                db.session.commit()
        return status
