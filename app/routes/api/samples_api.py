# app/routes/api/samples_api.py
# -*- coding: utf-8 -*-
"""
Дээжтэй холбоотой API endpoints:
  - /data - DataTables sample listing
  - /sample_summary - Sample summary with archive/unarchive
  - /sample_report/<int:sample_id> - Individual sample report
  - /sample_history/<int:sample_id> - Sample history
"""

from flask import (
    request,
    jsonify,
    url_for,
    redirect,
    render_template,
    flash,
)
from flask_login import login_required
from datetime import datetime, timedelta
import json

from app import db, limiter
from app.models import Sample, AnalysisResult, AnalysisResultLog
from app.utils.datetime import now_local
from app.utils.codes import to_base_list
from app.utils.security import escape_like_pattern
from .helpers import _aggregate_sample_status

# Service layer imports
from app.services import (
    archive_samples,
    get_sample_report_data,
    get_samples_with_results,
    build_sample_summary_data,
)


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # -----------------------------------------------------------
    # 1) DataTables-д өгөгдөл өгөх (index.html)
    #    GET /api/data
    # -----------------------------------------------------------
    @bp.route("/data", methods=["GET"])
    @login_required
    @limiter.limit("100 per minute")
    def data():
        draw = int(request.args.get("draw", 1))
        start = int(request.args.get("start", 0))
        length = min(int(request.args.get("length", 25)), 1000)  # Max 1000 хязгаарлалт

        # DataTables-н багана тус бүрийн шүүлтүүр
        column_search = {}
        i = 0
        while True:
            col_data = request.args.get(f"columns[{i}][data]")
            if col_data is None:
                break
            search_val = request.args.get(f"columns[{i}][search][value]", "").strip()
            column_search[i] = search_val
            i += 1

        date_start = request.args.get("dateFilterStart")
        date_end = request.args.get("dateFilterEnd")

        q = Sample.query

        if date_start:
            try:
                ds = datetime.fromisoformat(date_start)
                q = q.filter(Sample.received_date >= ds)
            except ValueError:
                pass  # Буруу огноо формат
        if date_end:
            try:
                de = datetime.fromisoformat(date_end)
                q = q.filter(Sample.received_date <= de)
            except ValueError:
                pass  # Буруу огноо формат

        # Баганын шүүлтүүрүүд
        for idx, val in column_search.items():
            if not val:
                continue
            if idx == 1:
                # ID
                try:
                    q = q.filter(Sample.id == int(val))
                except ValueError:
                    pass  # Тоо биш
            elif idx == 2:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.sample_code.ilike(f"%{safe_val}%"))
            elif idx == 3:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.client_name.ilike(f"%{safe_val}%"))
            elif idx == 4:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.sample_type.ilike(f"%{safe_val}%"))
            elif idx == 5:
                # ✅ ДЭЭЖНИЙ ТӨЛӨВ (хуурай / чийгтэй / шингэн)
                cond_col = None
                if hasattr(Sample, "sample_condition"):
                    cond_col = Sample.sample_condition
                elif hasattr(Sample, "sample_state"):
                    cond_col = Sample.sample_state
                else:
                    cond_col = Sample.status  # fallback
                safe_val = escape_like_pattern(val)
                q = q.filter(cond_col.ilike(f"%{safe_val}%"))
            elif idx == 6:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.delivered_by.ilike(f"%{safe_val}%"))
            elif idx == 7:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.prepared_by.ilike(f"%{safe_val}%"))
            elif idx == 9:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.notes.ilike(f"%{safe_val}%"))
            elif idx == 11:
                try:
                    w = float(val)
                    q = q.filter(Sample.weight == w)
                except ValueError:
                    pass  # Тоо биш
            elif idx == 13:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.analyses_to_perform.ilike(f"%{safe_val}%"))

        records_total = q.count()
        records_filtered = records_total

        samples = (
            q.order_by(Sample.received_date.desc())
            .offset(start)
            .limit(length)
            .all()
        )

        # ✅ Нэг дор бүх дээжийн шинжилгээний статустай map үүсгэнэ
        sample_ids = [s.id for s in samples]
        status_map: dict[int, set[str]] = {}
        if sample_ids:
            rows = (
                db.session.query(AnalysisResult.sample_id, AnalysisResult.status)
                .filter(AnalysisResult.sample_id.in_(sample_ids))
                .all()
            )
            for sid, st in rows:
                if sid not in status_map:
                    status_map[sid] = set()
                if st:
                    status_map[sid].add(st)

        data_rows = []
        for s in samples:
            # ✅ analyses_to_perform → base кодын жагсаалт
            try:
                raw_codes = json.loads(s.analyses_to_perform or "[]")
            except (json.JSONDecodeError, TypeError):
                raw_codes = []
            analyses_base = to_base_list(raw_codes)
            analyses_txt = json.dumps(analyses_base, ensure_ascii=False)

            # ✅ ДЭЭЖНИЙ ТӨЛӨВ (condition)
            sample_condition_val = ""
            if hasattr(s, "sample_condition") and getattr(s, "sample_condition") is not None:
                sample_condition_val = getattr(s, "sample_condition")  # Хуурай/Чийгтэй/Шингэн
            elif hasattr(s, "sample_state") and getattr(s, "sample_state") is not None:
                sample_condition_val = getattr(s, "sample_state")

            # ✅ НЭГТСЭН ТӨЛӨВ (шинжилгээний статус)
            result_statuses = status_map.get(s.id, set())
            workflow_status = _aggregate_sample_status(s.status or "", result_statuses)

            action_html = (
                f'<a href="{url_for("main.edit_sample", sample_id=s.id)}" '
                f'class="btn btn-sm btn-outline-primary">Засах</a>'
            )

            # Хадгалах хугацааны тооцоо
            retention_html = ""
            if s.return_sample:
                retention_html = '<span class="badge bg-primary">Буцаах</span>'
            elif s.retention_date:
                from datetime import date
                today = date.today()
                days_left = (s.retention_date - today).days
                if days_left < 0:
                    retention_html = f'<span class="badge bg-danger">{abs(days_left)} хоног хэтэрсэн</span>'
                elif days_left <= 7:
                    retention_html = f'<span class="badge bg-warning text-dark">{days_left} хоног</span>'
                elif days_left <= 30:
                    retention_html = f'<span class="badge bg-info">{days_left} хоног</span>'
                else:
                    retention_html = f'<span class="badge bg-success">{days_left} хоног</span>'
            else:
                retention_html = '<span class="badge bg-secondary">-</span>'

            data_rows.append(
                [
                    f'<input type="checkbox" class="sample-checkbox" value="{s.id}">',  # 0
                    s.id,  # 1
                    s.sample_code or "",  # 2
                    s.client_name or "",  # 3
                    s.sample_type or "",  # 4
                    sample_condition_val or "",  # 5  ✅ ДЭЭЖНИЙ ТӨЛӨВ
                    s.delivered_by or "",  # 6
                    s.prepared_by or "",  # 7
                    s.prepared_date.strftime("%Y-%m-%d") if s.prepared_date else "",  # 8
                    s.notes or "",  # 9
                    s.received_date.strftime("%Y-%m-%d %H:%M") if s.received_date else "",  # 10
                    s.weight or "",  # 11
                    workflow_status,  # 12 ✅ НЭГТСЭН ТӨЛӨВ
                    analyses_txt,  # 13
                    retention_html,  # 14 ✅ ХАДГАЛАХ ХУГАЦАА
                    action_html,  # 15
                ]
            )

        return jsonify(
            {
                "draw": draw,
                "recordsTotal": records_total,
                "recordsFiltered": records_filtered,
                "data": data_rows,
            }
        )

    # -----------------------------------------------------------
    # 2) sample_summary.html → архив / сэргээх (POST /api/sample_summary)
    #    ✅ REFACTORED: Service layer ашиглана
    # -----------------------------------------------------------
    @bp.route("/sample_summary", methods=["GET", "POST"])
    @login_required
    @limiter.limit("100 per minute")
    def sample_summary():
        # --- POST (Архивлах) - Service ашиглана ---
        if request.method == "POST":
            action = request.form.get("action")
            sample_ids_str = request.form.get("sample_ids")
            if sample_ids_str and action in ["archive", "unarchive"]:
                sample_ids = [
                    int(sid) for sid in sample_ids_str.split(",") if sid.isdigit()
                ]
                result = archive_samples(sample_ids, archive=(action == "archive"))
                flash(result.message, "success" if result.success else "danger")
                return redirect(url_for("api.sample_summary", **request.args))

        # --- GET: Service-ээс өгөгдөл авах ---
        samples = get_samples_with_results(exclude_archived=True, sort_by="full")
        summary_data = build_sample_summary_data(samples)

        return render_template(
            "sample_summary.html",
            title="Дээжний нэгтгэл",
            samples=samples,
            analysis_types=summary_data["analysis_types"],
            results_map=summary_data["results_map"],
            analysis_dates_map=summary_data["analysis_dates_map"],
        )

    # -----------------------------------------------------------
    # 3) ДЭЭЖНИЙ ТАЙЛАН
    #    ✅ REFACTORED: Service layer ашиглана
    # -----------------------------------------------------------
    @bp.route("/sample_report/<int:sample_id>")
    @login_required
    def sample_report(sample_id):
        # Service-ээс тайлангийн өгөгдөл авах
        report_data = get_sample_report_data(sample_id)

        # Алдаа шалгах
        if report_data.error == "SAMPLE_NOT_FOUND":
            flash("Дээж олдсонгүй.", "danger")
            return redirect(url_for("api.sample_summary"))

        if report_data.error:
            flash(
                f"{report_data.error}. Шаардлагатай (MT, Mad) утгууд орсон эсэхийг шалгана уу.",
                "danger",
            )
            return redirect(request.referrer or url_for("api.sample_summary"))

        return render_template(
            "report.html",
            title=f"Тайлан: {report_data.sample.sample_code}",
            sample=report_data.sample,
            calcs=report_data.calculations,
            report_date=report_data.report_date,
        )

    # -----------------------------------------------------------
    # 4) ДЭЭЖНИЙ ТҮҮХ
    # -----------------------------------------------------------
    @bp.route("/sample_history/<int:sample_id>")
    @login_required
    def sample_history(sample_id):
        sample = Sample.query.get_or_404(sample_id)
        results = (
            AnalysisResult.query.filter_by(sample_id=sample_id)
            .order_by(AnalysisResult.created_at.desc())
            .all()
        )
        logs = (
            AnalysisResultLog.query.filter_by(sample_id=sample_id)
            .order_by(AnalysisResultLog.timestamp.desc())
            .all()
        )
        return render_template(
            "sample_history.html",
            title=f"Түүх: {sample.sample_code}",  # ✅ sample_code болгосон
            sample=sample,
            results=results,
            logs=logs,
        )

    # -----------------------------------------------------------
    # 5) АРХИВ ТӨВ (Archive Hub)
    #    Нэгж → Он → Сар бүтэцтэй архивын удирдлага
    #    ✅ REFACTORED: Service layer ашиглана (unarchive)
    # -----------------------------------------------------------
    @bp.route("/archive_hub", methods=["GET", "POST"])
    @login_required
    @limiter.limit("100 per minute")
    def archive_hub():
        from sqlalchemy import func, extract
        from collections import defaultdict

        # --- POST: Сэргээх - Service ашиглана ---
        if request.method == "POST":
            action = request.form.get("action")
            sample_ids_str = request.form.get("sample_ids")
            if sample_ids_str and action == "unarchive":
                sample_ids = [
                    int(sid) for sid in sample_ids_str.split(",") if sid.isdigit()
                ]
                result = archive_samples(sample_ids, archive=False)
                flash(result.message, "success" if result.success else "danger")
            return redirect(url_for("api.archive_hub", **request.args))

        # --- GET: Архив харах ---
        # Шүүлтүүрийн параметрүүд
        selected_client = request.args.get("client")
        selected_type = request.args.get("type")
        selected_year = request.args.get("year", type=int)
        selected_month = request.args.get("month", type=int)

        # 1. Бүх архивлагдсан дээжүүдийн статистик (Нэгж → Төрөл → Он → Сар)
        archive_stats = (
            db.session.query(
                Sample.client_name,
                Sample.sample_type,
                extract("year", Sample.received_date).label("year"),
                extract("month", Sample.received_date).label("month"),
                func.count(Sample.id).label("count"),
            )
            .filter(Sample.status == "archived")
            .group_by(
                Sample.client_name,
                Sample.sample_type,
                extract("year", Sample.received_date),
                extract("month", Sample.received_date),
            )
            .order_by(
                Sample.client_name,
                Sample.sample_type,
                extract("year", Sample.received_date).desc(),
                extract("month", Sample.received_date).desc(),
            )
            .all()
        )

        # 2. Tree бүтэц: client -> sample_type -> year -> month
        tree_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
        client_totals = defaultdict(int)
        total_archived = 0

        for row in archive_stats:
            client = row.client_name or "Тодорхойгүй"
            stype = row.sample_type or "Бусад"
            year = int(row.year) if row.year else 0
            month = int(row.month) if row.month else 0
            count = row.count

            tree_data[client][stype][year][month] = count
            client_totals[client] += count
            total_archived += count

        # 3. Сонгосон бүлгийн дээжүүд (хэрэв шүүлтүүр байвал)
        samples = []
        results_map = {}

        if selected_client and selected_type:
            query = db.session.query(Sample).filter(
                Sample.status == "archived",
                Sample.client_name == selected_client,
                Sample.sample_type == selected_type,
            )
            if selected_year:
                query = query.filter(
                    extract("year", Sample.received_date) == selected_year
                )
            if selected_month:
                query = query.filter(
                    extract("month", Sample.received_date) == selected_month
                )

            query = query.order_by(Sample.received_date.desc())
            samples = query.limit(500).all()  # Max 500

            # Хялбар хэлбэр: Түүхий үр дүнг шууд авах
            if samples:
                sample_ids = [s.id for s in samples]
                all_results = (
                    AnalysisResult.query.filter(
                        AnalysisResult.sample_id.in_(sample_ids),
                        AnalysisResult.status.in_(["approved", "pending_review"]),
                    ).all()
                )
                for r in all_results:
                    if r.sample_id not in results_map:
                        results_map[r.sample_id] = {}
                    results_map[r.sample_id][r.analysis_code] = {
                        "id": r.id,
                        "value": r.final_result,
                        "status": r.status,
                    }

        # 4. Шинжилгээний төрлүүд (AnalysisType-аас)
        from app.models import AnalysisType
        analysis_types = AnalysisType.query.order_by(AnalysisType.order_num).all()

        # Сарын нэрс
        MONTH_NAMES = {
            1: "1-р сар", 2: "2-р сар", 3: "3-р сар", 4: "4-р сар",
            5: "5-р сар", 6: "6-р сар", 7: "7-р сар", 8: "8-р сар",
            9: "9-р сар", 10: "10-р сар", 11: "11-р сар", 12: "12-р сар",
        }

        return render_template(
            "archive_hub.html",
            title="Архив Төв",
            tree_data=dict(tree_data),
            client_totals=dict(client_totals),
            total_archived=total_archived,
            samples=samples,
            results_map=results_map,
            analysis_types=analysis_types,
            selected_client=selected_client,
            selected_type=selected_type,
            selected_year=selected_year,
            selected_month=selected_month,
            month_names=MONTH_NAMES,
        )

    # -----------------------------------------------------------
    # 6) DASHBOARD STATISTICS API
    #    Chart.js-д зориулсан статистик
    # -----------------------------------------------------------
    @bp.route("/dashboard_stats")
    @login_required
    def api_dashboard_stats():
        """
        Dashboard Chart.js-д зориулсан статистик

        Returns:
            - samples_by_day: Сүүлийн 7 хоногийн дээж тоо
            - samples_by_client: Client тус бүрийн дээж тоо
            - analysis_by_status: Шинжилгээний статусаар тоо
            - daily_trend: Өдрийн trend
        """
        from sqlalchemy import func, case

        today = now_local().date()

        # 1. Сүүлийн 7 хоногийн дээж тоо
        samples_by_day = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            count = Sample.query.filter(
                func.date(Sample.received_date) == day
            ).count()
            samples_by_day.append({
                "date": day.strftime("%m/%d"),
                "day_name": ["Ня", "Да", "Мя", "Лх", "Пү", "Ба", "Бя"][day.weekday()],
                "count": count
            })

        # 2. Client тус бүрийн дээж тоо (энэ сар)
        first_of_month = today.replace(day=1)
        samples_by_client = db.session.query(
            Sample.client_name,
            func.count(Sample.id).label("count")
        ).filter(
            Sample.received_date >= first_of_month
        ).group_by(Sample.client_name).all()

        # 3. Шинжилгээний статусаар тоо (өнөөдөр)
        analysis_by_status = db.session.query(
            AnalysisResult.status,
            func.count(AnalysisResult.id).label("count")
        ).filter(
            func.date(AnalysisResult.updated_at) == today
        ).group_by(AnalysisResult.status).all()

        # 4. Энэ сарын approve/reject харьцаа
        approval_stats = db.session.query(
            func.sum(case((AnalysisResult.status == 'approved', 1), else_=0)).label('approved'),
            func.sum(case((AnalysisResult.status == 'rejected', 1), else_=0)).label('rejected'),
            func.sum(case((AnalysisResult.status == 'pending_review', 1), else_=0)).label('pending')
        ).filter(
            AnalysisResult.updated_at >= first_of_month
        ).first()

        # 5. Өнөөдрийн нийт статистик
        today_samples = Sample.query.filter(
            func.date(Sample.received_date) == today
        ).count()

        today_analyses = AnalysisResult.query.filter(
            func.date(AnalysisResult.created_at) == today
        ).count()

        pending_review = AnalysisResult.query.filter(
            AnalysisResult.status == 'pending_review'
        ).count()

        return jsonify({
            "samples_by_day": samples_by_day,
            "samples_by_client": [
                {"client": c, "count": cnt} for c, cnt in samples_by_client
            ],
            "analysis_by_status": [
                {"status": s, "count": cnt} for s, cnt in analysis_by_status
            ],
            "approval_stats": {
                "approved": approval_stats.approved or 0,
                "rejected": approval_stats.rejected or 0,
                "pending": approval_stats.pending or 0
            },
            "today": {
                "samples": today_samples,
                "analyses": today_analyses,
                "pending_review": pending_review
            }
        })

    # -----------------------------------------------------------
    # 7) EXPORT TO EXCEL
    # -----------------------------------------------------------
    @bp.route("/export/samples")
    @login_required
    def export_samples():
        """Дээжний өгөгдлийг Excel экспорт"""
        from app.utils.exports import create_sample_export, send_excel_response

        # Query parameters
        client = request.args.get('client')
        sample_type = request.args.get('type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = min(int(request.args.get('limit', 1000)), 5000)

        query = Sample.query

        if client:
            query = query.filter(Sample.client_name == client)
        if sample_type:
            query = query.filter(Sample.sample_type == sample_type)
        if start_date:
            try:
                sd = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Sample.received_date >= sd)
            except ValueError:
                pass
        if end_date:
            try:
                ed = datetime.strptime(end_date, '%Y-%m-%d')
                ed = datetime.combine(ed, datetime.max.time())
                query = query.filter(Sample.received_date <= ed)
            except ValueError:
                pass

        samples = query.order_by(Sample.received_date.desc()).limit(limit).all()

        excel_data = create_sample_export(samples)
        filename = f"samples_{now_local().strftime('%Y%m%d_%H%M')}.xlsx"

        return send_excel_response(excel_data, filename)

    @bp.route("/export/analysis")
    @login_required
    def export_analysis():
        """Шинжилгээний үр дүнг Excel экспорт"""
        from app.utils.exports import create_analysis_export, send_excel_response

        # Query parameters
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = min(int(request.args.get('limit', 1000)), 5000)

        query = AnalysisResult.query

        if status:
            query = query.filter(AnalysisResult.status == status)
        if start_date:
            try:
                sd = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(AnalysisResult.created_at >= sd)
            except ValueError:
                pass
        if end_date:
            try:
                ed = datetime.strptime(end_date, '%Y-%m-%d')
                ed = datetime.combine(ed, datetime.max.time())
                query = query.filter(AnalysisResult.created_at <= ed)
            except ValueError:
                pass

        results = query.order_by(AnalysisResult.created_at.desc()).limit(limit).all()

        excel_data = create_analysis_export(results)
        filename = f"analysis_{now_local().strftime('%Y%m%d_%H%M')}.xlsx"

        return send_excel_response(excel_data, filename)

    # -----------------------------------------------------------
    # HTMX ENDPOINTS - HTML fragments буцаадаг
    # -----------------------------------------------------------

    @bp.route("/sample_count", methods=["GET"])
    @login_required
    def htmx_sample_count():
        """htmx: Нийт дээжний тоог HTML-ээр буцаах."""
        count = Sample.query.count()
        return f'<strong class="text-primary">{count}</strong> дээж'

    @bp.route("/search_samples", methods=["GET"])
    @login_required
    def htmx_search_samples():
        """htmx: Дээж хайх (partial HTML)."""
        from app.utils.security import escape_like_pattern

        q = request.args.get("q", "").strip()
        if len(q) < 2:
            return '<div class="text-muted small">2+ тэмдэгт оруулна уу</div>'

        safe_q = escape_like_pattern(q)
        samples = (
            Sample.query
            .filter(Sample.sample_code.ilike(f"%{safe_q}%"))
            .limit(10)
            .all()
        )

        if not samples:
            return '<div class="text-muted small">Олдсонгүй</div>'

        html = '<div class="list-group list-group-flush">'
        for s in samples:
            html += f'''
            <a href="/sample/{s.id}" class="list-group-item list-group-item-action py-2">
                <strong>{s.sample_code}</strong>
                <small class="text-muted ms-2">{s.client_name or ""}</small>
            </a>'''
        html += '</div>'
        return html
