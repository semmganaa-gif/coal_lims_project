# app/utils/transaction.py
# -*- coding: utf-8 -*-
"""
Transaction boundary decorator (CLAUDE.md convention).

Service layer-ийн entry function-уудад `@transactional`-ийг ашиглан DB
transaction-ийг автомат удирдана:

  ┌───────────────────────────────────────────────────────────────┐
  │ Route → @transactional service → Repository → Model           │
  │                ↓                       ↓                       │
  │            commit/rollback         add/delete (no commit)      │
  └───────────────────────────────────────────────────────────────┘

Зорилго:
- Services + Repositories `db.session.commit()` хийхгүй
- Зөвхөн `@transactional`-ийн дотор нэг commit явна
- Exception үед автомат rollback
- Олон Repository call-ийг нэг atomic transaction-аар хамгаалах

Хэрэглээ:

    from app.utils.transaction import transactional

    @transactional()
    def archive_samples(sample_ids: list[int]) -> ArchiveResult:
        # Олон Repository call атомик байх
        SampleRepository.update_status(sample_ids, "archived")
        for sid in sample_ids:
            log_audit(action="sample_archived", resource_id=sid)
        return ArchiveResult(success=True, ...)

Decorator commit хийнэ. Exception үед rollback + raise.

Read-only function-уудад:
    @transactional(readonly=True)
    def get_dashboard_stats() -> DashboardStats:
        ...

readonly=True үед commit/rollback хоёулаа skip — performance + safety.

Nested хэрэглээ:
    @transactional()
    def outer():
        inner()  # @transactional дотор @transactional — нэг transaction

    @transactional()
    def inner():
        ...

Аль нэг `@transactional` decorator-ыг дуудсан үед SAVEPOINT биш — гадна
transaction-ыг ашиглана. Хамгийн гадна `@transactional` нь commit-ыг
эзэмшинэ.
"""
from __future__ import annotations

import logging
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, TypeVar

from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# Context flag for nested @transactional — гадна нь commit удирдана
_in_transaction: ContextVar[bool] = ContextVar("_in_transaction", default=False)

F = TypeVar("F", bound=Callable[..., Any])


def transactional(*, readonly: bool = False, reraise: bool = True) -> Callable[[F], F]:
    """
    DB transaction boundary decorator.

    Args:
        readonly: True бол commit/rollback хоёулаа skip (read-only path).
        reraise: True (default) бол rollback-ийн дараа exception дахин raise.
                 False бол silent fallback (зөвхөн background task-д ашиглах).

    Returns:
        Decorated function.

    Behavior:
        - Function амжилттай дуусвал commit (readonly=False үед).
        - SQLAlchemyError эсвэл бусад exception үед rollback + raise.
        - Nested @transactional дуудлага үед гадна нь commit-ыг хариуцна.

    Example:
        >>> @transactional()
        ... def archive_samples(ids: list[int]) -> int:
        ...     count = SampleRepository.update_status(ids, "archived")
        ...     return count
        >>>
        >>> # Read-only:
        >>> @transactional(readonly=True)
        ... def get_stats() -> dict:
        ...     return {...}
    """
    def decorator(f: F) -> F:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Import inside function — circular import safety
            from app import db

            # Гадна транзакц нээгдсэн эсэхийг шалгах (nested @transactional)
            outer_already_open = _in_transaction.get()
            if outer_already_open:
                # Гадна нь commit/rollback-ыг хариуцна
                return f(*args, **kwargs)

            token = _in_transaction.set(True)
            try:
                result = f(*args, **kwargs)
                if not readonly:
                    db.session.commit()
                return result
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.exception("Transaction rollback (%s): %s", f.__name__, e)
                if reraise:
                    raise
                return None
            except Exception as e:
                # Бизнес логик exception — мөн rollback (Repository .add() etc-ийг буцаах).
                db.session.rollback()
                logger.exception("Transaction rollback on non-SQL exception (%s): %s", f.__name__, e)
                if reraise:
                    raise
                return None
            finally:
                _in_transaction.reset(token)

        return wrapper  # type: ignore[return-value]
    return decorator


def in_transaction() -> bool:
    """Одоо @transactional-ийн дотор байгаа эсэхийг буцаах (test/debug-д)."""
    return _in_transaction.get()
