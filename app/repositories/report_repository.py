# app/repositories/report_repository.py
# -*- coding: utf-8 -*-
"""Report Repository - Тайлангийн database operations.

SQLAlchemy 2.0 native API (`select()` builder) ашиглана.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import or_, select

from app import db
from app.models import LabReport, ReportSignature


class LabReportRepository:
    """LabReport model-ийн database operations."""

    @staticmethod
    def get_by_id(report_id: int) -> Optional[LabReport]:
        return db.session.get(LabReport, report_id)

    @staticmethod
    def get_by_id_or_404(report_id: int) -> LabReport:
        report = db.session.get(LabReport, report_id)
        if report is None:
            from flask import abort
            abort(404)
        return report

    @staticmethod
    def get_by_number(report_number: str) -> Optional[LabReport]:
        stmt = select(LabReport).where(LabReport.report_number == report_number)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_lab(lab_type: str, status: Optional[str] = None) -> list[LabReport]:
        stmt = select(LabReport).where(LabReport.lab_type == lab_type)
        if status:
            stmt = stmt.where(LabReport.status == status)
        stmt = stmt.order_by(LabReport.created_at.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_all(status: Optional[str] = None) -> list[LabReport]:
        stmt = select(LabReport)
        if status:
            stmt = stmt.where(LabReport.status == status)
        stmt = stmt.order_by(LabReport.created_at.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def save(report: LabReport, commit: bool = False) -> LabReport:
        db.session.add(report)
        if commit:
            db.session.commit()
        return report

    @staticmethod
    def delete(report: LabReport, commit: bool = False) -> bool:
        db.session.delete(report)
        if commit:
            db.session.commit()
        return True


class ReportSignatureRepository:
    """ReportSignature model-ийн database operations."""

    @staticmethod
    def get_by_id(sig_id: int) -> Optional[ReportSignature]:
        return db.session.get(ReportSignature, sig_id)

    @staticmethod
    def get_active(sig_type: Optional[str] = None, lab_type: Optional[str] = None) -> list[ReportSignature]:
        stmt = select(ReportSignature).where(ReportSignature.is_active.is_(True))
        if sig_type:
            stmt = stmt.where(ReportSignature.signature_type == sig_type)
        if lab_type:
            stmt = stmt.where(or_(
                ReportSignature.lab_type == lab_type,
                ReportSignature.lab_type == 'all',
            ))
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_by_user(user_id: int) -> list[ReportSignature]:
        stmt = select(ReportSignature).where(ReportSignature.user_id == user_id)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def save(sig: ReportSignature, commit: bool = False) -> ReportSignature:
        db.session.add(sig)
        if commit:
            db.session.commit()
        return sig

    @staticmethod
    def delete(sig: ReportSignature, commit: bool = False) -> bool:
        db.session.delete(sig)
        if commit:
            db.session.commit()
        return True
