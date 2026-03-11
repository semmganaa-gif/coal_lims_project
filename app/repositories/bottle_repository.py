# app/repositories/bottle_repository.py
# -*- coding: utf-8 -*-
"""Bottle Repository - Бортого/пикнометрийн database operations."""

from __future__ import annotations

from typing import Optional

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
        return Bottle.query.filter_by(serial_no=serial_no).first()

    @staticmethod
    def serial_exists(serial_no: str, exclude_id: Optional[int] = None) -> bool:
        query = Bottle.query.filter(Bottle.serial_no == serial_no)
        if exclude_id:
            query = query.filter(Bottle.id != exclude_id)
        return query.first() is not None

    @staticmethod
    def get_all() -> list[Bottle]:
        return Bottle.query.all()

    @staticmethod
    def get_active() -> list[Bottle]:
        return Bottle.query.filter_by(is_active=True).all()

    @staticmethod
    def save(bottle: Bottle, commit: bool = True) -> Bottle:
        db.session.add(bottle)
        if commit:
            db.session.commit()
        return bottle

    @staticmethod
    def delete(bottle: Bottle, commit: bool = True) -> bool:
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
        return (
            BottleConstant.query
            .filter_by(bottle_id=bottle_id)
            .order_by(BottleConstant.effective_from.desc())
            .all()
        )

    @staticmethod
    def save(constant: BottleConstant, commit: bool = True) -> BottleConstant:
        db.session.add(constant)
        if commit:
            db.session.commit()
        return constant
