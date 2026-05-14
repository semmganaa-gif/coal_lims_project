# app/repositories/report_repository.py
# -*- coding: utf-8 -*-
"""Report Repository - Тайлангийн database operations."""

from __future__ import annotations

from typing import Optional

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
        return LabReport.query.filter_by(report_number=report_number).first()

    @staticmethod
    def get_by_lab(lab_type: str, status: Optional[str] = None) -> list[LabReport]:
        query = LabReport.query.filter_by(lab_type=lab_type)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(LabReport.created_at.desc()).all()

    @staticmethod
    def get_all(status: Optional[str] = None) -> list[LabReport]:
        query = LabReport.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(LabReport.created_at.desc()).all()

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
        query = ReportSignature.query.filter_by(is_active=True)
        if sig_type:
            query = query.filter_by(signature_type=sig_type)
        if lab_type:
            from sqlalchemy import or_
            query = query.filter(or_(
                ReportSignature.lab_type == lab_type,
                ReportSignature.lab_type == 'all',
            ))
        return query.all()

    @staticmethod
    def get_by_user(user_id: int) -> list[ReportSignature]:
        return ReportSignature.query.filter_by(user_id=user_id).all()

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
