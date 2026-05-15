# app/routes/api/samples_api.py
# -*- coding: utf-8 -*-
"""
Sample-related API endpoints:
  - /data - DataTables sample listing
  - /sample_summary - Sample summary with archive/unarchive
  - /sample_report/<int:sample_id> - Individual sample report
  - /sample_history/<int:sample_id> - Sample history
"""

import logging
from datetime import datetime

from flask import (
    request,
    jsonify,
    url_for,
    redirect,
    render_template,
    flash,
    abort,
)
from flask_babel import gettext as _, lazy_gettext as _l
from flask_login import login_required, current_user
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload
from markupsafe import escape

from app import db, limiter
from app.models import AnalysisResult, Sample
from app.utils.datetime import now_local
from app.utils.security import escape_like_pattern

from app.services import (
    archive_samples,
    get_sample_report_data,
    get_samples_with_results,
    build_sample_summary_data,
)
from app.services.dashboard_service import (
    get_dashboard_stats,
    get_archive_tree,
    MONTH_NAMES,
)
from app.services.datatable_service import query_samples_datatable
from app.services.mg_service import get_mg_summary, repeat_analyses

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register routes on the given blueprint"""

    # -----------------------------------------------------------
    # 1) DataTables data provider (index.html)
    # -----------------------------------------------------------
    @bp.route("/data", methods=["GET"])
    @login_required
    @limiter.limit("100 per minute")
    async def data():
        # Parse DataTables parameters
        draw = int(request.args.get("draw", 1))
        start = int(request.args.get("start", 0))
        length = int(request.args.get("length", 25))

        column_search = {}
        i = 0
        while True:
            col_data = request.args.get(f"columns[{i}][data]")
            if col_data is None:
                break
            search_val = request.args.get(f"columns[{i}][search][value]", "").strip()
            column_search[i] = search_val
            i += 1

        result = query_samples_datatable(
            draw=draw,
            start=start,
            length=length,
            column_search=column_search,
            date_start=request.args.get("dateFilterStart"),
            date_end=request.args.get("dateFilterEnd"),
        )

        return jsonify({
            "draw": result.draw,
            "recordsTotal": result.records_total,
            "recordsFiltered": result.records_filtered,
            "data": result.data,
        })

    # -----------------------------------------------------------
    # 2) Sample Summary
    # -----------------------------------------------------------
    @bp.route("/sample_summary", methods=["GET", "POST"])
    @login_required
    @limiter.limit("100 per minute")
    async def sample_summary():
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

        samples = get_samples_with_results(exclude_archived=True, sort_by="full")
        summary_data = build_sample_summary_data(samples)

        from app.config.display_precision import DECIMAL_PLACES, DEFAULT_DECIMAL_PLACES
        precision_map = {code: dp for code, dp in DECIMAL_PLACES.items()}
        precision_map["_default"] = DEFAULT_DECIMAL_PLACES

        return render_template(
            "sample_summary.html",
            title="Sample Summary",
            samples=samples,
            analysis_types=summary_data["analysis_types"],
            results_map=summary_data["results_map"],
            analysis_dates_map=summary_data["analysis_dates_map"],
            precision_map=precision_map,
        )

    # -----------------------------------------------------------
    # 3) Sample Report
    # -----------------------------------------------------------
    @bp.route("/sample_report/<int:sample_id>")
    @login_required
    async def sample_report(sample_id):
        report_data = get_sample_report_data(sample_id)

        if report_data.error == "SAMPLE_NOT_FOUND":
            flash(_l("Дээж олдсонгүй."), "danger")
            return redirect(url_for("api.sample_summary"))

        if report_data.error:
            flash(
                f"{report_data.error}. Please check that required values (MT, Mad) are entered.",
                "danger",
            )
            return redirect(request.referrer or url_for("api.sample_summary"))

        return render_template(
            "report.html",
            title=f"Report: {report_data.sample.sample_code}",
            sample=report_data.sample,
            calcs=report_data.calculations,
            report_date=report_data.report_date,
        )

    # -----------------------------------------------------------
    # 4) Sample History
    # -----------------------------------------------------------
    @bp.route("/sample_history/<int:sample_id>")
    @login_required
    async def sample_history(sample_id):
        sample = db.session.get(Sample, sample_id)
        if not sample:
            abort(404)
        results = (
            AnalysisResult.query
            .options(joinedload(AnalysisResult.user))
            .filter_by(sample_id=sample_id)
            .order_by(AnalysisResult.created_at.desc())
            .all()
        )
        from app.repositories import AnalysisResultLogRepository
        logs = AnalysisResultLogRepository.get_for_sample(sample_id)
        return render_template(
            "sample_history.html",
            title=f"History: {sample.sample_code}",
            sample=sample,
            results=results,
            logs=logs,
        )

    # -----------------------------------------------------------
    # 5) Archive Hub
    # -----------------------------------------------------------
    @bp.route("/archive_hub", methods=["GET", "POST"])
    @login_required
    @limiter.limit("100 per minute")
    async def archive_hub():
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

        tree = get_archive_tree(
            selected_client=request.args.get("client"),
            selected_type=request.args.get("type"),
            selected_year=request.args.get("year", type=int),
            selected_month=request.args.get("month", type=int),
        )

        return render_template(
            "archive_hub.html",
            title="Archive Hub",
            tree_data=tree.tree_data,
            client_totals=tree.client_totals,
            total_archived=tree.total_archived,
            samples=tree.samples,
            results_map=tree.results_map,
            analysis_types=tree.analysis_types,
            selected_client=request.args.get("client"),
            selected_type=request.args.get("type"),
            selected_year=request.args.get("year", type=int),
            selected_month=request.args.get("month", type=int),
            month_names=MONTH_NAMES,
        )

    # -----------------------------------------------------------
    # 6) Dashboard Statistics API
    # -----------------------------------------------------------
    @bp.route("/dashboard_stats")
    @login_required
    async def api_dashboard_stats():
        stats = get_dashboard_stats()
        return jsonify({
            "samples_by_day": stats.samples_by_day,
            "samples_by_client": stats.samples_by_client,
            "analysis_by_status": stats.analysis_by_status,
            "approval_stats": stats.approval_stats,
            "today": stats.today,
        })

    # -----------------------------------------------------------
    # 7) Export to Excel
    # -----------------------------------------------------------
    @bp.route("/export/samples")
    @login_required
    async def export_samples():
        from app.utils.exports import create_sample_export, send_excel_response

        client = request.args.get("client")
        sample_type = request.args.get("type")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        limit = min(int(request.args.get("limit", 1000)), 5000)
        include_results = request.args.get("include_results", "false").lower() in ("1", "true", "yes")

        stmt = select(Sample).where(Sample.lab_type == "coal")
        if client:
            stmt = stmt.where(Sample.client_name == client)
        if sample_type:
            stmt = stmt.where(Sample.sample_type == sample_type)
        if start_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d")
                stmt = stmt.where(Sample.received_date >= sd)
            except ValueError:
                pass
        if end_date:
            try:
                ed = datetime.strptime(end_date, "%Y-%m-%d")
                ed = datetime.combine(ed, datetime.max.time())
                stmt = stmt.where(Sample.received_date <= ed)
            except ValueError:
                pass

        samples = list(db.session.execute(
            stmt.order_by(Sample.received_date.desc()).limit(limit)
        ).scalars().all())
        excel_data = create_sample_export(samples, _include_results=include_results)
        filename = f"samples_{now_local().strftime('%Y%m%d_%H%M')}.xlsx"
        return send_excel_response(excel_data, filename)

    @bp.route("/export/analysis")
    @login_required
    async def export_analysis():
        from app.utils.exports import create_analysis_export, send_excel_response
        from sqlalchemy.orm import joinedload as jl

        status = request.args.get("status")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        limit = min(int(request.args.get("limit", 1000)), 5000)

        stmt = select(AnalysisResult).options(
            jl(AnalysisResult.sample), jl(AnalysisResult.user)
        )
        if status:
            stmt = stmt.where(AnalysisResult.status == status)
        if start_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d")
                stmt = stmt.where(AnalysisResult.created_at >= sd)
            except ValueError:
                pass
        if end_date:
            try:
                ed = datetime.strptime(end_date, "%Y-%m-%d")
                ed = datetime.combine(ed, datetime.max.time())
                stmt = stmt.where(AnalysisResult.created_at <= ed)
            except ValueError:
                pass

        results = list(db.session.execute(
            stmt.order_by(AnalysisResult.created_at.desc()).limit(limit)
        ).scalars().all())
        excel_data = create_analysis_export(results)
        filename = f"analysis_{now_local().strftime('%Y%m%d_%H%M')}.xlsx"
        return send_excel_response(excel_data, filename)

    # -----------------------------------------------------------
    # HTMX Endpoints
    # -----------------------------------------------------------
    @bp.route("/sample_count", methods=["GET"])
    @login_required
    async def htmx_sample_count():
        count = db.session.execute(
            select(func.count(Sample.id)).where(Sample.lab_type == "coal")
        ).scalar_one()
        return f'<strong class="text-primary">{count}</strong> samples'

    @bp.route("/search_samples", methods=["GET"])
    @login_required
    async def htmx_search_samples():
        q = request.args.get("q", "").strip()
        if len(q) < 2:
            return '<div class="text-muted small">Enter 2+ characters</div>'

        safe_q = escape_like_pattern(q)
        samples = (
            Sample.query
            .filter(Sample.sample_code.ilike(f"%{safe_q}%"))
            .limit(10)
            .all()
        )

        if not samples:
            return '<div class="text-muted small">Not found</div>'

        html = '<div class="list-group list-group-flush">'
        for s in samples:
            html += (
                f'<a href="/sample/{s.id}" class="list-group-item list-group-item-action py-2">'
                f'<strong>{escape(s.sample_code or "")}</strong>'
                f'<small class="text-muted ms-2">{escape(s.client_name or "")}</small>'
                f"</a>"
            )
        html += "</div>"
        return html

    @bp.route("/sample_analysis_results/<int:sample_id>")
    @login_required
    async def sample_analysis_results(sample_id):
        results = list(db.session.execute(
            select(AnalysisResult)
            .where(AnalysisResult.sample_id == sample_id)
            .order_by(AnalysisResult.analysis_code)
        ).scalars().all())

        return jsonify({
            "success": True,
            "data": [
                {
                    "id": r.id,
                    "analysis_code": r.analysis_code,
                    "final_result": r.final_result,
                    "status": r.status,
                    "user": r.user.username if r.user else None,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else None,
                }
                for r in results
            ],
        })

    @bp.route("/search_samples_json", methods=["GET"])
    @login_required
    async def search_samples_json():
        q = request.args.get("q", "").strip()
        if len(q) < 2:
            return jsonify([])

        safe_q = escape_like_pattern(q)
        samples = (
            Sample.query
            .filter(Sample.sample_code.ilike(f"%{safe_q}%"))
            .order_by(Sample.received_date.desc())
            .limit(10)
            .all()
        )

        return jsonify([
            {
                "id": s.id,
                "sample_code": s.sample_code,
                "client_name": s.client_name or "",
                "lab_type": s.lab_type or "",
                "status": s.status or "",
            }
            for s in samples
        ])

    # -----------------------------------------------------------
    # MG Summary
    # -----------------------------------------------------------
    @bp.route("/mg_summary", methods=["GET", "POST"])
    @login_required
    async def mg_summary():
        # POST: Archive/Unarchive/Repeat
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            sample_ids = data.get("sample_ids", [])
            action = data.get("action", "archive")

            if sample_ids and action in ("archive", "unarchive"):
                result = archive_samples(sample_ids, archive=(action == "archive"))
                return jsonify({"success": result.success, "message": result.message})

            if sample_ids and action == "repeat":
                result = repeat_analyses(
                    sample_ids=sample_ids,
                    codes=data.get("codes", []),
                    user_role=getattr(current_user, "role", None),
                )
                if result.success:
                    status_code = 200
                elif "ахлах" in result.message:
                    status_code = 403
                elif "алдаа" in result.message:
                    status_code = 500
                else:
                    status_code = 400
                return jsonify({"success": result.success, "message": result.message}), status_code

            return jsonify({"success": False, "message": _("Буруу хүсэлт")}), 400

        # GET: MG summary data
        mg_data = get_mg_summary()
        return render_template(
            "mg_summary.html",
            title="MG Summary",
            samples=mg_data.samples,
            mg_data=mg_data.mg_data,
        )
