# app/constants/__init__.py
# -*- coding: utf-8 -*-
"""
Системийн тогтмолууд ба тохиргоонууд.

Шинжилгээний параметрүүд, дээжний төрөл, нэрийн алиасууд,
ээлжийн тохиргоо зэрэг бүх тогтмол утгуудыг энд тодорхойлно.

Backward compatibility: `from app.constants import X` бүгд ажиллана.
"""
import sys

# Windows console utf-8 fix
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError) as e:
        import logging
        logging.warning(f"UTF-8 encoding тохируулга амжилтгүй: {e}")

# Re-export sub-module-уудаас (тодорхой нэрсээр, wildcard биш)
from .nomenclature import (
    ANALYSIS_CODE_SUBSCRIPTS,
)
from .parameters import (
    PARAMETER_DEFINITIONS,
    PARAMETER_MAP,
    CANONICAL_TO_BASE_ANALYSIS,
    ALIAS_TO_BASE_ANALYSIS,
    param_key,
)
from .samples import (
    SAMPLE_TYPE_CHOICES_MAP,
    UNIT_ABBREVIATIONS,
    CHPP_2H_SAMPLES_ORDER,
    ALL_12H_SAMPLES,
    CONSTANT_12H_SAMPLES,
    CHPP_EQUIPMENT_SAMPLES,
    CHPP_CONFIG_GROUPS,
    GI_SHIFT_CONFIG,
    COM_PRIMARY_PRODUCTS,
    COM_SECONDARY_MAP,
    WTL_SAMPLE_NAMES_19,
    WTL_SAMPLE_NAMES_70,
    WTL_SAMPLE_NAMES_6,
    WTL_SAMPLE_NAMES_2,
    WTL_SIZE_NAMES,
    WTL_FL_NAMES,
    get_equipment_samples,
)
from .analysis_types import (
    MASTER_ANALYSIS_TYPES_LIST,
)
from .error_reasons import (
    ERROR_REASON_KEYS,
    ERROR_REASON_LABELS,
)
from .qc_specs import (
    NAME_CLASS_MASTER_SPECS,
    NAME_CLASS_SPEC_BANDS,
    SUMMARY_VIEW_COLUMNS,
)
from .app_config import (
    BOTTLE_TOLERANCE,
    MAX_ANALYSIS_RESULTS,
    MAX_SAMPLE_QUERY_LIMIT,
    MAX_IMPORT_BATCH_SIZE,
    DASHBOARD_RECENT_LIMIT,
    CHEMICAL_LIST_LIMIT,
    MIN_SAMPLE_WEIGHT,
    MAX_SAMPLE_WEIGHT,
    MIN_VALID_YEAR,
    MAX_VALID_YEAR,
    MAX_JSON_PAYLOAD_BYTES,
    DEFAULT_AUDIT_LOG_LIMIT,
    MAX_DESCRIPTION_LENGTH,
    LAB_TYPES,
    HTTP_OK,
    HTTP_MULTI_STATUS,
    HTTP_BAD_REQUEST,
    HTTP_UNAUTHORIZED,
    HTTP_FORBIDDEN,
    HTTP_NOT_FOUND,
    HTTP_SERVER_ERROR,
)

# Enum-уудыг тус тусдаа export (wildcard биш, тодорхой нэрсээр)
from .enums import (              # noqa: F401
    SampleStatus,
    AnalysisResultStatus,
    UserRole,
    UserLanguage,
    LabKey,
    ChemicalStatus,
    EquipmentStatus,
    CorrectiveActionStatus,
    CorrectiveActionSeverity,
)
