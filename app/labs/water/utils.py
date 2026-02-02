# app/labs/water/utils.py
"""Ус + Микробиологи дундын дээж бүртгэлийн helper."""

import json
from datetime import datetime, timedelta

from sqlalchemy import func, cast, Date as SADate

from app import db
from app.models import Sample
from app.utils.database import safe_commit
from app.labs.water.constants import WATER_ANALYSIS_TYPES
from app.labs.microbiology.constants import MICRO_ANALYSIS_TYPES

WATER_CODES = {at['code'] for at in WATER_ANALYSIS_TYPES}
MICRO_CODES = {at['code'] for at in MICRO_ANALYSIS_TYPES}


_MICRO_TYPES = ['microbiology', 'water & micro']
_CHEM_TYPES = ['water', 'water & micro']


def _generate_micro_lab_id(sample_date):
    """Микробиологийн лабын дугаар үүсгэх.

    Формат: XX_YY
      XX = тухайн лабд хэддэх өдөр дээж ирсэн (өдрийн дэс дугаар)
      YY = нийт дээжийн дэс дугаар (өмнөх бүх өдрүүдийн дээж + 1-ээс эхэлнэ)
    """
    micro_filter = Sample.lab_type.in_(_MICRO_TYPES)

    distinct_days = db.session.query(
        func.count(func.distinct(Sample.sample_date))
    ).filter(micro_filter).scalar() or 0

    today_count = Sample.query.filter(
        micro_filter,
        Sample.sample_date == sample_date,
    ).count()

    if today_count > 0:
        day_num = db.session.query(
            func.count(func.distinct(Sample.sample_date))
        ).filter(
            micro_filter,
            Sample.sample_date <= sample_date,
        ).scalar() or 1
    else:
        day_num = distinct_days + 1

    total_samples = Sample.query.filter(micro_filter).count()

    return day_num, total_samples


def _generate_chem_lab_id(sample_date):
    """Химийн лабын дугаар үүсгэх.

    Формат: {batch}_{seq}
      batch = тухайн огноонд хэддэх удаагийн дээж (water lab_type-тэй өдрүүдийн тоо)
      seq = нийт дэс дугаар (бүх өдрүүдийн нийлбэр)
    """
    chem_filter = Sample.lab_type.in_(_CHEM_TYPES)

    distinct_days = db.session.query(
        func.count(func.distinct(Sample.sample_date))
    ).filter(chem_filter).scalar() or 0

    today_count = Sample.query.filter(
        chem_filter,
        Sample.sample_date == sample_date,
    ).count()

    if today_count > 0:
        batch = db.session.query(
            func.count(func.distinct(Sample.sample_date))
        ).filter(
            chem_filter,
            Sample.sample_date <= sample_date,
        ).scalar() or 1
    else:
        batch = distinct_days + 1

    total_samples = Sample.query.filter(chem_filter).count()

    return batch, total_samples


def create_water_micro_samples(form, user_id):
    """Ус + микро дундын дээж үүсгэх.

    Returns: (created_names, skipped_names, analyses_count)
    """
    from app.utils.datetime import now_local

    sample_names = form.getlist('sample_codes')
    source_type = form.get('source_type', 'other')
    sample_date_str = form.get('sample_date')
    sample_date = (
        datetime.strptime(sample_date_str, '%Y-%m-%d').date()
        if sample_date_str else now_local().date()
    )

    analyses = form.getlist('analyses')

    # lab_type логик
    has_micro = any(a in MICRO_CODES for a in analyses)
    has_water = any(a in WATER_CODES for a in analyses)
    if has_water and has_micro:
        lab_type = 'water & micro'
    elif has_micro:
        lab_type = 'microbiology'
    else:
        lab_type = 'water'

    # Жин, буцаах, хадгалах хугацаа
    weight = form.get('weight')
    weight = float(weight) if weight else None
    return_sample = bool(form.get('return_sample'))
    retention_days = int(form.get('retention_period', 7))
    retention_date = sample_date + timedelta(days=retention_days)

    # Микро лабын дугаар тооцоолох
    needs_micro_id = has_micro
    if needs_micro_id:
        micro_day_num, micro_total = _generate_micro_lab_id(sample_date)
        micro_seq = micro_total
    else:
        micro_day_num = micro_seq = 0

    # Химийн лабын дугаар тооцоолох
    needs_chem_id = has_water
    if needs_chem_id:
        chem_batch, chem_total = _generate_chem_lab_id(sample_date)
        chem_seq = chem_total
    else:
        chem_batch = chem_seq = 0

    # sample_code-д micro lab_id ашиглах (хуучин формат хадгалах)
    needs_lab_id = lab_type in ('microbiology', 'water & micro')

    created = []
    skipped = []
    for sample_name in sample_names:
        sample_name = sample_name.strip()
        if not sample_name:
            continue

        # Micro lab_id
        cur_micro_lab_id = None
        if needs_micro_id:
            micro_seq += 1
            cur_micro_lab_id = f"{micro_day_num:02d}_{micro_seq:02d}"

        # Chem lab_id
        cur_chem_lab_id = None
        if needs_chem_id:
            chem_seq += 1
            cur_chem_lab_id = f"{chem_batch}_{chem_seq:02d}"

        # sample_code (хуучин формат хадгалах)
        if needs_lab_id:
            lab_id = cur_micro_lab_id
            sample_code = f"{lab_id}_{sample_name}_{sample_date.isoformat()}"
        else:
            sample_code = f"{sample_name}_{sample_date.isoformat()}"

        existing = Sample.query.filter_by(sample_code=sample_code).first()
        if existing:
            skipped.append(sample_name)
            continue

        sample = Sample(
            lab_type=lab_type,
            sample_code=sample_code,
            user_id=user_id,
            client_name=source_type,
            sample_type=lab_type,
            sample_date=sample_date,
            sampling_location=form.get('sampling_location', ''),
            sampled_by=form.get('sampled_by', ''),
            notes=form.get('notes', ''),
            analyses_to_perform=json.dumps(analyses, ensure_ascii=False),
            weight=weight,
            return_sample=return_sample,
            retention_date=retention_date,
            status='new',
            chem_lab_id=cur_chem_lab_id,
            micro_lab_id=cur_micro_lab_id,
        )
        db.session.add(sample)
        created.append(sample_name)

    if not safe_commit():
        raise RuntimeError('Дээж хадгалахад алдаа гарлаа')
    return (created, skipped, len(analyses))
