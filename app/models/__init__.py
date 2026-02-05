# app/models/__init__.py
# -*- coding: utf-8 -*-
"""
Coal LIMS Models Package.

Re-exports all models from models.py for backward compatibility.
Ирээдүйд энэ файлуудыг тусдаа модуль болгон задалж болно.

Usage:
    from app.models import User, Sample, AnalysisResult
"""

# Re-export everything from models.py
from app.models.models import (
    # Constants
    FLOAT_EPSILON,

    # Mixins
    HashableMixin,

    # User
    User,

    # Sample
    Sample,
    SampleCalculations,

    # Analysis
    AnalysisResult,
    AnalysisType,
    AnalysisProfile,
    AnalysisResultLog,

    # Equipment
    Equipment,
    MaintenanceLog,
    UsageLog,

    # Spare Parts
    SparePartCategory,
    SparePart,
    SparePartUsage,
    SparePartLog,

    # Chemicals
    Chemical,
    ChemicalUsage,
    ChemicalLog,
    ChemicalWaste,
    ChemicalWasteRecord,

    # Quality (ISO 17025)
    Bottle,
    BottleConstant,
    ControlStandard,
    GbwStandard,
    CorrectiveAction,
    ProficiencyTest,
    EnvironmentalLog,
    QCControlChart,
    CustomerComplaint,

    # Planning
    MonthlyPlan,
    StaffSettings,

    # Chat
    ChatMessage,
    UserOnlineStatus,

    # Audit
    AuditLog,

    # Settings
    SystemSetting,

    # License
    SystemLicense,
    LicenseLog,

    # Washability (Theoretical Yield)
    WashabilityTest,
    WashabilityFraction,
    TheoreticalYield,
    PlantYield,

    # Reports
    ReportSignature,
    LabReport,

    # Solutions
    SolutionPreparation,
    SolutionRecipe,
    SolutionRecipeIngredient,
)

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

    # Washability
    'WashabilityTest',
    'WashabilityFraction',
    'TheoreticalYield',
    'PlantYield',

    # Reports
    'ReportSignature',
    'LabReport',

    # Solutions
    'SolutionPreparation',
    'SolutionRecipe',
    'SolutionRecipeIngredient',
]
