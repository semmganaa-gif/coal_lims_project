# app/labs/water/__init__.py
"""Усны лаборатори."""

from app.labs.base import BaseLab


class WaterLab(BaseLab):
    """Усны лаборатори."""

    @property
    def key(self) -> str:
        return 'water'

    @property
    def name(self) -> str:
        return 'Усны лаборатори'

    @property
    def icon(self) -> str:
        return 'bi-droplet'

    @property
    def color(self) -> str:
        return '#0dcaf0'

    @property
    def analysis_codes(self) -> list[str]:
        from app.labs.water.constants import WATER_ANALYSIS_TYPES
        return [a['code'] for a in WATER_ANALYSIS_TYPES]
