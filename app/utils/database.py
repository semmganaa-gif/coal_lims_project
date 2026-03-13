# app/utils/database.py
# -*- coding: utf-8 -*-
"""
Өгөгдлийн сантай ажиллах туслах функцүүд.
Давхардсан error handling кодыг арилгах зорилготой.
"""
import logging
from typing import Optional, Any, List, Union
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError
from app import db

logger = logging.getLogger(__name__)


def _flash_msg(msg: str, category: str) -> None:
    """Flash message only when inside a request context."""
    try:
        from flask import flash
        flash(msg, category)
    except RuntimeError:
        # No request context (CLI, background task, test)
        pass


def safe_commit(
    success_msg: Optional[str] = None,
    error_msg: str = "Error saving data",
    notify: bool = True,
) -> bool:
    """
    Database commit-ийг аюулгүй хийх helper функц.

    Args:
        success_msg: Амжилттай үед харуулах мессеж (None бол харуулахгүй).
        error_msg: Алдаа гарсан үед харуулах мессеж.
        notify: False бол flash() дуудахгүй (service layer-д ашиглах).

    Returns:
        bool: True - амжилттай, False - алдаа гарсан
    """
    try:
        db.session.commit()
        if notify and success_msg:
            _flash_msg(success_msg, "success")
        return True
    except StaleDataError:
        db.session.rollback()
        logger.warning("StaleDataError: concurrent edit detected")
        if notify:
            _flash_msg(
                "Өөр хэрэглэгч энэ мэдээллийг засварласан байна. Дахин оролдоно уу.",
                "warning",
            )
        return False
    except IntegrityError:
        db.session.rollback()
        if notify:
            _flash_msg(error_msg, "danger")
        return False
    except SQLAlchemyError as e:
        try:
            db.session.rollback()
        except Exception as rb_err:
            logger.critical(f"Rollback failed: {rb_err}")
        logger.error(f"{error_msg}: {e}")
        if notify:
            _flash_msg(error_msg, "danger")
        return False


def safe_delete(
    obj: Any,
    success_msg: Optional[str] = None,
    error_msg: str = "Устгахад алдаа гарлаа",
    notify: bool = True,
) -> bool:
    """
    Объектыг аюулгүй устгах helper функц.

    Args:
        obj: Устгах SQLAlchemy объект.
        success_msg: Амжилттай үед харуулах мессеж.
        error_msg: Алдаа гарсан үед харуулах мессеж.
        notify: False бол flash() дуудахгүй.

    Returns:
        bool: True - амжилттай, False - алдаа гарсан
    """
    try:
        db.session.delete(obj)
        db.session.commit()
        if notify and success_msg:
            _flash_msg(success_msg, "success")
        return True
    except SQLAlchemyError as e:
        try:
            db.session.rollback()
        except Exception as rb_err:
            logger.critical(f"Rollback failed: {rb_err}")
        logger.error(f"{error_msg}: {e}")
        if notify:
            _flash_msg(error_msg, "danger")
        return False


def safe_add(
    obj: Union[Any, List[Any]],
    success_msg: Optional[str] = None,
    error_msg: str = "Нэмэхэд алдаа гарлаа",
    notify: bool = True,
) -> bool:
    """
    Объектыг аюулгүй нэмэх helper функц.

    Args:
        obj: Нэмэх SQLAlchemy объект (эсвэл objects-ийн list).
        success_msg: Амжилттай үед харуулах мессеж.
        error_msg: Алдаа гарсан үед харуулах мессеж.
        notify: False бол flash() дуудахгүй.

    Returns:
        bool: True - амжилттай, False - алдаа гарсан
    """
    try:
        if isinstance(obj, list):
            db.session.add_all(obj)
        else:
            db.session.add(obj)
        db.session.commit()
        if notify and success_msg:
            _flash_msg(success_msg, "success")
        return True
    except IntegrityError:
        db.session.rollback()
        if notify:
            _flash_msg(error_msg, "danger")
        return False
    except SQLAlchemyError as e:
        try:
            db.session.rollback()
        except Exception as rb_err:
            logger.critical(f"Rollback failed: {rb_err}")
        logger.error(f"{error_msg}: {e}")
        if notify:
            _flash_msg(error_msg, "danger")
        return False
