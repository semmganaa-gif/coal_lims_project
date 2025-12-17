# app/routes/analysis/helpers.py
# -*- coding: utf-8 -*-
"""
Analysis модулиудын хамтын хэрэгсэл, тогтмол, декоратор.
"""

from flask import request, redirect, url_for, abort
from flask_login import current_user
from functools import wraps

# =====================================================================
# QC DASHBOARD – тогтмолууд
# =====================================================================

# QC дээр харуулах үндсэн параметрүүд
QC_PARAM_CODES = ["Mad", "Aad", "Vdaf", "Qnet,ar", "CSN", "Gi"]

# Composite vs Hourly Avg-ийн хооронд зөвшөөрөгдөх зөрүү
QC_TOLERANCE = {
    "Mad": 0.30,
    "Aad": 0.50,
    "Vdaf": 0.50,
    "Qnet,ar": 150.0,
    "CSN": 0.30,
    "Gi": 3.0,
}

# Name/Class QC – default specification (fallback)
QC_SPEC_DEFAULT = {
    "Vdaf": (20.0, 30.0),
    "Aad": (8.0, 12.0),
    "CSN": (7.0, None),
    "Gi": (80.0, None),
}

# =====================================================================
# COMPOSITE QC тохиргоо
# =====================================================================
COMPOSITE_QC_CODES = ["Mt,ar", "Mad", "Aad", "Vad", "Vdaf", "Qgr,ar", "Qnet,ar", "CSN", "Gi", "TRD,ad"]

COMPOSITE_QC_LIMITS = {
    "Mt,ar": {"mode": "abs", "warn": 0.3, "fail": 0.6},
    "Mad": {"mode": "abs", "warn": 0.3, "fail": 0.5},
    "Aad": {"mode": "abs", "warn": 0.5, "fail": 1.0},
    "Vad": {"mode": "rel", "warn": 2.5, "fail": 5.0},
    "Vdaf": {"mode": "rel", "warn": 2.0, "fail": 4.0},
    "Qgr,ar": {"mode": "abs", "warn": 100, "fail": 200},
    "Qnet,ar": {"mode": "abs", "warn": 100, "fail": 200},
    "TRD,ad": {"mode": "rel", "warn": 1.0, "fail": 2.0},
    "CSN": {"mode": "abs", "warn": 0.5, "fail": 1.0},
    "Gi": {"mode": "rel", "warn": 5.0, "fail": 10.0},
}

# =====================================================================
# TIMER PRESETS
# =====================================================================
TIMER_PRESETS = {
    "Aad": {"layout": "right", "digit_size": "xl", "editable": True, "timers": [{"label": "Зуух #1", "seconds": 3600, "note": "815°C · 60′"}, {"label": "Зуух #2", "seconds": 3600, "note": "815°C · 60′"}, {"label": "Зуух #3", "seconds": 3600, "note": "815°C · 60′"}, {"label": "Десикатор", "seconds": 900, "note": "15′"}]},
    "Vad": {"layout": "right", "digit_size": "xl", "editable": True, "timers": [{"label": "Зуух", "seconds": 25200, "note": "7:00:00"}, {"label": "Десикатор", "seconds": 900, "note": "00:15:00"}]},
    "Mad": {"layout": "right", "digit_size": "lg", "editable": True, "timers": [{"label": "Шат", "seconds": 3600, "note": "60′"}, {"label": "Десикатор", "seconds": 900, "note": "15′"}]},
    "MT": {"layout": "right", "digit_size": "lg", "editable": True, "timers": [{"label": "Шат", "seconds": 3600, "note": "60′"}, {"label": "Десикатор", "seconds": 900, "note": "15′"}]},
    "Gi": {"layout": "right", "digit_size": "xl", "editable": True, "timers": [{"label": "Шат 1", "seconds": 54000, "note": "15:00:00"}, {"label": "Шат 2", "seconds": 1800, "note": "00:30:00"}]},
    "TRD": {"layout": "right", "digit_size": "lg", "editable": True, "timers": [{"label": "Шат", "seconds": 3600, "note": "60′"}, {"label": "Десикатор", "seconds": 900, "note": "15′"}]},
    "P": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "F": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "Cl": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "CSN": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "FM": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "SOLID": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
}


# =====================================================================
# QC HELPER FUNCTIONS - app/utils/qc.py-г ашиглана
# =====================================================================
# DEPRECATED: Эдгээр функцүүд app/utils/qc.py руу шилжсэн.
# Шууд import хийж ашиглана уу:
#   from app.utils.qc import (
#       qc_to_date, qc_split_family, qc_is_composite,
#       qc_check_spec, parse_numeric, eval_qc_status, split_stream_key
#   )
# =====================================================================


# =====================================================================
# ROLE DECORATOR - app/utils/decorators.py-г ашиглана
# =====================================================================
# DEPRECATED: analysis_role_required() функц app/utils/decorators.py руу шилжсэн.
# Шууд import хийж ашиглана уу:
#   from app.utils.decorators import analysis_role_required
# =====================================================================

def analysis_role_required(allowed_roles=None):
    """Шинжилгээний модульд хандах эрх шалгах декоратор"""
    if allowed_roles is None:
        allowed_roles = ["chemist", "senior", "manager", "admin", "prep"]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("main.login", next=request.url))
            if current_user.role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# =====================================================================
# SULFUR MAP - app/utils/qc.py-г ашиглана
# =====================================================================
# DEPRECATED: _sulfur_map_for() функц app/utils/qc.py руу шилжсэн.
# Шууд import хийж ашиглана уу:
#   from app.utils.qc import sulfur_map_for
# =====================================================================
