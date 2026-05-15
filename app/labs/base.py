# app/labs/base.py
"""
BaseLab abstract class.

Бүх лаборатори энэ классаас удамшина.
"""

from abc import ABC, abstractmethod

from sqlalchemy import func, select

from app.constants import SampleStatus


class BaseLab(ABC):
    """Лабораторийн суурь класс."""

    @property
    @abstractmethod
    def key(self) -> str:
        """Лабын өвөрмөц түлхүүр (ж: 'coal', 'petrography', 'water')."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Лабын нэр."""
        ...

    @property
    @abstractmethod
    def icon(self) -> str:
        """Bootstrap icon class."""
        ...

    @property
    @abstractmethod
    def color(self) -> str:
        """Лабын өнгө (hex)."""
        ...

    @property
    def analysis_codes(self) -> list[str]:
        """Энэ лабын шинжилгээний кодуудын жагсаалт."""
        return []

    def get_blueprint(self):
        """Flask Blueprint буцаах (хэрэв байвал)."""
        return None

    def sample_query(self, statuses=None):
        """Энэ лабын дээжийн `select()` statement (SQLAlchemy 2.0)."""
        from app.models import Sample
        stmt = select(Sample).where(Sample.lab_type == self.key)
        if statuses:
            stmt = stmt.where(Sample.status.in_(statuses))
        return stmt

    def sample_stats(self):
        """Dashboard-д хэрэглэх тоон мэдээлэл."""
        from app import db
        from app.models import Sample

        def _count(*conds):
            return db.session.execute(
                select(func.count(Sample.id)).where(
                    Sample.lab_type == self.key, *conds
                )
            ).scalar_one()

        return {
            'total': _count(),
            'new': _count(Sample.status == SampleStatus.NEW.value),
            'in_progress': _count(Sample.status.in_([SampleStatus.IN_PROGRESS.value, SampleStatus.ANALYSIS.value])),
            'completed': _count(Sample.status == SampleStatus.COMPLETED.value),
        }
