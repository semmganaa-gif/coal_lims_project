# app/labs/microbiology/__init__.py
"""Микробиологийн лаборатори."""

from app.labs.base import BaseLab


class MicrobiologyLab(BaseLab):
    """Микробиологийн лаборатори."""

    @property
    def key(self) -> str:
        return 'microbiology'

    @property
    def name(self) -> str:
        return 'Микробиологийн лаборатори'

    @property
    def icon(self) -> str:
        return 'bi-bug'

    @property
    def color(self) -> str:
        return '#20c997'

    @property
    def analysis_codes(self) -> list[str]:
        from app.labs.microbiology.constants import MICRO_ANALYSIS_TYPES
        return [a['code'] for a in MICRO_ANALYSIS_TYPES]
