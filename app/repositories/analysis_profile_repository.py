# app/repositories/analysis_profile_repository.py
# -*- coding: utf-8 -*-
"""
AnalysisProfile Repository - Шинжилгээний профайлын database operations.

Simple (client_name + sample_type) болон CHPP pattern profile-уудтай
ажиллах query-ууд.
"""

from __future__ import annotations

from typing import Optional

from app import db
from app.models import AnalysisProfile


class AnalysisProfileRepository:
    """AnalysisProfile model-ийн database operations."""

    # =========================================================================
    # Basic CRUD
    # =========================================================================

    @staticmethod
    def get_by_id(profile_id: int) -> Optional[AnalysisProfile]:
        """ID-аар профайл авах."""
        return db.session.get(AnalysisProfile, profile_id)

    @staticmethod
    def get_all() -> list[AnalysisProfile]:
        """Бүх профайл."""
        return AnalysisProfile.query.order_by(
            AnalysisProfile.priority.desc(), AnalysisProfile.id.asc()
        ).all()

    # =========================================================================
    # Filtered queries
    # =========================================================================

    @staticmethod
    def get_simple_profiles(exclude_chpp: bool = True,
                            ordered: bool = False) -> list[AnalysisProfile]:
        """Simple профайлууд (pattern=None). Default нь CHPP-ээс бусад."""
        query = AnalysisProfile.query.filter(
            (AnalysisProfile.pattern.is_(None)) | (AnalysisProfile.pattern == '')
        )
        if exclude_chpp:
            query = query.filter(AnalysisProfile.client_name != 'CHPP')
        if ordered:
            query = query.order_by(
                AnalysisProfile.client_name, AnalysisProfile.sample_type
            )
        return query.all()

    @staticmethod
    def get_chpp_profiles(ordered: bool = False) -> list[AnalysisProfile]:
        """CHPP pattern profile-уудыг буцаах."""
        query = AnalysisProfile.query.filter(
            AnalysisProfile.client_name == 'CHPP',
            AnalysisProfile.pattern.isnot(None),
            AnalysisProfile.pattern != ''
        )
        if ordered:
            query = query.order_by(
                AnalysisProfile.sample_type, AnalysisProfile.pattern
            )
        return query.all()

    @staticmethod
    def find_simple(client_name: str, sample_type: str) -> Optional[AnalysisProfile]:
        """Client + sample_type-аар simple профайл хайх (no pattern)."""
        return AnalysisProfile.query.filter(
            (AnalysisProfile.pattern.is_(None)) | (AnalysisProfile.pattern == ''),
            AnalysisProfile.client_name == client_name,
            AnalysisProfile.sample_type == sample_type
        ).first()

    @staticmethod
    def find_pattern(client_name: str, sample_type: str,
                     pattern: str) -> Optional[AnalysisProfile]:
        """Client + sample_type + pattern таарах профайл хайх."""
        return AnalysisProfile.query.filter(
            AnalysisProfile.client_name == client_name,
            AnalysisProfile.sample_type == sample_type,
            AnalysisProfile.pattern == pattern,
        ).first()
