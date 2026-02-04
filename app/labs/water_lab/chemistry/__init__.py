# app/labs/water_lab/chemistry/__init__.py
"""Усны хими лаборатори (Chemistry Lab)."""

from app.labs.base import BaseLab


class ChemistryLab(BaseLab):
    """Усны хими лаборатори."""

    @property
    def key(self) -> str:
        return 'water'  # Backward compatibility

    @property
    def name(self) -> str:
        return 'Хими лаборатори'

    @property
    def icon(self) -> str:
        return 'bi-droplet-half'

    @property
    def color(self) -> str:
        return '#0dcaf0'

    @property
    def analysis_codes(self) -> list[str]:
        from app.labs.water_lab.chemistry.constants import WATER_ANALYSIS_TYPES
        return [a['code'] for a in WATER_ANALYSIS_TYPES]

    def sample_query(self, statuses=None):
        """Усны хими дээжүүдийг шүүнэ."""
        from app.models import Sample
        q = Sample.query.filter(Sample.lab_type.in_(['water', 'water & micro']))
        if statuses:
            q = q.filter(Sample.status.in_(statuses))
        return q

    def sample_stats(self):
        """Усны хими дээжийн тоон мэдээлэл."""
        from app.models import Sample
        base = Sample.query.filter(Sample.lab_type.in_(['water', 'water & micro']))
        return {
            'total': base.count(),
            'new': base.filter(Sample.status == 'new').count(),
            'in_progress': base.filter(Sample.status.in_(['in_progress', 'analysis'])).count(),
            'completed': base.filter(Sample.status == 'completed').count(),
        }
