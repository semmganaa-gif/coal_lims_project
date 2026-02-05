# app/labs/water_lab/routes.py
"""Усны лабораторийн үндсэн routes (Хими + Микробиологи)."""

from flask import Blueprint, render_template
from flask_login import login_required
from app.utils.decorators import lab_required

water_lab_bp = Blueprint(
    'water_lab',
    __name__,
    url_prefix='/labs/water-lab'
)


@water_lab_bp.route('/')
@login_required
@lab_required('water')
def main_hub():
    """Усны лабораторийн нэгдсэн хуудас (Хими + Микробиологи)."""
    from app.labs.water_lab.chemistry.constants import WATER_ANALYSIS_TYPES
    from app.labs.water_lab.microbiology.constants import MICRO_ANALYSIS_TYPES
    from app.labs import get_lab

    # Нийт статистик (Хими + Микро)
    stats = get_lab('water_lab').sample_stats()
    water_count = len(WATER_ANALYSIS_TYPES)
    micro_count = len(MICRO_ANALYSIS_TYPES)

    return render_template(
        'labs/water/chemistry/water_lab_hub.html',
        title='Усны лаборатори',
        total_samples=stats['total'],
        new_samples=stats['new'],
        in_progress=stats['in_progress'],
        completed=stats['completed'],
        water_analysis_count=water_count,
        micro_analysis_count=micro_count,
    )
