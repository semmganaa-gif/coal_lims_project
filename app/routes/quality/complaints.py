# app/routes/quality/complaints.py
"""Санал гомдлын бүртгэл - LAB.02.00.01 / ISO 17025 Clause 7.9"""

from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import CustomerComplaint, ImprovementRecord, AnalysisResult, AnalysisResultLog
from app.utils.database import safe_commit
from app.utils.quality_helpers import (
    require_quality_edit,
    calculate_status_stats,
    generate_sequential_code
)
from datetime import date
from app.utils.datetime import now_local
from sqlalchemy import func, extract
from collections import defaultdict
import json
import logging

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Санал гомдлын route-уудыг бүртгэх."""

    @bp.route("/complaints")
    @login_required
    def complaints_list():
        complaints = CustomerComplaint.query.order_by(
            CustomerComplaint.complaint_date.desc()
        ).limit(2000).all()
        stats = calculate_status_stats(
            complaints,
            status_values=['received', 'resolved', 'closed']
        )
        return render_template(
            'quality/complaints_list.html',
            complaints=complaints,
            stats=stats,
            title="Санал гомдлын бүртгэл"
        )

    @bp.route("/complaints/dashboard")
    @login_required
    def complaints_dashboard():
        """Санал гомдлын дашбоард - Excel бүртгэлийн загвараар."""
        year = request.args.get('year', date.today().year, type=int)

        complaints = CustomerComplaint.query.filter(
            extract('year', CustomerComplaint.complaint_date) == year
        ).order_by(CustomerComplaint.complaint_date.desc()).all()

        total = len(complaints)

        # ═══ Үндэслэлтэй / Үгүй ═══
        justified_yes = 0
        justified_no = 0
        justified_pending = 0
        for c in complaints:
            if c.is_justified is True:
                justified_yes += 1
            elif c.is_justified is False:
                justified_no += 1
            else:
                justified_pending += 1

        # ═══ Шинжилгээний төрлөөр (reanalysis_codes-оос) ═══
        analysis_type_map = {
            'Aad': 'Үнслэг', 'Mad': 'Чийг', 'Vdaf': 'Дэгдэмхий',
            'CSN': 'CSN', 'TRD': 'Нягт',
            'St,d': 'Хүхэр', 'Qgr,ad': 'Илч', 'FCd': 'Тогтмол нүүрстөрөгч',
        }
        analysis_counts = defaultdict(int)
        for c in complaints:
            codes = c.get_reanalysis_codes()
            for code in codes:
                label = analysis_type_map.get(code, code)
                analysis_counts[label] += 1

        # ═══ Хаанаас ирсэн (complainant_department) ═══
        dept_map = {
            'CHPP': 'Баяжуулагч инженер', 'QC': 'Чанар', 'LAB': 'Лаб',
            'UHG-Geo': 'Геологи', 'BN-Geo': 'Геологи', 'Proc': 'Процесс',
            'WTL': 'WTL', 'uutsb': 'УУЦБ',
        }
        dept_counts = defaultdict(int)
        for c in complaints:
            dept = c.complainant_department or 'Бусад'
            label = dept_map.get(dept, dept)
            dept_counts[label] += 1

        # ═══ Сараар (monthly trend) ═══
        monthly = defaultdict(int)
        monthly_justified = defaultdict(int)
        monthly_not_justified = defaultdict(int)
        for c in complaints:
            if c.complaint_date:
                m = c.complaint_date.month
                monthly[m] += 1
                if c.is_justified is True:
                    monthly_justified[m] += 1
                elif c.is_justified is False:
                    monthly_not_justified[m] += 1

        months_data = []
        for m in range(1, 13):
            months_data.append({
                'month': m,
                'total': monthly.get(m, 0),
                'justified': monthly_justified.get(m, 0),
                'not_justified': monthly_not_justified.get(m, 0),
            })

        # ═══ Ахлах химичээр ═══
        senior_counts = defaultdict(int)
        for c in complaints:
            if c.receiver_name:
                senior_counts[c.receiver_name] += 1

        return render_template(
            'quality/complaints_dashboard.html',
            year=year,
            total=total,
            justified_yes=justified_yes,
            justified_no=justified_no,
            justified_pending=justified_pending,
            analysis_counts=dict(analysis_counts),
            dept_counts=dict(dept_counts),
            months_data=months_data,
            senior_counts=dict(senior_counts),
            complaints=complaints,
            title=f"Санал гомдлын дашбоард - {year}"
        )

    @bp.route("/complaints/new", methods=["GET", "POST"])
    @login_required
    @require_quality_edit('quality.complaints_list')
    def complaints_new():
        if request.method == "POST":
            complainant_name = request.form.get('complainant_name', '').strip()
            complaint_content = request.form.get('complaint_content', '').strip()

            if not complainant_name or not complaint_content:
                flash("Нэр болон агуулга шаардлагатай.", "danger")
                return render_template(
                    'quality/complaints_form.html',
                    today=date.today().isoformat(),
                    title="Шинэ санал гомдол"
                )

            complaint_no = generate_sequential_code(
                CustomerComplaint, 'complaint_no', 'COMP'
            )

            sample_id = request.form.get('related_sample_id', '').strip()

            complaint = CustomerComplaint(
                complaint_no=complaint_no,
                complaint_date=request.form.get('complaint_date') or date.today(),
                complainant_name=complainant_name,
                complainant_department=request.form.get('complainant_department', '').strip(),
                complaint_content=complaint_content,
                complainant_user_id=current_user.id,
                related_sample_id=int(sample_id) if sample_id else None,
                status='received'
            )

            # Дахин шинжилгээний сонголт
            reanalysis_codes_raw = request.form.get('reanalysis_codes', '').strip()
            snapshot_raw = request.form.get('original_results_snapshot', '').strip()
            reanalysis_codes = []
            original_snapshot = {}

            if reanalysis_codes_raw:
                try:
                    reanalysis_codes = json.loads(reanalysis_codes_raw)
                except (json.JSONDecodeError, TypeError):
                    reanalysis_codes = []

            if snapshot_raw:
                try:
                    original_snapshot = json.loads(snapshot_raw)
                except (json.JSONDecodeError, TypeError):
                    original_snapshot = {}

            if reanalysis_codes:
                complaint.set_reanalysis_codes(reanalysis_codes)
                complaint.set_original_results_snapshot(original_snapshot)

            db.session.add(complaint)
            db.session.flush()

            # Сонгосон approved result-уудыг автоматаар rejected болгох
            rejected_count = 0
            if reanalysis_codes and sample_id:
                result_ids = [
                    v.get('analysis_result_id')
                    for v in original_snapshot.values()
                    if v.get('analysis_result_id')
                ]
                if result_ids:
                    results = AnalysisResult.query.filter(
                        AnalysisResult.id.in_(result_ids),
                        AnalysisResult.sample_id == int(sample_id),
                        AnalysisResult.status == 'approved'
                    ).all()

                    from app.models import Sample
                    sample_obj = Sample.query.get(int(sample_id))
                    sample_code = sample_obj.sample_code if sample_obj else ''

                    for ar in results:
                        ar.status = 'rejected'
                        ar.rejection_comment = f"Санал гомдол: {complaint_no}"
                        ar.rejection_category = 'customer_complaint'
                        ar.error_reason = 'customer_complaint'
                        ar.updated_at = now_local()

                        log = AnalysisResultLog(
                            analysis_result_id=ar.id,
                            sample_id=ar.sample_id,
                            sample_code_snapshot=sample_code,
                            user_id=current_user.id,
                            action='rejected',
                            reason=f"Санал гомдол: {complaint_no}",
                            analysis_code=ar.analysis_code,
                            final_result_snapshot=ar.final_result,
                            rejection_category='customer_complaint',
                            error_reason='customer_complaint'
                        )
                        db.session.add(log)
                        rejected_count += 1

            success_msg = f"Гомдол {complaint_no} бүртгэгдлээ"
            if rejected_count:
                success_msg += f" | {rejected_count} шинжилгээ дахин шинжлүүлэхээр татгалзагдлаа"

            if not safe_commit(success_msg, "Гомдол хадгалахад алдаа гарлаа"):
                return redirect(url_for('quality.complaints_list'))

            logger.info(
                f"Complaint created: {complaint_no}, "
                f"by: {complainant_name}, user: {current_user.username}"
                f"{f', {rejected_count} results auto-rejected' if rejected_count else ''}"
            )
            return redirect(url_for('quality.complaints_list'))

        return render_template(
            'quality/complaints_form.html',
            today=date.today().isoformat(),
            title="Шинэ санал гомдол"
        )

    @bp.route("/complaints/<int:id>")
    @login_required
    def complaints_detail(id):
        complaint = CustomerComplaint.query.get_or_404(id)
        # Холбогдох дээжийн шинжилгээний үр дүн
        analysis_results = []
        if complaint.related_sample_id:
            analysis_results = AnalysisResult.query.filter_by(
                sample_id=complaint.related_sample_id
            ).order_by(AnalysisResult.analysis_code).all()

        # Дахин шинжилгээний мэдээлэл
        reanalysis_codes = complaint.get_reanalysis_codes()
        original_snapshot = complaint.get_original_results_snapshot()
        reanalysis_complete = True
        comparison_data = []

        if reanalysis_codes and complaint.related_sample_id:
            # Одоогийн үр дүнг code-оор нь group-лэх
            current_by_code = {}
            for ar in analysis_results:
                if ar.analysis_code in reanalysis_codes:
                    # Хамгийн сүүлийн approved эсвэл pending_review-г авна
                    if ar.status != 'rejected':
                        current_by_code[ar.analysis_code] = ar

            for code in reanalysis_codes:
                orig = original_snapshot.get(code, {})
                current = current_by_code.get(code)

                if not current:
                    reanalysis_complete = False

                orig_result = orig.get('final_result')
                new_result = current.final_result if current else None
                new_status = current.status if current else 'rejected'

                # Зөрүү тооцох
                diff = None
                if orig_result is not None and new_result is not None:
                    try:
                        diff = round(float(new_result) - float(orig_result), 4)
                    except (ValueError, TypeError):
                        diff = None

                comparison_data.append({
                    'analysis_code': code,
                    'original_result': orig_result,
                    'new_result': new_result,
                    'new_status': new_status,
                    'diff': diff
                })

        return render_template(
            'quality/complaints_detail.html',
            complaint=complaint,
            analysis_results=analysis_results,
            reanalysis_codes=reanalysis_codes,
            reanalysis_complete=reanalysis_complete,
            comparison_data=comparison_data,
            title=f"Санал гомдол - {complaint.complaint_no}"
        )

    @bp.route("/complaints/<int:id>/receive", methods=["POST"])
    @login_required
    @require_quality_edit('quality.complaints_list')
    def complaints_receive(id):
        """Хэсэг 2: Хүлээн авагч бөглөх."""
        complaint = CustomerComplaint.query.get_or_404(id)
        complaint.receiver_name = request.form.get('receiver_name', '').strip()
        complaint.action_taken = request.form.get('action_taken', '').strip()
        complaint.receiver_documentation = request.form.get('receiver_documentation', '').strip()
        complaint.is_justified = request.form.get('is_justified') == '1'
        complaint.response_detail = request.form.get('response_detail', '').strip()
        complaint.receiver_user_id = current_user.id
        complaint.status = 'received'
        if not safe_commit(
            f"{complaint.complaint_no} хүлээн авагдлаа",
            "Гомдол хүлээн авахад алдаа гарлаа"
        ):
            return redirect(url_for('quality.complaints_detail', id=id))

        logger.info(f"Complaint received: {complaint.complaint_no}, user: {current_user.username}")
        return redirect(url_for('quality.complaints_detail', id=id))

    @bp.route("/complaints/<int:id>/control", methods=["POST"])
    @login_required
    @require_quality_edit('quality.complaints_list')
    def complaints_control(id):
        """Хэсэг 3: Хяналтын хэсэг (Чанарын менежер)."""
        complaint = CustomerComplaint.query.get_or_404(id)
        complaint.action_corrective = request.form.get('action_corrective') == '1'
        complaint.action_improvement = request.form.get('action_improvement') == '1'
        complaint.action_partial_audit = request.form.get('action_partial_audit') == '1'
        complaint.quality_manager_id = current_user.id
        complaint.status = 'resolved'

        created_records = []

        # Сайжруулах → Improvementын бүртгэл автомат үүсгэх
        if complaint.action_improvement:
            imp_number = generate_sequential_code(
                ImprovementRecord, 'record_no', 'IMP'
            )
            imp = ImprovementRecord(
                record_no=imp_number,
                activity_description=f"[{complaint.complaint_no}] {complaint.complaint_content or complaint.description or ''}",
                source_complaint_id=complaint.id,
                created_by_id=current_user.id,
                status='pending'
            )
            db.session.add(imp)
            created_records.append(f"Сайжруулалт {imp_number}")

        success_msg = f"{complaint.complaint_no} хянагдлаа"
        if created_records:
            success_msg += f" | Үүсгэгдсэн: {', '.join(created_records)}"

        if not safe_commit(success_msg, "Гомдол хянахад алдаа гарлаа"):
            return redirect(url_for('quality.complaints_detail', id=id))

        logger.info(f"Complaint controlled: {complaint.complaint_no}, user: {current_user.username}")
        return redirect(url_for('quality.complaints_detail', id=id))

