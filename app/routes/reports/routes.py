# app/routes/reports/routes.py
# -*- coding: utf-8 -*-
"""
Reports blueprint + shared helpers.

Route-ууд тусдаа модулиудад:
  - dashboard.py:     /reports/dashboard
  - consumption.py:   /reports/consumption, /reports/consumption_cell
  - monthly_plan.py:  /reports/monthly_plan, APIs, /reports/chemist_report
"""

from flask import Blueprint, request, abort

from app import models as M
from app.utils.datetime import now_local
from app.constants import MIN_VALID_YEAR, MAX_VALID_YEAR

# alias-ууд (consumption.py-д хэрэглэгдэнэ)
AnalysisResult = M.AnalysisResult


def _format_short_name(full_name: str) -> str:
    """
    "Нэр Овог" → "Нэр.О" болгох
    Жишээ: "GANTULGA Ulziibuyan" → "Gantulga.U"
    DB-д: "Нэр Овог" форматаар хадгалагдсан
    """
    if not full_name:
        return ""
    parts = full_name.strip().split()
    if len(parts) >= 2:
        first_name = parts[0].capitalize()
        last_name = parts[1]
        return f"{first_name}.{last_name[0].upper()}"
    return full_name


# Blueprint
reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _year_arg() -> int:
    """?year параметрийг аюулгүй parse хийх."""
    try:
        y = int(request.args.get("year", now_local().year))
        if not (MIN_VALID_YEAR <= y <= MAX_VALID_YEAR):
            raise ValueError
        return y
    except (ValueError, TypeError):
        abort(400, "year параметр буруу байна")


def _pick_date_col():
    """
    AnalysisResult дээрх огнооны талбарыг runtime-д сонгоно.
    Давуу эрэмбэ: analysis_date → approved_at → updated_at → created_at
    """
    cand = ["analysis_date", "approved_at", "updated_at", "created_at"]
    for c in cand:
        if hasattr(AnalysisResult, c):
            return getattr(AnalysisResult, c)
    raise RuntimeError(
        "AnalysisResult дээр огнооны талбар олдсонгүй. "
        "'analysis_date/approved_at/updated_at/created_at'-ын аль нэг хэрэгтэй."
    )


def _code_expr_and_join(query):
    """
    Кодыг яаж авах вэ?
      - Хэрэв analysis_type_id байгаа бол AnalysisType-тай join хийгээд .code-г авна
      - Эсвэл AnalysisResult.analysis_code-г шууд авна
    """
    if hasattr(AnalysisResult, "analysis_type_id"):
        query = query.join(
            M.AnalysisType,
            M.AnalysisType.id == AnalysisResult.analysis_type_id,
        )
        code_expr = M.AnalysisType.code
    else:
        code_expr = getattr(AnalysisResult, "analysis_code")
    return query, code_expr


# Route модулиудыг бүртгэх (import-ийг доод талд байрлуулах - circular import-аас сэргийлэх)
from app.routes.reports import dashboard      # noqa: E402, F401
from app.routes.reports import consumption    # noqa: E402, F401
from app.routes.reports import monthly_plan   # noqa: E402, F401
