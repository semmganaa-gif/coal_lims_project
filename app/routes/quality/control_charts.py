# app/routes/quality/control_charts.py
"""QC Control Charts - ISO 17025 Clause 7.7.1

AnalysisResult-аас CM/GBW дээжний үр дүнг татаж Westgard шалгах.
"""

from flask import render_template, jsonify
from flask_login import login_required
from app import limiter
from app.models import Sample, AnalysisResult, AnalysisResultLog, ControlStandard, GbwStandard
from sqlalchemy import or_
import logging
import statistics

from app.utils.westgard import check_westgard_rules, get_qc_status, check_single_value
from app.monitoring import track_qc_check

logger = logging.getLogger(__name__)


# ============================================================
# DRY BASIS тооцоолол
# ============================================================
# Хуурай төлөв (dry basis) руу хөрвүүлэх mapping
# Key: CM стандарт дахь код (dry basis)
# Value: (DB дахь код (as-received), хөрвүүлэх эсэх)
DRY_BASIS_MAPPING = {
    'Ad': ('Aad', True),      # Aad -> Ad (хуурай)
    'Vd': ('Vad', True),      # Vad -> Vd (хуурай)
    'CV,d': ('CV', True),     # CV -> CV,d (хуурай)
    'St,d': ('TS', True),     # TS -> St,d (хуурай)
    'TRD,d': ('TRD', False),  # TRD аль хэдийн хуурай төлөвт
    'CSN': ('CSN', False),    # CSN хөрвүүлэхгүй
    'Gi': ('Gi', False),      # Gi хөрвүүлэхгүй
    'P': ('P', True),         # P -> хуурай (ad төлөвөөр ирдэг)
    'F': ('F', True),         # F -> хуурай (ad төлөвөөр ирдэг)
    'Cl': ('Cl', True),       # Cl -> хуурай (ad төлөвөөр ирдэг)
    'Mad': ('Mad', False),    # Mad өөрөө
}

# Урвуу mapping: DB код -> Стандарт код
DB_TO_STANDARD_CODE = {v[0]: k for k, v in DRY_BASIS_MAPPING.items()}


def convert_to_dry_basis(value: float, moisture: float) -> float:
    """As-received утгыг хуурай төлөв (dry basis) рүү хөрвүүлэх.

    Томъёо: dry = as_received * 100 / (100 - Mad)
    """
    if moisture is None or moisture >= 100:
        return value
    return value * 100 / (100 - moisture)


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


def _get_qc_results_from_log(sample_ids: list, analysis_code: str = None):
    """
    AnalysisResultLog-оос QC дээжүүдийн бүх түүхэн үр дүнг авах.
    Энэ нь AnalysisResult-аас өөр - нэг дээж дээр олон удаа хэмжсэн бүх үр дүнг авна.
    """
    query = AnalysisResultLog.query.filter(
        AnalysisResultLog.sample_id.in_(sample_ids),
        AnalysisResultLog.final_result_snapshot.isnot(None)
    )
    if analysis_code:
        query = query.filter(AnalysisResultLog.analysis_code == analysis_code)

    return query.order_by(AnalysisResultLog.timestamp.desc()).all()


def _get_active_cm_standard_name():
    """Идэвхтэй CM стандартын нэрийг авах"""
    active_cm = ControlStandard.query.filter_by(is_active=True).first()
    return active_cm.name if active_cm else 'CM'


def _extract_standard_name(sample_code: str) -> str:
    """
    Sample code-оос стандартын нэрийг задлах.

    Жишээ:
    - 'CM-2025-Q4_20251219_N' -> 'CM-2025-Q4'
    - 'CM_20251128_N_Q4' -> идэвхтэй CM стандарт нэр (жишээ: 'CM-2025-Q4')
    - 'GBW11135a_20241213A' -> 'GBW11135a'
    """
    if not sample_code:
        return ''

    sample_upper = sample_code.upper()

    # Хуучин CM формат: CM_YYYYMMDD_... -> идэвхтэй CM стандарт руу холбох
    # Шинэ формат: CM-2025-Q4_... -> CM-2025-Q4
    if sample_upper.startswith('CM_'):
        # Хуучин формат - идэвхтэй CM стандартын нэрийг ашиглах
        return _get_active_cm_standard_name()

    if sample_upper.startswith('CM-'):
        # Шинэ формат: CM-2025-Q4_20251219_N -> CM-2025-Q4
        parts = sample_code.split('_')
        if parts:
            return parts[0]  # CM-2025-Q4

    # GBW болон бусад формат
    parts = sample_code.split('_')
    if len(parts) >= 2:
        # Сүүлийн хэсэг нь огноо (8 оронтой тоо эхэлдэг)
        for i in range(len(parts) - 1, 0, -1):
            if len(parts[i]) >= 8 and parts[i][:8].isdigit():
                return '_'.join(parts[:i])
        return parts[0]
    return sample_code


def _get_target_and_tolerance(sample, analysis_code: str):
    """
    Sample code-оос стандартын нэрийг задалж, тэр стандартын target утга авах.

    Returns:
        (target, ucl, lcl, sd) эсвэл (None, None, None, None)
    """
    sample_code = sample.sample_code or ""
    standard_name = _extract_standard_name(sample_code)

    if not standard_name:
        return None, None, None, None

    # CM эсвэл GBW эсэхийг тодорхойлох
    sample_code_upper = sample_code.upper()

    active_std = None
    if "GBW" in sample_code_upper:
        # Стандарт нэрээр хайх
        active_std = GbwStandard.query.filter_by(name=standard_name).first()
    elif "CM" in sample_code_upper:
        # Стандарт нэрээр хайх
        active_std = ControlStandard.query.filter_by(name=standard_name).first()

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
    # Эхлээд шууд хайх, олдохгүй бол өөр нэршлүүд туршиж үзэх
    target_info = targets.get(analysis_code)

    if not target_info:
        # Reverse mapping: DB код -> Стандарт код (Aad -> Ad, TS -> St,d, гэх мэт)
        alt_codes = []
        for std_code, (db_code, _) in DRY_BASIS_MAPPING.items():
            if analysis_code == db_code:
                alt_codes.append(std_code)
            elif analysis_code == std_code:
                alt_codes.append(db_code)

        # Өөр нэршлүүд туршиж үзэх
        for alt_code in alt_codes:
            target_info = targets.get(alt_code)
            if target_info:
                break

    if not target_info:
        return None, None, None, None

    # Target утга авах
    if isinstance(target_info, dict):
        target = target_info.get('target') or target_info.get('value') or target_info.get('mean')
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
    @limiter.exempt
    @login_required
    def api_westgard_summary():
        """
        Бүх QC sample + analysis_code хослолд Westgard статус авах.
        AnalysisResultLog-оос түүхэн үр дүнг ашиглана (олон удаа хэмжсэн бүх үр дүн).
        CM стандартын бүх target шинжилгээг харуулна (өгөгдөл байхгүй ч гэсэн).
        """
        # Идэвхтэй CM стандартын target шинжилгээнүүд
        active_cm = ControlStandard.query.filter_by(is_active=True).first()
        cm_targets = {}
        cm_standard_name = None
        if active_cm and active_cm.targets:
            cm_standard_name = active_cm.name
            targets = active_cm.targets
            if isinstance(targets, str):
                import json
                try:
                    targets = json.loads(targets)
                except (json.JSONDecodeError, TypeError, ValueError):
                    targets = {}
            cm_targets = targets

        qc_samples = _get_qc_samples()
        if not qc_samples and not cm_targets:
            return jsonify({"qc_samples": []})

        sample_ids = [s.id for s in qc_samples]
        samples_map = {s.id: s for s in qc_samples}

        # AnalysisResultLog-оос бүх түүхэн үр дүнг авах
        all_results = _get_qc_results_from_log(sample_ids)

        # Mad (чийг) утгуудыг sample_id-аар цуглуулах
        # Тухайн дээжний хамгийн сүүлийн Mad утгыг ашиглана
        # (Mad нь дээжний шинж чанар тул огноогоор ялгах шаардлагагүй)
        mad_values = {}  # {sample_id: mad_value}
        mad_results_sorted = sorted(
            [r for r in all_results if r.analysis_code == 'Mad' and r.final_result_snapshot is not None],
            key=lambda x: x.timestamp or '',
            reverse=True  # Сүүлийнх нь эхэнд
        )
        for r in mad_results_sorted:
            if r.sample_id not in mad_values:  # Зөвхөн сүүлийн утгыг авах
                try:
                    mad_values[r.sample_id] = float(r.final_result_snapshot)
                except (ValueError, TypeError):
                    pass

        # Sample type + analysis_code-оор бүлэглэх (хуурай төлөв рүү хөрвүүлж)
        grouped = {}
        for r in all_results:
            sample = samples_map.get(r.sample_id)
            if not sample:
                continue

            # Sample code-оос стандарт нэрийг задлах
            standard_name = _extract_standard_name(sample.sample_code or "")
            if not standard_name:
                continue

            # CM эсвэл GBW эсэхийг тодорхойлох
            sample_code_upper = (sample.sample_code or "").upper()
            if "GBW" in sample_code_upper:
                qc_type = "GBW"
            elif "CM" in sample_code_upper:
                qc_type = "CM"
            else:
                continue

            # DB код -> Стандарт код руу хөрвүүлэх (Aad -> Ad, Vad -> Vd, гэх мэт)
            db_code = r.analysis_code
            standard_code = DB_TO_STANDARD_CODE.get(db_code, db_code)

            # CM стандартын target-д байгаа эсэхийг шалгах (MT гэх мэт хамааралгүй код хасах)
            if qc_type == "CM" and cm_targets and standard_code not in cm_targets:
                continue

            # Хуурай төлөв рүү хөрвүүлэх шаардлагатай эсэх
            needs_conversion = False
            if standard_code in DRY_BASIS_MAPPING:
                _, needs_conversion = DRY_BASIS_MAPPING[standard_code]

            # Стандарт нэр + стандарт код-оор бүлэглэх
            key = (standard_name, standard_code)
            if key not in grouped:
                grouped[key] = {
                    'results': [],
                    'sample': sample
                }

            if r.final_result_snapshot is not None:
                try:
                    value = float(r.final_result_snapshot)

                    # Хуурай төлөв рүү хөрвүүлэх (Mad ашиглан)
                    if needs_conversion and db_code != 'Mad':
                        mad = mad_values.get(r.sample_id)
                        if mad is None:
                            # Mad байхгүй бол хуурай төлөв тооцох боломжгүй - алгасах
                            continue
                        value = convert_to_dry_basis(value, mad)

                    grouped[key]['results'].append({
                        'value': value,
                        'date': r.timestamp,
                        'sample_code': sample.sample_code
                    })
                except (ValueError, TypeError):
                    pass

        # Westgard шалгах
        summary = []
        for (standard_name, analysis_code), data in grouped.items():
            results_list = data['results']
            sample = data['sample']

            # qc_type тодорхойлох (UI-д ашиглахад)
            qc_type = "GBW" if "GBW" in standard_name.upper() else "CM"

            if len(results_list) < 1:
                summary.append({
                    "standard_name": standard_name,
                    "qc_type": qc_type,
                    "analysis_code": analysis_code,
                    "status": "insufficient_data",
                    "count": len(results_list),
                    "message": "Хамгийн багадаа 1 хэмжилт хэрэгтэй"
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
                "standard_name": standard_name,
                "qc_type": qc_type,
                "analysis_code": analysis_code,
                "status": qc_status["status"],
                "rules_violated": qc_status.get("rules_violated", []),
                "count": len(values),
                "target": round(target, 4),
                "sd": round(sd, 4),
                "latest_value": round(values[0], 4) if values else None
            })

        # CM стандартын бүх target шинжилгээг нэмэх (өгөгдөл байхгүй ч гэсэн)
        if cm_standard_name and cm_targets:
            existing_codes = {item['analysis_code'] for item in summary if item['standard_name'] == cm_standard_name}
            for analysis_code, target_info in cm_targets.items():
                if analysis_code not in existing_codes:
                    # Target утга авах
                    if isinstance(target_info, dict):
                        target = target_info.get('target') or target_info.get('value') or target_info.get('mean')
                        sd = target_info.get('tolerance') or target_info.get('sd') or 0.5
                    else:
                        target = float(target_info) if target_info else None
                        sd = 0.5

                    summary.append({
                        "standard_name": cm_standard_name,
                        "qc_type": "CM",
                        "analysis_code": analysis_code,
                        "status": "no_data",
                        "count": 0,
                        "target": round(float(target), 4) if target else None,
                        "sd": round(float(sd), 4) if sd else None,
                        "latest_value": None,
                        "message": "Өгөгдөл байхгүй"
                    })

        # Тогтсон дараалал: Mad, Ad, Vd, St,d, CV,d, TRD,d, CSN, Gi, P, F, Cl
        ANALYSIS_ORDER = ['Mad', 'Ad', 'Vd', 'St,d', 'CV,d', 'TRD,d', 'CSN', 'Gi', 'P', 'F', 'Cl']

        def get_order(code):
            code_lower = code.lower()
            for i, o in enumerate(ANALYSIS_ORDER):
                if code_lower == o.lower() or code_lower.startswith(o.lower()):
                    return i
            return 999

        # Эрэмбэлэх (стандарт нэр, тогтсон дараалал)
        summary.sort(key=lambda x: (x['standard_name'], get_order(x['analysis_code'])))

        return jsonify({"qc_samples": summary})

    @bp.route("/api/westgard_detail/<qc_type>/<analysis_code>")
    @limiter.exempt
    @login_required
    def api_westgard_detail(qc_type, analysis_code):
        """
        Тодорхой QC төрөл + шинжилгээний дэлгэрэнгүй Westgard мэдээлэл.
        AnalysisResultLog-оос түүхэн үр дүнг ашиглана.
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

        # Стандарт код -> DB код руу хөрвүүлэх (Ad -> Aad, Vd -> Vad, гэх мэт)
        db_code = analysis_code
        needs_conversion = False
        if analysis_code in DRY_BASIS_MAPPING:
            db_code, needs_conversion = DRY_BASIS_MAPPING[analysis_code]

        # AnalysisResultLog-оос түүхэн үр дүнг авах (DB код ашиглан)
        results = _get_qc_results_from_log(sample_ids, db_code)

        # Mad (чийг) утгуудыг цуглуулах (хуурай төлөв рүү хөрвүүлэхэд)
        # Тухайн дээжний хамгийн сүүлийн Mad утгыг ашиглана
        mad_values = {}  # {sample_id: mad_value}
        if needs_conversion:
            mad_results = _get_qc_results_from_log(sample_ids, 'Mad')
            mad_results_sorted = sorted(
                [r for r in mad_results if r.final_result_snapshot is not None],
                key=lambda x: x.timestamp or '',
                reverse=True
            )
            for r in mad_results_sorted:
                if r.sample_id not in mad_values:
                    try:
                        mad_values[r.sample_id] = float(r.final_result_snapshot)
                    except (ValueError, TypeError):
                        pass

        data_points = []
        for r in results:
            sample = samples_map.get(r.sample_id)
            if not sample or r.final_result_snapshot is None:
                continue
            try:
                value = float(r.final_result_snapshot)

                # Хуурай төлөв рүү хөрвүүлэх
                if needs_conversion:
                    mad = mad_values.get(r.sample_id)
                    if mad is None:
                        # Mad байхгүй бол хуурай төлөв тооцох боломжгүй - алгасах
                        continue
                    value = convert_to_dry_basis(value, mad)

                data_points.append({
                    'value': value,
                    'date': r.timestamp.isoformat() if r.timestamp else None,
                    'sample_code': sample.sample_code,
                    'operator': r.user.username if r.user else None
                })
            except (ValueError, TypeError, AttributeError):
                pass

        if len(data_points) < 1:
            return jsonify({
                "qc_type": qc_type,
                "analysis_code": analysis_code,
                "status": "insufficient_data",
                "count": len(data_points),
                "data_points": []
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
