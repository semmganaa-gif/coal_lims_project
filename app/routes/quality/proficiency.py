# app/routes/quality/proficiency.py
# -*- coding: utf-8 -*-
"""
Proficiency Testing Management
ISO 17025 - Clause 7.7.2
"""
# Сорилтын үр дүнгийн гадаад хяналтын бүртгэл

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import ProficiencyTest
from app.utils.quality_helpers import (
    require_quality_edit,
    calculate_status_stats,
    parse_date
)
import logging

logger = logging.getLogger(__name__)


def register_routes(bp):
    """PT route-ууд"""

    @bp.route("/proficiency")
    @login_required
    def proficiency_list():
        """PT жагсаалт"""
        pts = ProficiencyTest.query.order_by(ProficiencyTest.test_date.desc()).all()
        stats = calculate_status_stats(
            pts,
            status_field='performance',
            status_values=['satisfactory', 'questionable', 'unsatisfactory']
        )
        return render_template('quality/proficiency_list.html', pts=pts, stats=stats, title="Proficiency Testing")

    @bp.route("/proficiency/new", methods=["GET", "POST"])
    @login_required
    @require_quality_edit('quality.proficiency_list')
    def proficiency_new():
        """Шинэ PT бүртгэх"""
        if request.method == "POST":
            try:
                # Z-score тооцох
                our_result = float(request.form.get('our_result', 0))
                assigned_value = float(request.form.get('assigned_value', 0))
                uncertainty = float(request.form.get('uncertainty', 0))
            except (ValueError, TypeError) as e:
                logger.warning(f"PT form validation error: {e}, user: {current_user.username}")
                flash("Тоон утга буруу байна. Зөв утга оруулна уу.", "danger")
                return render_template('quality/proficiency_form.html', title="Шинэ PT бүртгэх")

            z_score = (our_result - assigned_value) / uncertainty if uncertainty > 0 else 0

            # Performance үнэлэх
            if abs(z_score) <= 2:
                performance = 'satisfactory'
            elif abs(z_score) <= 3:
                performance = 'questionable'
            else:
                performance = 'unsatisfactory'

            # Parse test_date safely using helper
            test_date = parse_date(request.form.get('test_date'))

            pt = ProficiencyTest(
                pt_provider=request.form.get('pt_provider'),
                pt_program=request.form.get('pt_program'),
                round_number=request.form.get('round_number'),
                sample_code=request.form.get('sample_code'),
                analysis_code=request.form.get('analysis_code'),
                our_result=our_result,
                assigned_value=assigned_value,
                uncertainty=uncertainty,
                z_score=z_score,
                performance=performance,
                test_date=test_date,
                tested_by_id=current_user.id,
                notes=request.form.get('notes')
            )

            db.session.add(pt)
            db.session.commit()

            logger.info(f"PT created: {pt.pt_program}, Z-score: {z_score:.2f}, user: {current_user.username}")
            flash(f"PT {pt.pt_program} амжилттай бүртгэгдлээ (Z-score: {z_score:.2f})", "success")
            return redirect(url_for('quality.proficiency_list'))

        return render_template('quality/proficiency_form.html', title="Шинэ PT бүртгэх")
