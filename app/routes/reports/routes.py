# app/routes/report_routes.py
# -*- coding: utf-8 -*-
"""
Reports:
1) /reports/consumption
   - Нэгж (client_name) ▶ Дээжний төрөл (sample_type) ▶ Сар
   - 'Дээжний тоо' = тухайн сард давхардалгүй sample_id
   - Шинжилгээ бүрийн тоо = тухайн сард орсон үр дүнгийн тоо
   - Drill-down API: хүснэгтийн нүд дээр дарж жагсаалтыг харуулна

2) /reports/monthly_plan
   - Сарын төлөвлөгөө ба гүйцэтгэл
   - Долоо хоног бүрийн хэмжээ
   - Статистик графикууд
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
from app.constants import MIN_VALID_YEAR, MAX_VALID_YEAR

# ✅ ШИНЭ: Төвлөрсөн ээлжийн логикийг импортлох
from app.utils.shifts import get_shift_info

# alias-ууд
Sample = M.Sample
AnalysisResult = M.AnalysisResult
AnalysisResultLog = M.AnalysisResultLog


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


# ======================================================================
#  0. DASHBOARD - Нэгдсэн тайлан
# ======================================================================

@reports_bp.route("/dashboard")
@login_required
def dashboard():
    """
    Dashboard - Бүх тайлангийн товч мэдээлэл нэг дэлгэцэнд
    """
    from app.models import Sample, AnalysisResult, AnalysisResultLog, User

    now = now_local()
    year = now.year
    month = now.month

    # Энэ сарын эхлэл/төгсгөл
    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1)
    else:
        month_end = datetime(year, month + 1, 1)

    # Энэ жилийн эхлэл/төгсгөл
    year_start = datetime(year, 1, 1)
    year_end = datetime(year + 1, 1, 1)

    # ========== KPI-ууд ==========

    # 1. Дээжний тоо (энэ сар / энэ жил) — зөвхөн нүүрс
    samples_month = Sample.query.filter(
        Sample.lab_type == 'coal',
        Sample.received_date >= month_start.date(),
        Sample.received_date < month_end.date()
    ).count()

    samples_year = Sample.query.filter(
        Sample.lab_type == 'coal',
        Sample.received_date >= year_start.date(),
        Sample.received_date < year_end.date()
    ).count()

    # 2. Шинжилгээний тоо (энэ сар / энэ жил)
    work_actions = [
        'CREATED_AUTO_APPROVED', 'CREATED_PENDING', 'CREATED_REJECTED', 'CREATED_VOID_RETEST',
        'UPDATED_AUTO_APPROVED', 'UPDATED_PENDING', 'UPDATED_REJECTED', 'UPDATED_VOID_RETEST',
    ]

    analyses_month = db.session.query(func.count(AnalysisResultLog.id)).join(
        Sample, Sample.id == AnalysisResultLog.sample_id
    ).filter(
        Sample.lab_type == 'coal',
        AnalysisResultLog.action.in_(work_actions),
        AnalysisResultLog.timestamp >= month_start,
        AnalysisResultLog.timestamp < month_end
    ).scalar() or 0

    analyses_year = db.session.query(func.count(AnalysisResultLog.id)).join(
        Sample, Sample.id == AnalysisResultLog.sample_id
    ).filter(
        Sample.lab_type == 'coal',
        AnalysisResultLog.action.in_(work_actions),
        AnalysisResultLog.timestamp >= year_start,
        AnalysisResultLog.timestamp < year_end
    ).scalar() or 0

    # 3. Алдааны тоо (энэ сар / энэ жил) — зөвхөн нүүрс
    errors_month = db.session.query(func.count(AnalysisResultLog.id)).join(
        Sample, Sample.id == AnalysisResultLog.sample_id
    ).filter(
        Sample.lab_type == 'coal',
        AnalysisResultLog.action == 'REJECTED',
        AnalysisResultLog.timestamp >= month_start,
        AnalysisResultLog.timestamp < month_end
    ).scalar() or 0

    errors_year = db.session.query(func.count(AnalysisResultLog.id)).join(
        Sample, Sample.id == AnalysisResultLog.sample_id
    ).filter(
        Sample.lab_type == 'coal',
        AnalysisResultLog.action == 'REJECTED',
        AnalysisResultLog.timestamp >= year_start,
        AnalysisResultLog.timestamp < year_end
    ).scalar() or 0

    # 4. Идэвхтэй ажилтнууд (энэ сар) — зөвхөн нүүрс
    active_users_month = db.session.query(
        func.count(func.distinct(AnalysisResultLog.user_id))
    ).join(
        Sample, Sample.id == AnalysisResultLog.sample_id
    ).filter(
        Sample.lab_type == 'coal',
        AnalysisResultLog.action.in_(work_actions),
        AnalysisResultLog.timestamp >= month_start,
        AnalysisResultLog.timestamp < month_end
    ).scalar() or 0

    # 5. Сарын тоо (сүүлийн 6 сар)
    monthly_stats = []
    for i in range(5, -1, -1):
        m = month - i
        y = year
        if m <= 0:
            m += 12
            y -= 1
        m_start = datetime(y, m, 1)
        if m == 12:
            m_end = datetime(y + 1, 1, 1)
        else:
            m_end = datetime(y, m + 1, 1)

        cnt = db.session.query(func.count(AnalysisResultLog.id)).join(
            Sample, Sample.id == AnalysisResultLog.sample_id
        ).filter(
            Sample.lab_type == 'coal',
            AnalysisResultLog.action.in_(work_actions),
            AnalysisResultLog.timestamp >= m_start,
            AnalysisResultLog.timestamp < m_end
        ).scalar() or 0

        monthly_stats.append({
            'month': m,
            'year': y,
            'label': f"{m}-р сар",
            'count': cnt
        })

    # 6. Топ 5 ажилтан (энэ сар) — зөвхөн нүүрс
    top_users = (
        db.session.query(
            AnalysisResultLog.user_id,
            func.count(AnalysisResultLog.id).label('cnt')
        )
        .join(Sample, Sample.id == AnalysisResultLog.sample_id)
        .filter(
            Sample.lab_type == 'coal',
            AnalysisResultLog.action.in_(work_actions),
            AnalysisResultLog.user_id.isnot(None),
            AnalysisResultLog.timestamp >= month_start,
            AnalysisResultLog.timestamp < month_end
        )
        .group_by(AnalysisResultLog.user_id)
        .order_by(func.count(AnalysisResultLog.id).desc())
        .limit(5)
        .all()
    )

    top_users_data = []
    for uid, cnt in top_users:
        user = User.query.get(uid)
        if user:
            top_users_data.append({
                'name': _format_short_name(user.full_name) or user.username,
                'count': cnt
            })

    return render_template(
        "reports/dashboard.html",
        title="Dashboard",
        year=year,
        month=month,
        samples_month=samples_month,
        samples_year=samples_year,
        analyses_month=analyses_month,
        analyses_year=analyses_year,
        errors_month=errors_month,
        errors_year=errors_year,
        active_users_month=active_users_month,
        monthly_stats=monthly_stats,
        top_users=top_users_data,
    )


# ======================================================================
#  I. "Consumption" – grid + drill-down
# ======================================================================

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


@login_required
@reports_bp.route("/consumption")
def consumption():
    """Consumption – grid + drill-down."""
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
    except Exception:
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

    return jsonify({"success": True, "data": {"items": items}})


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
            Sample.lab_type == 'coal',
            AnalysisResult.status.in_(["approved", "pending_review"]),
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


@reports_bp.route("/monthly_plan", methods=["GET"])
@login_required
def monthly_plan():
    """
    MONTHLY PLAN - Сарын төлөвлөгөө
    Долоо хоног бүрийн төлөвлөгөө ба гүйцэтгэлийг харьцуулах.
    """
    from app.constants import SAMPLE_TYPE_CHOICES_MAP

    now = now_local()
    current_year = now.year
    current_month = now.month

    years = list(range(current_year - 3, current_year + 1))

    year = request.args.get("year", type=int) or current_year
    month = request.args.get("month", type=int) or current_month

    if year < current_year - 20 or year > current_year + 1:
        year = current_year
    if month < 1 or month > 12:
        month = current_month

    # Сарын нэр
    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    month_name = month_names[month]

    # Долоо хоногууд
    weeks_raw = _get_weeks_in_month(year, month)
    weeks = []
    for week_num, start_date, end_date in weeks_raw:
        # Долоо хоногийн өдрийн тоо (ачаалал тооцоход хэрэглэнэ)
        days_count = (end_date - start_date).days + 1
        weeks.append({
            'week': week_num,
            'start': start_date,
            'end': end_date,
            'days': days_count
        })

    # Planned тоонууд (DB-с)
    plans_db = M.MonthlyPlan.query.filter_by(year=year, month=month).all()
    plans = {}
    for p in plans_db:
        key = f"{p.client_name}|{p.sample_type}|{p.week}"
        plans[key] = p.planned_count or 0

    # Performance тоонууд (дээж хүлээн авсан)
    performance, _ = _calculate_weekly_performance(year, month)

    # Data structure with pre-calculated sums
    data = OrderedDict()
    week_totals = {w['week']: {'plan': 0, 'perf': 0} for w in weeks}
    grand_total = {'plan': 0, 'perf': 0}

    # Тодорхой дараалал
    consignor_order = ['UHG-Geo', 'BN-Geo', 'QC', 'Proc', 'WTL', 'CHPP', 'LAB']
    ordered_clients = [c for c in consignor_order if c in SAMPLE_TYPE_CHOICES_MAP]
    # Бусад нэгжүүдийг нэмэх (хэрэв байвал)
    for c in SAMPLE_TYPE_CHOICES_MAP.keys():
        if c not in ordered_clients:
            ordered_clients.append(c)

    for client_name in ordered_clients:
        client_data = OrderedDict()
        client_week_sums = {w['week']: {'plan': 0, 'perf': 0} for w in weeks}
        client_total = {'plan': 0, 'perf': 0}

        for sample_type in SAMPLE_TYPE_CHOICES_MAP[client_name]:
            row_total_plan = 0
            row_total_perf = 0
            week_values = {}

            for w in weeks:
                key = f"{client_name}|{sample_type}|{w['week']}"
                plan_val = plans.get(key, 0)
                perf_val = performance.get(key, 0)

                week_values[w['week']] = {'plan': plan_val, 'perf': perf_val}
                row_total_plan += plan_val
                row_total_perf += perf_val

                # Client week sum
                client_week_sums[w['week']]['plan'] += plan_val
                client_week_sums[w['week']]['perf'] += perf_val

                # Week totals (all clients)
                week_totals[w['week']]['plan'] += plan_val
                week_totals[w['week']]['perf'] += perf_val

            client_total['plan'] += row_total_plan
            client_total['perf'] += row_total_perf

            # Calculate percentage
            pct = (row_total_perf / row_total_plan * 100) if row_total_plan > 0 else 0

            client_data[sample_type] = {
                'weeks': week_values,
                'total_plan': row_total_plan,
                'total_perf': row_total_perf,
                'pct': pct
            }

        # Client percentage
        client_pct = (client_total['perf'] / client_total['plan'] * 100) if client_total['plan'] > 0 else 0

        data[client_name] = {
            'types': client_data,
            'week_sums': client_week_sums,
            'total': client_total,
            'pct': client_pct
        }

        grand_total['plan'] += client_total['plan']
        grand_total['perf'] += client_total['perf']

    # Grand percentage
    grand_pct = (grand_total['perf'] / grand_total['plan'] * 100) if grand_total['plan'] > 0 else 0

    # Өдрийн ачаалал тооцох (долоо хоног бүрд)
    for w in weeks:
        wt = week_totals[w['week']]
        wt['daily_plan'] = round(wt['plan'] / w['days'], 1) if w['days'] > 0 else 0
        wt['daily_perf'] = round(wt['perf'] / w['days'], 1) if w['days'] > 0 else 0

    # Сарын нийт өдөр
    total_days = sum(w['days'] for w in weeks)
    grand_total['daily_plan'] = round(grand_total['plan'] / total_days, 1) if total_days > 0 else 0
    grand_total['daily_perf'] = round(grand_total['perf'] / total_days, 1) if total_days > 0 else 0

    # Staff settings (хэдэн хүн ажиллах)
    staff_settings = M.StaffSettings.query.filter_by(year=year, month=month).first()
    staff_preparers = staff_settings.preparers if staff_settings else 6
    staff_chemists = staff_settings.chemists if staff_settings else 10

    return render_template(
        "reports/monthly_plan.html",
        title="Monthly Plan",
        years=years,
        year=year,
        month=month,
        month_name=month_name,
        weeks=weeks,
        data=data,
        plans=plans,
        performance=performance,
        week_totals=week_totals,
        grand_total=grand_total,
        grand_pct=grand_pct,
        staff_preparers=staff_preparers,
        staff_chemists=staff_chemists,
    )


# =====================================================================
# MONTHLY PLAN API (Planned тоог хадгалах/унших)
# =====================================================================
@reports_bp.route("/api/monthly_plan", methods=["GET"])
@login_required
def api_get_monthly_plan():
    """
    Сарын төлөвлөгөө авах.
    Query params: year, month
    """
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    if not year or not month:
        return jsonify({"error": "year болон month шаардлагатай"}), 400

    plans = M.MonthlyPlan.query.filter_by(year=year, month=month).all()

    result = {}
    for p in plans:
        key = f"{p.client_name}|{p.sample_type}|{p.week}"
        result[key] = p.planned_count

    return jsonify({"year": year, "month": month, "plans": result})


@reports_bp.route("/api/monthly_plan", methods=["POST"])
@login_required
def api_save_monthly_plan():
    """
    Сарын төлөвлөгөө хадгалах.
    JSON body: { year, month, plans: { "CHPP|2 hourly|1": 10, ... } }
    """
    if current_user.role not in ["senior", "admin"]:
        return jsonify({"error": "Зөвхөн ахлах эрхтэй"}), 403

    data = request.get_json()
    year = data.get("year")
    month = data.get("month")
    plans = data.get("plans", {})

    if not year or not month:
        return jsonify({"error": "year болон month шаардлагатай"}), 400

    saved_count = 0
    for key, planned_count in plans.items():
        parts = key.split("|")
        if len(parts) != 3:
            continue

        client_name, sample_type, week = parts
        week = int(week)

        # Upsert
        existing = M.MonthlyPlan.query.filter_by(
            year=year, month=month, week=week,
            client_name=client_name, sample_type=sample_type
        ).first()

        if existing:
            existing.planned_count = planned_count
            existing.updated_at = now_local()
        else:
            new_plan = M.MonthlyPlan(
                year=year, month=month, week=week,
                client_name=client_name, sample_type=sample_type,
                planned_count=planned_count,
                created_by_id=current_user.id
            )
            db.session.add(new_plan)

        saved_count += 1

    db.session.commit()
    return jsonify({"success": True, "saved": saved_count})


@reports_bp.route("/api/staff_settings", methods=["POST"])
@login_required
def api_save_staff_settings():
    """
    Ажилтны тоог хадгалах.
    JSON body: { year, month, staff_preparers, staff_chemists }
    """
    if current_user.role not in ["senior", "admin"]:
        return jsonify({"error": "Зөвхөн ахлах эрхтэй"}), 403

    data = request.get_json()
    year = data.get("year")
    month = data.get("month")
    preparers = data.get("staff_preparers", 6)
    chemists = data.get("staff_chemists", 10)

    if not year or not month:
        return jsonify({"error": "year болон month шаардлагатай"}), 400

    # Upsert
    existing = M.StaffSettings.query.filter_by(year=year, month=month).first()

    if existing:
        existing.preparers = preparers
        existing.chemists = chemists
        existing.updated_at = now_local()
    else:
        new_settings = M.StaffSettings(
            year=year, month=month,
            preparers=preparers, chemists=chemists
        )
        db.session.add(new_settings)

    db.session.commit()
    return jsonify({"success": True})


@reports_bp.route("/api/plan_statistics", methods=["GET"])
@login_required
def api_plan_statistics():
    """
    Статистик мэдээлэл - жилээр, сараар, долоо хоногоор.
    Query params: from_year, from_month, to_year, to_month
    Returns: { years: [...], months: [...], weeks: [...] }
    """
    from sqlalchemy import func
    from datetime import date
    import calendar

    now = now_local()
    current_year = now.year

    # Date range parameters
    from_year = request.args.get("from_year", type=int) or (current_year - 1)
    from_month = request.args.get("from_month", type=int) or 1
    to_year = request.args.get("to_year", type=int) or current_year
    to_month = request.args.get("to_month", type=int) or now.month

    # Validate
    if from_year > to_year or (from_year == to_year and from_month > to_month):
        from_year, from_month, to_year, to_month = to_year, to_month, from_year, from_month

    # Date range for queries
    range_start = date(from_year, from_month, 1)
    _, last_day = calendar.monthrange(to_year, to_month)
    range_end = date(to_year, to_month, last_day)

    # ===== Жилийн статистик (range дотор) =====
    yearly_stats = []
    for year in range(from_year, to_year + 1):
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        # Adjust for partial years
        if year == from_year:
            year_start = range_start
        if year == to_year:
            year_end = range_end

        # Төлөвлөгөө
        plan_query = db.session.query(func.sum(M.MonthlyPlan.planned_count)).filter(
            M.MonthlyPlan.year == year
        )
        if year == from_year:
            plan_query = plan_query.filter(M.MonthlyPlan.month >= from_month)
        if year == to_year:
            plan_query = plan_query.filter(M.MonthlyPlan.month <= to_month)
        planned = plan_query.scalar() or 0

        # Гүйцэтгэл
        perf_count = M.Sample.query.filter(
            M.Sample.received_date.between(year_start, year_end),
            M.Sample.status != 'cancelled'
        ).count()

        pct = round((perf_count / planned * 100), 1) if planned > 0 else 0
        yearly_stats.append({
            'year': year,
            'planned': planned,
            'actual': perf_count,
            'pct': pct
        })

    # ===== Сарын статистик =====
    monthly_stats = []
    for year in range(from_year, to_year + 1):
        start_m = from_month if year == from_year else 1
        end_m = to_month if year == to_year else 12

        for month in range(start_m, end_m + 1):
            # Skip future months
            if year == current_year and month > now.month:
                continue

            month_start = date(year, month, 1)
            _, last_day = calendar.monthrange(year, month)
            month_end = date(year, month, last_day)

            # Төлөвлөгөө
            planned = db.session.query(
                func.sum(M.MonthlyPlan.planned_count)
            ).filter_by(year=year, month=month).scalar() or 0

            # Гүйцэтгэл
            perf_count = M.Sample.query.filter(
                M.Sample.received_date.between(month_start, month_end),
                M.Sample.status != 'cancelled'
            ).count()

            pct = round((perf_count / planned * 100), 1) if planned > 0 else 0
            monthly_stats.append({
                'year': year,
                'month': month,
                'month_name': ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month],
                'planned': planned,
                'actual': perf_count,
                'pct': pct
            })

    # ===== Долоо хоногийн статистик =====
    weekly_stats = []
    for year in range(from_year, to_year + 1):
        start_m = from_month if year == from_year else 1
        end_m = to_month if year == to_year else 12

        for month in range(start_m, end_m + 1):
            if year == current_year and month > now.month:
                continue

            weeks_raw = _get_weeks_in_month(year, month)

            for week_num, start, end in weeks_raw:
                # Skip weeks outside range
                if start < range_start or end > range_end:
                    if start < range_start and end < range_start:
                        continue
                    if start > range_end and end > range_end:
                        continue

                # Төлөвлөгөө
                planned = db.session.query(
                    func.sum(M.MonthlyPlan.planned_count)
                ).filter_by(year=year, month=month, week=week_num).scalar() or 0

                # Гүйцэтгэл
                perf_count = M.Sample.query.filter(
                    M.Sample.received_date.between(start, end),
                    M.Sample.status != 'cancelled'
                ).count()

                pct = round((perf_count / planned * 100), 1) if planned > 0 else 0
                weekly_stats.append({
                    'year': year,
                    'month': month,
                    'week': week_num,
                    'label': f"{year}/{month}/W{week_num}",
                    'start': start.isoformat(),
                    'end': end.isoformat(),
                    'planned': planned,
                    'actual': perf_count,
                    'pct': pct
                })

    # ===== CONSIGNOR статистик =====
    consignor_stats = []
    from app.constants import SAMPLE_TYPE_CHOICES_MAP
    consignor_order = ['UHG-Geo', 'BN-Geo', 'QC', 'Proc', 'WTL', 'CHPP', 'LAB']

    for client in consignor_order:
        if client not in SAMPLE_TYPE_CHOICES_MAP:
            continue

        # Төлөвлөгөө (range дотор)
        plan_query = db.session.query(func.sum(M.MonthlyPlan.planned_count)).filter(
            M.MonthlyPlan.client_name == client,
            M.MonthlyPlan.year.between(from_year, to_year)
        )
        planned = plan_query.scalar() or 0

        # Гүйцэтгэл
        perf_count = M.Sample.query.filter(
            M.Sample.received_date.between(range_start, range_end),
            M.Sample.client_name == client,
            M.Sample.status != 'cancelled'
        ).count()

        pct = round((perf_count / planned * 100), 1) if planned > 0 else 0
        consignor_stats.append({
            'client': client,
            'planned': planned,
            'actual': perf_count,
            'pct': pct
        })

    # Summary totals
    total_planned = sum(m['planned'] for m in monthly_stats)
    total_actual = sum(m['actual'] for m in monthly_stats)
    total_pct = round((total_actual / total_planned * 100), 1) if total_planned > 0 else 0

    # Days in range (for daily average)
    days_in_range = (range_end - range_start).days + 1
    if range_end > now.date():
        days_in_range = (now.date() - range_start).days + 1
    daily_avg = round(total_actual / days_in_range, 1) if days_in_range > 0 else 0

    return jsonify({
        'current_year': current_year,
        'from_year': from_year,
        'from_month': from_month,
        'to_year': to_year,
        'to_month': to_month,
        'range_label': f"{from_year}/{from_month} - {to_year}/{to_month}",
        'total_planned': total_planned,
        'total_actual': total_actual,
        'total_pct': total_pct,
        'daily_avg': daily_avg,
        'yearly': yearly_stats,
        'monthly': monthly_stats,
        'weekly': weekly_stats,
        'consignor': consignor_stats
    })


def _get_weeks_in_month(year, month):
    """
    Сарын долоо хоногуудын эхлэл/төгсгөл огноог буцаах.
    Returns: [(week_num, start_date, end_date), ...]
    """
    import calendar
    from datetime import date

    _, last_day = calendar.monthrange(year, month)
    first = date(year, month, 1)
    last = date(year, month, last_day)

    weeks = []
    week_num = 1
    current = first

    while current <= last:
        # Долоо хоногийн эхлэл
        week_start = current
        # Долоо хоногийн төгсгөл (7 хоног эсвэл сарын төгсгөл)
        week_end = min(current + timedelta(days=6), last)

        weeks.append((week_num, week_start, week_end))

        current = week_end + timedelta(days=1)
        week_num += 1

    return weeks


def _calculate_weekly_performance(year, month):
    """
    Долоо хоног бүрийн гүйцэтгэл (дээжийн тоо) тооцох.
    Returns: { "CHPP|2 hourly|1": count, ... }
    """
    from app.models import Sample

    weeks = _get_weeks_in_month(year, month)
    result = {}

    for week_num, week_start, week_end in weeks:
        # Тухайн долоо хоногт хүлээн авсан дээжүүд
        samples = Sample.query.filter(
            func.date(Sample.received_date) >= week_start,
            func.date(Sample.received_date) <= week_end
        ).all()

        # client_name + sample_type-аар бүлэглэх
        counts = defaultdict(int)
        for s in samples:
            if s.client_name and s.sample_type:
                key = f"{s.client_name}|{s.sample_type}|{week_num}"
                counts[key] += 1

        result.update(counts)

    return result, weeks


@reports_bp.route("/api/weekly_performance", methods=["GET"])
@login_required
def api_weekly_performance():
    """
    Долоо хоногийн гүйцэтгэл (дээжийн тоо) авах.
    Query params: year, month
    """
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    if not year or not month:
        return jsonify({"error": "year болон month шаардлагатай"}), 400

    performance, weeks = _calculate_weekly_performance(year, month)

    weeks_info = [
        {"week": w[0], "start": w[1].strftime("%Y-%m-%d"), "end": w[2].strftime("%Y-%m-%d")}
        for w in weeks
    ]

    return jsonify({
        "year": year,
        "month": month,
        "weeks": weeks_info,
        "performance": performance
    })


# ======================================================================
#  III. ХИМИЧИЙН ТАЙЛАН - Chemist Performance Report
# ======================================================================


@reports_bp.route("/chemist_report")
@login_required
def chemist_report():
    """
    Химич нарын гүйцэтгэлийн тайлан:
    1. Сараар шинжилгээний тоо
    2. Шинжилгээний төрөл бүрээр тоо
    3. Error reason (8 төрөл) - алдааны тоо
    """
    from app.models import User, AnalysisResult, AnalysisResultLog, UsageLog, MaintenanceLog
    from app.constants import ERROR_REASON_KEYS, ERROR_REASON_LABELS
    from collections import defaultdict

    year = _year_arg()

    # Огнооны хүрээ (date_from, date_to параметрүүд)
    date_from_str = request.args.get("date_from", "")
    date_to_str = request.args.get("date_to", "")

    if date_from_str:
        try:
            start_dt = datetime.strptime(date_from_str, "%Y-%m-%d")
        except ValueError:
            start_dt = datetime(year, 1, 1)
    else:
        start_dt = datetime(year, 1, 1)
        date_from_str = start_dt.strftime("%Y-%m-%d")

    if date_to_str:
        try:
            end_dt = datetime.strptime(date_to_str, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            end_dt = datetime(year + 1, 1, 1)
    else:
        end_dt = datetime(year + 1, 1, 1)
        date_to_str = (end_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    # Шинжилгээ хийсэн action-ууд (CREATED болон UPDATED)
    work_actions = [
        'CREATED_AUTO_APPROVED',
        'CREATED_PENDING',
        'CREATED_REJECTED',
        'CREATED_VOID_RETEST',
        'UPDATED_AUTO_APPROVED',
        'UPDATED_PENDING',
        'UPDATED_REJECTED',
        'UPDATED_VOID_RETEST',
    ]

    # 1) Шинжилгээ хийсэн бүх хэрэглэгчдийг авах (бүх role)
    # CREATED_* action-д user_id нь шинжилгээ оруулсан хүн
    user_ids_with_results = (
        db.session.query(AnalysisResultLog.user_id)
        .filter(
            AnalysisResultLog.action.in_(work_actions),
            AnalysisResultLog.user_id.isnot(None),
            AnalysisResultLog.timestamp >= start_dt,
            AnalysisResultLog.timestamp < end_dt,
        )
        .distinct()
        .all()
    )
    user_ids = [uid[0] for uid in user_ids_with_results]

    # Тэдгээр хэрэглэгчдийн мэдээллийг авах
    chemists = User.query.filter(User.id.in_(user_ids)).order_by(User.full_name).all() if user_ids else []

    # 2) Шинжилгээний үр дүнг авах - CREATED_* action-д user_id ашиглах
    results = (
        db.session.query(
            AnalysisResultLog.user_id,
            AnalysisResultLog.analysis_code,
            extract("month", AnalysisResultLog.timestamp).label("month"),
            func.count(AnalysisResultLog.id).label("cnt")
        )
        .filter(
            AnalysisResultLog.action.in_(work_actions),
            AnalysisResultLog.user_id.isnot(None),
            AnalysisResultLog.timestamp >= start_dt,
            AnalysisResultLog.timestamp < end_dt,
        )
        .group_by(
            AnalysisResultLog.user_id,
            AnalysisResultLog.analysis_code,
            extract("month", AnalysisResultLog.timestamp)
        )
        .all()
    )

    # 3) Алдааны логуудыг авах (REJECTED)
    # AnalysisResult.user_id = анхны химич (алдаа гаргасан)
    error_logs = (
        db.session.query(
            AnalysisResult.user_id,
            AnalysisResultLog.error_reason,
            func.count(AnalysisResultLog.id).label("cnt")
        )
        .join(AnalysisResult, AnalysisResult.id == AnalysisResultLog.analysis_result_id)
        .filter(
            AnalysisResultLog.action == "REJECTED",
            AnalysisResultLog.error_reason.isnot(None),
            AnalysisResultLog.timestamp >= start_dt,
            AnalysisResultLog.timestamp < end_dt,
        )
        .group_by(
            AnalysisResult.user_id,
            AnalysisResultLog.error_reason
        )
        .all()
    )

    # 4) Өгөгдлийг бүтэцлэх
    # chemist_data[user_id] = {
    #   'name': ...,
    #   'monthly': {1: count, 2: count, ...},
    #   'by_analysis': {'Aad': count, 'Vad': count, ...},
    #   'errors': {'sample_prep': count, ...},
    #   'total': count
    # }
    chemist_data = {}

    # Химичуудыг map-д нэмэх
    for user in chemists:
        chemist_data[user.id] = {
            'id': user.id,
            'name': _format_short_name(user.full_name) or user.username,
            'monthly': {m: 0 for m in range(1, 13)},
            'by_analysis': defaultdict(int),
            'errors': {key: 0 for key in ERROR_REASON_KEYS},
            'total': 0,
            'error_total': 0,
            'rank_total': None,
            'rank_quality': None,
            'quarterly': [0, 0, 0, 0],
            'quarterly_growth': [0, 0, 0],
            'eq_usage_count': 0,
            'eq_usage_hours': 0.0,
            'eq_maint_count': 0,
            'eq_calib_count': 0,
        }

    # Шинжилгээний үр дүнг нэмэх
    all_analysis_codes = set()
    for row in results:
        user_id = row.user_id
        if user_id not in chemist_data:
            # Химич биш хэрэглэгч байж магадгүй
            user = User.query.get(user_id)
            if user:
                chemist_data[user_id] = {
                    'id': user_id,
                    'name': _format_short_name(user.full_name) or user.username,
                    'monthly': {m: 0 for m in range(1, 13)},
                    'by_analysis': defaultdict(int),
                    'errors': {key: 0 for key in ERROR_REASON_KEYS},
                    'total': 0,
                    'error_total': 0,
                    'rank_total': None,
                    'rank_quality': None,
                    'quarterly': [0, 0, 0, 0],
                    'quarterly_growth': [0, 0, 0],
                    'eq_usage_count': 0,
                    'eq_usage_hours': 0.0,
                    'eq_maint_count': 0,
                    'eq_calib_count': 0,
                }
            else:
                continue

        month = int(row.month) if row.month else 0
        code = row.analysis_code or ""
        cnt = row.cnt

        if month >= 1 and month <= 12:
            chemist_data[user_id]['monthly'][month] += cnt
        chemist_data[user_id]['by_analysis'][code] += cnt
        chemist_data[user_id]['total'] += cnt
        all_analysis_codes.add(code)

    # Алдааны логуудыг нэмэх
    for row in error_logs:
        user_id = row.user_id
        if user_id not in chemist_data:
            continue
        reason = row.error_reason or ""
        cnt = row.cnt
        if reason in chemist_data[user_id]['errors']:
            chemist_data[user_id]['errors'][reason] += cnt
            chemist_data[user_id]['error_total'] += cnt

    # 5) Нийт дүн тооцох
    grand_monthly = {m: 0 for m in range(1, 13)}
    grand_by_analysis = defaultdict(int)
    grand_errors = {key: 0 for key in ERROR_REASON_KEYS}
    grand_total = 0
    grand_error_total = 0

    for uid, data in chemist_data.items():
        for m in range(1, 13):
            grand_monthly[m] += data['monthly'][m]
        for code, cnt in data['by_analysis'].items():
            grand_by_analysis[code] += cnt
        for key in ERROR_REASON_KEYS:
            grand_errors[key] += data['errors'][key]
        grand_total += data['total']
        grand_error_total += data['error_total']

    # 6) Өмнөх жилийн өгөгдөл (харьцуулалтанд)
    prev_year = year - 1
    prev_start_dt = datetime(prev_year, 1, 1)
    prev_end_dt = datetime(prev_year + 1, 1, 1)

    prev_year_results = (
        db.session.query(
            extract("month", AnalysisResultLog.timestamp).label("month"),
            func.count(AnalysisResultLog.id).label("cnt")
        )
        .filter(
            AnalysisResultLog.action.in_(work_actions),
            AnalysisResultLog.user_id.isnot(None),
            AnalysisResultLog.timestamp >= prev_start_dt,
            AnalysisResultLog.timestamp < prev_end_dt,
        )
        .group_by(extract("month", AnalysisResultLog.timestamp))
        .all()
    )

    prev_monthly = {m: 0 for m in range(1, 13)}
    for row in prev_year_results:
        month = int(row.month) if row.month else 0
        if 1 <= month <= 12:
            prev_monthly[month] = row.cnt

    # 7) Эрэмбэлэх (нийт тоогоор буурах)
    sorted_chemists = sorted(
        chemist_data.values(),
        key=lambda x: x['total'],
        reverse=True
    )

    # Байр эзлүүлэх
    for idx, chemist in enumerate(sorted_chemists):
        chemist['rank_total'] = idx + 1

    # Чанараар эрэмбэлэх (алдааны хувь бага = сайн)
    sorted_by_quality = sorted(
        [c for c in chemist_data.values() if c['total'] >= 10],  # 10+ шинжилгээтэй
        key=lambda x: (x['error_total'] / x['total'] * 100) if x['total'] > 0 else 100
    )
    for idx, chemist in enumerate(sorted_by_quality):
        chemist['rank_quality'] = idx + 1

    # Сар бүрийн өсөлт/бууралт тооцох
    for chemist in chemist_data.values():
        monthly = chemist['monthly']
        growth = []
        for m in range(2, 13):
            prev = monthly.get(m - 1, 0)
            curr = monthly.get(m, 0)
            if prev > 0:
                pct = ((curr - prev) / prev) * 100
            elif curr > 0:
                pct = 100  # 0-ээс өссөн
            else:
                pct = 0
            growth.append(round(pct, 1))
        chemist['monthly_growth'] = growth

        # Улирлын дүн
        q1 = sum(monthly.get(m, 0) for m in [1, 2, 3])
        q2 = sum(monthly.get(m, 0) for m in [4, 5, 6])
        q3 = sum(monthly.get(m, 0) for m in [7, 8, 9])
        q4 = sum(monthly.get(m, 0) for m in [10, 11, 12])
        chemist['quarterly'] = [q1, q2, q3, q4]

        # Улирлын өсөлт
        quarterly_growth = []
        quarters = [q1, q2, q3, q4]
        for i in range(1, 4):
            prev = quarters[i - 1]
            curr = quarters[i]
            if prev > 0:
                pct = ((curr - prev) / prev) * 100
            elif curr > 0:
                pct = 100
            else:
                pct = 0
            quarterly_growth.append(round(pct, 1))
        chemist['quarterly_growth'] = quarterly_growth

    # 8) Багаж ашиглалтын статистик (UsageLog + MaintenanceLog)
    eq_user_ids = list(chemist_data.keys())
    if eq_user_ids:
        # UsageLog: ашигласан тоо, нийт минут
        usage_stats = (
            db.session.query(
                UsageLog.used_by_id,
                func.count(UsageLog.id),
                func.coalesce(func.sum(UsageLog.duration_minutes), 0),
            )
            .filter(
                UsageLog.used_by_id.in_(eq_user_ids),
                UsageLog.start_time >= start_dt,
                UsageLog.start_time < end_dt,
            )
            .group_by(UsageLog.used_by_id)
            .all()
        )
        for uid, cnt, mins in usage_stats:
            if uid in chemist_data:
                chemist_data[uid]['eq_usage_count'] = cnt
                chemist_data[uid]['eq_usage_hours'] = round(int(mins) / 60.0, 1)

        # MaintenanceLog: засвар/калибровка тоо
        maint_stats = (
            db.session.query(
                MaintenanceLog.performed_by_id,
                MaintenanceLog.action_type,
                func.count(MaintenanceLog.id),
            )
            .filter(
                MaintenanceLog.performed_by_id.in_(eq_user_ids),
                MaintenanceLog.action_date >= start_dt,
                MaintenanceLog.action_date < end_dt,
            )
            .group_by(MaintenanceLog.performed_by_id, MaintenanceLog.action_type)
            .all()
        )
        for uid, action_type, cnt in maint_stats:
            if uid in chemist_data:
                if action_type == 'Calibration':
                    chemist_data[uid]['eq_calib_count'] += cnt
                else:
                    chemist_data[uid]['eq_maint_count'] += cnt

    # Шинжилгээний кодуудыг эрэмбэлэх
    sorted_analysis_codes = sorted(all_analysis_codes)

    return render_template(
        "reports/chemist_report.html",
        title=f"Химичийн тайлан — {year}",
        year=year,
        date_from=date_from_str,
        date_to=date_to_str,
        chemists=sorted_chemists,
        chemists_by_quality=sorted_by_quality,
        analysis_codes=sorted_analysis_codes,
        error_reason_keys=ERROR_REASON_KEYS,
        error_reason_labels=ERROR_REASON_LABELS,
        grand_monthly=grand_monthly,
        grand_by_analysis=dict(grand_by_analysis),
        grand_errors=grand_errors,
        grand_total=grand_total,
        grand_error_total=grand_error_total,
        prev_year=prev_year,
        prev_monthly=prev_monthly,
    )
