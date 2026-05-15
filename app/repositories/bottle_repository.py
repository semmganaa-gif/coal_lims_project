# app/repositories/bottle_repository.py
# -*- coding: utf-8 -*-
"""Bottle Repository - Бортого/пикнометрийн database operations.

SQLAlchemy 2.0 native API (`select()` builder) ашиглана.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app import db
from app.models import Bottle, BottleConstant


class BottleRepository:
    """Bottle model-ийн database operations."""

    @staticmethod
    def get_by_id(bottle_id: int) -> Optional[Bottle]:
        return db.session.get(Bottle, bottle_id)

    @staticmethod
    def get_by_id_or_404(bottle_id: int) -> Bottle:
        bottle = db.session.get(Bottle, bottle_id)
        if bottle is None:
            from flask import abort
            abort(404)
        return bottle

    @staticmethod
    def get_by_serial(serial_no: str) -> Optional[Bottle]:
        stmt = select(Bottle).where(Bottle.serial_no == serial_no)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def serial_exists(serial_no: str, exclude_id: Optional[int] = None) -> bool:
        stmt = select(Bottle.id).where(Bottle.serial_no == serial_no)
        if exclude_id:
            stmt = stmt.where(Bottle.id != exclude_id)
        return db.session.execute(stmt.limit(1)).first() is not None

    @staticmethod
    def get_all() -> list[Bottle]:
        stmt = select(Bottle)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_active() -> list[Bottle]:
        stmt = select(Bottle).where(Bottle.is_active.is_(True))
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def save(bottle: Bottle, commit: bool = False) -> Bottle:
        db.session.add(bottle)
        if commit:
            db.session.commit()
        return bottle

    @staticmethod
    def delete(bottle: Bottle, commit: bool = False) -> bool:
        db.session.delete(bottle)
        if commit:
            db.session.commit()
        return True


class BottleConstantRepository:
    """BottleConstant model-ийн database operations."""

    @staticmethod
    def get_by_id(constant_id: int) -> Optional[BottleConstant]:
        return db.session.get(BottleConstant, constant_id)

    @staticmethod
    def get_by_bottle(bottle_id: int) -> list[BottleConstant]:
        stmt = (
            select(BottleConstant)
            .where(BottleConstant.bottle_id == bottle_id)
            .order_by(BottleConstant.effective_from.desc())
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def save(constant: BottleConstant, commit: bool = False) -> BottleConstant:
        db.session.add(constant)
        if commit:
            db.session.commit()
        return constant
