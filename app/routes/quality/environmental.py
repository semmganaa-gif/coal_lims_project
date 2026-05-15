# app/routes/quality/environmental.py
"""Environmental Monitoring - ISO 17025 Clause 6.3.3"""
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from flask_babel import lazy_gettext as _l
from app.models import EnvironmentalLog
from app.repositories import EnvironmentalLogRepository
from app.utils.database import safe_commit
from app.utils.quality_helpers import require_quality_edit


def register_routes(bp):
    """Орчны хяналтын route-уудыг бүртгэх."""
    @bp.route("/environmental")
    @login_required
    def environmental_list():
        logs = EnvironmentalLogRepository.get_all()
        return render_template('quality/environmental_list.html', logs=logs, title="Орчны хяналт")

    @bp.route("/environmental/add", methods=["POST"])
    @login_required
    @require_quality_edit('quality.environmental_list')
    def environmental_add():
        try:
            temp = float(request.form['temperature'])
            humidity = float(request.form['humidity'])
            temp_min = float(request.form.get('temp_min', 15))
            temp_max = float(request.form.get('temp_max', 30))
            humidity_min = float(request.form.get('humidity_min', 20))
            humidity_max = float(request.form.get('humidity_max', 70))
        except (ValueError, TypeError, KeyError):
            flash(_l("Тоон утга буруу байна."), "danger")
            return redirect(url_for('quality.environmental_list'))

        within_limits = (temp_min <= temp <= temp_max) and (humidity_min <= humidity <= humidity_max)

        log = EnvironmentalLog(
            location=request.form.get('location', 'Sample Storage'),
            temperature=temp,
            humidity=humidity,
            temp_min=temp_min,
            temp_max=temp_max,
            humidity_min=humidity_min,
            humidity_max=humidity_max,
            within_limits=within_limits,
            recorded_by_id=current_user.id,
            notes=request.form.get('notes')
        )
        EnvironmentalLogRepository.save(log, commit=False)
        if safe_commit(None, "Орчны хэмжилт хадгалахад алдаа гарлаа"):
            if within_limits:
                flash(_l("Орчны хэмжилт бүртгэгдлээ"), "success")
            else:
                flash(_l("Орчны хэмжилт бүртгэгдлээ — хязгаараас гадуур байна"), "warning")
        return redirect(url_for('quality.environmental_list'))
