# app/routes/reports/consumption.py
# -*- coding: utf-8 -*-
"""
Consumption report — grid + drill-down + shift/KPI нэгтгэл.
"""

from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict

from flask import request, jsonify, url_for, render_template
from flask_login import login_required
from sqlalchemy import extract, func
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app import models as M
from app.constants import AnalysisResultStatus
from app.utils.codes import norm_code
from app.utils.shifts import get_shift_info
from app.routes.reports.routes import reports_bp, _year_arg, _pick_date_col, _code_expr_and_join

Sample = M.Sample
AnalysisResult = M.AnalysisResult
AnalysisResultLog = M.AnalysisResultLog


@login_required
@reports_bp.route("/consumption")
def consumption():
    """Consumption – grid + drill-down."""
    year = _year_arg()

    prop_codes = []
    if hasattr(M, "AnalysisType"):
        try:
            at_rows = (
                db.session.query(M.AnalysisType.code)
                .order_by(M.AnalysisType.code.asc())
                .all()
            )
            prop_codes = [r.code for r in at_rows]
        except SQLAlchemyError:
            prop_codes = []

    date_col = _pick_date_col()

    base = (
        db.session.query(
            AnalysisResult.sample_id.label("sid"),
            extract("month", date_col).label("mon"),
            Sample.client_name.label("unit"),
            Sample.sample_type.label("stype"),
        )
        .join(Sample, Sample.id == AnalysisResult.sample_id)
        .filter(
            Sample.lab_type == 'coal',
            date_col.isnot(None),
            extract("year", date_col) == year,
        )
    )
    base, code_expr = _code_expr_and_join(base)

    rows = base.with_entities(
        AnalysisResult.sample_id.label("sid"),
        code_expr.label("code"),
        extract("month", date_col).label("mon"),
        Sample.client_name.label("unit"),
        Sample.sample_type.label("stype"),
    ).all()

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

    ordered_units = OrderedDict(
        sorted(data.items(), key=lambda kv: kv[0].lower())
    )
    for unit, stypes in list(ordered_units.items()):
        ordered_units[unit] = OrderedDict(
            sorted(stypes.items(), key=lambda kv: kv[0].lower())
        )

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

    grand = {
        "samples": {m: 0 for m in range(1, 13)},
        "props": defaultdict(lambda: {m: 0 for m in range(1, 13)}),
    }
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
        "reports/consumption.html",
        year=year,
        data=view,
        prop_codes=prop_codes,
        grand_samples=grand["samples"],
        grand_rows=grand_rows,
        title=f"Consumption — {year}",
        report_url=url_for("reports.consumption"),
    )


@login_required
@reports_bp.route("/consumption_cell")
def consumption_cell():
    """Consumption grid-ийн нүд дээр дарж гарч ирэх drill-down JSON."""
    try:
        year = int(request.args.get("year"))
        month = int(request.args.get("month"))
        unit = (request.args.get("unit") or "").strip()
        stype = (request.args.get("stype") or "").strip()
        kind = (request.args.get("kind") or "samples").strip()
        code = (request.args.get("code") or "").strip()
        if not (1 <= month <= 12):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Буруу параметр"}), 400

    date_col = _pick_date_col()

    q = (
        db.session.query(
            Sample.id.label("sample_id"),
            Sample.sample_code,
            Sample.client_name,
            Sample.sample_type,
            date_col.label("dt"),
        )
        .join(AnalysisResult, AnalysisResult.sample_id == Sample.id)
        .filter(
            Sample.client_name == unit,
            Sample.sample_type == stype,
            date_col.isnot(None),
            extract("year", date_col) == year,
            extract("month", date_col) == month,
        )
    )

    if kind == "code":
        if hasattr(AnalysisResult, "analysis_type_id"):
            q = q.join(
                M.AnalysisType,
                M.AnalysisType.id == AnalysisResult.analysis_type_id,
            ).filter(M.AnalysisType.code == code)
            code_expr = M.AnalysisType.code
        else:
            code_expr = getattr(AnalysisResult, "analysis_code")
            q = q.filter(code_expr == code)
        q = q.add_columns(code_expr.label("code"))

    rows = q.order_by(date_col.desc()).all()

    if kind == "samples":
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
                    "report_url": url_for(
                        "analysis.sample_report", sample_id=r.sample_id
                    ),
                }
            )

    return jsonify({"success": True, "data": {"items": items}})


# ======================================================================
#  Shift / KPI нэгтгэл helpers
# ======================================================================

def _parse_date_safe(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _calculate_consumption(
    year,
    client_filter=None,
    analysis_filter=None,
    shift_filter=None,
    date_from=None,
    date_to=None,
):
    """Жилээр нэгдсэн consumption тооцох."""
    if date_from:
        start_dt = datetime.combine(date_from, datetime.min.time())
    else:
        start_dt = datetime(year, 1, 1)

    if date_to:
        end_dt = datetime.combine(date_to, datetime.min.time()) + timedelta(days=1)
    else:
        end_dt = datetime(year + 1, 1, 1)

    q = (
        db.session.query(AnalysisResult, Sample)
        .join(Sample, Sample.id == AnalysisResult.sample_id)
        .filter(
            Sample.lab_type == 'coal',
            AnalysisResult.status.in_([AnalysisResultStatus.APPROVED.value, AnalysisResultStatus.PENDING_REVIEW.value]),
            AnalysisResult.created_at >= start_dt,
            AnalysisResult.created_at < end_dt,
        )
    )

    if client_filter:
        q = q.filter(Sample.client_name == client_filter)

    if analysis_filter:
        q = q.filter(AnalysisResult.analysis_code == analysis_filter)

    rows = q.all()

    per_client = defaultdict(lambda: defaultdict(lambda: [0] * 12))
    grand_total = defaultdict(lambda: [0] * 12)

    total_results = 0
    distinct_samples = set()

    for res, sample in rows:
        if not res.created_at:
            continue

        shift_info = get_shift_info(res.created_at)

        if shift_filter:
            if shift_filter.lower() != shift_info.shift_type:
                continue

        client_name = sample.client_name or "UNKNOWN"
        code = norm_code(res.analysis_code or "")

        op_date = shift_info.anchor_date
        month_idx = op_date.month - 1

        per_client[client_name][code][month_idx] += 1
        grand_total[code][month_idx] += 1

        total_results += 1
        if sample.id:
            distinct_samples.add(sample.id)

    client_blocks = []
    for client_name in sorted(per_client.keys()):
        rows_for_client = []
        for code in sorted(per_client[client_name].keys()):
            months = per_client[client_name][code]
            rows_for_client.append(
                {
                    "code": code,
                    "months": months,
                    "total": sum(months),
                }
            )
        client_blocks.append(
            {
                "client_name": client_name,
                "rows": rows_for_client,
            }
        )

    grand_rows = []
    for code in sorted(grand_total.keys()):
        months = grand_total[code]
        grand_rows.append(
            {
                "code": code,
                "months": months,
                "total": sum(months),
            }
        )

    kpi_stats = {
        "total_results": total_results,
        "distinct_samples": len(distinct_samples),
    }

    return client_blocks, grand_rows, kpi_stats


ERROR_REASON_LABELS = {
    "measurement_error":      "1. Хэмжилтийн / тооцооллын алдаа",
    "documentation_error":    "2. Бичилт / бүртгэлийн алдаа",
    "equipment_or_env":       "3. Тоног төхөөрөмж / орчны асуудал",
    "sop_not_followed":       "4. Журам мөрдөөгүй",
    "incomplete_data":        "5. Дутуу өгөгдөл",
    "wrong_sample_or_task":   "6. Буруу дээж / буруу даалгавар",
}


def _count_error_reasons(year: int):
    """Тухайн жилд бүртгэгдсэн алдааны ангиллуудыг тоолно."""
    start_dt = datetime(year, 1, 1)
    end_dt = datetime(year + 1, 1, 1)

    q = (
        db.session.query(
            AnalysisResultLog.error_reason,
            func.count(AnalysisResultLog.id),
        )
        .filter(
            AnalysisResultLog.error_reason.isnot(None),
            AnalysisResultLog.timestamp >= start_dt,
            AnalysisResultLog.timestamp < end_dt,
        )
        .group_by(AnalysisResultLog.error_reason)
    )

    raw_rows = q.all()

    items = []
    total = 0
    for code, cnt in raw_rows:
        label = ERROR_REASON_LABELS.get(code, code or "Тодорхойгүй")
        items.append({"code": code, "label": label, "count": cnt})
        total += cnt

    for code, label in ERROR_REASON_LABELS.items():
        if not any(it["code"] == code for it in items):
            items.append({"code": code, "label": label, "count": 0})

    items.sort(key=lambda x: x["code"])
    return items, total
