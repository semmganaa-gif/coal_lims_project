# app/utils/server_calculations/__init__.py
# -*- coding: utf-8 -*-
"""
Server-Side Calculation & Verification Package

Re-exports all public names for backward compatibility.
All existing `from app.utils.server_calculations import X` statements continue to work.
"""

from ._helpers import (                                      # noqa: F401
    CALC_MISMATCH_ABS_THRESHOLD,
    J_PER_CAL, MJ_PER_KCAL,
    cv_cal_to_mj, cv_mj_to_cal,
    _safe_float, _get_from_dict,
    security_logger,
)
from .proximate import (                                     # noqa: F401
    calc_moisture_mad, calc_ash_aad,
    calc_volatile_vad, calc_total_moisture_mt,
)
from .ultimate import (                                      # noqa: F401
    calc_sulfur_ts, calc_phosphorus_p,
    calc_fluorine_f, calc_chlorine_cl,
)
from .calorific import calc_calorific_value_cv                # noqa: F401
from .physical import (                                      # noqa: F401
    calc_csn, calc_gray_king_gi,
    calc_free_moisture_fm, calc_solid, calc_trd,
)
from .mg_calcs import (                                      # noqa: F401
    calc_mg_mt, calc_mg_trd,
    calc_mg_tube, calc_mg_size,
)
from .dispatcher import (                                    # noqa: F401
    CALCULATION_FUNCTIONS,
    verify_and_recalculate, bulk_verify_results,
)
