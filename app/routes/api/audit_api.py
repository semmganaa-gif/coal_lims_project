# app/routes/api/audit_api.py
# -*- coding: utf-8 -*-
"""
Аудиттай холбоотой API endpoints:
  - /audit_hub - Audit hub page
  - /audit_log/<analysis_code> - Audit log for specific analysis (шинэ загвар)
"""

from flask import (
    request,
    render_template,
)
from flask_login import login_required
from datetime import datetime
from app.utils.datetime import now_local
from app.utils.shifts import get_shift_date
from collections import defaultdict
import json

from app import db
from app.models import AnalysisResultLog, AnalysisType, Sample, User
from app.config.analysis_schema import get_analysis_schema
from app.utils.security import escape_like_pattern
from app.constants import ERROR_REASON_LABELS
from app.utils.shifts import get_shift_info
from app.utils.codes import norm_code


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
    # 2) АУДИТЫН МӨР ХУУДАС (Шинэ загвар - дээж бүрээр групплэсэн)
    # -----------------------------------------------------------
    @bp.route("/audit_log/<analysis_code>")
    @login_required
    def audit_log_page(analysis_code):
        # ✅ Normalize analysis code (Solid -> SOLID, St,ad -> TS г.м.)
        base_code = norm_code(analysis_code)

        # Analysis type олох
        analysis_type = AnalysisType.query.filter_by(code=analysis_code).first()
        if not analysis_type:
            analysis_type = type("FakeType", (), {"code": analysis_code, "name": analysis_code})()

        # Шүүлтүүрүүд
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        sample_name_str = request.args.get("sample_name")
        user_name_str = request.args.get("user_name")
        error_type_str = request.args.get("error_type")
        shift_str = request.args.get("shift")  # Ээлж: day, night, all

        # Default: Ээлжийн огноо
        today = get_shift_date()
        if not start_date_str:
            start_date_str = today.strftime("%Y-%m-%d")
        if not end_date_str:
            end_date_str = today.strftime("%Y-%m-%d")

        # Query - ✅ base_code ашиглах (DB-д normalized хэлбэрээр хадгалагдсан)
        q = (
            db.session.query(AnalysisResultLog, Sample, User)
            .join(Sample, AnalysisResultLog.sample_id == Sample.id)
            .join(User, AnalysisResultLog.user_id == User.id)
            .filter(AnalysisResultLog.analysis_code == base_code)
        )

        # Огноо шүүлтүүр
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                q = q.filter(AnalysisResultLog.timestamp >= start_date)
            except ValueError:
                pass
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                end_dt = datetime.combine(end_date, datetime.max.time())
                q = q.filter(AnalysisResultLog.timestamp <= end_dt)
            except ValueError:
                pass

        # Дээжний нэр шүүлтүүр
        if sample_name_str:
            safe_sample = escape_like_pattern(sample_name_str)
            q = q.filter(Sample.sample_code.ilike(f"%{safe_sample}%"))

        # Химичийн нэр шүүлтүүр
        if user_name_str:
            safe_user = escape_like_pattern(user_name_str)
            q = q.filter(User.username.ilike(f"%{safe_user}%"))

        # Алдааны төрөл шүүлтүүр
        if error_type_str and error_type_str != "all":
            q = q.filter(AnalysisResultLog.error_reason == error_type_str)

        # Ээлжийн шүүлтүүр (08:00-20:00 = өдөр, 20:00-08:00 = шөнө)
        if shift_str == "day":
            from sqlalchemy import extract
            q = q.filter(extract('hour', AnalysisResultLog.timestamp).between(8, 19))
        elif shift_str == "night":
            from sqlalchemy import extract, or_
            q = q.filter(or_(
                extract('hour', AnalysisResultLog.timestamp) >= 20,
                extract('hour', AnalysisResultLog.timestamp) < 8
            ))

        rows = q.order_by(AnalysisResultLog.timestamp.asc()).all()

        # ========== Дээж бүрээр групплэх ==========
        sample_groups = defaultdict(lambda: {
            "sample": None,
            "attempts": [],  # Оролдлого бүр
            "retry_count": 0,
            "has_rejection": False,
            "final_status": None,
        })

        for log_obj, sample_obj, user_obj in rows:
            sid = log_obj.sample_id
            group = sample_groups[sid]
            group["sample"] = sample_obj
            # ✅ Дээжний код snapshot (sample устсан ч харагдана)
            if log_obj.sample_code_snapshot:
                group["sample_code_snapshot"] = log_obj.sample_code_snapshot

            # Raw data parse
            try:
                raw_data = json.loads(log_obj.raw_data_snapshot or "{}")
            except Exception:
                raw_data = {}

            # Ээлжийн мэдээлэл тооцоолох
            shift_info = get_shift_info(log_obj.timestamp)

            # ✅ Анхны химичийн мэдээлэл олох
            original_user = None
            if log_obj.original_user_id:
                original_user = User.query.get(log_obj.original_user_id)

            attempt = {
                "id": log_obj.id,
                "timestamp": log_obj.timestamp,
                "user": user_obj,
                "action": log_obj.action,
                "raw_data": raw_data,
                "final_result": log_obj.final_result_snapshot,
                "reason": log_obj.reason,
                "error_reason": log_obj.error_reason,
                "rejection_category": getattr(log_obj, 'rejection_category', None),
                "shift_team": shift_info.team,  # A, B, C
                "shift_type": shift_info.shift_type,  # day, night
                # ✅ ШИНЭ: Анхны мэдээлэл
                "original_user": original_user,
                "original_timestamp": log_obj.original_timestamp,
                # ✅ ШИНЭ: Hash (өөрчлөгдсөн эсэхийг шалгах)
                "data_hash": log_obj.data_hash,
                "hash_valid": log_obj.verify_hash() if log_obj.data_hash else None,
            }
            group["attempts"].append(attempt)

            # Тоолох
            if log_obj.action in ("REJECTED", "CREATED_REJECTED", "UPDATED_REJECTED"):
                group["has_rejection"] = True
                group["retry_count"] += 1

            # Эцсийн статус
            group["final_status"] = log_obj.action

        # List болгох + эрэмбэлэх (сүүлд өөрчлөгдсөн эхэнд)
        grouped_list = []
        for sid, group in sample_groups.items():
            if group["attempts"]:
                group["last_timestamp"] = group["attempts"][-1]["timestamp"]
                grouped_list.append(group)

        grouped_list.sort(key=lambda x: x["last_timestamp"], reverse=True)

        # Статистик
        stats = {
            "total_samples": len(grouped_list),
            "with_retries": sum(1 for g in grouped_list if g["retry_count"] > 0),
            "approved": sum(1 for g in grouped_list if "APPROVED" in (g["final_status"] or "")),
            "pending": sum(1 for g in grouped_list if "PENDING" in (g["final_status"] or "")),
            "rejected": sum(1 for g in grouped_list if g["final_status"] in ("REJECTED",)),
        }

        # Химичийн жагсаалт (шүүлтүүрт ашиглах)
        all_users = User.query.filter(User.role.in_(["chemist", "senior", "manager", "admin"])).all()

        return render_template(
            "audit_log_page.html",
            title=f"Аудит: {analysis_type.name}",
            analysis_type=analysis_type,
            grouped_samples=grouped_list,
            stats=stats,
            error_labels=ERROR_REASON_LABELS,
            all_users=all_users,
            analysis_schema=get_analysis_schema(base_code),  # ✅ base_code ашиглах
        )

    # -----------------------------------------------------------
    # 3) АУДИТ ХАЙЛТ API
    # -----------------------------------------------------------
    @bp.route("/audit_search")
    @login_required
    def api_audit_search():
        """
        Бүх шинжилгээнээс аудит хайх API

        Parameters:
            - q: Хайлтын үг (дээжний код, химичийн нэр)
            - start_date, end_date: Огнооны хязгаар
            - analysis_code: Шинжилгээний код
            - action: Үйлдлийн төрөл (APPROVED, REJECTED, etc)
            - limit: Хязгаар (default 100, max 500)
        """
        from flask import jsonify

        q = request.args.get('q', '').strip()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        analysis_code = request.args.get('analysis_code')
        action = request.args.get('action')
        limit = min(int(request.args.get('limit', 100)), 500)

        query = db.session.query(
            AnalysisResultLog, Sample, User
        ).join(
            Sample, AnalysisResultLog.sample_id == Sample.id
        ).join(
            User, AnalysisResultLog.user_id == User.id
        )

        # Хайлтын үг
        if q:
            from sqlalchemy import or_
            safe_q = escape_like_pattern(q)
            query = query.filter(or_(
                Sample.sample_code.ilike(f"%{safe_q}%"),
                User.username.ilike(f"%{safe_q}%"),
                AnalysisResultLog.analysis_code.ilike(f"%{safe_q}%")
            ))

        # Огноо шүүлтүүр
        if start_date:
            try:
                sd = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(AnalysisResultLog.timestamp >= sd)
            except ValueError:
                pass
        if end_date:
            try:
                ed = datetime.strptime(end_date, '%Y-%m-%d')
                ed = datetime.combine(ed, datetime.max.time())
                query = query.filter(AnalysisResultLog.timestamp <= ed)
            except ValueError:
                pass

        # Шинжилгээний код
        if analysis_code:
            query = query.filter(AnalysisResultLog.analysis_code == norm_code(analysis_code))

        # Үйлдэл
        if action:
            query = query.filter(AnalysisResultLog.action.ilike(f"%{action}%"))

        results = query.order_by(AnalysisResultLog.timestamp.desc()).limit(limit).all()

        return jsonify({
            "count": len(results),
            "results": [
                {
                    "id": log.id,
                    "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else None,
                    "sample_code": sample.sample_code,
                    "analysis_code": log.analysis_code,
                    "action": log.action,
                    "user": user.username,
                    "final_result": log.final_result_snapshot,
                    "reason": log.reason,
                    "error_reason": log.error_reason,
                }
                for log, sample, user in results
            ]
        })

    # -----------------------------------------------------------
    # 4) АУДИТ EXPORT
    # -----------------------------------------------------------
    @bp.route("/export/audit")
    @login_required
    def export_audit():
        """Аудит логийг Excel экспорт"""
        from app.utils.exports import send_excel_response
        from app.models import AuditLog

        # Query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        action = request.args.get('action')
        limit = min(int(request.args.get('limit', 1000)), 5000)

        query = AuditLog.query

        if start_date:
            try:
                sd = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(AuditLog.timestamp >= sd)
            except ValueError:
                pass
        if end_date:
            try:
                ed = datetime.strptime(end_date, '%Y-%m-%d')
                ed = datetime.combine(ed, datetime.max.time())
                query = query.filter(AuditLog.timestamp <= ed)
            except ValueError:
                pass
        if action:
            query = query.filter(AuditLog.action.ilike(f"%{action}%"))

        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

        # Excel export
        from app.utils.exports import create_audit_export
        excel_data = create_audit_export(logs)
        filename = f"audit_log_{now_local().strftime('%Y%m%d_%H%M')}.xlsx"

        return send_excel_response(excel_data, filename)
