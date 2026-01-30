"""Update QC Control Charts API with date filtering and more metadata"""
import re

path = r'D:/coal_lims_project/app/routes/quality/control_charts.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# New api_westgard_detail function
new_detail = '''    @bp.route("/api/westgard_detail/<qc_type>/<analysis_code>")
    @limiter.exempt
    @login_required
    def api_westgard_detail(qc_type, analysis_code):
        """
        Тодорхой QC төрөл + шинжилгээний дэлгэрэнгүй Westgard мэдээлэл.
        Query params:
          - period: today, 7d, 30d, quarter, all (default: all)
        """
        # Огноо шүүлт
        period = request.args.get('period', 'all')
        now = datetime.now()
        date_from = None
        date_to = None

        if period == 'today':
            date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_to = now
        elif period == '7d':
            date_from = now - timedelta(days=7)
            date_to = now
        elif period == '30d':
            date_from = now - timedelta(days=30)
            date_to = now
        elif period == 'quarter':
            quarter_month = ((now.month - 1) // 3) * 3 + 1
            date_from = now.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)
            date_to = now

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

        # Үр дүнгүүд авах (огноо шүүлттэй)
        results = _get_qc_results(sample_ids, analysis_code, date_from, date_to)

        # Target авах
        target, ucl, lcl, sd = _get_target_and_tolerance(filtered_samples[0], analysis_code)

        if target is None:
            return jsonify({
                "qc_type": qc_type,
                "analysis_code": analysis_code,
                "status": "no_target",
                "message": "Энэ шинжилгээнд target утга тодорхойлогдоогүй байна"
            })

        # Өдөр бүрийн хэмжилтүүдийг бүлэглэх (давтан шинжилгээ илрүүлэх)
        by_day = {}
        data_points = []

        for r in results:
            sample = samples_map.get(r.sample_id)
            if not sample or r.final_result is None:
                continue
            try:
                val = float(r.final_result)
                date_str = r.updated_at.strftime('%Y-%m-%d') if r.updated_at else 'unknown'

                if date_str not in by_day:
                    by_day[date_str] = []

                # Target-аас хэтэрсэн эсэх
                in_2sd = lcl <= val <= ucl
                in_1sd = (target - sd) <= val <= (target + sd)

                point_status = 'ok'
                if not in_2sd:
                    point_status = 'out_of_control'
                elif not in_1sd:
                    point_status = 'warning'

                point = {
                    'value': val,
                    'date': r.updated_at.isoformat() if r.updated_at else None,
                    'date_short': date_str,
                    'sample_code': sample.sample_code,
                    'operator': r.user.username if r.user else None,
                    'result_status': r.status,
                    'point_status': point_status,
                    'is_retest': False
                }
                by_day[date_str].append(point)
                data_points.append(point)
            except (ValueError, TypeError, AttributeError):
                pass

        # Давтан шинжилгээг тэмдэглэх (өдөрт 2-оос олон бол)
        for date_str, points in by_day.items():
            if len(points) > 2:
                for i, p in enumerate(points):
                    if i >= 2:
                        p['is_retest'] = True

        values = [d['value'] for d in data_points]

        if len(values) < 1:
            return jsonify({
                "qc_type": qc_type,
                "analysis_code": analysis_code,
                "period": period,
                "status": "no_data",
                "count": 0,
                "target": round(target, 4),
                "sd": round(sd, 4),
                "data_points": []
            })

        if sd <= 0:
            sd = 0.001

        recent_values = values[:20] if len(values) >= 20 else values
        violations = check_westgard_rules(recent_values, target, sd) if len(recent_values) >= 2 else []
        qc_status = get_qc_status(violations) if violations or len(recent_values) >= 2 else {"status": "insufficient_data"}
        latest_check = check_single_value(values[0], target, sd) if values else None

        total_count = len(data_points)
        ok_count = sum(1 for d in data_points if d['point_status'] == 'ok')
        warning_count = sum(1 for d in data_points if d['point_status'] == 'warning')
        out_count = sum(1 for d in data_points if d['point_status'] == 'out_of_control')
        retest_count = sum(1 for d in data_points if d['is_retest'])
        rejected_count = sum(1 for d in data_points if d['result_status'] == 'rejected')

        return jsonify({
            "qc_type": qc_type,
            "analysis_code": analysis_code,
            "period": period,
            "count": total_count,
            "stats": {
                "ok": ok_count,
                "warning": warning_count,
                "out_of_control": out_count,
                "retest": retest_count,
                "rejected": rejected_count
            },
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
            "data_points": data_points
        })
'''

# Find and replace the old function
pattern = r'    @bp\.route\("/api/westgard_detail/<qc_type>/<analysis_code>"\).*?(?=\n\n|$)'
content = re.sub(pattern, new_detail.strip(), content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api_westgard_detail endpoint successfully')
