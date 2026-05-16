# app/constants/enums.py
# -*- coding: utf-8 -*-
"""
Системийн төлвүүдийн Enum class-ууд (single source of truth).

CheckConstraint, Marshmallow schema validation, business logic — бүгд эндээс
утгуудыг авна. Hard-coded string literal-уудыг (`'admin'`, `'new'` гэх мэт)
энд тодорхойлсон enum-аар орлуулна.

Жишээ хэрэглээ:
    from app.constants.enums import SampleStatus, UserRole

    # Model CheckConstraint:
    CheckConstraint(SampleStatus.check_constraint("status"), name="ck_sample_status")

    # Schema validation:
    role = fields.Str(validate=validate.OneOf(UserRole.values()))

    # Business logic:
    if current_user.role == UserRole.ADMIN.value:
        ...
"""
from __future__ import annotations

from enum import Enum


class _StrEnum(str, Enum):
    """Base class for string enums with helpers for SQL/Schema integration."""

    @classmethod
    def values(cls) -> list[str]:
        """Бүх утгуудын жагсаалт (Schema-д `OneOf`-д ашиглана)."""
        return [member.value for member in cls]

    @classmethod
    def check_constraint(cls, column: str) -> str:
        """
        SQLAlchemy `CheckConstraint`-д ашиглах SQL fragment гаргах.

        >>> SampleStatus.check_constraint("status")
        "status IN ('new','in_progress','analysis','completed','archived')"
        """
        quoted = ",".join(f"'{member.value}'" for member in cls)
        return f"{column} IN ({quoted})"


# ─────────────────────────────────────────────────────────────
# Sample & Analysis
# ─────────────────────────────────────────────────────────────

class SampleStatus(_StrEnum):
    """Дээжний workflow status — Sample.status CheckConstraint-тэй sync.

    NOTE: Disposal нь Sample.disposal_date талбараар хянагдана (status биш).
    """
    NEW = "new"
    IN_PROGRESS = "in_progress"
    ANALYSIS = "analysis"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AnalysisResultStatus(_StrEnum):
    """AnalysisResult.status CheckConstraint-тэй sync."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REANALYSIS = "reanalysis"


# ─────────────────────────────────────────────────────────────
# User & Auth
# ─────────────────────────────────────────────────────────────

class UserRole(_StrEnum):
    """User.role утгууд. workflow_engine-ийн role list-тэй sync."""
    PREP = "prep"
    CHEMIST = "chemist"
    SENIOR = "senior"
    MANAGER = "manager"
    ADMIN = "admin"


class UserLanguage(_StrEnum):
    """User.language utgууд."""
    EN = "en"
    MN = "mn"


# ─────────────────────────────────────────────────────────────
# Lab
# ─────────────────────────────────────────────────────────────

class LabKey(_StrEnum):
    """Registered lab keys — INSTALLED_LABS-тэй sync (bootstrap/blueprints.py)."""
    COAL = "coal"
    PETROGRAPHY = "petrography"
    WATER_CHEMISTRY = "water_chemistry"
    MICROBIOLOGY = "microbiology"


# ─────────────────────────────────────────────────────────────
# Chemicals & Equipment
# ─────────────────────────────────────────────────────────────

class ChemicalStatus(_StrEnum):
    """Chemical.status CheckConstraint-тэй sync."""
    ACTIVE = "active"
    LOW_STOCK = "low_stock"
    EXPIRED = "expired"
    EMPTY = "empty"
    DISPOSED = "disposed"


class EquipmentStatus(_StrEnum):
    """Equipment.status CheckConstraint-тэй sync.

    Lifecycle:
      normal → calibration/maintenance → normal
             → needs_spare (degraded, can still operate, awaiting parts)
             → out_of_service (cannot operate, requires major intervention)
             → retired (terminal — permanently decommissioned)
    """
    NORMAL = "normal"
    MAINTENANCE = "maintenance"
    CALIBRATION = "calibration"
    NEEDS_SPARE = "needs_spare"
    OUT_OF_SERVICE = "out_of_service"
    RETIRED = "retired"


# ─────────────────────────────────────────────────────────────
# Quality
# ─────────────────────────────────────────────────────────────

class CorrectiveActionStatus(_StrEnum):
    """CorrectiveAction.status CheckConstraint-тэй sync."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REVIEWED = "reviewed"
    CLOSED = "closed"


class CorrectiveActionSeverity(_StrEnum):
    """CorrectiveAction.severity CheckConstraint-тэй sync."""
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"
