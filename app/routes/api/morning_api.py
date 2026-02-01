# app/routes/api/morning_api.py
# -*- coding: utf-8 -*-
"""
Өглөөний dashboard API:
  - /api/morning_dashboard — Өдрийг эхлэхэд шаардлагатай мэдээлэл
"""

from datetime import date, timedelta
from flask import jsonify, request as flask_request
from flask_login import login_required
from app import db
from app.models import Equipment, Sample


# Лаб төрөл → дээжийн lab_type, тоног төхөөрөмжийн category
_LAB_CONFIG = {
    'water': {
        'sample_types': ['water'],
        'equip_categories': ['water'],
    },
    'micro': {
        'sample_types': ['water', 'microbiology'],
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

        ?lab=coal|water|micro  (default: coal)
        """
        today = date.today()
        lab = flask_request.args.get('lab', 'coal')
        cfg = _LAB_CONFIG.get(lab, _LAB_CONFIG['coal'])
        sample_types = cfg['sample_types']
        equip_cats = cfg['equip_categories']

        # Тоног төхөөрөмжийн category шүүлтүүр
        def _equip_base():
            return Equipment.query.filter(
                Equipment.category.in_(equip_cats),
                Equipment.status != 'retired',
            )

        # 1. Баталгаажуулалт дуусах дөхсөн (7 хоногийн дотор)
        week_later = today + timedelta(days=7)
        calibration_due = _equip_base().filter(
            Equipment.next_calibration_date <= week_later,
            Equipment.next_calibration_date >= today,
        ).order_by(Equipment.next_calibration_date).all()

        # 2. Хугацаа хэтэрсэн
        calibration_overdue = _equip_base().filter(
            Equipment.next_calibration_date < today,
        ).order_by(Equipment.next_calibration_date).all()

        # 3. Эвдрэлтэй / засвартай
        broken_equipment = Equipment.query.filter(
            Equipment.category.in_(equip_cats),
            Equipment.status.in_(['broken', 'maintenance', 'needs_spare']),
        ).all()

        # 4. Дээж — лаб төрлөөр шүүх
        today_new = Sample.query.filter(
            Sample.lab_type.in_(sample_types),
            Sample.status == 'new',
        ).count()
        today_in_progress = Sample.query.filter(
            Sample.lab_type.in_(sample_types),
            Sample.status.in_(['in_progress', 'analysis']),
        ).count()
        today_total = Sample.query.filter(
            Sample.lab_type.in_(sample_types),
            db.func.date(Sample.received_date) == today,
        ).count()

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
