# app/labs/water_lab/chemistry/utils.py
"""Ус + Микробиологи дундын дээж бүртгэлийн helper."""

import json
from datetime import datetime, timedelta

from sqlalchemy import func

from app import db
from app.models import Sample
from app.utils.database import safe_commit
from app.labs.water_lab.chemistry.constants import WATER_ANALYSIS_TYPES
from app.labs.water_lab.microbiology.constants import MICRO_ANALYSIS_TYPES

WATER_CODES = {at['code'] for at in WATER_ANALYSIS_TYPES}
MICRO_CODES = {at['code'] for at in MICRO_ANALYSIS_TYPES}


_MICRO_TYPES = ['microbiology', 'water & micro']
_CHEM_TYPES = ['water', 'water & micro']


def _generate_micro_lab_id(sample_date, next_batch=False):
    """Микробиологийн лабын дугаар үүсгэх.

    Формат: XX_YY
      XX = тухайн лабд хэддэх өдөр дээж ирсэн (өдрийн дэс дугаар)
      YY = нийт дээжийн дэс дугаар (өмнөх бүх өдрүүдийн дээж + 1-ээс эхэлнэ)
    """
    micro_filter = Sample.lab_type.in_(_MICRO_TYPES)

    # Хамгийн том day_num олох (micro_lab_id-аас)
    max_day_num = 0
    rows = db.session.query(Sample.micro_lab_id).filter(
        micro_filter,
        Sample.micro_lab_id.isnot(None),
        Sample.micro_lab_id != '',
    ).all()
    for (lid,) in rows:
        if lid and '_' in lid:
            try:
                d = int(lid.split('_')[0])
                if d > max_day_num:
                    max_day_num = d
            except (ValueError, IndexError):
                pass

    today_count = Sample.query.filter(
        micro_filter,
        Sample.sample_date == sample_date,
    ).count()

    if next_batch:
        # Шинэ багц - хамгийн том day_num + 1 (үргэлж шинэ дугаар)
        day_num = max_day_num + 1
        # Хэрэв өнөөдрийн дээж байгаа ч гэсэн шинэ багц үүсгэнэ
        if today_count > 0:
            # Мөн өнөөдрийн хамгийн том day_num-тай харьцуулж, том нь-г авна
            existing_today = db.session.query(Sample.micro_lab_id).filter(
                micro_filter,
                Sample.sample_date == sample_date,
                Sample.micro_lab_id.isnot(None),
            ).all()
            for (lid,) in existing_today:
                if lid and '_' in lid:
                    try:
                        d = int(lid.split('_')[0])
                        if d >= day_num:
                            day_num = d + 1
                    except (ValueError, IndexError):
                        pass
    elif today_count > 0:
        # Өнөөдрийн дээж байгаа - тэр өдрийн day_num авах
        existing = db.session.query(Sample.micro_lab_id).filter(
            micro_filter,
            Sample.sample_date == sample_date,
            Sample.micro_lab_id.isnot(None),
        ).first()
        if existing and existing[0] and '_' in existing[0]:
            try:
                day_num = int(existing[0].split('_')[0])
            except (ValueError, IndexError):
                day_num = max_day_num + 1
        else:
            day_num = max_day_num + 1
    else:
        # Шинэ өдөр - шинэ day_num
        day_num = max_day_num + 1

    total_samples = Sample.query.filter(micro_filter).count()

    return day_num, total_samples


def _max_batch(extra_filters=None):
    """Хамгийн том batch дугаар олох (chem_lab_id байгаа бүх дээжээс)."""
    chem_filter = Sample.lab_type.in_(_CHEM_TYPES)
    q = db.session.query(Sample.chem_lab_id).filter(
        chem_filter,
        Sample.chem_lab_id.isnot(None),
        Sample.chem_lab_id != '',
    )
    if extra_filters:
        for f in extra_filters:
            q = q.filter(f)
    rows = q.all()
    max_b = 0
    for (lid,) in rows:
        if lid and '_' in lid:
            try:
                b = int(lid.split('_')[0])
                if b > max_b:
                    max_b = b
            except (ValueError, IndexError):
                pass
    return max_b


def _generate_chem_lab_id(sample_date, next_batch=False):
    """Химийн лабын дугаар үүсгэх.

    Формат: {batch}_{seq}
      batch = багц дугаар (next_batch=True бол өмнөх max + 1)
      seq = нийт дэс дугаар
    """
    chem_filter = Sample.lab_type.in_(_CHEM_TYPES)

    max_b = _max_batch()

    today_count = Sample.query.filter(
        chem_filter,
        Sample.sample_date == sample_date,
    ).count()

    if next_batch:
        batch = max_b + 1
    elif today_count > 0:
        today_b = _max_batch([Sample.sample_date == sample_date])
        batch = today_b if today_b else max_b + 1
    else:
        batch = max_b + 1

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

    # Эзэлхүүн (2л=2000мл, 0.5л=500мл), буцаах, хадгалах хугацаа
    vol_2l = bool(form.get('volume_2l'))
    vol_05l = bool(form.get('volume_05l'))
    weight = None
    if vol_2l and vol_05l:
        weight = 2500.0
    elif vol_2l:
        weight = 2000.0
    elif vol_05l:
        weight = 500.0
    return_sample = bool(form.get('return_sample'))
    try:
        retention_days = int(form.get('retention_period', 7))
    except (ValueError, TypeError):
        retention_days = 7
    retention_date = sample_date + timedelta(days=retention_days)

    # Микро лабын дугаар тооцоолох
    next_batch = bool(form.get('next_batch'))
    needs_micro_id = has_micro
    if needs_micro_id:
        micro_day_num, micro_total = _generate_micro_lab_id(sample_date, next_batch=next_batch)
        micro_seq = micro_total
    else:
        micro_day_num = micro_seq = 0

    # Химийн лабын дугаар тооцоолох
    needs_chem_id = has_water
    if needs_chem_id:
        chem_batch, chem_total = _generate_chem_lab_id(sample_date, next_batch=next_batch)
        chem_seq = chem_total
    else:
        chem_batch = chem_seq = 0

    # sample_code-д micro lab_id ашиглах (хуучин формат хадгалах)
    needs_lab_id = lab_type in ('microbiology', 'water & micro')

    # Ахуйн ус: Оролт/Гаралт хос үүсгэх
    wastewater_only = {
        a['code'] for a in WATER_ANALYSIS_TYPES
        if 'wastewater' in a.get('categories', [])
        and 'drinking' not in a.get('categories', [])
    }
    has_wastewater = any(a in wastewater_only for a in analyses)
    suffixes = [' (Оролт)', ' (Гаралт)'] if has_wastewater else ['']

    created = []
    skipped = []
    for sample_name in sample_names:
        sample_name = sample_name.strip()
        if not sample_name:
            continue

        for suffix in suffixes:
            actual_name = sample_name + suffix

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

            # sample_code
            if needs_lab_id:
                lab_id = cur_micro_lab_id
                sample_code = f"{lab_id}_{actual_name}_{sample_date.isoformat()}"
            else:
                sample_code = f"{actual_name}_{sample_date.isoformat()}"

            existing = Sample.query.filter_by(sample_code=sample_code).first()
            if existing:
                skipped.append(actual_name)
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
            from app.services.sla_service import assign_sla
            assign_sla(sample)
            db.session.add(sample)
            created.append(actual_name)

    if not safe_commit():
        raise RuntimeError('Дээж хадгалахад алдаа гарлаа')
    return (created, skipped, len(analyses))
