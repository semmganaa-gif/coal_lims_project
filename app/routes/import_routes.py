# app/routes/import_routes.py
# -*- coding: utf-8 -*-
"""
Түүхэн CSV импорт (2009–оноос хойш)

Дэмжих 2 хэлбэр:
1) "LONG" – мөр бүрт нэг шинжилгээ:
   sample_code, client_name, sample_type, analysis_code, value, analysis_date, ...
2) "WIDE" – нэг мөрт олон шинжилгээ (чиний 2009–2025 Excel шиг):
   ID, Дээжний нэр, Нэгж, Төрөл, Бүртгэсэн, Шинжилсэн, Mt,ar, Mad, Aad, ... гэх мэт.

- Alias → base код хэвшүүлэх (ALIAS_TO_BASE)
- Idempotent upsert: (sample_id, analysis_type, analysis_date) түвшинд
- Том файлд batch=1000 мөрөөр коммит
- Dry-run (зөвхөн шалгах) горим
"""

import csv
import io
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app import models as M

# Танайд аль хэдийнээ alias mapping байдаг бол түүнийг ашиглая.
try:
    from app.utils.analysis_aliases import ALIAS_TO_BASE as _ALIAS_TO_BASE  # noqa: F401
    ALIAS_TO_BASE: Dict[str, str] = {k.lower(): v for k, v in _ALIAS_TO_BASE.items()}
except Exception:
    # Резерв – багахан нийтлэг alias-ууд
    ALIAS_TO_BASE = {
        "ts": "TS",
        "st,ad": "TS",
        "s": "TS",
        "cv": "CV",
        "qgr,ad": "CV",
        "qnet,ar": "CV",
        "mad": "Mad",
        "mt": "MT",
        "fm": "FM",
        "aad": "Aad",
        "vad": "Vad",
        "trd": "TRD",
        "csn": "CSN",
        "gi": "Gi",
        "p": "P",
        "f": "F",
        "cl": "Cl",
        "pl": "PL",
        "cri": "CRI",
        "csr": "CSR",
        "solid": "Solid",
    }

import_bp = Blueprint("importer", __name__, url_prefix="/admin/import")


# -------------------- Helpers --------------------

def _norm(s: Any) -> str:
    return (str(s).strip() if s is not None else "")


def _to_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    s = str(v).strip().replace(" ", "").replace("\u00A0", "")
    if s == "" or s.lower() in {"null", "none", "na"}:
        return None
    # 1,234.56 / 1 234,56 / 1234,56 → normalize
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


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
            pass
    try:
        y = int(t)
        if 2000 <= y <= 2100:
            return datetime(y, 1, 1)
    except Exception:
        pass
    return None


# header синонимууд
HEADER_KEYS = {
    "sample_code": {
        "sample_code",
        "sample",
        "code",
        "internal_code",
        "дотоод код",
        "дээж код",
        "дээжний нэр",  # ← чиний файл
    },
    "name": {"name", "sample_name", "дээжний нэр"},
    "client_name": {"client_name", "unit", "нэгж", "organization", "dept"},
    "sample_type": {"sample_type", "type", "төрөл"},
    "received_date": {"received_date", "reg_date", "бүртгэсэн", "registered_at"},
    # Analysis тал
    "analysis_date": {
        "analysis_date",
        "date",
        "огноо",
        "tested_at",
        "approved_at",
        "updated_at",
        "created_at",
        "шинжилсэн",  # ← чиний файл
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


def _get_or_create_analysis_type(code: str) -> M.AnalysisType:
    row = db.session.query(M.AnalysisType).filter(M.AnalysisType.code == code).first()
    if row:
        return row
    row = M.AnalysisType(code=code, name=code)
    db.session.add(row)
    db.session.flush()
    return row


def _get_or_create_sample(sample_code: str, defaults: Dict[str, Any]) -> M.Sample:
    q = db.session.query(M.Sample).filter(M.Sample.sample_code == sample_code)
    row = q.first()
    if row:
        changed = False
        for k in ["name", "client_name", "sample_type", "received_date"]:
            v = defaults.get(k)
            if v and getattr(row, k, None) in (None, "",):
                setattr(row, k, v)
                changed = True
        if changed:
            db.session.flush()
        return row

    row = M.Sample(
        sample_code=sample_code,
        name=defaults.get("name"),
        client_name=defaults.get("client_name"),
        sample_type=defaults.get("sample_type"),
        received_date=defaults.get("received_date"),
    )
    db.session.add(row)
    db.session.flush()
    return row


def _upsert_result(
    sample_id: int,
    atype: M.AnalysisType,
    analysis_date: Optional[datetime],
    value: Optional[float],
    unit: Optional[str],
    status: Optional[str],
) -> Tuple[bool, int]:
    """
    Upsert = байгаа бол шинэчилнэ, үгүй бол шинээр үүсгэнэ.
    Unique жишиг: (sample_id, analysis_type_id, analysis_date (date only))
    """
    date_key = None
    if analysis_date:
        date_key = datetime(analysis_date.year, analysis_date.month, analysis_date.day)

    R = M.AnalysisResult
    filters = [R.sample_id == sample_id, R.analysis_type_id == atype.id]
    if hasattr(R, "analysis_date") and date_key is not None:
        filters.append(R.analysis_date >= date_key)
        filters.append(R.analysis_date < date_key + timedelta(days=1))
    elif hasattr(R, "approved_at") and date_key is not None:
        filters.append(R.approved_at >= date_key)
        filters.append(R.approved_at < date_key + timedelta(days=1))
    elif hasattr(R, "updated_at") and date_key is not None:
        filters.append(R.updated_at >= date_key)
        filters.append(R.updated_at < date_key + timedelta(days=1))

    row = db.session.query(R).filter(and_(*filters)).first() if filters else None

    if row:
        if value is not None and hasattr(row, "value"):
            row.value = value
        if unit and hasattr(row, "unit"):
            row.unit = unit
        if status and hasattr(row, "status"):
            row.status = status
        if analysis_date:
            for c in ("analysis_date", "approved_at", "updated_at", "created_at"):
                if hasattr(row, c) and getattr(row, c) is None:
                    setattr(row, c, analysis_date)
        db.session.flush()
        return (False, getattr(row, "id", 0))

    kwargs = dict(sample_id=sample_id, analysis_type_id=atype.id)
    if hasattr(R, "value"):
        kwargs["value"] = value
    if hasattr(R, "unit"):
        kwargs["unit"] = unit
    if hasattr(R, "status"):
        kwargs["status"] = status
    for c in ("analysis_date", "approved_at", "updated_at", "created_at"):
        if hasattr(R, c) and analysis_date:
            kwargs[c] = analysis_date
            break

    new_row = R(**kwargs)
    db.session.add(new_row)
    db.session.flush()
    return (True, getattr(new_row, "id", 0))


# -------------------- Views --------------------

@import_bp.route("/historical_csv", methods=["GET", "POST"])
@login_required
def import_historical_csv():
    if request.method == "GET":
        return render_template("admin/import_historical.html", title="Түүхэн CSV импорт")

    file = request.files.get("file")
    dry_run = request.form.get("dry_run") == "on"
    batch_size = int(request.form.get("batch_size") or 1000)

    if not file or file.filename == "":
        flash("Файл сонгоогүй байна.", "danger")
        return redirect(url_for("importer.import_historical_csv"))

    # UTF-8 with BOM хамгаална
    raw = file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1251", errors="ignore")

    # Чиний Excel / TXT – TAB тусгаарлагч
    delim = "\t"

    # newline="" гэж өгөхгүй бол "new-line character seen in unquoted field" алдаа гарч болно
    text_io = io.StringIO(text, newline="")
    reader = csv.reader(text_io, delimiter=delim)

    try:
        header = next(reader)
    except StopIteration:
        flash("Хоосон файл.", "danger")
        return redirect(url_for("importer.import_historical_csv"))

    # --- Header map ---
    cols: Dict[str, int] = {}
    for i, h in enumerate(header):
        key = _map_header(h)
        if key:
            cols[key] = i

    has_long_shape = ("analysis_code" in cols and "value" in cols)

    # 1) LONG FORMAT – мөр бүр нэг шинжилгээ
    if has_long_shape:
        required = ["sample_code", "client_name", "sample_type", "analysis_code", "value", "analysis_date"]
        missing = [k for k in required if k not in cols]
        if missing:
            flash("Дутуу багана байна (заавал): " + ", ".join(missing), "danger")
            return redirect(url_for("importer.import_historical_csv"))

        total = 0
        created_samples = 0
        created_types = 0
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

                    name = _norm(row[cols["name"]]) if "name" in cols else ""
                    client_name = _norm(row[cols["client_name"]])
                    sample_type = _norm(row[cols["sample_type"]])

                    received_date = _parse_date(row[cols["received_date"]]) if "received_date" in cols else None
                    analysis_date = _parse_date(row[cols["analysis_date"]])

                    analysis_code_raw = _norm(row[cols["analysis_code"]])
                    analysis_code = _base_code(analysis_code_raw)

                    value = _to_float(row[cols["value"]])
                    unit = _norm(row[cols["unit"]]) if "unit" in cols else None
                    status = _norm(row[cols["status"]]) if "status" in cols else None

                    before_flush = len(db.session.new)
                    s = _get_or_create_sample(
                        sample_code,
                        {
                            "name": name,
                            "client_name": client_name,
                            "sample_type": sample_type,
                            "received_date": received_date,
                        },
                    )
                    if len(db.session.new) > before_flush:
                        created_samples += 1

                    before_flush = len(db.session.new)
                    at = _get_or_create_analysis_type(analysis_code)
                    if len(db.session.new) > before_flush:
                        created_types += 1

                    ins, _rid = _upsert_result(s.id, at, analysis_date, value, unit, status)
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

        except SQLAlchemyError as e:
            db.session.rollback()
            flash("Базад бичих үед алдаа гарлаа: %s" % e, "danger")
            return redirect(url_for("importer.import_historical_csv"))

        summary = {
            "Формат": "LONG",
            "Нийт мөр": total,
            "Шинэ дээж": created_samples,
            "Шинэ шинжилгээний төрөл": created_types,
            "Оруулсан үр дүн": inserted_results,
            "Шинэчилсэн үр дүн": updated_results,
            "Алдаа": len(errors),
            "Dry-run": dry_run,
            "Batch size": batch_size,
            "Delimiter": delim,
        }
        return render_template(
            "admin/import_historical.html",
            title="Түүхэн CSV импорт",
            summary=summary,
            errors=errors[:200],
        )

    # 2) WIDE FORMAT – нэг мөрт олон шинжилгээ (чиний 2009–2025 файл)
    required_wide = ["sample_code", "client_name", "sample_type", "analysis_date"]
    missing = [k for k in required_wide if k not in cols]
    if missing:
        flash("Дутуу багана байна (заавал): " + ", ".join(missing), "danger")
        return redirect(url_for("importer.import_historical_csv"))

    # Мета баганын индексүүд (дээжийн үндсэн мэдээлэл)
    meta_indexes = set(cols.values())

    total = 0
    created_samples = 0
    created_types = 0
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

                name = _norm(row[cols["name"]]) if "name" in cols else ""
                client_name = _norm(row[cols["client_name"]])
                sample_type = _norm(row[cols["sample_type"]])

                received_date = _parse_date(row[cols["received_date"]]) if "received_date" in cols else None
                analysis_date = _parse_date(row[cols["analysis_date"]])

                before_flush = len(db.session.new)
                s = _get_or_create_sample(
                    sample_code,
                    {
                        "name": name,
                        "client_name": client_name,
                        "sample_type": sample_type,
                        "received_date": received_date or analysis_date,
                    },
                )
                if len(db.session.new) > before_flush:
                    created_samples += 1

                # Мета биш багана бүрийг шинжилгээ гэж үзнэ
                for idx, col_name in enumerate(header):
                    if idx in meta_indexes:
                        continue
                    raw_val = row[idx] if idx < len(row) else ""
                    value = _to_float(raw_val)
                    if value is None:
                        continue  # хоосон / тоо биш → алгас

                    base_code = _base_code(col_name)
                    if not base_code:
                        continue

                    before_flush = len(db.session.new)
                    at = _get_or_create_analysis_type(base_code)
                    if len(db.session.new) > before_flush:
                        created_types += 1

                    ins, _rid = _upsert_result(s.id, at, analysis_date, value, None, None)
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

    except SQLAlchemyError as e:
        db.session.rollback()
        flash("Базад бичих үед алдаа гарлаа: %s" % e, "danger")
        return redirect(url_for("importer.import_historical_csv"))

    summary = {
        "Формат": "WIDE",
        "Нийт мөр": total,
        "Шинэ дээж": created_samples,
        "Шинэ шинжилгээний төрөл": created_types,
        "Оруулсан үр дүн": inserted_results,
        "Шинэчилсэн үр дүн": updated_results,
        "Алдаа": len(errors),
        "Dry-run": dry_run,
        "Batch size": batch_size,
        "Delimiter": delim,
    }
    return render_template(
        "admin/import_historical.html",
        title="Түүхэн CSV импорт",
        summary=summary,
        errors=errors[:200],
    )
