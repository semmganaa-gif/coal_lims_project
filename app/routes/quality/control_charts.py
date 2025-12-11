# app/routes/quality/control_charts.py
"""QC Control Charts - ISO 17025 Clause 7.7.1

AnalysisResult-аас CM/GBW дээжний үр дүнг татаж Westgard шалгах.
"""

from flask import render_template, jsonify
from flask_login import login_required
from app import db
from app.models import Sample, AnalysisResult, ControlStandard, GbwStandard
from sqlalchemy import or_
import logging
import statistics

from app.utils.westgard import check_westgard_rules, get_qc_status, check_single_value
from app.monitoring import track_qc_check

logger = logging.getLogger(__name__)


def _get_qc_samples():
    """CM болон GBW дээжүүдийг олох"""
    return Sample.query.filter(
        or_(
            Sample.sample_type.ilike('%CM%'),
            Sample.sample_type.ilike('%GBW%'),
            Sample.sample_code.ilike('%CM%'),
            Sample.sample_code.ilike('%GBW%'),
        )
    ).order_by(Sample.id.desc()).all()


def _get_qc_results(sample_ids: list, analysis_code: str = None):
    """QC дээжүүдийн шинжилгээний үр дүнг авах"""
    query = AnalysisResult.query.filter(
        AnalysisResult.sample_id.in_(sample_ids),
        AnalysisResult.status.in_(['approved', 'pending_review']),
        AnalysisResult.final_result.isnot(None)
    )
    if analysis_code:
        query = query.filter(AnalysisResult.analysis_code == analysis_code)

    return query.order_by(AnalysisResult.updated_at.desc()).all()


def _get_target_and_tolerance(sample, analysis_code: str):
    """
    Дээжний төрлөөс хамаарч target утга болон tolerance авах.

    Returns:
        (target, ucl, lcl, sd) эсвэл (None, None, None, None)
    """
    sample_type = (sample.sample_type or "").upper()
    sample_code = (sample.sample_code or "").upper()

    # CM эсвэл GBW эсэхийг тодорхойлох
    is_cm = "CM" in sample_type or "CM" in sample_code
    is_gbw = "GBW" in sample_type or "GBW" in sample_code

    active_std = None
    if is_cm:
        active_std = ControlStandard.query.filter_by(is_active=True).first()
    elif is_gbw:
        active_std = GbwStandard.query.filter_by(is_active=True).first()

    if not active_std or not active_std.targets:
        return None, None, None, None

    targets = active_std.targets
    if isinstance(targets, str):
        import json
        try:
            targets = json.loads(targets)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None, None, None, None

    # Analysis code-д тохирох target олох
    target_info = targets.get(analysis_code)
    if not target_info:
        return None, None, None, None

    # Target утга авах
    if isinstance(target_info, dict):
        target = target_info.get('target') or target_info.get('value')
        tolerance = target_info.get('tolerance') or target_info.get('sd') or 0.5
    else:
        target = float(target_info)
        tolerance = 0.5  # Default tolerance

    if target is None:
        return None, None, None, None

    target = float(target)
    sd = float(tolerance)
    ucl = target + 2 * sd
    lcl = target - 2 * sd

    return target, ucl, lcl, sd


def register_routes(bp):
    @bp.route("/control_charts")
    @login_required
    def control_charts_list():
        """QC Control Charts хуудас - CM/GBW үр дүнгүүд"""

        # CM/GBW дээжүүд олох
        qc_samples = _get_qc_samples()
        sample_ids = [s.id for s in qc_samples]

        # Үр дүнгүүд авах
        results = []
        if sample_ids:
            all_results = _get_qc_results(sample_ids)
            samples_map = {s.id: s for s in qc_samples}

            for r in all_results:
                sample = samples_map.get(r.sample_id)
                if not sample:
                    continue

                target, ucl, lcl, sd = _get_target_and_tolerance(sample, r.analysis_code)

                in_control = True
                if target is not None and r.final_result is not None:
                    try:
                        val = float(r.final_result)
                        in_control = lcl <= val <= ucl if lcl and ucl else True
                    except (ValueError, TypeError):
                        pass

                results.append({
                    'sample': sample,
                    'result': r,
                    'target': target,
                    'ucl': ucl,
                    'lcl': lcl,
                    'in_control': in_control
                })

        return render_template(
            'quality/control_charts.html',
            qc_results=results,
            title="QC Control Charts"
        )

    @bp.route("/api/westgard_summary")
    @login_required
    def api_westgard_summary():
        """
        Бүх QC sample + analysis_code хослолд Westgard статус авах.
        AnalysisResult-аас CM/GBW дээжний үр дүнг ашиглана.
        """
        qc_samples = _get_qc_samples()
        if not qc_samples:
            return jsonify({"qc_samples": []})

        sample_ids = [s.id for s in qc_samples]
        samples_map = {s.id: s for s in qc_samples}

        # Бүх QC үр дүнг авах
        all_results = _get_qc_results(sample_ids)

        # Sample type + analysis_code-оор бүлэглэх
        # Key: (sample_type, analysis_code)
        grouped = {}
        for r in all_results:
            sample = samples_map.get(r.sample_id)
            if not sample:
                continue

            # Sample type тодорхойлох (CM эсвэл GBW)
            sample_type = (sample.sample_type or "").upper()
            sample_code = (sample.sample_code or "").upper()

            if "GBW" in sample_type or "GBW" in sample_code:
                qc_type = "GBW"
            elif "CM" in sample_type or "CM" in sample_code:
                qc_type = "CM"
            else:
                continue

            key = (qc_type, r.analysis_code)
            if key not in grouped:
                grouped[key] = {
                    'results': [],
                    'sample': sample  # Эхний sample-ийг хадгалах (target авахад)
                }

            if r.final_result is not None:
                try:
                    grouped[key]['results'].append({
                        'value': float(r.final_result),
                        'date': r.updated_at,
                        'sample_code': sample.sample_code
                    })
                except (ValueError, TypeError):
                    pass

        # Westgard шалгах
        summary = []
        for (qc_type, analysis_code), data in grouped.items():
            results_list = data['results']
            sample = data['sample']

            if len(results_list) < 2:
                summary.append({
                    "qc_type": qc_type,
                    "analysis_code": analysis_code,
                    "status": "insufficient_data",
                    "count": len(results_list),
                    "message": "Хамгийн багадаа 2 хэмжилт хэрэгтэй"
                })
                continue

            # Огноогоор эрэмбэлэх (сүүлийнх нь эхэнд)
            results_list.sort(key=lambda x: x['date'] or '', reverse=True)
            values = [r['value'] for r in results_list[:20]]  # Сүүлийн 20

            # Target болон SD авах
            target, ucl, lcl, sd = _get_target_and_tolerance(sample, analysis_code)

            if target is None:
                # Target байхгүй бол өөрөө тооцох
                target = statistics.mean(values)
                sd = statistics.stdev(values) if len(values) >= 2 else 1

            if sd <= 0:
                sd = 0.001

            # Westgard шалгах
            violations = check_westgard_rules(values, target, sd)
            qc_status = get_qc_status(violations)

            # ✅ Prometheus metrics: QC check-ийг track хийх
            track_qc_check(
                check_type="westgard",
                result=qc_status["status"]  # pass, warning, fail
            )

            summary.append({
                "qc_type": qc_type,
                "analysis_code": analysis_code,
                "status": qc_status["status"],
                "rules_violated": qc_status.get("rules_violated", []),
                "count": len(values),
                "target": round(target, 4),
                "sd": round(sd, 4),
                "latest_value": round(values[0], 4) if values else None
            })

        # Эрэмбэлэх
        summary.sort(key=lambda x: (x['qc_type'], x['analysis_code']))

        return jsonify({"qc_samples": summary})

    @bp.route("/api/westgard_detail/<qc_type>/<analysis_code>")
    @login_required
    def api_westgard_detail(qc_type, analysis_code):
        """
        Тодорхой QC төрөл + шинжилгээний дэлгэрэнгүй Westgard мэдээлэл.
        """
        qc_samples = _get_qc_samples()
        if not qc_samples:
            return jsonify({"error": "QC дээж олдсонгүй"})

        # Төрлөөр шүүх
        filtered_samples = []
        for s in qc_samples:
            sample_type = (s.sample_type or "").upper()
            sample_code = (s.sample_code or "").upper()

            if qc_type.upper() == "GBW":
                if "GBW" in sample_type or "GBW" in sample_code:
                    filtered_samples.append(s)
            elif qc_type.upper() == "CM":
                if "CM" in sample_type or "CM" in sample_code:
                    filtered_samples.append(s)

        if not filtered_samples:
            return jsonify({"error": f"{qc_type} дээж олдсонгүй"})

        sample_ids = [s.id for s in filtered_samples]
        samples_map = {s.id: s for s in filtered_samples}

        # Үр дүнгүүд авах
        results = _get_qc_results(sample_ids, analysis_code)

        data_points = []
        for r in results:
            sample = samples_map.get(r.sample_id)
            if not sample or r.final_result is None:
                continue
            try:
                data_points.append({
                    'value': float(r.final_result),
                    'date': r.updated_at.isoformat() if r.updated_at else None,
                    'sample_code': sample.sample_code,
                    'operator': r.user.username if r.user else None
                })
            except (ValueError, TypeError, AttributeError):
                pass

        if len(data_points) < 2:
            return jsonify({
                "qc_type": qc_type,
                "analysis_code": analysis_code,
                "status": "insufficient_data",
                "count": len(data_points)
            })

        # Огноогоор эрэмбэлэх
        data_points.sort(key=lambda x: x['date'] or '', reverse=True)
        values = [d['value'] for d in data_points[:20]]

        # Target авах
        target, ucl, lcl, sd = _get_target_and_tolerance(filtered_samples[0], analysis_code)

        if target is None:
            target = statistics.mean(values)
            sd = statistics.stdev(values) if len(values) >= 2 else 1
            ucl = target + 2 * sd
            lcl = target - 2 * sd

        if sd <= 0:
            sd = 0.001

        # Westgard шалгах
        violations = check_westgard_rules(values, target, sd)
        qc_status = get_qc_status(violations)
        latest_check = check_single_value(values[0], target, sd) if values else None

        return jsonify({
            "qc_type": qc_type,
            "analysis_code": analysis_code,
            "count": len(values),
            "target": round(target, 4),
            "ucl": round(ucl, 4),
            "lcl": round(lcl, 4),
            "sd": round(sd, 4),
            "qc_status": qc_status,
            "latest_value": {
                "value": round(values[0], 4) if values else None,
                "check": latest_check
            },
            "violations": [
                {
                    "rule": v.rule,
                    "description": v.description,
                    "severity": v.severity,
                    "values": [round(x, 4) for x in v.values]
                }
                for v in violations
            ],
            "data_points": data_points[:20]
        })
