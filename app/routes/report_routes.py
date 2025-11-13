# app/routes/report_routes.py
# -*- coding: utf-8 -*-
"""
Monthly Registers (Consumption)
- Нэгж (client_name) ▶ Дээжний төрөл (sample_type) ▶ Сар
- 'Дээжний тоо'  = тухайн сард давхардалгүй sample_id
- Шинжилгээ бүрийн тоо = тухайн сард орсон үр дүнгийн тоо
- Drill-down API: хүснэгтийн нүд дээр дарж жагсаалтыг харуулна

⚙ Схем-д уян хатан зохицуулалт:
  - AnalysisResult.analysis_date байхгүй бол approved_at → updated_at → created_at хэрэглэнэ
  - AnalysisResult.analysis_type_id байхгүй бол AnalysisResult.analysis_code (string) хэрэглэнэ
"""

from datetime import datetime
from collections import defaultdict, OrderedDict

from flask import Blueprint, render_template, request, abort, jsonify, url_for
from flask_login import login_required
from sqlalchemy import extract

from app import db
from app import models as M


# Blueprint
reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


# ----------------------- Helpers -----------------------
def _year_arg() -> int:
    try:
        y = int(request.args.get("year", datetime.now().year))
        if not (2000 <= y <= 2100):
            raise ValueError
        return y
    except Exception:
        abort(400, "year параметр буруу байна")


def _pick_date_col():
    """
    Танай AnalysisResult дээр ямар огнооны багана байгааг
    runtime дээр шалгаад хамгийн тохирохыг буцаана.
    """
    cand = ["analysis_date", "approved_at", "updated_at", "created_at"]
    for c in cand:
        if hasattr(M.AnalysisResult, c):
            return getattr(M.AnalysisResult, c)
    raise RuntimeError(
        "AnalysisResult дээр огнооны талбар олдсонгүй. 'analysis_date/approved_at/updated_at/created_at'-ын аль нэг хэрэгтэй."
    )


def _code_expr_and_join(query):
    """
    Кодыг яаж авах вэ?
    - Хэрэв analysis_type_id байгаа бол AnalysisType-тай join хийгээд .code-г авна
    - Эсвэл AnalysisResult.analysis_code-г шууд авна
    """
    if hasattr(M.AnalysisResult, "analysis_type_id"):
        query = query.join(M.AnalysisType, M.AnalysisType.id == M.AnalysisResult.analysis_type_id)
        code_expr = M.AnalysisType.code
    else:
        # Нэмэлтээр AnalysisType-тай join хэрэггүй (optionally left join хийж alias-н жигдлэл хийх боломжтой)
        code_expr = getattr(M.AnalysisResult, "analysis_code")
    return query, code_expr


# ----------------------- Main Page -----------------------
@login_required
@reports_bp.route("/monthly_registers_strict")
def monthly_registers_strict():
    year = _year_arg()

    # 0) Проп-уудын боломжит кодууд – хэрэв AnalysisType хүснэгт байгаа бол жагсаалтаар нь эхлүүлнэ
    prop_codes = []
    if hasattr(M, "AnalysisType"):
        try:
            at_rows = db.session.query(M.AnalysisType.code).order_by(M.AnalysisType.code.asc()).all()
            prop_codes = [r.code for r in at_rows]
        except Exception:
            prop_codes = []

    # 1) Үр дүнгийн мөрүүдийг унших (хүснэгт хоорондын нэршилд уян хатан)
    date_col = _pick_date_col()

    base = (
        db.session.query(
            M.AnalysisResult.sample_id.label("sid"),
            # code_expr-г доор нэмнэ (join хийсний дараа)
            extract("month", date_col).label("mon"),
            M.Sample.client_name.label("unit"),
            M.Sample.sample_type.label("stype"),
        )
        .join(M.Sample, M.Sample.id == M.AnalysisResult.sample_id)
        .filter(
            date_col.isnot(None),
            extract("year", date_col) == year,
        )
    )
    base, code_expr = _code_expr_and_join(base)

    rows = base.with_entities(
        M.AnalysisResult.sample_id.label("sid"),
        code_expr.label("code"),
        extract("month", date_col).label("mon"),
        M.Sample.client_name.label("unit"),
        M.Sample.sample_type.label("stype"),
    ).all()

    # 2) Нэгж -> төрөл -> хүснэгтийн дата
    def blank_table():
        return {
            "samples": {m: set() for m in range(1, 13)},
            "props": defaultdict(lambda: {m: 0 for m in range(1, 13)}),
        }

    data = defaultdict(lambda: defaultdict(blank_table))

    for r in rows:
        mon = int(r.mon) if r.mon else None
        if not mon:
            continue
        unit = (r.unit or "—").strip()
        stype = (r.stype or "—").strip()
        code = (r.code or "").strip()

        tbl = data[unit][stype]
        tbl["samples"][mon].add(r.sid)
        if code:
            tbl["props"][code][mon] += 1
            if code not in prop_codes:
                prop_codes.append(code)

    # 3) Эрэмбэлэлт
    ordered_units = OrderedDict(sorted(data.items(), key=lambda kv: kv[0].lower()))
    for unit, stypes in list(ordered_units.items()):
        ordered_units[unit] = OrderedDict(sorted(stypes.items(), key=lambda kv: kv[0].lower()))

    # 4) View загвар
    view = []
    for unit, stypes in ordered_units.items():
        sub_views = []
        for stype, tbl in stypes.items():
            sample_cnt = {m: len(tbl["samples"][m]) for m in range(1, 13)}
            sample_total = sum(sample_cnt.values())
            prop_rows = []
            for code in sorted(prop_codes):
                monthly = tbl["props"].get(code, {m: 0 for m in range(1, 13)})
                row_total = sum(monthly[m] for m in range(1, 13))
                if row_total == 0:
                    continue
                prop_rows.append((code, monthly, row_total))
            sub_views.append(
                {
                    "stype": stype,
                    "sample_cnt": sample_cnt,
                    "sample_total": sample_total,
                    "prop_rows": prop_rows,
                }
            )
        view.append((unit, sub_views))

    # 5) Grand total
    grand = {"samples": {m: 0 for m in range(1, 13)}, "props": defaultdict(lambda: {m: 0 for m in range(1, 13)})}
    for _, stypes in ordered_units.items():
        for _, tbl in stypes.items():
            for m in range(1, 13):
                grand["samples"][m] += len(tbl["samples"][m])
            for c, monthly in tbl["props"].items():
                for m in range(1, 13):
                    grand["props"][c][m] += monthly[m]

    grand_rows = []
    for c in sorted(grand["props"].keys()):
        monthly = grand["props"][c]
        total = sum(monthly[m] for m in range(1, 13))
        if total > 0:
            grand_rows.append((c, monthly, total))

    return render_template(
        "reports/monthly_registers_strict.html",
        year=year,
        data=view,
        prop_codes=prop_codes,
        grand_samples=grand["samples"],
        grand_rows=grand_rows,
        title=f"Бүртгэлийн нэгтгэл (Consumption) — {year}",
        report_url=url_for("reports.monthly_registers_strict"),
    )


# ----------------------- Drill-down API -----------------------
@login_required
@reports_bp.route("/monthly_registers_strict_cell")
def monthly_registers_strict_cell():
    try:
        year = int(request.args.get("year"))
        month = int(request.args.get("month"))
        unit = (request.args.get("unit") or "").strip()
        stype = (request.args.get("stype") or "").strip()
        kind = (request.args.get("kind") or "samples").strip()
        code = (request.args.get("code") or "").strip()
        if not (1 <= month <= 12):
            raise ValueError
    except Exception:
        return jsonify({"ok": False, "message": "параметр буруу"}), 400

    date_col = _pick_date_col()

    q = (
        db.session.query(
            M.Sample.id.label("sample_id"),
            M.Sample.sample_code,
            M.Sample.name,
            M.Sample.client_name,
            M.Sample.sample_type,
            date_col.label("dt"),
        )
        .join(M.AnalysisResult, M.AnalysisResult.sample_id == M.Sample.id)
        .filter(
            M.Sample.client_name == unit,
            M.Sample.sample_type == stype,
            date_col.isnot(None),
            extract("year", date_col) == year,
            extract("month", date_col) == month,
        )
    )

    # Кодыг сонгох/шүүх
    if kind == "code":
        if hasattr(M.AnalysisResult, "analysis_type_id"):
            q = q.join(M.AnalysisType, M.AnalysisType.id == M.AnalysisResult.analysis_type_id).filter(
                M.AnalysisType.code == code
            )
            code_expr = M.AnalysisType.code
        else:
            code_expr = getattr(M.AnalysisResult, "analysis_code")
            q = q.filter(code_expr == code)
        q = q.add_columns(code_expr.label("code"))
    else:
        # samples горимд код нэмэхгүй (шигшээд unique болгоно)
        pass

    rows = q.order_by(date_col.desc()).all()

    if kind == "samples":
        # давхардалгүй sample
        seen = set()
        items = []
        for r in rows:
            sid = r.sample_id
            if sid in seen:
                continue
            seen.add(sid)
            items.append(
                {
                    "sample_id": sid,
                    "sample_code": r.sample_code,
                    "name": r.name,
                    "client_name": r.client_name,
                    "sample_type": r.sample_type,
                    "analysis_date": (r.dt.isoformat() if r.dt else ""),
                    "report_url": url_for("analysis.sample_report", sample_id=sid),
                }
            )
    else:
        items = []
        for r in rows:
            code_val = getattr(r, "code", code)
            items.append(
                {
                    "sample_id": r.sample_id,
                    "sample_code": r.sample_code,
                    "name": r.name,
                    "analysis_date": (r.dt.isoformat() if r.dt else ""),
                    "code": code_val,
                    "report_url": url_for("analysis.sample_report", sample_id=r.sample_id),
                }
            )

    return jsonify({"ok": True, "items": items})
