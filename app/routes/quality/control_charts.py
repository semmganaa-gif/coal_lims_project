# app/routes/quality/control_charts.py
"""QC Control Charts - ISO 17025 Clause 7.7.1

AnalysisResult-аас CM/GBW дээжний үр дүнг татаж Westgard шалгах.
"""

import json
import logging
import statistics
from datetime import datetime

from flask import render_template, jsonify, request, Response
from flask_login import login_required, current_user

from app.models import Sample, AnalysisResult, ControlStandard, GbwStandard
from app.repositories import ControlStandardRepository, GbwStandardRepository
from app.monitoring import track_qc_check
from app.utils.westgard import check_westgard_rules, get_qc_status, check_single_value
from app.services.qc_chart_service import (
    calculate_capability,
    calculate_moving_average,
    calculate_cusum,
    calculate_ewma,
    export_chart_data,
    create_corrective_action_from_violation,
)

logger = logging.getLogger(__name__)

# ad төлөвөөс хуурай төлөв (d) руу хөрвүүлэх шаардлагатай шинжилгээнүүд
AD_ANALYSES = {'Aad', 'Vad', 'Sad', 'Oad', 'Pad', 'Fad', 'Clad'}


def _convert_to_dry_basis(value: float, mad: float) -> float:
    """
    ad (air-dried) төлөвийг d (dry) төлөв рүү хөрвүүлэх.

    Formula: Value_d = Value_ad × 100 / (100 - Mad)
    """
    if mad is None or mad >= 100:
        return value
    return value * 100 / (100 - mad)


def _get_mad_for_sample(sample_id: int):
    """Sample-ийн Mad утгыг авах (хамгийн сүүлийн Mad-г авна)"""
    mad_result = (
        AnalysisResult.query
        .filter_by(sample_id=sample_id, analysis_code='Mad')
        .filter(AnalysisResult.final_result.isnot(None))
        .order_by(AnalysisResult.updated_at.desc())
        .first()
    )

    if mad_result and mad_result.final_result is not None:
        try:
            return float(mad_result.final_result)
        except (ValueError, TypeError):
            pass
    return None


def _get_qc_samples():
    """CM болон GBW дээжүүдийг олох (sample_type яг таарах)"""
    return Sample.query.filter(
        Sample.lab_type == 'coal',
        Sample.sample_type.in_(['CM', 'GBW'])
    ).order_by(Sample.id.desc()).all()


def _get_qc_results(sample_ids: list, analysis_code: str = None):
    """QC дээжүүдийн шинжилгээний үр дүнг авах"""
    # QC chart-д бүх үр дүнг (approved, pending_review, rejected) оруулна
    # rejected ч гэсэн түүхэнд бүртгэгдэх ёстой
    query = AnalysisResult.query.filter(
        AnalysisResult.sample_id.in_(sample_ids),
        AnalysisResult.status.in_(['approved', 'pending_review', 'rejected']),
        AnalysisResult.final_result.isnot(None)
    )
    if analysis_code:
        query = query.filter(AnalysisResult.analysis_code == analysis_code)

    return query.order_by(AnalysisResult.updated_at.desc()).all()


def _extract_standard_name(sample_code: str, sample_type: str = None) -> str:
    """
    Sample code-оос стандартын нэрийг задлах.

    Жишээ:
    - 'GBW11135a_20241213A' -> 'GBW11135a'
    - 'CM-2025-Q4_20241213AQ4' -> 'CM-2025-Q4'
    - 'CM_20241213A' -> идэвхтэй ControlStandard.name (fallback)
    """
    if not sample_code:
        return ''

    parts = sample_code.split('_')
    extracted = sample_code
    if len(parts) >= 2:
        # Сүүлийн хэсэг нь огноо (8 оронтой тоо эхэлдэг)
        for i in range(len(parts) - 1, 0, -1):
            if len(parts[i]) >= 8 and parts[i][:8].isdigit():
                extracted = '_'.join(parts[:i])
                break
        else:
            extracted = parts[0]

    # "CM" → идэвхтэй ControlStandard нэрээр солих
    if extracted.upper() == 'CM' and (sample_type or '').upper() == 'CM':
        active = ControlStandardRepository.get_active()
        if active:
            return active.name

    return extracted


def _get_target_and_tolerance(sample, analysis_code: str):
    """
    Sample code-оос стандартын нэрийг задалж, тэр стандартын target утга авах.

    Returns:
        (target, ucl, lcl, sd) эсвэл (None, None, None, None)
    """
    sample_code = sample.sample_code or ""
    standard_name = _extract_standard_name(sample_code, getattr(sample, 'sample_type', None))

    if not standard_name:
        return None, None, None, None

    # CM эсвэл GBW эсэхийг тодорхойлох
    sample_code_upper = sample_code.upper()

    sample_type = getattr(sample, 'sample_type', '') or ''
    active_std = None
    if sample_type.upper() == 'GBW' or 'GBW' in sample_code_upper:
        active_std = GbwStandardRepository.get_active_or_by_name(standard_name)
    elif sample_type.upper() == 'CM' or 'CM' in sample_code_upper:
        active_std = ControlStandardRepository.get_active_or_by_name(standard_name)
        if active_std:
            if active_std.name != standard_name:
                logger.info(f"CM fallback: '{standard_name}' -> '{active_std.name}'")

    if not active_std or not active_std.targets:
        return None, None, None, None

    targets = active_std.targets
    if isinstance(targets, str):
        try:
            targets = json.loads(targets)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None, None, None, None

    target_info = targets.get(analysis_code)
    if not target_info:
        return None, None, None, None

    # Target / SD авах
    try:
        if isinstance(target_info, dict):
            target = target_info.get('mean') or target_info.get('target') or target_info.get('value')
            tolerance = target_info.get('sd') or target_info.get('tolerance') or 0.5
        else:
            target = float(target_info)
            tolerance = 0.5

        if target is None:
            return None, None, None, None

        target = float(target)
        sd = float(tolerance)
    except (ValueError, TypeError):
        return None, None, None, None

    # (Чиний одоогийн шийдэлтэй адил) UCL/LCL = ±2SD
    ucl = target + 2 * sd
    lcl = target - 2 * sd

    return target, ucl, lcl, sd


def register_routes(bp):
    @bp.route("/control_charts")
    @login_required
    def control_charts_list():
        """QC Control Charts хуудас - CM/GBW үр дүнгүүд"""

        qc_samples = _get_qc_samples()
        sample_ids = [s.id for s in qc_samples]

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

                        if lcl is not None and val < lcl:
                            in_control = False
                        if ucl is not None and val > ucl:
                            in_control = False
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
        Бүх QC standard_name + analysis_code хослолд Westgard статус авах.
        AnalysisResult-аас CM/GBW дээжний үр дүнг ашиглана.
        """
        qc_samples = _get_qc_samples()
        if not qc_samples:
            return jsonify({"qc_samples": []})

        sample_ids = [s.id for s in qc_samples]
        samples_map = {s.id: s for s in qc_samples}

        all_results = _get_qc_results(sample_ids)

        # Key: (standard_name, analysis_code)
        grouped = {}

        for r in all_results:
            sample = samples_map.get(r.sample_id)
            if not sample:
                continue

            standard_name = _extract_standard_name(sample.sample_code or "", sample.sample_type)
            if not standard_name:
                continue

            st = (sample.sample_type or "").upper()
            if st == "GBW":
                qc_type = "GBW"
            elif st == "CM":
                qc_type = "CM"
            else:
                continue

            key = (standard_name, r.analysis_code)
            if key not in grouped:
                grouped[key] = {
                    'results': [],
                    'sample': sample,
                    'qc_type': qc_type,
                }

            if r.final_result is None:
                continue

            try:
                value = float(r.final_result)

                # ad -> dry
                if r.analysis_code in AD_ANALYSES:
                    mad = _get_mad_for_sample(r.sample_id)
                    if mad is not None:
                        value = _convert_to_dry_basis(value, mad)

                grouped[key]['results'].append({
                    'value': value,
                    'date': r.updated_at,
                    'sample_code': sample.sample_code
                })
            except (ValueError, TypeError):
                pass

        summary = []

        for (standard_name, analysis_code), data in grouped.items():
            results_list = data['results']
            sample = data['sample']
            qc_type = data.get('qc_type', 'CM')

            if len(results_list) < 2:
                summary.append({
                    "standard_name": standard_name,
                    "qc_type": qc_type,
                    "analysis_code": analysis_code,
                    "status": "insufficient_data",
                    "count": len(results_list),
                    "message": "Хамгийн багадаа 2 хэмжилт шаардлагатай"
                })
                continue

            # Westgard rules-д: хуучнаас шинэ дараалал
            results_list.sort(key=lambda x: x['date'] or datetime.min)
            values_all = [r['value'] for r in results_list]
            values = values_all[-20:]  # хамгийн сүүлийн 20 (chronological хэвээр)

            target, ucl, lcl, sd = _get_target_and_tolerance(sample, analysis_code)

            if target is None:
                target = statistics.mean(values)
                sd = statistics.stdev(values) if len(values) >= 2 else 1

            if sd <= 0:
                sd = 0.001

            violations = check_westgard_rules(values, target, sd)
            qc_status = get_qc_status(violations)

            track_qc_check(
                check_type="westgard",
                result=qc_status["status"]  # pass, warning, fail
            )

            latest_val = values[-1] if values else None

            summary.append({
                "standard_name": standard_name,
                "qc_type": qc_type,
                "analysis_code": analysis_code,
                "status": qc_status["status"],
                "rules_violated": qc_status.get("rules_violated", []),
                "count": len(values),
                "target": round(target, 4),
                "sd": round(sd, 4),
                "latest_value": round(latest_val, 4) if latest_val is not None else None
            })

        summary.sort(key=lambda x: (x['standard_name'], x['analysis_code']))
        return jsonify({"qc_samples": summary})

    @bp.route("/api/westgard_detail/<qc_type>/<analysis_code>")
    @login_required
    def api_westgard_detail(qc_type, analysis_code):
        """
        Тодорхой QC төрөл + шинжилгээний дэлгэрэнгүй Westgard мэдээлэл.
        """
        from flask import request as req
        standard_name_filter = req.args.get('standard_name')

        qc_samples = _get_qc_samples()
        if not qc_samples:
            return jsonify({"error": "QC дээж олдсонгүй"})

        filtered_samples = []
        for s in qc_samples:
            st = (s.sample_type or "").upper()
            if qc_type.upper() == "GBW" and st == "GBW":
                filtered_samples.append(s)
            elif qc_type.upper() == "CM" and st == "CM":
                filtered_samples.append(s)

        if not filtered_samples:
            return jsonify({"error": f"{qc_type} дээж олдсонгүй"})

        # standard_name-ээр шүүх (өөр стандартын дата холилдохгүй)
        if standard_name_filter:
            filtered_samples = [
                s for s in filtered_samples
                if _extract_standard_name(s.sample_code or "", s.sample_type) == standard_name_filter
            ]

        sample_ids = [s.id for s in filtered_samples]
        samples_map = {s.id: s for s in filtered_samples}

        results = _get_qc_results(sample_ids, analysis_code)

        data_points = []
        for r in results:
            sample = samples_map.get(r.sample_id)
            if not sample or r.final_result is None:
                continue

            try:
                value = float(r.final_result)

                # ad -> dry
                if analysis_code in AD_ANALYSES:
                    mad = _get_mad_for_sample(r.sample_id)
                    if mad is not None:
                        value = _convert_to_dry_basis(value, mad)

                data_points.append({
                    'value': value,
                    'date': r.updated_at.isoformat() if r.updated_at else None,
                    'sample_code': sample.sample_code,
                    'operator': r.user.username if getattr(r, "user", None) else None
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

        # String isoformat тул chronological sort хийхэд safe
        data_points.sort(key=lambda x: x['date'] or '', reverse=False)  # хуучнаас шинэ
        values_all = [d['value'] for d in data_points]
        values = values_all[-20:]  # хамгийн сүүлийн 20 (chronological)

        target, ucl, lcl, sd = _get_target_and_tolerance(filtered_samples[0], analysis_code)

        if target is None:
            target = statistics.mean(values)
            sd = statistics.stdev(values) if len(values) >= 2 else 1
            ucl = target + 2 * sd
            lcl = target - 2 * sd

        if sd <= 0:
            sd = 0.001

        violations = check_westgard_rules(values, target, sd)
        qc_status = get_qc_status(violations)

        latest_val = values[-1] if values else None
        latest_check = check_single_value(latest_val, target, sd) if latest_val is not None else None

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
                "value": round(latest_val, 4) if latest_val is not None else None,
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
            "data_points": data_points[-20:]  # хамгийн сүүлийн 20-г (хуучнаас шинэ) буцаана
        })

    @bp.route("/api/chart_advanced/<qc_type>/<analysis_code>")
    @login_required
    def api_chart_advanced(qc_type, analysis_code):
        """
        Advanced chart data: capability indices, moving average, CUSUM, EWMA.
        """
        standard_name = request.args.get('standard_name', '')

        qc_samples = _get_qc_samples()
        if not qc_samples:
            return jsonify(success=False, message="QC дээж олдсонгүй")

        filtered_samples = [
            s for s in qc_samples
            if (s.sample_type or "").upper() == qc_type.upper()
        ]

        if standard_name:
            filtered_samples = [
                s for s in filtered_samples
                if _extract_standard_name(s.sample_code or "", s.sample_type) == standard_name
            ]

        if not filtered_samples:
            return jsonify(success=False, message=f"{qc_type} дээж олдсонгүй")

        sample_ids = [s.id for s in filtered_samples]
        samples_map = {s.id: s for s in filtered_samples}
        results = _get_qc_results(sample_ids, analysis_code)

        data_points = []
        for r in results:
            sample = samples_map.get(r.sample_id)
            if not sample or r.final_result is None:
                continue
            try:
                value = float(r.final_result)
                if analysis_code in AD_ANALYSES:
                    mad = _get_mad_for_sample(r.sample_id)
                    if mad is not None:
                        value = _convert_to_dry_basis(value, mad)
                data_points.append({
                    'value': value,
                    'date': r.updated_at.isoformat() if r.updated_at else None,
                    'sample_code': sample.sample_code,
                    'operator': r.user.username if getattr(r, "user", None) else None
                })
            except (ValueError, TypeError, AttributeError):
                pass

        if len(data_points) < 2:
            return jsonify(success=False, message="Хангалттай өгөгдөл байхгүй", count=len(data_points))

        data_points.sort(key=lambda x: x['date'] or '')
        values = [d['value'] for d in data_points]

        target, ucl, lcl, sd = _get_target_and_tolerance(filtered_samples[0], analysis_code)
        if target is None:
            target = statistics.mean(values)
            sd = statistics.stdev(values) if len(values) >= 2 else 1
            ucl = target + 2 * sd
            lcl = target - 2 * sd

        if sd <= 0:
            sd = 0.001

        # Capability indices
        capability = calculate_capability(values, target, sd, ucl, lcl)

        # Moving average
        ma_window = min(int(request.args.get('ma_window', 5)), 20)
        moving_avg = calculate_moving_average(values, ma_window)

        # CUSUM
        cusum = calculate_cusum(values, target, sd=sd)

        # EWMA
        lam = min(float(request.args.get('ewma_lambda', 0.2)), 1.0)
        ewma = calculate_ewma(values, target, lam=lam, sd=sd)

        return jsonify(success=True, data={
            "capability": {
                "cp": capability.cp,
                "cpk": capability.cpk,
                "rsd_percent": capability.rsd_percent,
                "mean": capability.mean,
                "sd": capability.sd,
                "n": capability.n,
                "bias": capability.bias,
                "bias_percent": capability.bias_percent,
            },
            "moving_average": moving_avg,
            "ma_window": ma_window,
            "cusum": cusum,
            "ewma": ewma,
        })

    @bp.route("/api/chart_export/<qc_type>/<analysis_code>")
    @login_required
    def api_chart_export(qc_type, analysis_code):
        """Export chart data as CSV or JSON."""
        standard_name = request.args.get('standard_name', '')
        fmt = request.args.get('format', 'csv')

        qc_samples = _get_qc_samples()
        filtered_samples = [
            s for s in qc_samples
            if (s.sample_type or "").upper() == qc_type.upper()
        ]
        if standard_name:
            filtered_samples = [
                s for s in filtered_samples
                if _extract_standard_name(s.sample_code or "", s.sample_type) == standard_name
            ]

        if not filtered_samples:
            return jsonify(success=False, message="Дээж олдсонгүй"), 404

        sample_ids = [s.id for s in filtered_samples]
        samples_map = {s.id: s for s in filtered_samples}
        results = _get_qc_results(sample_ids, analysis_code)

        data_points = []
        for r in results:
            sample = samples_map.get(r.sample_id)
            if not sample or r.final_result is None:
                continue
            try:
                value = float(r.final_result)
                if analysis_code in AD_ANALYSES:
                    mad = _get_mad_for_sample(r.sample_id)
                    if mad is not None:
                        value = _convert_to_dry_basis(value, mad)
                data_points.append({
                    'value': round(value, 4),
                    'date': r.updated_at.isoformat() if r.updated_at else None,
                    'sample_code': sample.sample_code,
                    'operator': r.user.username if getattr(r, "user", None) else None
                })
            except (ValueError, TypeError, AttributeError):
                pass

        data_points.sort(key=lambda x: x['date'] or '')

        target, ucl, lcl, sd = _get_target_and_tolerance(filtered_samples[0], analysis_code)
        if target is None:
            values = [d['value'] for d in data_points]
            target = statistics.mean(values) if values else 0
            sd = statistics.stdev(values) if len(values) >= 2 else 1

        if sd <= 0:
            sd = 0.001

        content = export_chart_data(data_points, analysis_code, standard_name, target, sd, fmt)

        if fmt == "json":
            return Response(content, mimetype="application/json",
                            headers={"Content-Disposition": f"attachment; filename=qc_{analysis_code}.json"})
        else:
            return Response(content, mimetype="text/csv",
                            headers={"Content-Disposition": f"attachment; filename=qc_{analysis_code}.csv"})

    @bp.route("/api/chart_auto_ca", methods=["POST"])
    @login_required
    def api_chart_auto_ca():
        """Auto-create Corrective Action from QC violation."""
        if current_user.role not in ("admin", "manager", "senior_analyst"):
            return jsonify(success=False, message="Эрх хүрэлцэхгүй"), 403

        data = request.json or {}
        standard_name = data.get("standard_name", "")
        analysis_code = data.get("analysis_code", "")
        violations = data.get("violations", [])

        if not standard_name or not analysis_code:
            return jsonify(success=False, message="standard_name, analysis_code шаардлагатай"), 400

        ca_id = create_corrective_action_from_violation(
            standard_name, analysis_code, violations, current_user.id
        )

        if ca_id:
            return jsonify(success=True, data={"ca_id": ca_id},
                           message="Засвар арга хэмжээ автоматаар үүсгэгдлээ")
        else:
            return jsonify(success=False, message="Reject зөрчил олдсонгүй")
