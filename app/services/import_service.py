# app/services/import_service.py
# -*- coding: utf-8 -*-
"""
Business logic for historical CSV import (2009+).

Two formats supported:
1) Long format: sample_code, client_name, sample_type, analysis_code, value, analysis_date
2) CHPP wide format: _sel, ID, Дээжний нэр, Нэгж, Төрөл, Бүртгэсэн, Шинжилсэн, Mt,ar, Mad, ...

All functions accept plain Python parameters (no Flask request objects).
"""

import csv
import io
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app import models as M
from app.constants import MIN_VALID_YEAR, MAX_VALID_YEAR
from app.utils.analysis_aliases import ALIAS_TO_BASE as _ALIAS_TO_BASE
from app.utils.converters import to_float

logger = logging.getLogger(__name__)

# -------------------------------------------------
# Alias mapping (lowercase keys)
# -------------------------------------------------
ALIAS_TO_BASE: Dict[str, str] = {k.lower(): v for k, v in _ALIAS_TO_BASE.items()}

# --- Header synonyms (long format) ---
HEADER_KEYS = {
    "sample_code": {
        "sample_code", "sample", "code", "internal_code",
        "дотоод код", "дээж код", "дээжний нэр",
    },
    "name": {"name", "sample_name"},
    "client_name": {"client_name", "unit", "нэгж", "organization", "dept"},
    "sample_type": {"sample_type", "type", "төрөл"},
    "received_date": {"received_date", "reg_date", "бүртгэсэн", "registered_at"},
    "analysis_date": {
        "analysis_date", "date", "огноо", "tested_at",
        "approved_at", "updated_at", "created_at",
    },
    "analysis_code": {"analysis_code", "code", "test", "property", "анализ", "шинжилгээ"},
    "value": {"value", "result", "үр дүн", "тоо"},
    "unit": {"unit", "μ", "meas_unit"},
    "status": {"status", "state"},
}


# -------------------------------------------------
# Helper functions
# -------------------------------------------------


def _norm(s: Any) -> str:
    """Strip whitespace from value, return empty string for None."""
    return str(s).strip() if s is not None else ""


def _parse_date(s: Any) -> Optional[datetime]:
    """Parse a date string trying multiple formats. Returns None on failure."""
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
        except ValueError:
            continue

    try:
        y = int(t)
        if MIN_VALID_YEAR <= y <= MAX_VALID_YEAR:
            return datetime(y, 1, 1)
    except (ValueError, TypeError):
        pass
    return None


def _map_header(h: str) -> Optional[str]:
    """Map a raw CSV header to a standard key using HEADER_KEYS synonyms."""
    key = h.strip().lower()
    for std, alts in HEADER_KEYS.items():
        if key in {a.lower() for a in alts}:
            return std
    return None


def _base_code(raw: str) -> str:
    """Normalize an analysis code via alias mapping."""
    if not raw:
        return ""
    x = raw.strip()
    key = x.lower()
    if key in ALIAS_TO_BASE:
        return ALIAS_TO_BASE[key]
    return x


# -------------------------------------------------
# DB operations
# -------------------------------------------------


def _get_or_create_sample(sample_code: str, defaults: Dict[str, Any]) -> M.Sample:
    """
    Find Sample by sample_code; create if missing.
    Updates empty fields (client_name, sample_type, received_date) on existing rows.
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
    Upsert AnalysisResult on (sample_id, analysis_code).
    Returns (was_created, row_id).
    """
    R = M.AnalysisResult
    filters = [R.sample_id == sample_id, R.analysis_code == analysis_code]
    row = db.session.query(R).filter(and_(*filters)).first()

    if row:
        if value is not None and hasattr(row, "final_result"):
            row.final_result = value
        if status and hasattr(row, "status"):
            row.status = status
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
# CSV parsing
# -------------------------------------------------


def decode_csv_bytes(raw: bytes) -> str:
    """Decode raw file bytes to string (utf-8-sig first, then cp1251 fallback)."""
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1251", errors="ignore")


def detect_delimiter(text: str) -> str:
    """Auto-detect CSV delimiter from the first 10 lines."""
    lines = text.splitlines()
    sample_lines = "\n".join(lines[:10])
    try:
        sniff = csv.Sniffer().sniff(sample_lines, delimiters=",;\t")
        return sniff.delimiter
    except csv.Error:
        return ","


def parse_csv_header(text: str, delim: str) -> Tuple[csv.reader, List[str]]:
    """
    Parse CSV text: read and clean the header row.
    Returns (reader positioned after header, cleaned header list).
    Raises ValueError if the file is empty.
    """
    string_io = io.StringIO(text, newline="")
    reader = csv.reader(string_io, delimiter=delim)
    try:
        raw_header = next(reader)
    except StopIteration:
        raise ValueError("Хоосон файл.")

    header = [(h or "").replace("\ufeff", "").strip() for h in raw_header]
    return reader, header


# -------------------------------------------------
# CHPP wide CSV import (positional)
# -------------------------------------------------


def import_chpp_wide(
    reader: csv.reader,
    header: List[str],
    dry_run: bool,
    batch_size: int,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Import CHPP wide CSV format (positional columns).

    Columns: _sel, ID, Дээжний нэр, Нэгж, Төрөл, Бүртгэсэн, Шинжилсэн, [analysis cols...]
    """
    errors: List[str] = []

    if len(header) < 7:
        errors.append(
            "CHPP wide формат гэж үзсэн ч хамгийн багадаа 7 багана байх ёстой "
            "(_sel, ID, Дээжний нэр, Нэгж, Төрөл, Бүртгэсэн, Шинжилсэн)."
        )
        summary = {
            "Нийт мөр": 0, "Шинэ дээж": 0,
            "Шинэ шинжилгээний төрөл": 0, "Оруулсан үр дүн": 0,
            "Шинэчилсэн үр дүн": 0, "Алдаа": len(errors),
            "Dry-run": dry_run, "Batch size": batch_size, "Delimiter": ",",
        }
        return summary, errors

    idx_sample = 2
    idx_client = 3
    idx_type = 4
    idx_regd = 5
    idx_tested = 6

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
            received_date = _parse_date(row[idx_regd]) if len(row) > idx_regd else None
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

            for col_index, col_header in analysis_cols:
                if col_index >= len(row):
                    continue
                value = to_float(row[col_index])
                if value is None:
                    continue

                analysis_code = _base_code(col_header)
                ins, _rid = _upsert_result(
                    s.id, analysis_code, analysis_date, value, status=None,
                )
                if ins:
                    inserted_results += 1
                else:
                    updated_results += 1

            batch_count += 1
            if not dry_run and batch_count >= batch_size:
                try:
                    db.session.commit()
                except SQLAlchemyError as e:
                    db.session.rollback()
                    logger.error("CHPP wide batch commit error at row %d: %s", total, e)
                    errors.append(f"Batch commit алдаа (мөр ~{total}): {e}")
                batch_count = 0

        except (SQLAlchemyError, ValueError, TypeError, IndexError) as e:
            errors.append(f"Мөр {total}: {e}")
            continue

    if dry_run:
        db.session.rollback()
    else:
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error("CHPP wide final commit error: %s", e)
            errors.append(f"Эцсийн commit алдаа: {e}")

    summary = {
        "Нийт мөр": total, "Шинэ дээж": created_samples,
        "Шинэ шинжилгээний төрөл": 0, "Оруулсан үр дүн": inserted_results,
        "Шинэчилсэн үр дүн": updated_results, "Алдаа": len(errors),
        "Dry-run": dry_run, "Batch size": batch_size, "Delimiter": ",",
    }
    return summary, errors


# -------------------------------------------------
# Long format import
# -------------------------------------------------


def import_long(
    reader: csv.reader,
    header: List[str],
    dry_run: bool,
    batch_size: int,
    delim: str,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Import long-format CSV.
    Raises ValueError if required columns are missing.
    """
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
                analysis_code = _base_code(_norm(row[cols["analysis_code"]]))
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
                    s.id, analysis_code, analysis_date, value, status=status,
                )
                if ins:
                    inserted_results += 1
                else:
                    updated_results += 1

                batch_count += 1
                if not dry_run and batch_count >= batch_size:
                    try:
                        db.session.commit()
                    except SQLAlchemyError as e:
                        db.session.rollback()
                        logger.error("Long format batch commit error at row %d: %s", total, e)
                        errors.append(f"Batch commit алдаа (мөр ~{total}): {e}")
                    batch_count = 0

            except (SQLAlchemyError, ValueError, TypeError, IndexError) as e:
                errors.append(f"Мөр {total}: {e}")
                continue

        if dry_run:
            db.session.rollback()
        else:
            try:
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error("Long format final commit error: %s", e)
                errors.append(f"Эцсийн commit алдаа: {e}")

    except SQLAlchemyError:
        db.session.rollback()
        raise

    summary = {
        "Нийт мөр": total, "Шинэ дээж": created_samples,
        "Шинэ шинжилгээний төрөл": 0, "Оруулсан үр дүн": inserted_results,
        "Шинэчилсэн үр дүн": updated_results, "Алдаа": len(errors),
        "Dry-run": dry_run, "Batch size": batch_size, "Delimiter": delim,
    }
    return summary, errors


# -------------------------------------------------
# Orchestrator: parse file bytes and import
# -------------------------------------------------


def process_csv_import(
    file_bytes: bytes,
    dry_run: bool = False,
    batch_size: int = 1000,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    High-level entry point: decode, detect format, and import.

    Args:
        file_bytes: Raw bytes of the uploaded CSV file.
        dry_run: If True, rollback all changes after processing.
        batch_size: Commit interval.

    Returns:
        (summary_dict, error_list)

    Raises:
        ValueError: On empty file or unrecoverable parse error.
        SQLAlchemyError: On unrecoverable DB error.
    """
    text = decode_csv_bytes(file_bytes)
    delim = detect_delimiter(text)
    reader, header = parse_csv_header(text, delim)

    try:
        return import_long(reader, header, dry_run, batch_size, delim)
    except ValueError as ve:
        if "Дутуу багана байна" not in str(ve):
            raise
        # Fall back to CHPP wide format
        logger.warning("IMPORT: CHPP wide positional mapping ашиглалаа.")
        reader, header = parse_csv_header(text, delim)
        return import_chpp_wide(reader, header, dry_run, batch_size)
