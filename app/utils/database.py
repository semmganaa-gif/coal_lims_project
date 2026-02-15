# app/utils/database.py
# -*- coding: utf-8 -*-
"""
Өгөгдлийн сантай ажиллах туслах функцүүд.
Давхардсан error handling кодыг арилгах зорилготой.
"""
from typing import Optional, Any, List, Union
from flask import flash
from sqlalchemy.exc import IntegrityError
from app import db


def safe_commit(success_msg: Optional[str] = None, error_msg: str = "Error saving data") -> bool:
    """
    Database commit-ийг аюулгүй хийх helper функц.
    IntegrityError болон бусад алдааг барьж, хэрэглэгчид мэдэгдэнэ.

    Args:
        success_msg (str, optional): Амжилттай үед харуулах мессеж.
                                     None бол flash харуулахгүй.
        error_msg (str): Алдаа гарсан үед харуулах мессеж.

    Returns:
        bool: True - амжилттай, False - алдаа гарсан

    Жишээ ашиглалт:
        >>> if safe_commit("Хадгалагдлаа!", "Давхардсан код байна"):
        >>>     return redirect(url_for('main.index'))
        >>> else:
        >>>     return render_template('form.html', form=form)
    """
    try:
        db.session.commit()
        if success_msg:
            flash(success_msg, "success")
        return True
    except IntegrityError:
        db.session.rollback()
        flash(error_msg, "danger")
        return False
    except Exception as e:
        db.session.rollback()
        # Ерөнхий алдааг барих
        flash(f"{error_msg}: {str(e)}", "danger")
        return False


def safe_delete(obj: Any, success_msg: Optional[str] = None, error_msg: str = "Устгахад алдаа гарлаа") -> bool:
    """
    Объектыг аюулгүй устгах helper функц.

    Args:
        obj: Устгах SQLAlchemy объект
        success_msg (str, optional): Амжилттай үед харуулах мессеж
        error_msg (str): Алдаа гарсан үед харуулах мессеж

    Returns:
        bool: True - амжилттай, False - алдаа гарсан

    Жишээ ашиглалт:
        >>> sample = Sample.query.get(sample_id)
        >>> if safe_delete(sample, "Дээж deleted.):
        >>>     return redirect(url_for('main.index'))
    """
    try:
        db.session.delete(obj)
        db.session.commit()
        if success_msg:
            flash(success_msg, "success")
        return True
    except Exception as e:
        db.session.rollback()
        flash(f"{error_msg}: {str(e)}", "danger")
        return False


def safe_add(
    obj: Union[Any, List[Any]],
    success_msg: Optional[str] = None,
    error_msg: str = "Нэмэхэд алдаа гарлаа"
) -> bool:
    """
    Объектыг аюулгүй нэмэх helper функц.

    Args:
        obj: Нэмэх SQLAlchemy объект (эсвэл objects-ийн list)
        success_msg (str, optional): Амжилттай үед харуулах мессеж
        error_msg (str): Алдаа гарсан үед харуулах мессеж

    Returns:
        bool: True - амжилттай, False - алдаа гарсан

    Жишээ ашиглалт:
        >>> user = User(username="test")
        >>> if safe_add(user, "Хэрэглэгч added., "Нэр давхардсан"):
        >>>     return redirect(url_for('admin.users'))
    """
    try:
        if isinstance(obj, list):
            db.session.add_all(obj)
        else:
            db.session.add(obj)
        db.session.commit()
        if success_msg:
            flash(success_msg, "success")
        return True
    except IntegrityError:
        db.session.rollback()
        flash(error_msg, "danger")
        return False
    except Exception as e:
        db.session.rollback()
        flash(f"{error_msg}: {str(e)}", "danger")
        return False
