# app/repositories/__init__.py
# -*- coding: utf-8 -*-
"""
Repository Layer - Database access abstraction.

Repositories модулиуд нь database query-уудыг нэг дор төвлөрүүлнэ.
"""

from app.repositories.sample_repository import SampleRepository
from app.repositories.analysis_result_repository import AnalysisResultRepository
from app.repositories.analysis_type_repository import AnalysisTypeRepository
from app.repositories.standard_repository import GbwStandardRepository, ControlStandardRepository
from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.chemical_repository import ChemicalRepository
from app.repositories.system_setting_repository import SystemSettingRepository
from app.repositories.user_repository import UserRepository
from app.repositories.bottle_repository import BottleRepository, BottleConstantRepository
from app.repositories.chat_repository import ChatMessageRepository, UserOnlineStatusRepository
from app.repositories.audit_repository import AuditLogRepository
from app.repositories.quality_repository import (
    ComplaintRepository,
    CAPARepository,
    NonConformityRepository,
    ImprovementRepository,
    ProficiencyTestRepository,
    EnvironmentalLogRepository,
)
from app.repositories.report_repository import LabReportRepository, ReportSignatureRepository
from app.repositories.maintenance_repository import MaintenanceLogRepository, UsageLogRepository
from app.repositories.analysis_profile_repository import AnalysisProfileRepository
from app.repositories.instrument_repository import InstrumentReadingRepository
from app.repositories.planning_repository import MonthlyPlanRepository, StaffSettingsRepository
from app.repositories.spare_parts_repository import (
    SparePartRepository,
    SparePartCategoryRepository,
    SparePartUsageRepository,
    SparePartLogRepository,
)
from app.repositories.chemical_usage_repository import (
    ChemicalUsageRepository,
    ChemicalLogRepository,
    ChemicalWasteRepository,
    ChemicalWasteRecordRepository,
)
from app.repositories.solutions_repository import (
    SolutionRecipeRepository,
    SolutionPreparationRepository,
    SolutionRecipeIngredientRepository,
)

__all__ = [
    "SampleRepository",
    "AnalysisResultRepository",
    "AnalysisTypeRepository",
    "AnalysisProfileRepository",
    "InstrumentReadingRepository",
    "MonthlyPlanRepository",
    "StaffSettingsRepository",
    "SparePartRepository",
    "SparePartCategoryRepository",
    "SparePartUsageRepository",
    "SparePartLogRepository",
    "ChemicalUsageRepository",
    "ChemicalLogRepository",
    "ChemicalWasteRepository",
    "ChemicalWasteRecordRepository",
    "SolutionRecipeRepository",
    "SolutionPreparationRepository",
    "SolutionRecipeIngredientRepository",
    "GbwStandardRepository",
    "ControlStandardRepository",
    "EquipmentRepository",
    "ChemicalRepository",
    "SystemSettingRepository",
    "UserRepository",
    "BottleRepository",
    "BottleConstantRepository",
    "ChatMessageRepository",
    "UserOnlineStatusRepository",
    "AuditLogRepository",
    "ComplaintRepository",
    "CAPARepository",
    "NonConformityRepository",
    "ImprovementRepository",
    "ProficiencyTestRepository",
    "EnvironmentalLogRepository",
    "LabReportRepository",
    "ReportSignatureRepository",
    "MaintenanceLogRepository",
    "UsageLogRepository",
]
