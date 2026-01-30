# app/labs/coal/__init__.py
"""
Нүүрсний лаборатори.

Одоо байгаа кодруу заана — шинэ route/template нэмэхгүй.
"""

from app.labs.base import BaseLab


class CoalLab(BaseLab):
    """Нүүрсний лаборатори (одоо байгаа LIMS)."""

    @property
    def key(self) -> str:
        return 'coal'

    @property
    def name(self) -> str:
        return 'Нүүрсний лаборатори'

    @property
    def icon(self) -> str:
        return 'bi-fire'

    @property
    def color(self) -> str:
        return '#dc3545'

    @property
    def analysis_codes(self) -> list[str]:
        return [
            'MT', 'Mad', 'Aad', 'Vad', 'TS', 'CV', 'CSN', 'Gi',
            'TRD', 'P', 'Solid', 'FM', 'F', 'Cl', 'X', 'Y',
            'CRI', 'CSR', 'm'
        ]
