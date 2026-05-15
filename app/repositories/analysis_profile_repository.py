# app/repositories/analysis_profile_repository.py
# -*- coding: utf-8 -*-
"""
AnalysisProfile Repository - Шинжилгээний профайлын database operations.

Simple (client_name + sample_type) болон CHPP pattern profile-уудтай
ажиллах query-ууд. SQLAlchemy 2.0 native API (`select()`) ашиглана.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select

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
        stmt = select(AnalysisProfile).order_by(
            AnalysisProfile.priority.desc(), AnalysisProfile.id.asc()
        )
        return list(db.session.execute(stmt).scalars().all())

    # =========================================================================
    # Filtered queries
    # =========================================================================

    @staticmethod
    def get_simple_profiles(exclude_chpp: bool = True,
                            ordered: bool = False) -> list[AnalysisProfile]:
        """Simple профайлууд (pattern=None). Default нь CHPP-ээс бусад."""
        stmt = select(AnalysisProfile).where(
            (AnalysisProfile.pattern.is_(None)) | (AnalysisProfile.pattern == '')
        )
        if exclude_chpp:
            stmt = stmt.where(AnalysisProfile.client_name != 'CHPP')
        if ordered:
            stmt = stmt.order_by(
                AnalysisProfile.client_name, AnalysisProfile.sample_type
            )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_chpp_profiles(ordered: bool = False) -> list[AnalysisProfile]:
        """CHPP pattern profile-уудыг буцаах."""
        stmt = select(AnalysisProfile).where(
            AnalysisProfile.client_name == 'CHPP',
            AnalysisProfile.pattern.isnot(None),
            AnalysisProfile.pattern != ''
        )
        if ordered:
            stmt = stmt.order_by(
                AnalysisProfile.sample_type, AnalysisProfile.pattern
            )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def find_simple(client_name: str, sample_type: str) -> Optional[AnalysisProfile]:
        """Client + sample_type-аар simple профайл хайх (no pattern)."""
        stmt = select(AnalysisProfile).where(
            (AnalysisProfile.pattern.is_(None)) | (AnalysisProfile.pattern == ''),
            AnalysisProfile.client_name == client_name,
            AnalysisProfile.sample_type == sample_type,
        )
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def find_pattern(client_name: str, sample_type: str,
                     pattern: str) -> Optional[AnalysisProfile]:
        """Client + sample_type + pattern таарах профайл хайх."""
        stmt = select(AnalysisProfile).where(
            AnalysisProfile.client_name == client_name,
            AnalysisProfile.sample_type == sample_type,
            AnalysisProfile.pattern == pattern,
        )
        return db.session.execute(stmt).scalar_one_or_none()
