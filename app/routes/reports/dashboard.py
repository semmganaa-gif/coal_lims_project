# app/routes/reports/dashboard.py
# -*- coding: utf-8 -*-
"""
Reports Dashboard — нэгдсэн тайлангийн товч мэдээлэл.
"""

from datetime import datetime

from flask import render_template
from flask_login import login_required
from sqlalchemy import func, select

from app import db
from app.utils.datetime import now_local
from app.routes.reports.routes import reports_bp, _format_short_name
from app import models as M

Sample = M.Sample
AnalysisResultLog = M.AnalysisResultLog


@reports_bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard - Бүх тайлангийн товч мэдээлэл нэг дэлгэцэнд"""
    from app.models import User

    now = now_local()
    year = now.year
    month = now.month

    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1)
    else:
        month_end = datetime(year, month + 1, 1)

    year_start = datetime(year, 1, 1)
    year_end = datetime(year + 1, 1, 1)

    # ========== KPI-ууд ==========

    # 1. Дээжний тоо
    samples_month = db.session.execute(
        select(func.count(Sample.id)).where(
            Sample.lab_type == 'coal',
            Sample.received_date >= month_start.date(),
            Sample.received_date < month_end.date(),
        )
    ).scalar_one()

    samples_year = db.session.execute(
        select(func.count(Sample.id)).where(
            Sample.lab_type == 'coal',
            Sample.received_date >= year_start.date(),
            Sample.received_date < year_end.date(),
        )
    ).scalar_one()

    # 2. Шинжилгээний тоо
    work_actions = [
        'CREATED_AUTO_APPROVED', 'CREATED_PENDING', 'CREATED_REJECTED', 'CREATED_VOID_RETEST',
        'UPDATED_AUTO_APPROVED', 'UPDATED_PENDING', 'UPDATED_REJECTED', 'UPDATED_VOID_RETEST',
    ]

    analyses_month = db.session.query(func.count(AnalysisResultLog.id)).join(
        Sample, Sample.id == AnalysisResultLog.sample_id
    ).filter(
        Sample.lab_type == 'coal',
        AnalysisResultLog.action.in_(work_actions),
        AnalysisResultLog.timestamp >= month_start,
        AnalysisResultLog.timestamp < month_end
    ).scalar() or 0

    analyses_year = db.session.query(func.count(AnalysisResultLog.id)).join(
        Sample, Sample.id == AnalysisResultLog.sample_id
    ).filter(
        Sample.lab_type == 'coal',
        AnalysisResultLog.action.in_(work_actions),
        AnalysisResultLog.timestamp >= year_start,
        AnalysisResultLog.timestamp < year_end
    ).scalar() or 0

    # 3. Алдааны тоо
    errors_month = db.session.query(func.count(AnalysisResultLog.id)).join(
        Sample, Sample.id == AnalysisResultLog.sample_id
    ).filter(
        Sample.lab_type == 'coal',
        AnalysisResultLog.action == 'REJECTED',
        AnalysisResultLog.timestamp >= month_start,
        AnalysisResultLog.timestamp < month_end
    ).scalar() or 0

    errors_year = db.session.query(func.count(AnalysisResultLog.id)).join(
        Sample, Sample.id == AnalysisResultLog.sample_id
    ).filter(
        Sample.lab_type == 'coal',
        AnalysisResultLog.action == 'REJECTED',
        AnalysisResultLog.timestamp >= year_start,
        AnalysisResultLog.timestamp < year_end
    ).scalar() or 0

    # 4. Идэвхтэй ажилтнууд
    active_users_month = db.session.query(
        func.count(func.distinct(AnalysisResultLog.user_id))
    ).join(
        Sample, Sample.id == AnalysisResultLog.sample_id
    ).filter(
        Sample.lab_type == 'coal',
        AnalysisResultLog.action.in_(work_actions),
        AnalysisResultLog.timestamp >= month_start,
        AnalysisResultLog.timestamp < month_end
    ).scalar() or 0

    # 5. Сарын тоо (сүүлийн 6 сар)
    monthly_stats = []
    for i in range(5, -1, -1):
        m = month - i
        y = year
        if m <= 0:
            m += 12
            y -= 1
        m_start = datetime(y, m, 1)
        if m == 12:
            m_end = datetime(y + 1, 1, 1)
        else:
            m_end = datetime(y, m + 1, 1)

        cnt = db.session.query(func.count(AnalysisResultLog.id)).join(
            Sample, Sample.id == AnalysisResultLog.sample_id
        ).filter(
            Sample.lab_type == 'coal',
            AnalysisResultLog.action.in_(work_actions),
            AnalysisResultLog.timestamp >= m_start,
            AnalysisResultLog.timestamp < m_end
        ).scalar() or 0

        monthly_stats.append({
            'month': m,
            'year': y,
            'label': f"{m}-р сар",
            'count': cnt
        })

    # 6. Топ 5 ажилтан
    top_users = (
        db.session.query(
            AnalysisResultLog.user_id,
            func.count(AnalysisResultLog.id).label('cnt')
        )
        .join(Sample, Sample.id == AnalysisResultLog.sample_id)
        .filter(
            Sample.lab_type == 'coal',
            AnalysisResultLog.action.in_(work_actions),
            AnalysisResultLog.user_id.isnot(None),
            AnalysisResultLog.timestamp >= month_start,
            AnalysisResultLog.timestamp < month_end
        )
        .group_by(AnalysisResultLog.user_id)
        .order_by(func.count(AnalysisResultLog.id).desc())
        .limit(5)
        .all()
    )

    top_users_data = []
    for uid, cnt in top_users:
        user = db.session.get(User, uid)
        if user:
            top_users_data.append({
                'name': _format_short_name(user.full_name) or user.username,
                'count': cnt
            })

    return render_template(
        "reports/dashboard.html",
        title="Dashboard",
        year=year,
        month=month,
        samples_month=samples_month,
        samples_year=samples_year,
        analyses_month=analyses_month,
        analyses_year=analyses_year,
        errors_month=errors_month,
        errors_year=errors_year,
        active_users_month=active_users_month,
        monthly_stats=monthly_stats,
        top_users=top_users_data,
    )
