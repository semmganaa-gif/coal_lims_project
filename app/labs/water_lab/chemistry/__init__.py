# app/labs/water_lab/chemistry/__init__.py
"""Усны хими лаборатори (Chemistry Lab)."""

from sqlalchemy import func, select

from app.constants import SampleStatus
from app.labs.base import BaseLab


class ChemistryLab(BaseLab):
    """Усны хими лаборатори."""

    @property
    def key(self) -> str:
        return 'water_chemistry'

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
        stmt = select(Sample).where(Sample.lab_type.in_(['water_chemistry']))
        if statuses:
            stmt = stmt.where(Sample.status.in_(statuses))
        return stmt

    def sample_stats(self):
        """Усны хими дээжийн тоон мэдээлэл."""
        from app import db
        from app.models import Sample

        def _count(*conds):
            return db.session.execute(
                select(func.count(Sample.id)).where(
                    Sample.lab_type.in_(['water_chemistry']), *conds
                )
            ).scalar_one()

        return {
            'total': _count(),
            'new': _count(Sample.status == SampleStatus.NEW.value),
            'in_progress': _count(Sample.status.in_([SampleStatus.IN_PROGRESS.value, SampleStatus.ANALYSIS.value])),
            'completed': _count(Sample.status == SampleStatus.COMPLETED.value),
        }
