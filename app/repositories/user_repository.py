# app/repositories/user_repository.py
# -*- coding: utf-8 -*-
"""User Repository - Хэрэглэгчийн database operations.

SQLAlchemy 2.0 native API (`select()` builder) ашиглана.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app import db
from app.models import User


class UserRepository:
    """User model-ийн database operations."""

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_id_or_404(user_id: int) -> User:
        user = db.session.get(User, user_id)
        if user is None:
            from flask import abort
            abort(404)
        return user

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def username_exists(username: str, exclude_id: Optional[int] = None) -> bool:
        stmt = select(User.id).where(User.username == username)
        if exclude_id:
            stmt = stmt.where(User.id != exclude_id)
        return db.session.execute(stmt.limit(1)).first() is not None

    @staticmethod
    def get_all() -> list[User]:
        stmt = select(User).order_by(User.username)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_by_role(role: str) -> list[User]:
        stmt = select(User).where(User.role == role).order_by(User.username)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_by_roles(roles: list[str]) -> list[User]:
        stmt = select(User).where(User.role.in_(roles)).order_by(User.username)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def save(user: User, commit: bool = False) -> User:
        db.session.add(user)
        if commit:
            db.session.commit()
        return user

    @staticmethod
    def delete(user: User, commit: bool = False) -> bool:
        db.session.delete(user)
        if commit:
            db.session.commit()
        return True
