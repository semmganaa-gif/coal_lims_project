# app/labs/base.py
"""
BaseLab abstract class.

Бүх лаборатори энэ классаас удамшина.
"""

from abc import ABC, abstractmethod


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
        """Энэ лабын дээжийн query."""
        from app.models import Sample
        q = Sample.query.filter(Sample.lab_type == self.key)
        if statuses:
            q = q.filter(Sample.status.in_(statuses))
        return q

    def sample_stats(self):
        """Dashboard-д хэрэглэх тоон мэдээлэл."""
        from app.models import Sample
        base = Sample.query.filter(Sample.lab_type == self.key)
        return {
            'total': base.count(),
            'new': base.filter(Sample.status == 'new').count(),
            'in_progress': base.filter(Sample.status.in_(['in_progress', 'analysis'])).count(),
            'completed': base.filter(Sample.status == 'completed').count(),
        }
