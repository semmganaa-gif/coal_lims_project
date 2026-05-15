# app/labs/water_lab/microbiology/__init__.py
"""Микробиологийн лаборатори (Microbiology Lab)."""

from sqlalchemy import func, select

from app.constants import SampleStatus
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
        """Микробиологийн дээжүүдийг шүүнэ."""
        from app.models import Sample
        stmt = select(Sample).where(Sample.lab_type.in_(['microbiology']))
        if statuses:
            stmt = stmt.where(Sample.status.in_(statuses))
        return stmt

    def sample_stats(self):
        """Микробиологийн тоон мэдээлэл."""
        from app import db
        from app.models import Sample

        def _count(*conds):
            return db.session.execute(
                select(func.count(Sample.id)).where(
                    Sample.lab_type.in_(['microbiology']), *conds
                )
            ).scalar_one()

        return {
            'total': _count(),
            'new': _count(Sample.status == SampleStatus.NEW.value),
            'in_progress': _count(Sample.status.in_([SampleStatus.IN_PROGRESS.value, SampleStatus.ANALYSIS.value])),
            'completed': _count(Sample.status == SampleStatus.COMPLETED.value),
        }
