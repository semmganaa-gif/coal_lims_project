# app/repositories/quality_repository.py
# -*- coding: utf-8 -*-
"""Quality Repository - Чанарын бүртгэлүүдийн database operations."""

from __future__ import annotations

from typing import Optional

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
        query = CustomerComplaint.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(CustomerComplaint.complaint_date.desc()).all()

    @staticmethod
    def get_next_number() -> str:
        from app.utils.datetime import now_local as now_mn
        year = now_mn().year
        last = (
            CustomerComplaint.query
            .filter(CustomerComplaint.complaint_no.like(f"COMP-{year}-%"))
            .order_by(CustomerComplaint.id.desc())
            .first()
        )
        if last and last.complaint_no:
            try:
                seq = int(last.complaint_no.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"COMP-{year}-{seq:03d}"

    @staticmethod
    def save(complaint: CustomerComplaint, commit: bool = True) -> CustomerComplaint:
        db.session.add(complaint)
        if commit:
            db.session.commit()
        return complaint

    @staticmethod
    def delete(complaint: CustomerComplaint, commit: bool = True) -> bool:
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
        query = CorrectiveAction.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(CorrectiveAction.issue_date.desc()).all()

    @staticmethod
    def save(capa: CorrectiveAction, commit: bool = True) -> CorrectiveAction:
        db.session.add(capa)
        if commit:
            db.session.commit()
        return capa

    @staticmethod
    def delete(capa: CorrectiveAction, commit: bool = True) -> bool:
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
        query = NonConformityRecord.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(NonConformityRecord.record_date.desc()).all()

    @staticmethod
    def save(record: NonConformityRecord, commit: bool = True) -> NonConformityRecord:
        db.session.add(record)
        if commit:
            db.session.commit()
        return record

    @staticmethod
    def delete(record: NonConformityRecord, commit: bool = True) -> bool:
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
        query = ImprovementRecord.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(ImprovementRecord.record_date.desc()).all()

    @staticmethod
    def save(record: ImprovementRecord, commit: bool = True) -> ImprovementRecord:
        db.session.add(record)
        if commit:
            db.session.commit()
        return record

    @staticmethod
    def delete(record: ImprovementRecord, commit: bool = True) -> bool:
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
        return ProficiencyTest.query.order_by(ProficiencyTest.test_date.desc()).all()

    @staticmethod
    def get_by_analysis(analysis_code: str) -> list[ProficiencyTest]:
        return (
            ProficiencyTest.query
            .filter_by(analysis_code=analysis_code)
            .order_by(ProficiencyTest.test_date.desc())
            .all()
        )

    @staticmethod
    def save(test: ProficiencyTest, commit: bool = True) -> ProficiencyTest:
        db.session.add(test)
        if commit:
            db.session.commit()
        return test

    @staticmethod
    def delete(test: ProficiencyTest, commit: bool = True) -> bool:
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
        return EnvironmentalLog.query.order_by(EnvironmentalLog.log_date.desc()).all()

    @staticmethod
    def get_by_location(location: str) -> list[EnvironmentalLog]:
        return (
            EnvironmentalLog.query
            .filter_by(location=location)
            .order_by(EnvironmentalLog.log_date.desc())
            .all()
        )

    @staticmethod
    def save(log: EnvironmentalLog, commit: bool = True) -> EnvironmentalLog:
        db.session.add(log)
        if commit:
            db.session.commit()
        return log
