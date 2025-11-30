# app/routes/equipment_routes.py
# -*- coding: utf-8 -*-

import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Equipment, MaintenanceLog, UsageLog
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_
from sqlalchemy.exc import IntegrityError

equipment_bp = Blueprint("equipment", __name__)

# File upload constraints
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt'}

# -------------------------------------------------
# 1. Төхөөрөмжийн жагсаалт
# -------------------------------------------------
@equipment_bp.route("/equipment_list")
@login_required
def equipment_list():
    today = datetime.now().date()
    warning_date = today + timedelta(days=30)
    view = request.args.get("view", "all")
    page = request.args.get("page", 1, type=int)
    per_page = 50  # Хуудас тутамд харуулах тоо

    query = Equipment.query

    # View шүүлтүүрүүд
    if view == "retired":
        query = query.filter(Equipment.status == "retired")
    elif view == "spares":
        query = query.filter(Equipment.status.in_(["needs_spare", "broken"]))
    elif view != "all":
        # Хэрэв view нь category-тай таарч байвал шүүнэ
        query = query.filter(Equipment.category == view)

    # "Retired" төлөвтэйг үндсэн жагсаалтад харуулахгүй байх (хэрэв тусгайлан retired-ийг сонгоогүй бол)
    if view != "retired":
        query = query.filter(Equipment.status != "retired")

    # ✅ Pagination нэмсэн: Бүх төхөөрөмжийг нэг дор уншихгүй байх
    pagination = query.order_by(Equipment.name.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    equipments = pagination.items

    # Тоолох логик (Optional: Tab дээр тоо харуулахад хэрэгтэй бол энд нэмж болно)
    view_counts = {}

    return render_template(
        "equipment_list.html",
        equipments=equipments,
        pagination=pagination,
        today=today,
        warning_date=warning_date,
        view=view,
        view_counts=view_counts,
    )

# -------------------------------------------------
# 2. Дэлгэрэнгүй & CRUD
# -------------------------------------------------
@equipment_bp.route("/equipment/<int:id>")
@login_required
def equipment_detail(id):
    eq = Equipment.query.get_or_404(id)
    return render_template("equipment_detail.html", eq=eq)

@equipment_bp.route("/add_equipment", methods=["POST"])
@login_required
def add_equipment():
    if current_user.role not in ["ahlah", "admin"]:
        flash("Эрх хүрэхгүй.", "danger"); return redirect(url_for("equipment.equipment_list"))

    # Form data with validation
    try:
        quantity = int(request.form.get("quantity", "1"))
        if quantity <= 0:
            raise ValueError("Тоо ширхэг эерэг тоо байх ёстой")
    except ValueError as e:
        flash(f"Буруу тоо ширхэг: {e}", "error")
        return redirect(url_for("equipment.equipment_list"))

    try:
        calibration_cycle_days = int(request.form.get("cycle", "365"))
        if calibration_cycle_days <= 0:
            raise ValueError("Калибрацийн мөчлөг эерэг тоо байх ёстой")
    except ValueError as e:
        flash(f"Буруу калибрацийн мөчлөг: {e}", "error")
        return redirect(url_for("equipment.equipment_list"))

    new_eq = Equipment(
        name = request.form.get("name"),
        manufacturer = request.form.get("manufacturer"),
        model = request.form.get("model"),
        serial_number = request.form.get("serial"),
        lab_code = request.form.get("lab_code"),
        quantity = quantity,
        calibration_cycle_days = calibration_cycle_days,
        location = request.form.get("location"),
        room_number = request.form.get("room"),
        related_analysis = request.form.get("related"),
        calibration_note = request.form.get("calibration_note"),
        status = "normal",
        category = request.form.get("category") or "other"
    )
    db.session.add(new_eq)
    db.session.commit()
    flash("Амжилттай бүртгэгдлээ", "success")
    return redirect(url_for("equipment.equipment_list"))

@equipment_bp.route("/edit_equipment/<int:id>", methods=["POST"])
@login_required
def edit_equipment(id):
    if current_user.role not in ["ahlah", "admin"]:
        flash("Эрх хүрэхгүй.", "danger"); return redirect(url_for("equipment.equipment_detail", id=id))

    eq = Equipment.query.get_or_404(id)
    eq.name = request.form.get("name")
    eq.manufacturer = request.form.get("manufacturer")
    eq.model = request.form.get("model")
    if request.form.get("serial"): eq.serial_number = request.form.get("serial")
    eq.lab_code = request.form.get("lab_code")
    eq.location = request.form.get("location")
    eq.room_number = request.form.get("room")
    eq.related_analysis = request.form.get("related")

    # Input validation for calibration cycle
    if request.form.get("cycle"):
        try:
            cycle_value = int(request.form.get("cycle"))
            if cycle_value <= 0:
                raise ValueError("Калибрацийн мөчлөг эерэг тоо байх ёстой")
            eq.calibration_cycle_days = cycle_value
        except ValueError as e:
            flash(f"Буруу калибрацийн мөчлөг: {e}", "error")
            return redirect(url_for("equipment.equipment_detail", id=id))

    if request.form.get("status"): eq.status = request.form.get("status")
    eq.calibration_note = request.form.get("calibration_note")
    eq.remark = request.form.get("remark")
    eq.category = request.form.get("category") or "other"

    try:
        db.session.commit()
        flash("Шинэчлэгдлээ.", "success")
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"IntegrityError in edit_equipment: {e}")
        flash("Өгөгдлийн конфликт гарлаа (давхардсан утга).", "danger")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in edit_equipment: {e}")
        flash(f"Алдаа гарлаа: {str(e)[:100]}", "danger")
    return redirect(url_for("equipment.equipment_detail", id=id))

# --- SINGLE DELETE (Ганцаарчилж устгах) ---
@equipment_bp.route("/equipment/delete/<int:id>", methods=["POST"])
@login_required
def delete_equipment(id):
    if current_user.role not in ["ahlah", "admin"]:
        flash("Эрх хүрэхгүй.", "danger")
        return redirect(url_for("equipment.equipment_list"))

    eq = Equipment.query.get_or_404(id)
    
    # Түүхтэй эсэхийг шалгах
    has_history = MaintenanceLog.query.filter_by(equipment_id=eq.id).first() or \
                  UsageLog.query.filter_by(equipment_id=eq.id).first()

    if has_history:
        eq.status = "retired"
        flash(f"'{eq.name}' төхөөрөмж түүхтэй тул 'Retired' (Ашиглалтаас гарсан) төлөвт шилжүүллээ.", "warning")
    else:
        db.session.delete(eq)
        flash(f"'{eq.name}' устгагдлаа.", "success")
    
    db.session.commit()
    return redirect(url_for("equipment.equipment_list"))

# --- BULK DELETE (Олноор устгах) ---
@equipment_bp.route("/bulk_delete", methods=["POST"])
@login_required
def bulk_delete():
    if current_user.role not in ["ahlah", "admin"]:
        flash("Эрх хүрэхгүй.", "danger")
        return redirect(url_for("equipment.equipment_list"))

    # HTML checkbox name="equipment_ids"
    ids = request.form.getlist('equipment_ids')
    
    if not ids:
        flash("Төхөөрөмж сонгоогүй байна.", "warning")
        return redirect(url_for("equipment.equipment_list"))

    deleted_count = 0
    retired_count = 0

    for eq_id in ids:
        eq = Equipment.query.get(eq_id)
        if eq:
            # Түүхтэй эсэхийг шалгах
            has_history = MaintenanceLog.query.filter_by(equipment_id=eq.id).first() or \
                          UsageLog.query.filter_by(equipment_id=eq.id).first()
            
            if has_history:
                eq.status = "retired"
                retired_count += 1
            else:
                db.session.delete(eq)
                deleted_count += 1

    db.session.commit()
    
    msg = []
    if deleted_count > 0: msg.append(f"{deleted_count} төхөөрөмж устгагдлаа.")
    if retired_count > 0: msg.append(f"{retired_count} төхөөрөмж түүхтэй тул 'Retired' боллоо.")
    
    flash(" ".join(msg), "success" if msg else "info")
    return redirect(url_for("equipment.equipment_list"))


# -------------------------------------------------
# 3. LOGS & FILES
# -------------------------------------------------
@equipment_bp.route("/add_log/<int:id>", methods=["POST"])
@login_required
def add_maintenance_log(id):
    eq = Equipment.query.get_or_404(id)
    action_type = request.form.get("action_type")
    
    action_date_str = request.form.get("action_date")
    action_date = datetime.strptime(action_date_str, "%Y-%m-%d") if action_date_str else datetime.now()

    file_filename = None
    if 'certificate_file' in request.files:
        file = request.files['certificate_file']
        if file and file.filename != '':
            # ✅ File size validation
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning

            if file_size > MAX_FILE_SIZE:
                flash(f"Файл хэт том байна (max {MAX_FILE_SIZE/1024/1024:.0f}MB)", "danger")
                return redirect(url_for("equipment.equipment_detail", id=id))

            # ✅ File extension validation
            filename = secure_filename(file.filename)
            if '.' not in filename:
                flash("Файлын өргөтгөл тодорхойгүй байна", "danger")
                return redirect(url_for("equipment.equipment_detail", id=id))

            ext = filename.rsplit('.', 1)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                flash(f"Зөвшөөрөгдөхгүй файлын төрөл (.{ext}). Зөвшөөрөгдсөн: {', '.join(ALLOWED_EXTENSIONS)}", "danger")
                return redirect(url_for("equipment.equipment_detail", id=id))

            # Save file
            unique_filename = f"{int(datetime.now().timestamp())}_{filename}"
            upload_folder = current_app.config.get('UPLOAD_FOLDER')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder, mode=0o755)
            file.save(os.path.join(upload_folder, unique_filename))
            file_filename = unique_filename

    log = MaintenanceLog(
        equipment_id=eq.id, action_type=action_type, description=request.form.get("description"),
        performed_by=request.form.get("performed_by"), certificate_no=request.form.get("certificate_no"),
        action_date=action_date, file_path=file_filename
    )
    
    if action_type == "Calibration":
        eq.calibration_date = action_date.date()
        eq.next_calibration_date = eq.calibration_date + timedelta(days=eq.calibration_cycle_days or 365)
        if eq.status != "retired": eq.status = "normal"
    elif action_type == "Repair":
        eq.status = "maintenance"

    db.session.add(log)
    db.session.commit()
    return redirect(url_for("equipment.equipment_detail", id=id))

@equipment_bp.route("/download_cert/<int:log_id>")
@login_required
def download_certificate(log_id):
    log = MaintenanceLog.query.get_or_404(log_id)
    if not log.file_path:
        flash("Файл алга.", "warning"); return redirect(request.referrer)
    return send_from_directory(os.path.abspath(current_app.config.get('UPLOAD_FOLDER')), log.file_path, as_attachment=True)

@equipment_bp.route("/api/log_usage_bulk", methods=["POST"])
@login_required
def log_usage_bulk():
    data = request.get_json() or {}
    items = data.get("items", [])
    # ... Log logic ...
    # Энд өмнөх API логик байх ёстой
    # Товчлов (Таны хуучин код дээр энэ хэсэг бүтнээрээ байсан, түүнийг хэвээр үлдээгээрэй)
    return jsonify({"status": "success"})

# -------------------------------------------------
# 4. API: SUMMARY & STATS (Category Filter-тэй)
# -------------------------------------------------

def _filter_equipment_by_category(query, category):
    """Бүх API-д ашиглах шүүлтүүр"""
    if category and category != "all":
        return query.filter(Equipment.category == category)
    return query

# A. Нэгдсэн тойм (Summary Grid)
@equipment_bp.route("/api/equipment/usage_summary")
@login_required
def api_equipment_usage_summary():
    today = datetime.now().date()
    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")
    category = request.args.get("category", "all") 

    start_dt = datetime.strptime(start_str, "%Y-%m-%d") if start_str else datetime.now() - timedelta(days=30)
    end_dt = datetime.strptime(end_str, "%Y-%m-%d") if end_str else datetime.now()
    end_dt = end_dt.replace(hour=23, minute=59, second=59)

    eq_query = _filter_equipment_by_category(Equipment.query, category)
    # Retired төхөөрөмжүүдийг summary дээр харуулах эсэхээ шийднэ. 
    # Жишээ нь: eq_query = eq_query.filter(Equipment.status != 'retired') 
    equipments = eq_query.order_by(Equipment.name.asc()).all()
    eq_ids = [e.id for e in equipments]

    if not eq_ids:
        return jsonify({"rows": []})

    usage_stats = db.session.query(UsageLog.equipment_id, func.sum(UsageLog.duration_minutes), func.max(UsageLog.start_time)).filter(UsageLog.start_time >= start_dt, UsageLog.start_time <= end_dt, UsageLog.equipment_id.in_(eq_ids)).group_by(UsageLog.equipment_id).all()
    usage_map = {r[0]: {"total": r[1], "last": r[2]} for r in usage_stats}

    maint_stats = db.session.query(MaintenanceLog.equipment_id, func.count(MaintenanceLog.id), func.max(MaintenanceLog.action_date)).filter(MaintenanceLog.action_date >= start_dt, MaintenanceLog.action_date <= end_dt, MaintenanceLog.equipment_id.in_(eq_ids)).group_by(MaintenanceLog.equipment_id).all()
    maint_map = {r[0]: {"cnt": r[1], "last": r[2]} for r in maint_stats}

    rows = []
    for eq in equipments:
        u = usage_map.get(eq.id, {})
        m = maint_map.get(eq.id, {})
        total_mins = int(u.get("total") or 0)
        is_expired = (eq.next_calibration_date and eq.next_calibration_date < today)

        rows.append({
            "equipment_id": eq.id, "lab_code": eq.lab_code, "name": eq.name, 
            "location": eq.location, "room": eq.room_number, "status": eq.status or "normal",
            "total_usage_hours": round(total_mins/60.0, 2), "maintenance_count": m.get("cnt", 0),
            "last_usage_end": u.get("last", None), "last_maintenance": m.get("last", None),
            "next_calibration_date": eq.next_calibration_date.strftime("%Y-%m-%d") if eq.next_calibration_date else None,
            "is_calibration_expired": is_expired
        })
    return jsonify({"rows": rows, "start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")})

# B. Дэлгэрэнгүй журнал (Detailed Journal)
@equipment_bp.route("/api/equipment/journal_detailed")
@login_required
def api_equipment_journal_detailed():
    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")
    category = request.args.get("category", "all") 

    start_dt = datetime.strptime(start_str, "%Y-%m-%d") if start_str else datetime.now() - timedelta(days=30)
    end_dt = datetime.strptime(end_str, "%Y-%m-%d") if end_str else datetime.now()
    end_dt = end_dt.replace(hour=23, minute=59, second=59)

    m_logs = db.session.query(MaintenanceLog, Equipment).join(Equipment).filter(
        MaintenanceLog.action_date >= start_dt, MaintenanceLog.action_date <= end_dt
    )
    m_logs = _filter_equipment_by_category(m_logs, category).all()

    u_logs = db.session.query(UsageLog, Equipment).join(Equipment).filter(
        UsageLog.start_time >= start_dt, UsageLog.start_time <= end_dt
    )
    u_logs = _filter_equipment_by_category(u_logs, category).all()

    combined = []
    for log, eq in m_logs:
        combined.append({
            "date": log.action_date.strftime("%Y-%m-%d %H:%M"), "timestamp": log.action_date.timestamp(),
            "lab_code": eq.lab_code, "equipment": eq.name, "category": "Maintenance", "type": log.action_type,
            "user": log.performed_by, "description": log.description, "result": log.result or ""
        })
    for log, eq in u_logs:
        combined.append({
            "date": log.start_time.strftime("%Y-%m-%d %H:%M"), "timestamp": log.start_time.timestamp(),
            "lab_code": eq.lab_code, "equipment": eq.name, "category": "Usage", "type": "Ашиглалт",
            "user": "-", "description": f"{log.duration_minutes} мин", "result": "Normal"
        })
    
    combined.sort(key=lambda x: x["timestamp"], reverse=True)
    return jsonify({"rows": combined})

# C. Сарын нэгтгэл (Monthly Stats)
@equipment_bp.route("/api/equipment/monthly_stats")
@login_required
def api_equipment_monthly_stats():
    year = int(request.args.get("year", datetime.now().year))
    category = request.args.get("category", "all")

    start_dt = datetime(year, 1, 1)
    end_dt = datetime(year, 12, 31, 23, 59, 59)

    eq_query = _filter_equipment_by_category(Equipment.query, category)
    equips = eq_query.all()
    eq_ids = [e.id for e in equips]

    if not eq_ids: return jsonify({"rows": [], "year": year})

    data_map = {e.id: {"lab_code": e.lab_code, "name": e.name, "months": {m: {"usage":0, "maint":0} for m in range(1,13)}} for e in equips}

    usage_rows = db.session.query(UsageLog.equipment_id, func.extract('month', UsageLog.start_time), func.sum(UsageLog.duration_minutes)).filter(UsageLog.start_time.between(start_dt, end_dt), UsageLog.equipment_id.in_(eq_ids)).group_by(UsageLog.equipment_id, func.extract('month', UsageLog.start_time)).all()
    for eid, mon, val in usage_rows:
        if eid in data_map: data_map[eid]["months"][int(mon)]["usage"] = int(val or 0)

    maint_rows = db.session.query(MaintenanceLog.equipment_id, func.extract('month', MaintenanceLog.action_date), func.count(MaintenanceLog.id)).filter(MaintenanceLog.action_date.between(start_dt, end_dt), MaintenanceLog.equipment_id.in_(eq_ids)).group_by(MaintenanceLog.equipment_id, func.extract('month', MaintenanceLog.action_date)).all()
    for eid, mon, val in maint_rows:
        if eid in data_map: data_map[eid]["months"][int(mon)]["maint"] = int(val or 0)

    rows = []
    for eid, info in data_map.items():
        row = {"lab_code": info["lab_code"], "name": info["name"]}
        for m in range(1, 13):
            row[f"usage_{m}"] = info["months"][m]["usage"]
            row[f"maint_{m}"] = info["months"][m]["maint"]
        rows.append(row)

    return jsonify({"rows": rows, "year": year})

# -------------------------------------------------
# 5. NAVIGATION ROUTES
# -------------------------------------------------
@equipment_bp.route("/equipment_journal", endpoint="equipment_journal")
@login_required
def equipment_journal_hub():
    return render_template("equipment_hub.html")

@equipment_bp.route("/equipment_journal/grid", endpoint="equipment_journal_grid")
@login_required
def equipment_journal_grid():
    category = request.args.get("category", "all")
    titles = {
        "all": "Нэгдсэн тойм (Бүгд)",
        "furnace": "1. Шатаах зуух",
        "prep": "2. Дээж бэлтгэл",
        "analysis": "3. Шинжилгээний багаж",
        "water": "4. Усны лаб",
        "micro": "5. Микробиологи лаб",
        "wtl": "6. БС лаб",
        "balance": "7. Жин",
        "other": "8. Бусад"
    }
    title = titles.get(category, "Тоног Төхөөрөмжийн Журнал")
    
    today = datetime.now().date()
    return render_template("equipment_journal.html", title=title, start_date=today-timedelta(days=29), end_date=today, category=category)