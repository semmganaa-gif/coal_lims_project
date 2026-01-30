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
