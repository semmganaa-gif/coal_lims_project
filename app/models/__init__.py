# app/models/__init__.py
# -*- coding: utf-8 -*-
"""
Coal LIMS Models Package.

Re-exports all models from split modules for backward compatibility.
"""

from app.models.mixins import FLOAT_EPSILON, HashableMixin
from app.models.core import User, Sample
from app.models.analysis import AnalysisResult, AnalysisType, AnalysisProfile, SampleCalculations
from app.models.analysis_audit import AnalysisResultLog
from app.models.spare_parts import SparePartCategory, SparePart, SparePartUsage, SparePartLog
from app.models.bottles import Bottle, BottleConstant
from app.models.settings import SystemSetting
from app.models.quality_standards import ControlStandard, GbwStandard
from app.models.audit import AuditLog
from app.models.quality_records import (
    CorrectiveAction,
    ProficiencyTest,
    EnvironmentalLog,
    QCControlChart,
    CustomerComplaint,
    ImprovementRecord,
    NonConformityRecord,
)
from app.models.planning import MonthlyPlan, StaffSettings
from app.models.chat import ChatMessage, UserOnlineStatus
from app.models.license import SystemLicense, LicenseLog
from app.models.reports import ReportSignature, LabReport
from app.models.solutions import SolutionPreparation, SolutionRecipe, SolutionRecipeIngredient
from app.models.equipment import Equipment, MaintenanceLog, UsageLog
from app.models.instrument import InstrumentReading
from app.models.chemicals import Chemical, ChemicalUsage, ChemicalLog, ChemicalWaste, ChemicalWasteRecord

__all__ = [
    # Constants
    'FLOAT_EPSILON',

    # Mixins
    'HashableMixin',

    # User
    'User',

    # Sample
    'Sample',
    'SampleCalculations',

    # Analysis
    'AnalysisResult',
    'AnalysisType',
    'AnalysisProfile',
    'AnalysisResultLog',

    # Equipment
    'Equipment',
    'MaintenanceLog',
    'UsageLog',

    # Instrument Integration
    'InstrumentReading',

    # Spare Parts
    'SparePartCategory',
    'SparePart',
    'SparePartUsage',
    'SparePartLog',

    # Chemicals
    'Chemical',
    'ChemicalUsage',
    'ChemicalLog',
    'ChemicalWaste',
    'ChemicalWasteRecord',

    # Quality
    'Bottle',
    'BottleConstant',
    'ControlStandard',
    'GbwStandard',
    'CorrectiveAction',
    'ProficiencyTest',
    'EnvironmentalLog',
    'QCControlChart',
    'CustomerComplaint',
    'ImprovementRecord',
    'NonConformityRecord',

    # Planning
    'MonthlyPlan',
    'StaffSettings',

    # Chat
    'ChatMessage',
    'UserOnlineStatus',

    # Audit
    'AuditLog',

    # Settings
    'SystemSetting',

    # License
    'SystemLicense',
    'LicenseLog',

    # Reports
    'ReportSignature',
    'LabReport',

    # Solutions
    'SolutionPreparation',
    'SolutionRecipe',
    'SolutionRecipeIngredient',
]
