# app/repositories/user_repository.py
# -*- coding: utf-8 -*-
"""User Repository - Хэрэглэгчийн database operations."""

from __future__ import annotations

from typing import Optional

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
        return User.query.filter_by(username=username).first()

    @staticmethod
    def username_exists(username: str, exclude_id: Optional[int] = None) -> bool:
        query = User.query.filter_by(username=username)
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        return query.first() is not None

    @staticmethod
    def get_all() -> list[User]:
        return User.query.order_by(User.username).all()

    @staticmethod
    def get_by_role(role: str) -> list[User]:
        return User.query.filter_by(role=role).order_by(User.username).all()

    @staticmethod
    def get_by_roles(roles: list[str]) -> list[User]:
        return User.query.filter(User.role.in_(roles)).order_by(User.username).all()

    @staticmethod
    def save(user: User, commit: bool = True) -> User:
        db.session.add(user)
        if commit:
            db.session.commit()
        return user

    @staticmethod
    def delete(user: User, commit: bool = True) -> bool:
        db.session.delete(user)
        if commit:
            db.session.commit()
        return True
