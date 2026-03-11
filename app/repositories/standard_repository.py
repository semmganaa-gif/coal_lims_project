# app/repositories/standard_repository.py
# -*- coding: utf-8 -*-
"""GbwStandard / ControlStandard Repository — стандарт дээжний database operations."""

from __future__ import annotations
from typing import Optional

from app import db
from app.models import GbwStandard, ControlStandard


class GbwStandardRepository:
    """GbwStandard model-ийн database operations."""

    @staticmethod
    def get_by_id(standard_id: int) -> Optional[GbwStandard]:
        return db.session.get(GbwStandard, standard_id)

    @staticmethod
    def get_all_ordered() -> list[GbwStandard]:
        return GbwStandard.query.order_by(GbwStandard.created_at.desc()).all()

    @staticmethod
    def get_active() -> Optional[GbwStandard]:
        return GbwStandard.query.filter_by(is_active=True).first()

    @staticmethod
    def get_by_name(name: str, active_only: bool = False) -> Optional[GbwStandard]:
        q = GbwStandard.query.filter_by(name=name)
        if active_only:
            q = q.filter_by(is_active=True)
        return q.first()

    @staticmethod
    def get_active_or_by_name(name: str) -> Optional[GbwStandard]:
        """Нэрээр идэвхтэй хайж, олдохгүй бол нэрээр ямар ч статустай хайна."""
        std = GbwStandard.query.filter_by(name=name, is_active=True).first()
        if not std:
            std = GbwStandard.query.filter_by(name=name).first()
        return std

    @staticmethod
    def deactivate_all(commit: bool = False) -> int:
        count = GbwStandard.query.update({GbwStandard.is_active: False})
        if commit:
            db.session.commit()
        return count

    @staticmethod
    def save(standard: GbwStandard, commit: bool = True) -> GbwStandard:
        db.session.add(standard)
        if commit:
            db.session.commit()
        return standard

    @staticmethod
    def delete(standard: GbwStandard, commit: bool = True) -> bool:
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
        return ControlStandard.query.order_by(ControlStandard.created_at.desc()).all()

    @staticmethod
    def get_active() -> Optional[ControlStandard]:
        return ControlStandard.query.filter_by(is_active=True).first()

    @staticmethod
    def get_by_name(name: str, active_only: bool = False) -> Optional[ControlStandard]:
        q = ControlStandard.query.filter_by(name=name)
        if active_only:
            q = q.filter_by(is_active=True)
        return q.first()

    @staticmethod
    def get_active_or_by_name(name: str) -> Optional[ControlStandard]:
        """Нэрээр идэвхтэй хайж, олдохгүй бол нэрээр ямар ч статустай хайна."""
        std = ControlStandard.query.filter_by(name=name, is_active=True).first()
        if not std:
            std = ControlStandard.query.filter_by(name=name).first()
        if not std:
            std = ControlStandard.query.filter_by(is_active=True).first()
        return std

    @staticmethod
    def deactivate_all(commit: bool = False) -> int:
        count = ControlStandard.query.update({ControlStandard.is_active: False})
        if commit:
            db.session.commit()
        return count

    @staticmethod
    def save(standard: ControlStandard, commit: bool = True) -> ControlStandard:
        db.session.add(standard)
        if commit:
            db.session.commit()
        return standard

    @staticmethod
    def delete(standard: ControlStandard, commit: bool = True) -> bool:
        db.session.delete(standard)
        if commit:
            db.session.commit()
        return True
