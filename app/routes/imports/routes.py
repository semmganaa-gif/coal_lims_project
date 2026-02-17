# app/routes/import_routes.py
# -*- coding: utf-8 -*-
"""
Түүхэн CSV импорт (2009–оноос хойш)

1) Ерөнхий "урт" (long) формат:
   sample_code, client_name, sample_type, analysis_code, value, analysis_date (+ нэмэлт баганууд)

2) CHPP wide формат:
   _sel, ID, Дээжний нэр, Нэгж, Төрөл, Бүртгэсэн, Шинжилсэн, Mt,ar, Mad, Aad, ... , SOLID, FM, m

Одоогийн тохиргоо:
- "Дээжний нэр" баганын утгыг БАЙГААГААР НЬ Sample.sample_code дээр хадгална.
- Нэрийн бүтэц (regex, pattern) шалгах ямар ч логик байхгүй.
- Alias → base код хэвшүүлэхдээ танай ALIAS_TO_BASE map-ыг (app.utils.analysis_aliases) ашиглана.
- AnalysisResult дээр upsert (sample_id, analysis_code) зарчмаар давхар бичихгүй.
"""

import csv
import io
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app

logger = logging.getLogger(__name__)
from flask_login import login_required
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.utils.converters import to_float
from app import models as M
from app.constants import MIN_VALID_YEAR, MAX_VALID_YEAR

# -------------------------------------------------
# Alias mapping
# -------------------------------------------------
from app.utils.analysis_aliases import ALIAS_TO_BASE as _ALIAS_TO_BASE
ALIAS_TO_BASE: Dict[str, str] = {k.lower(): v for k, v in _ALIAS_TO_BASE.items()}

import_bp = Blueprint("importer", __name__, url_prefix="/admin/import")

# -------------------------------------------------
# Туслах функцууд
# -------------------------------------------------


def _norm(s: Any) -> str:
    return str(s).strip() if s is not None else ""


def _parse_date(s: Any) -> Optional[datetime]:
    if not s:
        return None
    t = str(s).strip()
    if t == "" or t.lower() in {"null", "none"}:
        return None

    fmts = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    ]
    for f in fmts:
        try:
            dt = datetime.strptime(t, f)
            if f == "%Y-%m":
                return datetime(dt.year, dt.month, 1)
            return dt
        except Exception:
            continue

    try:
        y = int(t)
        if MIN_VALID_YEAR <= y <= MAX_VALID_YEAR:
            return datetime(y, 1, 1)
    except (ValueError, TypeError):
        pass
    return None


# --- Header синонимууд (long формат) ---
HEADER_KEYS = {
    "sample_code": {
        "sample_code",
        "sample",
        "code",
        "internal_code",
        "дотоод код",
        "дээж код",
        "дээжний нэр",
    },
    "name": {"name", "sample_name"},
    "client_name": {"client_name", "unit", "нэгж", "organization", "dept"},
    "sample_type": {"sample_type", "type", "төрөл"},
    "received_date": {"received_date", "reg_date", "бүртгэсэн", "registered_at"},
    "analysis_date": {
        "analysis_date",
        "date",
        "огноо",
        "tested_at",
        "approved_at",
        "updated_at",
        "created_at",
    },
    "analysis_code": {"analysis_code", "code", "test", "property", "анализ", "шинжилгээ"},
    "value": {"value", "result", "үр дүн", "тоо"},
    "unit": {"unit", "μ", "meas_unit"},
    "status": {"status", "state"},
}


def _map_header(h: str) -> Optional[str]:
    key = h.strip().lower()
    for std, alts in HEADER_KEYS.items():
        if key in {a.lower() for a in alts}:
            return std
    return None


def _base_code(raw: str) -> str:
    if not raw:
        return ""
    x = raw.strip()
    key = x.lower()
    if key in ALIAS_TO_BASE:
        return ALIAS_TO_BASE[key]
    return x


def _get_or_create_sample(sample_code: str, defaults: Dict[str, Any]) -> M.Sample:
    """
    Sample-г sample_code дээр нь олж, байхгүй бол шинээр үүсгэнэ.

    АНХААР:
    - Sample моделд name байхгүй тул зөвхөн client_name, sample_type, received_date
      гэсэн талбаруудыг л ашиглана.
    """
    Sample = M.Sample
    q = db.session.query(Sample).filter(Sample.sample_code == sample_code)
    row = q.first()
    if row:
        changed = False
        for k in ["client_name", "sample_type", "received_date"]:
            if hasattr(row, k):
                v = defaults.get(k)
                if v and getattr(row, k, None) in (None, ""):
                    setattr(row, k, v)
                    changed = True
        if changed:
            db.session.flush()
        return row

    kwargs: Dict[str, Any] = {"sample_code": sample_code}
    for k in ["client_name", "sample_type", "received_date"]:
        if k in defaults and defaults[k] and hasattr(Sample, k):
            kwargs[k] = defaults[k]

    row = Sample(**kwargs)
    db.session.add(row)
    db.session.flush()
    return row


def _upsert_result(
    sample_id: int,
    analysis_code: str,
    analysis_date: Optional[datetime],
    value: Optional[float],
    status: Optional[str],
) -> Tuple[bool, int]:
    """
    AnalysisResult (танай одоогийн загвар) дээр upsert хийнэ.
    Unique жишиг: (sample_id, analysis_code)

    Буцаалт: (шинээр үүссэн үү?, id)
    """
    R = M.AnalysisResult

    filters = [R.sample_id == sample_id, R.analysis_code == analysis_code]

    row = db.session.query(R).filter(and_(*filters)).first()

    if row:
        if value is not None and hasattr(row, "final_result"):
            row.final_result = value
        if status and hasattr(row, "status"):
            row.status = status
        # created_at / updated_at – автоматаар now_mn-ээр шинэчлэгдэнэ
        db.session.flush()
        return (False, getattr(row, "id", 0))

    kwargs: Dict[str, Any] = dict(sample_id=sample_id, analysis_code=analysis_code)
    if hasattr(R, "final_result"):
        kwargs["final_result"] = value
    if hasattr(R, "status") and status:
        kwargs["status"] = status

    new_row = R(**kwargs)
    db.session.add(new_row)
    db.session.flush()
    return (True, getattr(new_row, "id", 0))


# -------------------------------------------------
# CHPP wide CSV импорт (позициор)
# -------------------------------------------------


def _import_chpp_wide(
    reader: csv.reader,
    header: List[str],
    dry_run: bool,
    batch_size: int,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Таны 2009–2025 CHPP wide CSV форматыг уншина.

    Дээжний нэр: яг байгаагаар нь Sample.sample_code дээр бичнэ.
    Нэрийн бүтэц ШАЛГАХГҮЙ.

    Формат (позициор):
    0: _sel
    1: ID
    2: Дээжний нэр
    3: Нэгж
    4: Төрөл
    5: Бүртгэсэн
    6: Шинжилсэн
    7+: Mt,ar, Mad, Aad, ...
    """

    errors: List[str] = []

    if len(header) < 7:
        errors.append(
            "CHPP wide формат гэж үзсэн ч хамгийн багадаа 7 багана байх ёстой "
            "(_sel, ID, Дээжний нэр, Нэгж, Төрөл, Бүртгэсэн, Шинжилсэн)."
        )
        summary = {
            "Нийт мөр": 0,
            "Шинэ дээж": 0,
            "Шинэ шинжилгээний төрөл": 0,
            "Оруулсан үр дүн": 0,
            "Шинэчилсэн үр дүн": 0,
            "Алдаа": len(errors),
            "Dry-run": dry_run,
            "Batch size": batch_size,
            "Delimiter": ",",
        }
        return summary, errors

    # Позици тогтмол
    idx_sample = 2
    idx_client = 3
    idx_type = 4
    idx_regd = 5
    idx_tested = 6

    # Анализын баганууд – "Шинжилсэн" баганын дараах бүх багана
    start_idx = idx_tested + 1
    analysis_cols: List[Tuple[int, str]] = []
    for i in range(start_idx, len(header)):
        col_name = (header[i] or "").strip()
        if not col_name:
            continue
        analysis_cols.append((i, col_name))

    total = 0
    created_samples = 0
    inserted_results = 0
    updated_results = 0
    errors = []

    batch_count = 0

    for row in reader:
        total += 1
        try:
            if len(row) <= idx_sample:
                continue

            sample_code = _norm(row[idx_sample])
            if not sample_code:
                continue

            client_name = _norm(row[idx_client]) if len(row) > idx_client else ""
            sample_type = _norm(row[idx_type]) if len(row) > idx_type else ""

            received_date = (
                _parse_date(row[idx_regd]) if len(row) > idx_regd else None
            )
            analysis_date = (
                _parse_date(row[idx_tested]) if len(row) > idx_tested else received_date
            )

            before_new = len(db.session.new)
            s = _get_or_create_sample(
                sample_code,
                {
                    "client_name": client_name,
                    "sample_type": sample_type,
                    "received_date": received_date,
                },
            )
            if len(db.session.new) > before_new:
                created_samples += 1

            # Анализын бүх багана дээр гүйж AnalysisResult үүсгэнэ
            for col_index, col_header in analysis_cols:
                if col_index >= len(row):
                    continue
                value = to_float(row[col_index])
                if value is None:
                    continue

                analysis_code_raw = col_header
                analysis_code = _base_code(analysis_code_raw)

                ins, _rid = _upsert_result(
                    s.id,
                    analysis_code,
                    analysis_date,
                    value,
                    status=None,
                )
                if ins:
                    inserted_results += 1
                else:
                    updated_results += 1

            batch_count += 1
            if not dry_run and batch_count >= batch_size:
                db.session.commit()
                batch_count = 0

        except Exception as e:
            errors.append(f"Мөр {total}: {e}")
            continue

    if dry_run:
        db.session.rollback()
    else:
        db.session.commit()

    summary = {
        "Нийт мөр": total,
        "Шинэ дээж": created_samples,
        "Шинэ шинжилгээний төрөл": 0,
        "Оруулсан үр дүн": inserted_results,
        "Шинэчилсэн үр дүн": updated_results,
        "Алдаа": len(errors),
        "Dry-run": dry_run,
        "Batch size": batch_size,
        "Delimiter": ",",
    }
    return summary, errors


# -------------------------------------------------
# Long формат импорт
# -------------------------------------------------


def _import_long(
    reader: csv.reader,
    header: List[str],
    dry_run: bool,
    batch_size: int,
    delim: str,
) -> Tuple[Dict[str, Any], List[str]]:
    cols: Dict[str, int] = {}
    for i, h in enumerate(header):
        key = _map_header(h)
        if key:
            cols[key] = i

    required = ["sample_code", "client_name", "sample_type", "analysis_code", "value", "analysis_date"]
    missing = [k for k in required if k not in cols]
    if missing:
        raise ValueError("Дутуу багана байна (заавал): " + ", ".join(missing))

    total = 0
    created_samples = 0
    inserted_results = 0
    updated_results = 0
    errors: List[str] = []

    batch_count = 0

    try:
        for row in reader:
            total += 1
            try:
                sample_code = _norm(row[cols["sample_code"]])
                if not sample_code:
                    continue

                client_name = _norm(row[cols["client_name"]])
                sample_type = _norm(row[cols["sample_type"]])

                received_date = (
                    _parse_date(row[cols["received_date"]]) if "received_date" in cols else None
                )
                analysis_date = _parse_date(row[cols["analysis_date"]])

                analysis_code_raw = _norm(row[cols["analysis_code"]])
                analysis_code = _base_code(analysis_code_raw)

                value = to_float(row[cols["value"]])
                status = _norm(row[cols["status"]]) if "status" in cols else None

                before_new = len(db.session.new)
                s = _get_or_create_sample(
                    sample_code,
                    {
                        "client_name": client_name,
                        "sample_type": sample_type,
                        "received_date": received_date,
                    },
                )
                if len(db.session.new) > before_new:
                    created_samples += 1

                ins, _rid = _upsert_result(
                    s.id,
                    analysis_code,
                    analysis_date,
                    value,
                    status=status,
                )
                if ins:
                    inserted_results += 1
                else:
                    updated_results += 1

                batch_count += 1
                if not dry_run and batch_count >= batch_size:
                    db.session.commit()
                    batch_count = 0

            except Exception as e:
                errors.append(f"Мөр {total}: {e}")
                continue

        if dry_run:
            db.session.rollback()
        else:
            db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        raise

    summary = {
        "Нийт мөр": total,
        "Шинэ дээж": created_samples,
        "Шинэ шинжилгээний төрөл": 0,
        "Оруулсан үр дүн": inserted_results,
        "Шинэчилсэн үр дүн": updated_results,
        "Алдаа": len(errors),
        "Dry-run": dry_run,
        "Batch size": batch_size,
        "Delimiter": delim,
    }
    return summary, errors


# -------------------------------------------------
# View – /admin/import/historical_csv
# -------------------------------------------------


@import_bp.route("/historical_csv", methods=["GET", "POST"])
@login_required
def import_historical_csv():
    if request.method == "GET":
        return render_template("admin/import_historical.html", title="Түүхэн CSV импорт")

    file = request.files.get("file")
    dry_run = request.form.get("dry_run") == "on"
    batch_size = int(request.form.get("batch_size") or 1000)

    if not file or file.filename == "":
        flash("Файл сонгогдоогүй байна.", "danger")
        return redirect(url_for("importer.import_historical_csv"))

    raw = file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1251", errors="ignore")

    # Delimiter autodetect
    lines = text.splitlines()
    sample_lines = "\n".join(lines[:10])
    try:
        sniff = csv.Sniffer().sniff(sample_lines, delimiters=",;\t")
        delim = sniff.delimiter
    except Exception:
        delim = ","

    string_io = io.StringIO(text, newline="")
    reader = csv.reader(string_io, delimiter=delim)

    try:
        raw_header = next(reader)
    except StopIteration:
        flash("Хоосон файл.", "danger")
        return redirect(url_for("importer.import_historical_csv"))

    # BOM, whitespace цэвэрлэе
    header = [(h or "").replace("\ufeff", "").strip() for h in raw_header]

    summary: Dict[str, Any]
    errors: List[str]

    try:
        # Эхлээд long формат гэж үзнэ
        summary, errors = _import_long(reader, header, dry_run, batch_size, delim)
    except ValueError as ve:
        msg = str(ve)
        if "Дутуу багана байна" in msg:
            # Wide CHPP CSV гэж үзээд позициор уншина
            current_app.logger.warning("IMPORT: CHPP wide positional mapping ашиглалаа.")
            string_io.seek(0)
            reader = csv.reader(string_io, delimiter=delim)
            raw_header = next(reader)
            header = [(h or "").replace("\ufeff", "").strip() for h in raw_header]
            summary, errors = _import_chpp_wide(reader, header, dry_run, batch_size)
        else:
            flash(str(ve), "danger")
            return redirect(url_for("importer.import_historical_csv"))
    except SQLAlchemyError as db_err:
        db.session.rollback()
        flash(f"Мэдээллийн сан бичих алдаа: {db_err}", "danger")
        return redirect(url_for("importer.import_historical_csv"))

    return render_template(
        "admin/import_historical.html",
        title="Түүхэн CSV импорт",
        summary=summary,
        errors=errors[:200],
    )
