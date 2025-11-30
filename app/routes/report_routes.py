# app/routes/report_routes.py
# -*- coding: utf-8 -*-
"""
Reports:
1) /reports/monthly_registers_strict
   - Нэгж (client_name) ▶ Дээжний төрөл (sample_type) ▶ Сар
   - 'Дээжний тоо' = тухайн сард давхардалгүй sample_id
   - Шинжилгээ бүрийн тоо = тухайн сард орсон үр дүнгийн тоо
   - Drill-down API: хүснэгтийн нүд дээр дарж жагсаалтыг харуулна

2) /reports/shift_kpi
   - Жил / нэгж / шинжилгээний төрөл / shift (DAY, NIGHT)
   - Consumption + KPI (нийт үр дүн, давхардалгүй дээж гэх мэт)
   - Алдааны ангиллын тайлан
"""

from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict

from flask import Blueprint, render_template, request, abort, jsonify, url_for
from flask_login import login_required, current_user
from sqlalchemy import extract, func

from app import db
from app import models as M
from app.utils.datetime import now_local
from app.utils.codes import norm_code

# ✅ ШИНЭ: Төвлөрсөн ээлжийн логикийг импортлох
from app.utils.shifts import get_shift_info

# alias-ууд
Sample = M.Sample
AnalysisResult = M.AnalysisResult
AnalysisResultLog = M.AnalysisResultLog

# Blueprint
reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


# ======================================================================
#  I. Хуучин "Бүртгэлийн нэгтгэл (Consumption) – grid + drill-down"
# ======================================================================

def _year_arg() -> int:
    """?year параметрийг аюулгүй parse хийх."""
    try:
        y = int(request.args.get("year", datetime.now().year))
        if not (2000 <= y <= 2100):
            raise ValueError
        return y
    except Exception:
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


@login_required
@reports_bp.route("/monthly_registers_strict")
def monthly_registers_strict():
    """Хуучин grid + drill-down бүртгэлийн нэгтгэл."""
    year = _year_arg()

    # 0) Боломжит prop_codes – AnalysisType хүснэгт байвал жагсаалтаар нь эхлүүлнэ
    prop_codes = []
    if hasattr(M, "AnalysisType"):
        try:
            at_rows = (
                db.session.query(M.AnalysisType.code)
                .order_by(M.AnalysisType.code.asc())
                .all()
            )
            prop_codes = [r.code for r in at_rows]
        except Exception:
            prop_codes = []

    # 1) Үр дүнгийн мөрүүдийг унших (schema-д уян хатан)
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
    ordered_units = OrderedDict(
        sorted(data.items(), key=lambda kv: kv[0].lower())
    )
    for unit, stypes in list(ordered_units.items()):
        ordered_units[unit] = OrderedDict(
            sorted(stypes.items(), key=lambda kv: kv[0].lower())
        )

    # 4) View загвар – template-д ээлтэй struct
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
        "reports/monthly_registers_strict.html",
        year=year,
        data=view,
        prop_codes=prop_codes,
        grand_samples=grand["samples"],
        grand_rows=grand_rows,
        title=f"Бүртгэлийн нэгтгэл (Consumption) — {year}",
        report_url=url_for("reports.monthly_registers_strict"),
    )


@login_required
@reports_bp.route("/monthly_registers_strict_cell")
def monthly_registers_strict_cell():
    """Grid-ийн нүд дээр дарж гарч ирэх drill-down JSON."""
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
            Sample.id.label("sample_id"),
            Sample.sample_code,
            Sample.name,
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

    # Кодыг сонгох/шүүх (code горимд)
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
                    "report_url": url_for(
                        "analysis.sample_report", sample_id=r.sample_id
                    ),
                }
            )

    return jsonify({"ok": True, "items": items})


# ======================================================================
#  II. ШИНЭ "Shift / KPI нэгтгэл" – тусдаа хуудас (ШИНЭЧЛЭГДСЭН)
# ======================================================================

def _parse_date_safe(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None


def _calculate_consumption(
    year,
    client_filter=None,
    analysis_filter=None,
    shift_filter=None,
    date_from=None,
    date_to=None,
):
    """
    Жилээр нэгдсэн consumption:
      - Клиент (нэгж)
      - Шинжилгээний төрөл
      - 1–12 сар + нийт дүн
    
    ✅ ШИНЭЧЛЭЛ: 'shifts.py' логикийг ашиглан DAY/NIGHT болон DATE-ийг тооцно.
    """
    # 1) Огнооны интервал бодох
    if date_from:
        start_dt = datetime.combine(date_from, datetime.min.time())
    else:
        start_dt = datetime(year, 1, 1)

    if date_to:
        end_dt = datetime.combine(date_to, datetime.min.time()) + timedelta(days=1)
    else:
        end_dt = datetime(year + 1, 1, 1)

    # 2) DB-с approved/pending_review үр дүнг авна
    q = (
        db.session.query(AnalysisResult, Sample)
        .join(Sample, Sample.id == AnalysisResult.sample_id)
        .filter(
            AnalysisResult.status.in_(["approved", "pending_review"]),
            # created_at ашиглах нь зүйтэй (ажил хэзээ хийгдсэн)
            AnalysisResult.created_at >= start_dt,
            AnalysisResult.created_at < end_dt,
        )
    )

    if client_filter:
        q = q.filter(Sample.client_name == client_filter)

    if analysis_filter:
        q = q.filter(AnalysisResult.analysis_code == analysis_filter)

    rows = q.all()

    # 3) Aggregation structures
    per_client = defaultdict(lambda: defaultdict(lambda: [0] * 12))
    grand_total = defaultdict(lambda: [0] * 12)

    total_results = 0
    distinct_samples = set()

    for res, sample in rows:
        if not res.created_at:
            continue

        # ✅ ТӨВЛӨРСӨН ЛОГИК АШИГЛАХ
        shift_info = get_shift_info(res.created_at)
        
        # SHIFT filter (DAY/NIGHT)
        if shift_filter:
            # shift_filter нь "DAY" эсвэл "NIGHT" гэж ирнэ.
            # shift_info.shift_type нь "day" эсвэл "night" байна.
            if shift_filter.lower() != shift_info.shift_type:
                continue

        client_name = sample.client_name or "UNKNOWN"
        code = norm_code(res.analysis_code or "")

        # Тайлан дээр "Сар" гэдгийг operational date буюу ээлж хамаарах өдрөөр нь бүртгэе
        # (Шөнө 02:00 цагт хийсэн бол урд өдрийнхөө сард орно)
        op_date = shift_info.anchor_date
        month_idx = op_date.month - 1  # 0..11

        per_client[client_name][code][month_idx] += 1
        grand_total[code][month_idx] += 1

        total_results += 1
        if sample.id:
            distinct_samples.add(sample.id)

    # 4) Template-д ээлтэй формат руу хөрвүүлэх
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


# Алдааны ангиллын label-ууд (constants.py-аас авах нь зөв ч энд давхар байлгая)
ERROR_REASON_LABELS = {
    "measurement_error":      "1. Хэмжилтийн / тооцооллын алдаа",
    "documentation_error":    "2. Бичилт / бүртгэлийн алдаа",
    "equipment_or_env":       "3. Тоног төхөөрөмж / орчны асуудал",
    "sop_not_followed":       "4. Журам мөрдөөгүй",
    "incomplete_data":        "5. Дутуу өгөгдөл",
    "wrong_sample_or_task":   "6. Буруу дээж / буруу даалгавар",
}


def _count_error_reasons(year: int):
    """
    Тухайн жилд бүртгэгдсэн audit / log доторхи
    алдааны ангиллуудыг тоолно.
    """
    start_dt = datetime(year, 1, 1)
    end_dt = datetime(year + 1, 1, 1)

    q = (
        db.session.query(
            AnalysisResultLog.error_reason,
            func.count(AnalysisResultLog.id),
        )
        .filter(
            AnalysisResultLog.error_reason.isnot(None),
            # ✅ ЗАСВАР: AnalysisResultLog.timestamp ашиглана
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
        items.append(
            {
                "code": code,
                "label": label,
                "count": cnt,
            }
        )
        total += cnt

    # бүх кодуудыг хүсвэл 0 утгатайгаар ч харуулж болно
    for code, label in ERROR_REASON_LABELS.items():
        if not any(it["code"] == code for it in items):
            items.append(
                {
                    "code": code,
                    "label": label,
                    "count": 0,
                }
            )

    # тухайн кодоор нь эрэмбэлж байя
    items.sort(key=lambda x: x["code"])

    return items, total


@reports_bp.route("/shift_kpi", methods=["GET"])
@login_required
def shift_kpi():
    """
    ШИНЭ ХУУДАС: /reports/shift_kpi
    Жил, нэгж, шинжилгээний төрөл, shift (DAY/NIGHT)-ээр consumption + KPI +
    алдааны ангиллын статистик.
    """
    now = now_local()
    current_year = now.year

    years = list(range(current_year - 3, current_year + 1))

    year = request.args.get("year", type=int) or current_year
    if year < current_year - 20 or year > current_year + 1:
        year = current_year

    # Огнооны шүүлтүүр
    date_from = _parse_date_safe(request.args.get("date_from"))
    date_to = _parse_date_safe(request.args.get("date_to"))

    unit = request.args.get("unit") or ""          # Sample.client_name filter
    analysis_code = request.args.get("analysis_code") or ""
    shift = request.args.get("shift") or ""        # 'DAY', 'NIGHT'

    # Consumption + KPI (get_shift_info логикоор)
    client_blocks, grand_rows, kpi_stats = _calculate_consumption(
        year=year,
        client_filter=unit or None,
        analysis_filter=analysis_code or None,
        shift_filter=shift or None,
        date_from=date_from,
        date_to=date_to,
    )

    # Алдааны ангиллын статистик
    error_reason_items, error_reason_total = _count_error_reasons(year)

    # Нэгжийн сонголтууд
    unit_choices = (
        db.session.query(Sample.client_name)
        .distinct()
        .order_by(Sample.client_name)
        .all()
    )
    unit_choices = [u[0] for u in unit_choices if u[0]]

    # Шинжилгээний кодын сонголт
    analysis_choices = (
        db.session.query(AnalysisResult.analysis_code)
        .distinct()
        .order_by(AnalysisResult.analysis_code)
        .all()
    )
    analysis_choices = [a[0] for a in analysis_choices if a[0]]

    return render_template(
        "reports/shift_kpi.html",
        title="Чанар & Ачааллын KPI (Yearly)",
        years=years,
        year=year,
        unit_choices=unit_choices,
        analysis_choices=analysis_choices,
        selected_unit=unit,
        selected_analysis=analysis_code,
        selected_shift=shift,
        date_from=date_from,
        date_to=date_to,
        client_blocks=client_blocks,
        grand_rows=grand_rows,
        kpi_stats=kpi_stats,
        error_reason_items=error_reason_items,
        error_reason_total=error_reason_total,
    )