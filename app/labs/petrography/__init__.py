# app/labs/petrography/__init__.py
"""Петрограф лаборатори."""

from app.labs.base import BaseLab


class PetrographyLab(BaseLab):
    """Петрограф лаборатори."""

    @property
    def key(self) -> str:
        return 'petrography'

    @property
    def name(self) -> str:
        return 'Петрограф лаборатори'

    @property
    def icon(self) -> str:
        return 'bi-gem'

    @property
    def color(self) -> str:
        return '#6f42c1'

    @property
    def analysis_codes(self) -> list[str]:
        from app.labs.petrography.constants import PETRO_ANALYSIS_TYPES
        return [a['code'] for a in PETRO_ANALYSIS_TYPES]
