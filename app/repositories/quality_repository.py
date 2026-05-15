# app/repositories/quality_repository.py
# -*- coding: utf-8 -*-
"""Quality Repository - Чанарын бүртгэлүүдийн database operations.

SQLAlchemy 2.0 native API (`select()` builder) ашиглана.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app import db
from app.models import (
    CustomerComplaint,
    CorrectiveAction,
    NonConformityRecord,
    ImprovementRecord,
    ProficiencyTest,
    EnvironmentalLog,
)


class ComplaintRepository:
    """CustomerComplaint model-ийн database operations."""

    @staticmethod
    def get_by_id(complaint_id: int) -> Optional[CustomerComplaint]:
        return db.session.get(CustomerComplaint, complaint_id)

    @staticmethod
    def get_by_id_or_404(complaint_id: int) -> CustomerComplaint:
        obj = db.session.get(CustomerComplaint, complaint_id)
        if obj is None:
            from flask import abort
            abort(404)
        return obj

    @staticmethod
    def get_all(status: Optional[str] = None) -> list[CustomerComplaint]:
        stmt = select(CustomerComplaint)
        if status:
            stmt = stmt.where(CustomerComplaint.status == status)
        stmt = stmt.order_by(CustomerComplaint.complaint_date.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_next_number() -> str:
        from app.utils.datetime import now_local as now_mn
        year = now_mn().year
        stmt = (
            select(CustomerComplaint)
            .where(CustomerComplaint.complaint_no.like(f"COMP-{year}-%"))
            .order_by(CustomerComplaint.id.desc())
            .limit(1)
        )
        last = db.session.execute(stmt).scalar_one_or_none()
        if last and last.complaint_no:
            try:
                seq = int(last.complaint_no.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"COMP-{year}-{seq:03d}"

    @staticmethod
    def save(complaint: CustomerComplaint, commit: bool = False) -> CustomerComplaint:
        db.session.add(complaint)
        if commit:
            db.session.commit()
        return complaint

    @staticmethod
    def delete(complaint: CustomerComplaint, commit: bool = False) -> bool:
        db.session.delete(complaint)
        if commit:
            db.session.commit()
        return True


class CAPARepository:
    """CorrectiveAction model-ийн database operations."""

    @staticmethod
    def get_by_id(capa_id: int) -> Optional[CorrectiveAction]:
        return db.session.get(CorrectiveAction, capa_id)

    @staticmethod
    def get_by_id_or_404(capa_id: int) -> CorrectiveAction:
        obj = db.session.get(CorrectiveAction, capa_id)
        if obj is None:
            from flask import abort
            abort(404)
        return obj

    @staticmethod
    def get_all(status: Optional[str] = None) -> list[CorrectiveAction]:
        stmt = select(CorrectiveAction)
        if status:
            stmt = stmt.where(CorrectiveAction.status == status)
        stmt = stmt.order_by(CorrectiveAction.issue_date.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def save(capa: CorrectiveAction, commit: bool = False) -> CorrectiveAction:
        db.session.add(capa)
        if commit:
            db.session.commit()
        return capa

    @staticmethod
    def delete(capa: CorrectiveAction, commit: bool = False) -> bool:
        db.session.delete(capa)
        if commit:
            db.session.commit()
        return True


class NonConformityRepository:
    """NonConformityRecord model-ийн database operations."""

    @staticmethod
    def get_by_id(record_id: int) -> Optional[NonConformityRecord]:
        return db.session.get(NonConformityRecord, record_id)

    @staticmethod
    def get_by_id_or_404(record_id: int) -> NonConformityRecord:
        obj = db.session.get(NonConformityRecord, record_id)
        if obj is None:
            from flask import abort
            abort(404)
        return obj

    @staticmethod
    def get_all(status: Optional[str] = None) -> list[NonConformityRecord]:
        stmt = select(NonConformityRecord)
        if status:
            stmt = stmt.where(NonConformityRecord.status == status)
        stmt = stmt.order_by(NonConformityRecord.record_date.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def save(record: NonConformityRecord, commit: bool = False) -> NonConformityRecord:
        db.session.add(record)
        if commit:
            db.session.commit()
        return record

    @staticmethod
    def delete(record: NonConformityRecord, commit: bool = False) -> bool:
        db.session.delete(record)
        if commit:
            db.session.commit()
        return True


class ImprovementRepository:
    """ImprovementRecord model-ийн database operations."""

    @staticmethod
    def get_by_id(record_id: int) -> Optional[ImprovementRecord]:
        return db.session.get(ImprovementRecord, record_id)

    @staticmethod
    def get_by_id_or_404(record_id: int) -> ImprovementRecord:
        obj = db.session.get(ImprovementRecord, record_id)
        if obj is None:
            from flask import abort
            abort(404)
        return obj

    @staticmethod
    def get_all(status: Optional[str] = None) -> list[ImprovementRecord]:
        stmt = select(ImprovementRecord)
        if status:
            stmt = stmt.where(ImprovementRecord.status == status)
        stmt = stmt.order_by(ImprovementRecord.record_date.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def save(record: ImprovementRecord, commit: bool = False) -> ImprovementRecord:
        db.session.add(record)
        if commit:
            db.session.commit()
        return record

    @staticmethod
    def delete(record: ImprovementRecord, commit: bool = False) -> bool:
        db.session.delete(record)
        if commit:
            db.session.commit()
        return True


class ProficiencyTestRepository:
    """ProficiencyTest model-ийн database operations."""

    @staticmethod
    def get_by_id(test_id: int) -> Optional[ProficiencyTest]:
        return db.session.get(ProficiencyTest, test_id)

    @staticmethod
    def get_by_id_or_404(test_id: int) -> ProficiencyTest:
        obj = db.session.get(ProficiencyTest, test_id)
        if obj is None:
            from flask import abort
            abort(404)
        return obj

    @staticmethod
    def get_all() -> list[ProficiencyTest]:
        stmt = select(ProficiencyTest).order_by(ProficiencyTest.test_date.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_by_analysis(analysis_code: str) -> list[ProficiencyTest]:
        stmt = (
            select(ProficiencyTest)
            .where(ProficiencyTest.analysis_code == analysis_code)
            .order_by(ProficiencyTest.test_date.desc())
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def save(test: ProficiencyTest, commit: bool = False) -> ProficiencyTest:
        db.session.add(test)
        if commit:
            db.session.commit()
        return test

    @staticmethod
    def delete(test: ProficiencyTest, commit: bool = False) -> bool:
        db.session.delete(test)
        if commit:
            db.session.commit()
        return True


class EnvironmentalLogRepository:
    """EnvironmentalLog model-ийн database operations."""

    @staticmethod
    def get_by_id(log_id: int) -> Optional[EnvironmentalLog]:
        return db.session.get(EnvironmentalLog, log_id)

    @staticmethod
    def get_all() -> list[EnvironmentalLog]:
        stmt = select(EnvironmentalLog).order_by(EnvironmentalLog.log_date.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_by_location(location: str) -> list[EnvironmentalLog]:
        stmt = (
            select(EnvironmentalLog)
            .where(EnvironmentalLog.location == location)
            .order_by(EnvironmentalLog.log_date.desc())
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def save(log: EnvironmentalLog, commit: bool = False) -> EnvironmentalLog:
        db.session.add(log)
        if commit:
            db.session.commit()
        return log
