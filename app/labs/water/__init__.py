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

    def sample_query(self, statuses=None):
        """Ус + Микро хоёр lab_type-ыг хамтад нь шүүнэ."""
        from app.models import Sample
        q = Sample.query.filter(Sample.lab_type.in_(['water', 'microbiology', 'water & micro']))
        if statuses:
            q = q.filter(Sample.status.in_(statuses))
        return q

    def sample_stats(self):
        """Ус + Микро хамтын тоон мэдээлэл."""
        from app.models import Sample
        base = Sample.query.filter(Sample.lab_type.in_(['water', 'microbiology', 'water & micro']))
        return {
            'total': base.count(),
            'new': base.filter(Sample.status == 'new').count(),
            'in_progress': base.filter(Sample.status.in_(['in_progress', 'analysis'])).count(),
            'completed': base.filter(Sample.status == 'completed').count(),
        }
