# app/utils/server_calculations/dispatcher.py
# -*- coding: utf-8 -*-
"""
Calculation dispatcher: maps analysis codes to calculation functions,
provides verify_and_recalculate() and bulk_verify_results().
"""

from typing import Tuple, Optional, Dict, Any, List

from ._helpers import security_logger, CALC_MISMATCH_ABS_THRESHOLD
from .proximate import calc_moisture_mad, calc_ash_aad, calc_volatile_vad, calc_total_moisture_mt
from .ultimate import calc_sulfur_ts, calc_phosphorus_p, calc_fluorine_f, calc_chlorine_cl
from .calorific import calc_calorific_value_cv
from .physical import calc_csn, calc_gray_king_gi, calc_free_moisture_fm, calc_solid, calc_trd
from .mg_calcs import calc_mg_tube, calc_mg_size


# Map analysis codes to calculation functions
CALCULATION_FUNCTIONS = {
    # ---- Moisture & Ash ----
    "Mad": calc_moisture_mad,
    "M": calc_moisture_mad,

    "Aad": calc_ash_aad,
    "A": calc_ash_aad,

    "Vad": calc_volatile_vad,
    "V": calc_volatile_vad,

    "MT": calc_total_moisture_mt,

    # ---- Sulfur, Phosphorus ----
    "TS": calc_sulfur_ts,
    "St,ad": calc_sulfur_ts,
    "S": calc_sulfur_ts,

    "CSN": calc_csn,

    "P": calc_phosphorus_p,
    "P,ad": calc_phosphorus_p,

    # ---- Fluorine, Chlorine ----
    "F": calc_fluorine_f,
    "F,ad": calc_fluorine_f,

    "Cl": calc_chlorine_cl,
    "Cl,ad": calc_chlorine_cl,

    # ---- Calorific Value ----
    "CV": calc_calorific_value_cv,
    "Qgr,ad": calc_calorific_value_cv,
    "Qgr": calc_calorific_value_cv,

    # ---- Gray-King Index ----
    "Gi": calc_gray_king_gi,
    "GI": calc_gray_king_gi,

    # ---- Free Moisture ----
    "FM": calc_free_moisture_fm,

    # ---- Solid Content ----
    "Solid": calc_solid,

    # ---- True Relative Density ----
    "TRD": calc_trd,
    "TRD,d": calc_trd,

    # ---- WTL MG Analyses ----
    "MG": calc_mg_tube,
    "MG_SIZE": calc_mg_size,
}


def verify_and_recalculate(
    analysis_code: str,
    client_final_result: Optional[float],
    raw_data: Dict[str, Any],
    user_id: Optional[int] = None,
    sample_id: Optional[int] = None
) -> Tuple[Optional[float], List[str]]:
    """
    Verify client-submitted result by recalculating on server.

    Args:
        analysis_code: Analysis code (e.g., "Mad", "Aad")
        client_final_result: Final result submitted by client
        raw_data: Raw measurement data
        user_id: User ID (for logging)
        sample_id: Sample ID (for logging)

    Returns:
        (final_result, warnings)
        - final_result: Server-calculated result (or client if no calculation available)
        - warnings: List of warning messages
    """
    warnings = []

    # Normalize code
    from app.utils.codes import norm_code
    analysis_code = norm_code(analysis_code)

    # Get calculation function
    calc_func = CALCULATION_FUNCTIONS.get(analysis_code)

    if calc_func is None:
        # No server-side calculation available for this analysis
        # Use client value but log it
        if client_final_result is not None:
            security_logger.info(
                f"No server calculation for {analysis_code} - using client value: "
                f"{client_final_result} (user={user_id}, sample={sample_id})"
            )
        return client_final_result, warnings

    # Calculate on server
    try:
        server_result = calc_func(raw_data)
    except (ValueError, TypeError, KeyError, ZeroDivisionError, ArithmeticError) as e:
        error_msg = f"Server calculation error for {analysis_code}: {str(e)}"
        security_logger.error(
            f"{error_msg} (user={user_id}, sample={sample_id})",
            exc_info=True
        )
        warnings.append(error_msg)
        # Fallback to client value
        return client_final_result, warnings

    # Compare server vs client
    if server_result is not None and client_final_result is not None:
        diff = abs(server_result - client_final_result)
        percent_diff = (diff / max(abs(server_result), 0.0001)) * 100

        if diff > CALC_MISMATCH_ABS_THRESHOLD and percent_diff > 1.0:  # More than 1% difference
            warning_msg = (
                f"⚠️ CALCULATION MISMATCH: {analysis_code} - "
                f"Client={client_final_result:.4f}, Server={server_result:.4f}, "
                f"Diff={diff:.4f} ({percent_diff:.2f}%)"
            )
            warnings.append(warning_msg)

            # Security log
            security_logger.warning(
                f"POTENTIAL TAMPERING: {analysis_code} calculation mismatch - "
                f"client={client_final_result:.4f}, server={server_result:.4f}, "
                f"diff={diff:.4f} ({percent_diff:.2f}%) "
                f"(user={user_id}, sample={sample_id}, raw_data={raw_data})"
            )

    # Use server-calculated result if available
    if server_result is not None:
        return server_result, warnings

    # Fallback to client value
    return client_final_result, warnings


def bulk_verify_results(
    items: List[Dict[str, Any]],
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Verify multiple results in bulk.

    Args:
        items: List of items with analysis_code, final_result, raw_data
        user_id: User ID for logging

    Returns:
        {
            "verified_items": [...],  # Items with server-calculated results
            "total_warnings": int,
            "total_mismatches": int,
        }
    """
    verified_items = []
    total_warnings = 0
    total_mismatches = 0

    for item in items:
        analysis_code = item.get("analysis_code")
        client_result = item.get("final_result")
        raw_data = item.get("raw_data") or {}
        sample_id = item.get("sample_id")

        server_result, warnings = verify_and_recalculate(
            analysis_code=analysis_code,
            client_final_result=client_result,
            raw_data=raw_data,
            user_id=user_id,
            sample_id=sample_id
        )

        # Create verified item
        verified_item = dict(item)
        verified_item["final_result"] = server_result
        verified_item["server_verified"] = True
        verified_item["verification_warnings"] = warnings

        if warnings:
            total_warnings += len(warnings)
            if any("MISMATCH" in w for w in warnings):
                total_mismatches += 1

        verified_items.append(verified_item)

    return {
        "verified_items": verified_items,
        "total_warnings": total_warnings,
        "total_mismatches": total_mismatches,
    }
