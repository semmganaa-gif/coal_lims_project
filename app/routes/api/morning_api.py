# app/routes/api/morning_api.py
# -*- coding: utf-8 -*-
"""
Өглөөний dashboard API:
  - /api/morning_dashboard — Өдрийг эхлэхэд шаардлагатай мэдээлэл
"""

from datetime import date, timedelta
from flask import jsonify, request as flask_request
from flask_login import login_required
from sqlalchemy import func, select

from app import db
from app.constants import SampleStatus
from app.models import Equipment, Sample


# Лаб төрөл → дээжийн lab_type, тоног төхөөрөмжийн category
_LAB_CONFIG = {
    'water_chemistry': {
        'sample_types': ['water_chemistry'],
        'equip_categories': ['water'],
    },
    'micro': {
        'sample_types': ['microbiology'],
        'equip_categories': ['micro'],
    },
    'coal': {
        'sample_types': ['coal'],
        'equip_categories': ['furnace', 'prep', 'analysis', 'balance', 'other'],
    },
    'petro': {
        'sample_types': ['petrography'],
        'equip_categories': ['analysis', 'prep'],
    },
}


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх."""

    @bp.route('/morning_dashboard')
    @login_required
    def morning_dashboard():
        """Өглөөний dashboard дата.

        ?lab=coal|water_chemistry|micro  (default: coal)
        """
        today = date.today()
        lab = flask_request.args.get('lab', 'coal')
        cfg = _LAB_CONFIG.get(lab, _LAB_CONFIG['coal'])
        sample_types = cfg['sample_types']
        equip_cats = cfg['equip_categories']

        # Тоног төхөөрөмжийн base filter conditions
        equip_base_conds = [
            Equipment.category.in_(equip_cats),
            Equipment.status != 'retired',
        ]

        # 1. Баталгаажуулалт дуусах дөхсөн (7 хоногийн дотор)
        week_later = today + timedelta(days=7)
        calibration_due = list(db.session.execute(
            select(Equipment)
            .where(
                *equip_base_conds,
                Equipment.next_calibration_date <= week_later,
                Equipment.next_calibration_date >= today,
            )
            .order_by(Equipment.next_calibration_date)
        ).scalars().all())

        # 2. Хугацаа хэтэрсэн
        calibration_overdue = list(db.session.execute(
            select(Equipment)
            .where(
                *equip_base_conds,
                Equipment.next_calibration_date < today,
            )
            .order_by(Equipment.next_calibration_date)
        ).scalars().all())

        # 3. Эвдрэлтэй / засвартай
        broken_equipment = list(db.session.execute(
            select(Equipment).where(
                Equipment.category.in_(equip_cats),
                Equipment.status.in_(['broken', 'maintenance', 'needs_spare']),
            )
        ).scalars().all())

        # 4. Дээж — лаб төрлөөр шүүх
        def _count_samples(*conds):
            return db.session.execute(
                select(func.count(Sample.id)).where(*conds)
            ).scalar_one()

        today_new = _count_samples(
            Sample.lab_type.in_(sample_types),
            Sample.status == SampleStatus.NEW.value,
        )
        today_in_progress = _count_samples(
            Sample.lab_type.in_(sample_types),
            Sample.status.in_([SampleStatus.IN_PROGRESS.value, SampleStatus.ANALYSIS.value]),
        )
        today_total = _count_samples(
            Sample.lab_type.in_(sample_types),
            func.date(Sample.received_date) == today,
        )

        return jsonify({
            'calibration_due': [{
                'id': e.id,
                'lab_code': e.lab_code or '',
                'name': e.name,
                'next_calibration': e.next_calibration_date.isoformat(),
                'days_left': (e.next_calibration_date - today).days,
            } for e in calibration_due],
            'calibration_overdue': [{
                'id': e.id,
                'lab_code': e.lab_code or '',
                'name': e.name,
                'next_calibration': e.next_calibration_date.isoformat(),
                'days_overdue': (today - e.next_calibration_date).days,
            } for e in calibration_overdue],
            'broken_equipment': [{
                'id': e.id,
                'lab_code': e.lab_code or '',
                'name': e.name,
                'status': e.status,
            } for e in broken_equipment],
            'samples': {
                'new': today_new,
                'in_progress': today_in_progress,
                'today_received': today_total,
            },
        })
