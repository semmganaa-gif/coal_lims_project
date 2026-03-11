# app/routes/api/audit_api.py
# -*- coding: utf-8 -*-
"""
Аудиттай холбоотой API endpoints:
  - /audit_hub - Audit hub page
  - /audit_log/<analysis_code> - Audit log for specific analysis (шинэ загвар)
"""

import asyncio
import json

from collections import defaultdict
from datetime import datetime

from flask import request, jsonify, render_template
from flask_login import login_required, current_user
from sqlalchemy import extract, or_
from sqlalchemy.orm import joinedload

from app import db
from app.models import (
    AnalysisResult, AnalysisResultLog, AnalysisType,
    AuditLog, Sample, User,
)
from app.repositories import AnalysisTypeRepository
from app.config.analysis_schema import get_analysis_schema
from app.constants import ERROR_REASON_LABELS
from app.utils.codes import norm_code
from app.utils.datetime import now_local
from app.utils.security import escape_like_pattern
from app.utils.shifts import get_shift_date, get_shift_info


def _audit_admin_required(f):
    """Аудит хуудсуудад зөвхөн admin эрхтэй хэрэглэгч хандана."""
    from functools import wraps
    from flask import abort

    @wraps(f)
    async def decorated(*args, **kwargs):
        if getattr(current_user, "role", None) != "admin":
            abort(403)
        return await f(*args, **kwargs)
    return decorated


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # -----------------------------------------------------------
    # 1) АУДИТЫН ТӨВ
    # -----------------------------------------------------------
    @bp.route("/audit_hub")
    @login_required
    @_audit_admin_required
    async def audit_hub():
        return render_template("audit_hub.html", title="Аудитын мөр")

    # -----------------------------------------------------------
    # 2) АУДИТЫН МӨР ХУУДАС (Шинэ загвар - дээж бүрээр групплэсэн)
    # -----------------------------------------------------------
    @bp.route("/audit_log/<analysis_code>")
    @login_required
    @_audit_admin_required
    async def audit_log_page(analysis_code):
        # Normalize analysis code (Solid -> SOLID, St,ad -> TS г.м.)
        base_code = norm_code(analysis_code)

        # Analysis type олох
        analysis_type = AnalysisTypeRepository.get_by_code(analysis_code)
        if not analysis_type:
            from dataclasses import dataclass as _dc

            @_dc
            class _AnalysisTypeStub:
                code: str
                name: str
            analysis_type = _AnalysisTypeStub(code=analysis_code, name=analysis_code)

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

        # Query - base_code ашиглах (DB-д normalized хэлбэрээр хадгалагдсан)
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
            q = q.filter(extract('hour', AnalysisResultLog.timestamp).between(8, 19))
        elif shift_str == "night":
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

        # N+1 query-ээс сэргийлж original_user-уудыг нэг query-гээр авах
        original_user_ids = {
            log_obj.original_user_id for log_obj, _, _ in rows
            if log_obj.original_user_id
        }
        original_users_map = {}
        if original_user_ids:
            original_users_map = {
                u.id: u for u in User.query.filter(User.id.in_(original_user_ids)).all()
            }

        for log_obj, sample_obj, user_obj in rows:
            sid = log_obj.sample_id
            group = sample_groups[sid]
            group["sample"] = sample_obj
            # Дээжний код snapshot (sample устсан ч харагдана)
            if log_obj.sample_code_snapshot:
                group["sample_code_snapshot"] = log_obj.sample_code_snapshot

            # Raw data parse
            try:
                raw_data = json.loads(log_obj.raw_data_snapshot or "{}")
            except (json.JSONDecodeError, TypeError):
                raw_data = {}

            # Ээлжийн мэдээлэл тооцоолох
            shift_info = get_shift_info(log_obj.timestamp)

            # Анхны химичийн мэдээлэл
            original_user = original_users_map.get(log_obj.original_user_id) if log_obj.original_user_id else None

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
                "original_user": original_user,
                "original_timestamp": log_obj.original_timestamp,
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

        # Дээж бүрийн одоогийн AnalysisResult дээр _repeat байгаа эсэх
        for group in grouped_list:
            sample = group.get("sample")
            if sample:
                current_res = (
                    AnalysisResult.query
                    .filter_by(sample_id=sample.id, analysis_code=base_code)
                    .first()
                )
                if current_res:
                    raw = current_res.get_raw_data()
                    repeat_info = raw.get("_repeat")
                    if repeat_info:
                        group["repeat_info"] = {
                            "result_id": current_res.id,
                            "original_final_result": repeat_info.get("original_final_result"),
                            "repeat_final_result": repeat_info.get("repeat_final_result"),
                            "use_original": repeat_info.get("use_original", False),
                            "repeated_at": repeat_info.get("repeated_at"),
                            "current_final_result": current_res.final_result,
                        }

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

        is_senior = getattr(current_user, "role", "") in ("senior", "admin")

        return render_template(
            "audit_log_page.html",
            title=f"Аудит: {analysis_type.name}",
            analysis_type=analysis_type,
            grouped_samples=grouped_list,
            stats=stats,
            error_labels=ERROR_REASON_LABELS,
            all_users=all_users,
            analysis_schema=get_analysis_schema(base_code),
            is_senior=is_senior,
        )

    # -----------------------------------------------------------
    # 3) АУДИТ ХАЙЛТ API
    # -----------------------------------------------------------
    @bp.route("/audit_search")
    @login_required
    @_audit_admin_required
    async def api_audit_search():
        """
        Бүх шинжилгээнээс аудит хайх API

        Parameters:
            - q: Хайлтын үг (дээжний код, химичийн нэр)
            - start_date, end_date: Огнооны хязгаар
            - analysis_code: Шинжилгээний код
            - action: Үйлдлийн төрөл (APPROVED, REJECTED, etc)
            - limit: Хязгаар (default 100, max 500)
        """
        q = request.args.get('q', '').strip()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        analysis_code = request.args.get('analysis_code')
        action = request.args.get('action')
        try:
            limit = min(int(request.args.get('limit', 100)), 500)
        except (ValueError, TypeError):
            limit = 100

        query = db.session.query(
            AnalysisResultLog, Sample, User
        ).join(
            Sample, AnalysisResultLog.sample_id == Sample.id
        ).join(
            User, AnalysisResultLog.user_id == User.id
        )

        # Хайлтын үг
        if q:
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
            safe_action = escape_like_pattern(action)
            query = query.filter(AnalysisResultLog.action.ilike(f"%{safe_action}%", escape='\\'))

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
    @_audit_admin_required
    async def export_audit():
        """Аудит логийг Excel экспорт"""
        from app.utils.exports import send_excel_response

        # Query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        action = request.args.get('action')
        try:
            limit = min(int(request.args.get('limit', 1000)), 5000)
        except (ValueError, TypeError):
            limit = 1000

        query = AuditLog.query.options(joinedload(AuditLog.user))

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
            safe_action = escape_like_pattern(action)
            query = query.filter(AuditLog.action.ilike(f"%{safe_action}%", escape='\\'))

        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

        # Excel export
        from app.utils.exports import create_audit_export
        excel_data = create_audit_export(logs)
        filename = f"audit_log_{now_local().strftime('%Y%m%d_%H%M')}.xlsx"

        return send_excel_response(excel_data, filename)

    # -----------------------------------------------------------
    # 5) СИСТЕМИЙН АУДИТ ХУУДАС
    # -----------------------------------------------------------
    @bp.route("/system_audit")
    @login_required
    @_audit_admin_required
    async def system_audit():
        """Системийн аудит лог — login, logout, delete, approve гэх мэт."""
        # JSON API хүсэлт (AG-Grid-ээс)
        if request.args.get('format') == 'json':
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            action_filter = request.args.get('action')
            user_filter = request.args.get('user_id')
            resource_filter = request.args.get('resource_type')
            q = request.args.get('q', '').strip()
            try:
                limit = min(int(request.args.get('limit', 500)), 2000)
            except (ValueError, TypeError):
                limit = 500

            query = AuditLog.query.options(joinedload(AuditLog.user))

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

            if action_filter:
                safe_action = escape_like_pattern(action_filter)
                query = query.filter(AuditLog.action.ilike(f"%{safe_action}%", escape='\\'))

            if user_filter:
                try:
                    query = query.filter(AuditLog.user_id == int(user_filter))
                except ValueError:
                    pass

            if resource_filter:
                safe_res = escape_like_pattern(resource_filter)
                query = query.filter(AuditLog.resource_type.ilike(f"%{safe_res}%", escape='\\'))

            if q:
                safe_q = escape_like_pattern(q)
                query = query.filter(or_(
                    AuditLog.action.ilike(f"%{safe_q}%", escape='\\'),
                    AuditLog.resource_type.ilike(f"%{safe_q}%", escape='\\'),
                    AuditLog.details.ilike(f"%{safe_q}%", escape='\\'),
                    AuditLog.ip_address.ilike(f"%{safe_q}%", escape='\\'),
                ))

            logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

            return jsonify({
                'success': True,
                'data': [
                    {
                        'id': log.id,
                        'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else None,
                        'user': log.user.username if log.user else '-',
                        'user_id': log.user_id,
                        'action': log.action,
                        'resource_type': log.resource_type or '-',
                        'resource_id': log.resource_id,
                        'details': log.details or '',
                        'ip_address': log.ip_address or '-',
                        'user_agent': log.user_agent or '',
                        'hash_valid': log.verify_hash() if log.data_hash else None,
                    }
                    for log in logs
                ],
                'count': len(logs),
            })

        # HTML хуудас
        # Хэрэглэгчдийн жагсаалт (шүүлтүүрт)
        users = User.query.filter(
            User.role.in_(['chemist', 'senior', 'manager', 'admin'])
        ).order_by(User.username).all()

        return render_template(
            "system_audit.html",
            title="Системийн аудит",
            users=users,
            use_aggrid=True,
        )
