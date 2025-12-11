# app/routes/api/mass_api.py
# -*- coding: utf-8 -*-
"""
Массын ажлын талбартай холбоотой API endpoints:
  - /mass/update_sample_status - Archive/unarchive samples
  - /mass/eligible - Get eligible samples for mass workspace
  - /mass/save - Save mass measurements
  - /mass/update_weight - Update sample weight
  - /mass/unready - Mark samples as not ready
  - /mass/delete - Delete samples
"""

from flask import (
    request,
    jsonify,
    url_for,
    redirect,
    current_app,
)
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError

from app.utils.security import escape_like_pattern

from app import db, limiter
from app.models import Sample
from app.utils.datetime import now_local
from .helpers import _has_m_task_sql, _can_delete_sample, api_ok, api_fail


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # -----------------------------------------------------------
    # 1) МАССЫН АЖЛЫН ТАЛБАР (архив/сэргээлт)
    # -----------------------------------------------------------
    @bp.route("/mass/update_sample_status", methods=["POST"])
    @login_required
    @limiter.limit("30 per minute")
    def update_sample_status():
        action = request.form.get("action")
        sample_ids = request.form.getlist("sample_ids")

        if not sample_ids:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"message": "Дээж сонгогдоогүй"}), 400
            return redirect(url_for("api.sample_summary"))

        try:
            sample_ids_int = [int(sid) for sid in sample_ids]
        except ValueError:
            sample_ids_int = []

        samples = Sample.query.filter(Sample.id.in_(sample_ids_int)).all()
        count = 0
        for s in samples:
            if action == "archive":
                s.status = "archived"
                count += 1
            elif action == "unarchive":
                s.status = "new"
                count += 1

        db.session.commit()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"message": f"{count} дээжийн статус шинэчлэгдлээ."}), 200

        return redirect(url_for("api.sample_summary"))

    # ===========================================================
    # 2) 🆕 Массын ажлын талбар (+ delete / unready / update)
    # ===========================================================

    @bp.route("/mass/eligible", methods=["GET"])
    @login_required
    @limiter.limit("30 per minute")
    def mass_eligible():
        """
        Массын ажлын талбарт харагдах дээжүүд:
          - status ∈ {"new","New"}
          - analyses_to_perform дотор "m" байгаа
          - include_ready=0 (default) үед mass_ready != True л гарна
          - include_ready=1 үед mass_ready == True мөрүүдийг ч хамт харуулна (саарал badge)
          - q=<sample_code> хайлт
        """
        include_ready = request.args.get("include_ready", "0") in ("1", "true", "True")
        q_text = (request.args.get("q") or "").strip()

        base_filters = [
            Sample.status.in_(["new", "New"]),
            _has_m_task_sql(),
        ]

        if not include_ready:
            base_filters.append(
                or_(Sample.mass_ready.is_(False), Sample.mass_ready.is_(None))
            )

        q = Sample.query.filter(and_(*base_filters))

        if q_text:
            safe_text = escape_like_pattern(q_text)
            q = q.filter(Sample.sample_code.ilike(f"%{safe_text}%"))

        rows = q.order_by(Sample.received_date.desc()).limit(400).all()

        return jsonify(
            {
                "samples": [
                    {
                        "id": s.id,
                        "sample_code": s.sample_code or "",
                        "client_name": s.client_name or "",
                        "sample_type": s.sample_type or "",
                        "weight": s.weight,
                        "received_date": s.received_date.strftime("%Y-%m-%d %H:%M")
                        if s.received_date
                        else "",
                        "mass_ready": bool(getattr(s, "mass_ready", False)),
                    }
                    for s in rows
                ]
            }
        )

    @bp.route("/mass/save", methods=["POST"])
    @login_required
    @limiter.limit("30 per minute")
    def mass_save():
        """
        Payload:
        {
          "items": [{"sample_id": 123, "weight": 2500.0}, ...],
          "mark_ready": true   # default: true
        }
        """
        data = request.get_json(silent=True) or {}
        items = data.get("items") or []
        mark_ready = bool(data.get("mark_ready", True))

        if not items:
            return api_fail("Хадгалах мөр олдсонгүй.")

        user_id = getattr(current_user, "id", None)
        now_ts = now_local()

        # ✅ N+1 query асуудал засварлах: Бүх sample-г нэг query-гээр авах
        sample_ids = [it.get("sample_id") for it in items if it.get("sample_id")]
        if not sample_ids:
            return api_fail("Хүчинтэй ID олдсонгүй.")

        # Bulk load: Нэг query-гээр бүх sample-г татна
        samples_map = {s.id: s for s in Sample.query.filter(Sample.id.in_(sample_ids)).all()}

        # Items-ийг map-аар давтаж шинэчилнэ
        weight_map = {it.get("sample_id"): it.get("weight") for it in items if "weight" in it}

        updated = []
        for sid in sample_ids:
            s = samples_map.get(sid)
            if not s:
                continue

            # weight шинэчлэх (гр → кг хөрвүүлэлт)
            if sid in weight_map and isinstance(weight_map[sid], (int, float)):
                weight_g = float(weight_map[sid])
                s.weight = round(weight_g / 1000, 3)  # гр → кг

            # mass_ready тэмдэглэх эсэх
            if mark_ready:
                s.mass_ready = True
                s.mass_ready_at = now_ts
                s.mass_ready_by_id = user_id

            db.session.add(s)
            updated.append(sid)

        if not updated:
            return api_fail("Мөрүүд хүчинтэй биш байна.")

        try:
            db.session.commit()
            return api_ok(f"{len(updated)} дээж шинэчлэгдлээ.", updated_ids=updated)
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error in mass_save: {e}")
            return api_fail("Өгөгдлийн конфликт гарлаа", 409)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in mass_save: {e}")
            return api_fail("Өгөгдөл хадгалахад алдаа гарлаа", 500)

    @bp.route("/mass/update_weight", methods=["POST"])
    @login_required
    @limiter.limit("30 per minute")
    def mass_update_weight():
        """
        Mass Ready болсон байсан ч зөвхөн жинг нь засаж хадгална.
        Payload: {"sample_id": 123, "weight": 1800}
        """
        data = request.get_json(silent=True) or {}
        sid = data.get("sample_id")
        w = data.get("weight")
        if not sid or not isinstance(w, (int, float)):
            return api_fail("Параметр дутуу.")

        s = db.session.get(Sample, sid)
        if not s:
            return api_fail("Дээж олдсонгүй.", 404)

        # гр → кг хөрвүүлэлт
        weight_g = float(w)
        s.weight = round(weight_g / 1000, 3)  # гр → кг
        s.received_date = s.received_date or now_local()  # хоосон байсан тохиолдолд
        db.session.add(s)

        try:
            db.session.commit()
            return api_ok("Жин шинэчлэгдлээ.", sample_id=s.id)
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error in mass_update_weight: {e}")
            return api_fail("Өгөгдлийн конфликт гарлаа", 409)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in mass_update_weight: {e}")
            return api_fail("Өгөгдөл хадгалахад алдаа гарлаа", 500)

    @bp.route("/mass/unready", methods=["POST"])
    @login_required
    @limiter.limit("30 per minute")
    def mass_unready():
        """
        mass_ready-г буцааж false болгоно.
        Payload: {"sample_ids":[1,2,3]}
        """
        data = request.get_json(silent=True) or {}
        ids = data.get("sample_ids") or []
        if not ids:
            return api_fail("ID ирсэнгүй.")

        rows = Sample.query.filter(Sample.id.in_(ids)).all()
        for s in rows:
            s.mass_ready = False
            s.mass_ready_at = None
            s.mass_ready_by_id = None
            db.session.add(s)

        try:
            db.session.commit()
            return api_ok(f"{len(rows)} дээжийг Unready болголоо.")
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error in mass_unready: {e}")
            return api_fail("Өгөгдлийн конфликт гарлаа", 409)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in mass_unready: {e}")
            return api_fail("Өгөгдөл хадгалахад алдаа гарлаа", 500)

    @bp.route("/mass/delete", methods=["POST"])
    @login_required
    @limiter.limit("20 per minute")
    def mass_delete():
        """
        Дээжийг бүртгэлээс бүр мөсөн устгана (каскадтай).
        Payload: {"sample_id": 123}
        Зөвхөн admin/ahlah.
        """
        if not _can_delete_sample():
            return api_fail("Энэ үйлдэлд эрх хүрэхгүй.", 403)

        data = request.get_json(silent=True) or {}
        sid = data.get("sample_id")
        if not sid:
            return api_fail("ID дутуу.")

        s = db.session.get(Sample, sid)
        if not s:
            return api_fail("Дээж олдсонгүй.", 404)

        db.session.delete(s)

        try:
            db.session.commit()
            return api_ok("Дээж устгагдлаа.", deleted_id=sid)
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error in mass_delete: {e}")
            return api_fail("Өгөгдөл устгах боломжгүй (холбоотой бичлэгүүд байна)", 409)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in mass_delete: {e}")
            return api_fail("Өгөгдөл устгахад алдаа гарлаа", 500)
