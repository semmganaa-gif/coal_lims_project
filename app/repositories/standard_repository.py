# app/repositories/standard_repository.py
# -*- coding: utf-8 -*-
"""GbwStandard / ControlStandard Repository — стандарт дээжний database operations.

SQLAlchemy 2.0 native API (`select()` / `update()`) ашиглана.
"""

from __future__ import annotations
from typing import Optional

from sqlalchemy import select, update

from app import db
from app.models import GbwStandard, ControlStandard


class GbwStandardRepository:
    """GbwStandard model-ийн database operations."""

    @staticmethod
    def get_by_id(standard_id: int) -> Optional[GbwStandard]:
        return db.session.get(GbwStandard, standard_id)

    @staticmethod
    def get_all_ordered() -> list[GbwStandard]:
        stmt = select(GbwStandard).order_by(GbwStandard.created_at.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_active() -> Optional[GbwStandard]:
        stmt = select(GbwStandard).where(GbwStandard.is_active.is_(True))
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_name(name: str, active_only: bool = False) -> Optional[GbwStandard]:
        stmt = select(GbwStandard).where(GbwStandard.name == name)
        if active_only:
            stmt = stmt.where(GbwStandard.is_active.is_(True))
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_active_or_by_name(name: str) -> Optional[GbwStandard]:
        """Нэрээр идэвхтэй хайж, олдохгүй бол нэрээр ямар ч статустай хайна."""
        active_stmt = select(GbwStandard).where(
            GbwStandard.name == name,
            GbwStandard.is_active.is_(True),
        )
        std = db.session.execute(active_stmt).scalar_one_or_none()
        if not std:
            any_stmt = select(GbwStandard).where(GbwStandard.name == name)
            std = db.session.execute(any_stmt).scalar_one_or_none()
        return std

    @staticmethod
    def deactivate_all(commit: bool = False) -> int:
        stmt = update(GbwStandard).values(is_active=False)
        count = db.session.execute(stmt).rowcount
        if commit:
            db.session.commit()
        return count

    @staticmethod
    def save(standard: GbwStandard, commit: bool = False) -> GbwStandard:
        db.session.add(standard)
        if commit:
            db.session.commit()
        return standard

    @staticmethod
    def delete(standard: GbwStandard, commit: bool = False) -> bool:
        db.session.delete(standard)
        if commit:
            db.session.commit()
        return True


class ControlStandardRepository:
    """ControlStandard model-ийн database operations."""

    @staticmethod
    def get_by_id(standard_id: int) -> Optional[ControlStandard]:
        return db.session.get(ControlStandard, standard_id)

    @staticmethod
    def get_all_ordered() -> list[ControlStandard]:
        stmt = select(ControlStandard).order_by(ControlStandard.created_at.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_active() -> Optional[ControlStandard]:
        stmt = select(ControlStandard).where(ControlStandard.is_active.is_(True))
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_name(name: str, active_only: bool = False) -> Optional[ControlStandard]:
        stmt = select(ControlStandard).where(ControlStandard.name == name)
        if active_only:
            stmt = stmt.where(ControlStandard.is_active.is_(True))
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_active_or_by_name(name: str) -> Optional[ControlStandard]:
        """Нэрээр идэвхтэй хайж, олдохгүй бол нэрээр ямар ч статустай хайна."""
        active_stmt = select(ControlStandard).where(
            ControlStandard.name == name,
            ControlStandard.is_active.is_(True),
        )
        std = db.session.execute(active_stmt).scalar_one_or_none()
        if not std:
            any_stmt = select(ControlStandard).where(ControlStandard.name == name)
            std = db.session.execute(any_stmt).scalar_one_or_none()
        if not std:
            fallback_stmt = select(ControlStandard).where(ControlStandard.is_active.is_(True))
            std = db.session.execute(fallback_stmt).scalar_one_or_none()
        return std

    @staticmethod
    def deactivate_all(commit: bool = False) -> int:
        stmt = update(ControlStandard).values(is_active=False)
        count = db.session.execute(stmt).rowcount
        if commit:
            db.session.commit()
        return count

    @staticmethod
    def save(standard: ControlStandard, commit: bool = False) -> ControlStandard:
        db.session.add(standard)
        if commit:
            db.session.commit()
        return standard

    @staticmethod
    def delete(standard: ControlStandard, commit: bool = False) -> bool:
        db.session.delete(standard)
        if commit:
            db.session.commit()
        return True
