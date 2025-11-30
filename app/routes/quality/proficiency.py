# app/routes/quality/proficiency.py
# -*- coding: utf-8 -*-
"""
Proficiency Testing Management
ISO 17025 - Clause 7.7.2
"""
#Сорилтын үр дүнгийн гадаад хяналтын бүртгэл
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import ProficiencyTest, User
from datetime import datetime


def register_routes(bp):
    """PT route-ууд"""

    @bp.route("/proficiency")
    @login_required
    def proficiency_list():
        """PT жагсаалт"""
        pts = ProficiencyTest.query.order_by(ProficiencyTest.test_date.desc()).all()

        stats = {
            'total': len(pts),
            'satisfactory': len([p for p in pts if p.performance == 'satisfactory']),
            'questionable': len([p for p in pts if p.performance == 'questionable']),
            'unsatisfactory': len([p for p in pts if p.performance == 'unsatisfactory'])
        }

        return render_template('quality/proficiency_list.html', pts=pts, stats=stats, title="Proficiency Testing")

    @bp.route("/proficiency/new", methods=["GET", "POST"])
    @login_required
    def proficiency_new():
        """Шинэ PT бүртгэх"""
        if request.method == "POST":
            # Z-score тооцох
            our_result = float(request.form['our_result'])
            assigned_value = float(request.form['assigned_value'])
            uncertainty = float(request.form['uncertainty'])
            z_score = (our_result - assigned_value) / uncertainty if uncertainty > 0 else 0

            # Performance үнэлэх
            if abs(z_score) <= 2:
                performance = 'satisfactory'
            elif abs(z_score) <= 3:
                performance = 'questionable'
            else:
                performance = 'unsatisfactory'

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
                test_date=datetime.strptime(request.form['test_date'], '%Y-%m-%d').date() if request.form.get('test_date') else None,
                tested_by_id=current_user.id,
                notes=request.form.get('notes')
            )

            db.session.add(pt)
            db.session.commit()

            flash(f"PT {pt.pt_program} амжилттай бүртгэгдлээ (Z-score: {z_score:.2f})", "success")
            return redirect(url_for('quality.proficiency_list'))

        return render_template('quality/proficiency_form.html', title="Шинэ PT бүртгэх")
