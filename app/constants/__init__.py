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

# Re-export бүх sub-module-уудаас
from .nomenclature import *      # noqa: F401,F403
from .parameters import *        # noqa: F401,F403
from .samples import *           # noqa: F401,F403
from .analysis_types import *    # noqa: F401,F403
from .error_reasons import *     # noqa: F401,F403
from .qc_specs import *          # noqa: F401,F403
from .app_config import *        # noqa: F401,F403

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
