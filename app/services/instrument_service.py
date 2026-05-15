# app/services/instrument_service.py
# -*- coding: utf-8 -*-
"""
Instrument reading business logic — parse, store, review, approve.
"""

import hashlib

from flask import current_app
from sqlalchemy import and_, select

from app.bootstrap.extensions import db
from app.models.instrument import InstrumentReading
from app.models.core import Sample
from app.models.analysis import AnalysisResult
from app.repositories.instrument_repository import InstrumentReadingRepository
from app.instrument_parsers import get_parser, PARSER_REGISTRY
from app.utils.datetime import now_local
from app.utils.transaction import transactional


def parse_instrument_file(file_path: str, instrument_type: str,
                          instrument_name: str = "") -> list[InstrumentReading]:
    """Parse an instrument file and create InstrumentReading records (unsaved)."""
    parser = get_parser(instrument_type)

    if not parser.can_parse(file_path):
        raise ValueError(
            f"File extension not supported by {instrument_type} parser. "
            f"Supported: {parser.supported_extensions}"
        )

    readings_data = parser.parse(file_path)
    if not readings_data:
        return []

    # Compute file hash for duplicate detection
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    # Check for duplicate file
    existing = InstrumentReadingRepository.get_by_file_hash(file_hash)
    if existing:
        raise ValueError(
            f"File already imported (hash match). "
            f"Original import: {existing.created_at}"
        )

    instrument_readings = []
    for rd in readings_data:
        # Try to find matching sample
        sample = db.session.execute(
            select(Sample).where(Sample.sample_code == rd.sample_code)
        ).scalar_one_or_none()

        reading = InstrumentReading(
            instrument_name=instrument_name or rd.instrument_name,
            instrument_type=instrument_type,
            source_file=file_path,
            file_hash=file_hash,
            sample_id=sample.id if sample else None,
            sample_code=rd.sample_code,
            analysis_code=rd.analysis_code,
            raw_data=rd.raw_data,
            parsed_value=rd.value,
            unit=rd.unit,
            status="pending",
        )
        instrument_readings.append(reading)

    return instrument_readings


@transactional()
def import_instrument_file(file_path: str, instrument_type: str,
                           instrument_name: str = "") -> int:
    """Parse and save instrument readings to database. Returns count."""
    readings = parse_instrument_file(file_path, instrument_type, instrument_name)
    if not readings:
        return 0

    for r in readings:
        db.session.add(r)
    return len(readings)


def get_pending_readings(instrument_type: str = None,
                         limit: int = 100) -> list[InstrumentReading]:
    """Get pending readings for review."""
    return InstrumentReadingRepository.get_pending(instrument_type, limit)


@transactional()
def approve_reading(reading_id: int, user_id: int) -> InstrumentReading:
    """Approve a pending reading and link to AnalysisResult."""
    reading = db.session.get(InstrumentReading, reading_id)
    if reading is None:
        raise ValueError(f"Reading {reading_id} not found")
    if reading.status != "pending":
        raise ValueError(f"Reading {reading_id} is already {reading.status}")

    reading.status = "approved"
    reading.reviewed_by_id = user_id
    reading.reviewed_at = now_local()

    # Link to AnalysisResult if sample exists
    if reading.sample_id and reading.analysis_code:
        result = db.session.execute(
            select(AnalysisResult).where(
                AnalysisResult.sample_id == reading.sample_id,
                AnalysisResult.analysis_code == reading.analysis_code,
            )
        ).scalar_one_or_none()

        if result:
            result.final_result = reading.parsed_value
            reading.analysis_result_id = result.id
        else:
            current_app.logger.warning(
                f"No AnalysisResult for sample_id={reading.sample_id}, "
                f"analysis_code={reading.analysis_code}"
            )

    return reading


@transactional()
def reject_reading(reading_id: int, user_id: int,
                   reason: str = "") -> InstrumentReading:
    """Reject a pending reading."""
    reading = db.session.get(InstrumentReading, reading_id)
    if reading is None:
        raise ValueError(f"Reading {reading_id} not found")
    if reading.status != "pending":
        raise ValueError(f"Reading {reading_id} is already {reading.status}")

    reading.status = "rejected"
    reading.reviewed_by_id = user_id
    reading.reviewed_at = now_local()
    reading.reject_reason = reason

    return reading


def bulk_approve(reading_ids: list[int], user_id: int) -> int:
    """Approve multiple readings. Returns count approved."""
    count = 0
    for rid in reading_ids:
        try:
            approve_reading(rid, user_id)
            count += 1
        except ValueError:
            continue
    return count


def bulk_reject(reading_ids: list[int], user_id: int,
                reason: str = "") -> int:
    """Reject multiple readings. Returns count rejected."""
    count = 0
    for rid in reading_ids:
        try:
            reject_reading(rid, user_id, reason)
            count += 1
        except ValueError:
            continue
    return count


def get_reading_stats() -> dict:
    """Get summary statistics of instrument readings."""
    return InstrumentReadingRepository.get_status_counts()


def get_supported_instruments() -> list[dict]:
    """List supported instrument types."""
    return [
        {"type": key, "name": key.replace("_", " ").title()}
        for key in PARSER_REGISTRY.keys()
    ]
