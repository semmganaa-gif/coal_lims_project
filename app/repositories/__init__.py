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

__all__ = [
    "SampleRepository",
    "AnalysisResultRepository",
    "AnalysisTypeRepository",
    "GbwStandardRepository",
    "ControlStandardRepository",
    "EquipmentRepository",
    "ChemicalRepository",
    "SystemSettingRepository",
]
