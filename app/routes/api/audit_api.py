# app/routes/api/audit_api.py
# -*- coding: utf-8 -*-
"""
Аудиттай холбоотой API endpoints:
  - /audit_hub - Audit hub page
  - /audit_log/<analysis_code> - Audit log for specific analysis
"""

from flask import (
    request,
    render_template,
    flash,
)
from flask_login import login_required
from datetime import datetime
import json

from app import db
from app.models import AnalysisResult, AnalysisResultLog, AnalysisType, Sample, User
from app.utils.normalize import normalize_raw_data
from app.config.analysis_schema import get_analysis_schema
from app.utils.security import escape_like_pattern


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # -----------------------------------------------------------
    # 1) АУДИТЫН ТӨВ
    # -----------------------------------------------------------
    @bp.route("/audit_hub")
    @login_required
    def audit_hub():
        return render_template("audit_hub.html", title="Аудитын мөр")

    # -----------------------------------------------------------
    # 2) АУДИТЫН МӨР ХУУДАС
    # -----------------------------------------------------------
    @bp.route("/audit_log/<analysis_code>")
    @login_required
    def audit_log_page(analysis_code):
        try:
            analysis_type = AnalysisType.query.filter_by(code=analysis_code).first_or_404()
        except Exception:
            first_res = (
                AnalysisResult.query.filter_by(analysis_code=analysis_code).first()
            )
            if first_res:
                analysis_type = type(
                    "FakeType",
                    (object,),
                    {"code": analysis_code, "name": first_res.analysis_code},
                )()
            else:
                analysis_type = type(
                    "FakeType",
                    (object,),
                    {"code": analysis_code, "name": analysis_code},
                )()

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        sample_name_str = request.args.get("sample_name")
        user_name_str = request.args.get("user_name")

        q = (
            db.session.query(AnalysisResultLog, Sample, User)
            .join(Sample, AnalysisResultLog.sample_id == Sample.id)
            .join(User, AnalysisResultLog.user_id == User.id)
            .filter(AnalysisResultLog.analysis_code == analysis_code)
        )

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                q = q.filter(AnalysisResultLog.timestamp >= start_date)
            except ValueError:
                flash("Буруу эхлэх огноо.", "warning")
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                end_dt = datetime.combine(end_date, datetime.max.time())
                q = q.filter(AnalysisResultLog.timestamp <= end_dt)
            except ValueError:
                flash("Буруу дуусах огноо.", "warning")
        if sample_name_str:
            safe_sample = escape_like_pattern(sample_name_str)
            q = q.filter(Sample.sample_code.ilike(f"%{safe_sample}%"))
        if user_name_str:
            safe_user = escape_like_pattern(user_name_str)
            q = q.filter(User.username.ilike(f"%{safe_user}%"))

        rows = q.order_by(AnalysisResultLog.timestamp.desc()).all()

        prepared_logs = []
        for log_obj, sample_obj, user_obj in rows:
            view_obj = type("AuditView", (), {})()
            view_obj.id = log_obj.id
            view_obj.sample_id = log_obj.sample_id
            view_obj.analysis_result_id = log_obj.analysis_result_id
            view_obj.analysis_code = log_obj.analysis_code
            view_obj.action = log_obj.action
            view_obj.final_result_snapshot = log_obj.final_result_snapshot
            view_obj.raw_data_snapshot = log_obj.raw_data_snapshot
            view_obj.reason = log_obj.reason
            view_obj.timestamp = log_obj.timestamp
            view_obj.sample = sample_obj
            view_obj.user = user_obj
            prepared_logs.append(view_obj)

        def get_log_raw_data(log):
            try:
                parsed = json.loads(log.raw_data_snapshot or "{}")
            except Exception:
                parsed = {}
            return normalize_raw_data(parsed, analysis_type.code)

        return render_template(
            "audit_log_page.html",
            title=f"Аудит: {analysis_type.name}",
            analysis_type=analysis_type,
            logs=prepared_logs,
            get_log_raw_data=get_log_raw_data,
            analysis_schema=get_analysis_schema(analysis_type.code),
        )
