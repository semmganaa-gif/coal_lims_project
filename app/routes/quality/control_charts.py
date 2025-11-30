# app/routes/quality/control_charts.py
"""QC Control Charts - ISO 17025 Clause 7.7.1"""
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import QCControlChart
from datetime import datetime

def register_routes(bp):
    @bp.route("/control_charts")
    @login_required
    def control_charts_list():
        charts = QCControlChart.query.order_by(QCControlChart.measurement_date.desc()).all()
        return render_template('quality/control_charts.html', charts=charts, title="QC Control Charts")

    @bp.route("/control_charts/add", methods=["POST"])
    @login_required
    def control_charts_add():
        target = float(request.form['target_value'])
        measured = float(request.form['measured_value'])
        ucl = float(request.form['ucl'])
        lcl = float(request.form['lcl'])
        in_control = lcl <= measured <= ucl

        chart = QCControlChart(
            analysis_code=request.form['analysis_code'],
            qc_sample_name=request.form['qc_sample_name'],
            target_value=target,
            ucl=ucl,
            lcl=lcl,
            measured_value=measured,
            measurement_date=datetime.strptime(request.form['measurement_date'], '%Y-%m-%d').date(),
            in_control=in_control,
            operator_id=current_user.id
        )
        db.session.add(chart)
        db.session.commit()
        flash(f"QC хэмжилт {'✅ Хэвийн' if in_control else '⚠️ Хэмжээнээс гарсан'}", "success" if in_control else "danger")
        return redirect(url_for('quality.control_charts_list'))
