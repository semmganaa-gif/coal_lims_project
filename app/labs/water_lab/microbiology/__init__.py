# app/labs/water_lab/microbiology/__init__.py
"""Микробиологийн лаборатори (Microbiology Lab)."""

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
        from app.labs.water_lab.microbiology.constants import MICRO_ANALYSIS_TYPES
        return [a['code'] for a in MICRO_ANALYSIS_TYPES]

    def sample_query(self, statuses=None):
        """Ус + Микро хоёр lab_type-ыг хамтад нь шүүнэ."""
        from app.models import Sample
        q = Sample.query.filter(Sample.lab_type.in_(['microbiology']))
        if statuses:
            q = q.filter(Sample.status.in_(statuses))
        return q

    def sample_stats(self):
        """Ус + Микро хамтын тоон мэдээлэл."""
        from app.models import Sample
        base = Sample.query.filter(Sample.lab_type.in_(['microbiology']))
        return {
            'total': base.count(),
            'new': base.filter(Sample.status == 'new').count(),
            'in_progress': base.filter(Sample.status.in_(['in_progress', 'analysis'])).count(),
            'completed': base.filter(Sample.status == 'completed').count(),
        }
