# app/routes/api/samples_api.py
# -*- coding: utf-8 -*-
"""
Дээжтэй холбоотой API endpoints:
  - /data - DataTables sample listing
  - /sample_summary - Sample summary with archive/unarchive
  - /sample_report/<int:sample_id> - Individual sample report
  - /sample_history/<int:sample_id> - Sample history
"""

from flask import (
    request,
    jsonify,
    url_for,
    redirect,
    render_template,
    flash,
)
from flask_login import login_required
from datetime import datetime, timedelta
import json

from app import db, limiter
from app.models import Sample, AnalysisResult, AnalysisResultLog
from app.utils.datetime import now_local
from app.utils.codes import to_base_list
from app.utils.conversions import calculate_all_conversions
from app.utils.parameters import PARAMETER_DEFINITIONS, get_canonical_name
from app.utils.security import escape_like_pattern
from app.constants import SUMMARY_VIEW_COLUMNS
from .helpers import _aggregate_sample_status


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # -----------------------------------------------------------
    # 1) DataTables-д өгөгдөл өгөх (index.html)
    #    GET /api/data
    # -----------------------------------------------------------
    @bp.route("/data", methods=["GET"])
    @login_required
    @limiter.limit("30 per minute")
    def data():
        draw = int(request.args.get("draw", 1))
        start = int(request.args.get("start", 0))
        length = int(request.args.get("length", 25))

        # DataTables-н багана тус бүрийн шүүлтүүр
        column_search = {}
        i = 0
        while True:
            col_data = request.args.get(f"columns[{i}][data]")
            if col_data is None:
                break
            search_val = request.args.get(f"columns[{i}][search][value]", "").strip()
            column_search[i] = search_val
            i += 1

        date_start = request.args.get("dateFilterStart")
        date_end = request.args.get("dateFilterEnd")

        q = Sample.query

        if date_start:
            try:
                ds = datetime.fromisoformat(date_start)
                q = q.filter(Sample.received_date >= ds)
            except Exception:
                pass
        if date_end:
            try:
                de = datetime.fromisoformat(date_end)
                q = q.filter(Sample.received_date <= de)
            except Exception:
                pass

        # Баганын шүүлтүүрүүд
        for idx, val in column_search.items():
            if not val:
                continue
            if idx == 1:
                # ID
                try:
                    q = q.filter(Sample.id == int(val))
                except Exception:
                    pass
            elif idx == 2:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.sample_code.ilike(f"%{safe_val}%"))
            elif idx == 3:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.client_name.ilike(f"%{safe_val}%"))
            elif idx == 4:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.sample_type.ilike(f"%{safe_val}%"))
            elif idx == 5:
                # ✅ ДЭЭЖНИЙ ТӨЛӨВ (хуурай / чийгтэй / шингэн)
                cond_col = None
                if hasattr(Sample, "sample_condition"):
                    cond_col = Sample.sample_condition
                elif hasattr(Sample, "sample_state"):
                    cond_col = Sample.sample_state
                else:
                    cond_col = Sample.status  # fallback
                safe_val = escape_like_pattern(val)
                q = q.filter(cond_col.ilike(f"%{safe_val}%"))
            elif idx == 6:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.delivered_by.ilike(f"%{safe_val}%"))
            elif idx == 7:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.prepared_by.ilike(f"%{safe_val}%"))
            elif idx == 9:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.notes.ilike(f"%{safe_val}%"))
            elif idx == 11:
                try:
                    w = float(val)
                    q = q.filter(Sample.weight == w)
                except Exception:
                    pass
            elif idx == 13:
                safe_val = escape_like_pattern(val)
                q = q.filter(Sample.analyses_to_perform.ilike(f"%{safe_val}%"))

        records_total = q.count()
        records_filtered = records_total

        samples = (
            q.order_by(Sample.received_date.desc())
            .offset(start)
            .limit(length)
            .all()
        )

        # ✅ Нэг дор бүх дээжийн шинжилгээний статустай map үүсгэнэ
        sample_ids = [s.id for s in samples]
        status_map: dict[int, set[str]] = {}
        if sample_ids:
            rows = (
                db.session.query(AnalysisResult.sample_id, AnalysisResult.status)
                .filter(AnalysisResult.sample_id.in_(sample_ids))
                .all()
            )
            for sid, st in rows:
                if sid not in status_map:
                    status_map[sid] = set()
                if st:
                    status_map[sid].add(st)

        data_rows = []
        for s in samples:
            # ✅ analyses_to_perform → base кодын жагсаалт
            try:
                raw_codes = json.loads(s.analyses_to_perform or "[]")
            except Exception:
                raw_codes = []
            analyses_base = to_base_list(raw_codes)
            analyses_txt = json.dumps(analyses_base, ensure_ascii=False)

            # ✅ ДЭЭЖНИЙ ТӨЛӨВ (condition)
            sample_condition_val = ""
            if hasattr(s, "sample_condition") and getattr(s, "sample_condition") is not None:
                sample_condition_val = getattr(s, "sample_condition")  # Хуурай/Чийгтэй/Шингэн
            elif hasattr(s, "sample_state") and getattr(s, "sample_state") is not None:
                sample_condition_val = getattr(s, "sample_state")

            # ✅ НЭГТСЭН ТӨЛӨВ (шинжилгээний статус)
            result_statuses = status_map.get(s.id, set())
            workflow_status = _aggregate_sample_status(s.status or "", result_statuses)

            action_html = (
                f'<a href="{url_for("main.edit_sample", sample_id=s.id)}" '
                f'class="btn btn-sm btn-outline-primary">Засах</a>'
            )

            data_rows.append(
                [
                    f'<input type="checkbox" class="sample-checkbox" value="{s.id}">',  # 0
                    s.id,  # 1
                    s.sample_code or "",  # 2
                    s.client_name or "",  # 3
                    s.sample_type or "",  # 4
                    sample_condition_val or "",  # 5  ✅ ДЭЭЖНИЙ ТӨЛӨВ
                    s.delivered_by or "",  # 6
                    s.prepared_by or "",  # 7
                    s.prepared_date.strftime("%Y-%m-%d") if s.prepared_date else "",  # 8
                    s.notes or "",  # 9
                    s.received_date.strftime("%Y-%m-%d %H:%M") if s.received_date else "",  # 10
                    s.weight or "",  # 11
                    workflow_status,  # 12 ✅ НЭГТСЭН ТӨЛӨВ
                    analyses_txt,  # 13
                    action_html,  # 14
                ]
            )

        return jsonify(
            {
                "draw": draw,
                "recordsTotal": records_total,
                "recordsFiltered": records_filtered,
                "data": data_rows,
            }
        )

    # -----------------------------------------------------------
    # 2) sample_summary.html → архив / сэргээх (POST /api/sample_summary)
    # -----------------------------------------------------------
    @bp.route("/sample_summary", methods=["GET", "POST"])
    @login_required
    @limiter.limit("20 per minute")
    def sample_summary():
        # --- POST (Архивлах) ---
        if request.method == "POST":
            action = request.form.get("action")
            sample_ids_str = request.form.get("sample_ids")
            if sample_ids_str and action in ["archive", "unarchive"]:
                try:
                    sample_ids = [
                        int(sid) for sid in sample_ids_str.split(",") if sid.isdigit()
                    ]
                    if sample_ids:
                        new_status = (
                            "archived" if action == "archive" else "new"
                        )  # (!!! "received" биш "new" болгов)
                        updated_count = (
                            db.session.query(Sample)
                            .filter(Sample.id.in_(sample_ids))
                            .update(
                                {Sample.status: new_status},
                                synchronize_session=False,
                            )
                        )
                        db.session.commit()
                        msg = (
                            f"{updated_count} дээжийг амжилттай архивд шилжүүллээ."
                            if action == "archive"
                            else f"{updated_count} дээжийг архивнаас амжилттай сэргээллээ."
                        )
                        flash(msg, "success")
                    return redirect(url_for("api.sample_summary", **request.args))
                except Exception as e:
                    db.session.rollback()
                    flash(f"Архивлах үед алдаа гарлаа: {e}", "danger")

        # -----------------------------------------------------------------
        # --- GET (Хуудас ачааллах) ---
        # -----------------------------------------------------------------
        page = request.args.get("page", 1, type=int)
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        show_archived = request.args.get("show_archived") == "on"
        filter_name = request.args.get("filter_name")

        # 1. Дээжүүдийг шүүж авах
        query = db.session.query(Sample)
        if show_archived:
            query = query.filter(Sample.status == "archived")
        else:
            query = query.filter(Sample.status != "archived")

        exists_q = (
            db.session.query(AnalysisResult.id)
            .filter(
                AnalysisResult.sample_id == Sample.id,
                AnalysisResult.status.in_(["approved", "pending_review"]),
            )
            .exists()
        )
        query = query.filter(exists_q)

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                query = query.filter(Sample.received_date >= start_date)
            except ValueError:
                flash(f"'{start_date_str}' буруу огнооны формат байна.", "warning")
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(Sample.received_date < end_date)
            except ValueError:
                flash(f"'{end_date_str}' буруу огнооны формат байна.", "warning")
        if filter_name:
            safe_filter_name = escape_like_pattern(filter_name)
            query = query.filter(Sample.sample_code.ilike(f"%{safe_filter_name}%"))

        query = query.order_by(Sample.received_date.desc())
        pagination = query.paginate(page=page, per_page=50, error_out=False)
        samples = pagination.items

        # -----------------------------------------------------------------
        # 🧮 ШИНЭЧИЛСЭН ТООЦООЛЛЫН ЛОГИК
        # -----------------------------------------------------------------
        results_map: dict[int, dict] = {}
        analysis_dates_map: dict[int, str] = {}
        final_analysis_types: list = []

        if samples:
            sample_ids = [s.id for s in samples]

            # 2) түүхий үр дүнг нэг дор
            all_db_results = (
                AnalysisResult.query.filter(
                    AnalysisResult.sample_id.in_(sample_ids),
                    AnalysisResult.status.in_(["approved", "pending_review"]),
                ).all()
            )

            # 3) sample + canonical
            canonical_results_by_sample = {sid: {} for sid in sample_ids}
            analysis_dates_raw_map = {sid: [] for sid in sample_ids}

            for r in all_db_results:
                canonical_name = get_canonical_name(r.analysis_code)
                if canonical_name:
                    canonical_results_by_sample[r.sample_id][canonical_name] = {
                        "value": r.final_result,
                        "id": r.id,
                        "status": r.status,
                    }
                if r.created_at:
                    analysis_dates_raw_map[r.sample_id].append(r.created_at)

            # 4) тооцооллын хөдөлгүүр
            for sample_id in sample_ids:
                raw_canonical_data = canonical_results_by_sample.get(sample_id, {})

                all_calculated_data = calculate_all_conversions(
                    raw_canonical_data, PARAMETER_DEFINITIONS
                )

                # 5) Template-д зориулж alias руу буцаах
                final_data_for_template = {}
                for col_view in SUMMARY_VIEW_COLUMNS:
                    template_code = col_view["code"]
                    canonical_base = col_view["canonical_base"]

                    lookup_key = get_canonical_name(template_code)

                    if template_code == "Ad":
                        lookup_key = "ash_d"
                    elif template_code == "Vdaf":
                        lookup_key = "volatile_matter_daf"
                    elif template_code == "FC,ad":
                        lookup_key = "fixed_carbon_ad"
                    elif template_code == "FC,d":
                        lookup_key = "fixed_carbon_d"
                    elif template_code == "FC,daf":
                        lookup_key = "fixed_carbon_daf"
                    elif template_code == "St,d":
                        lookup_key = "total_sulfur_d"
                    elif template_code == "St,daf":
                        lookup_key = "total_sulfur_daf"
                    elif template_code == "Qgr,d":
                        lookup_key = "calorific_value_d"
                    elif template_code == "Qgr,daf":
                        lookup_key = "calorific_value_daf"
                    elif template_code == "Qnet,ar":
                        lookup_key = "qnet_ar"
                    # (!!! ШИНЭЧИЛЛЭЛ)
                    elif template_code == "TRD,ad":
                        lookup_key = "relative_density"
                    elif template_code == "TRD,d":
                        lookup_key = "relative_density_d"
                    # (/!!! ШИНЭЧИЛЛЭЛ)
                    elif template_code == "H,d":
                        lookup_key = "hydrogen_d"
                    elif template_code == "P,d":
                        lookup_key = "phosphorus_d"
                    elif template_code == "F,d":
                        lookup_key = "total_fluorine_d"
                    elif template_code == "Cl,d":
                        lookup_key = "total_chlorine_d"

                    if lookup_key in all_calculated_data:
                        calculated_value = all_calculated_data[lookup_key]
                        if calculated_value is None:
                            continue

                        if isinstance(calculated_value, (int, float)):
                            raw_data_base = raw_canonical_data.get(canonical_base, {})
                            final_data_for_template[template_code] = {
                                "value": calculated_value,
                                "id": raw_data_base.get("id"),
                                "status": "calculated",
                            }
                        elif isinstance(calculated_value, dict):
                            final_data_for_template[template_code] = calculated_value

                results_map[sample_id] = final_data_for_template

            # 6) хамгийн эртний огноо
            for sample_id, dates in analysis_dates_raw_map.items():
                if dates:
                    analysis_dates_map[sample_id] = min(dates).strftime("%Y-%m-%d")

            # 7) grid-д харуулах нэршлүүд
            for col_map in SUMMARY_VIEW_COLUMNS:
                final_code = col_map["code"]
                canonical_name = get_canonical_name(final_code)

                if final_code == "Ad":
                    canonical_name = "ash_d"
                elif final_code == "Vdaf":
                    canonical_name = "volatile_matter_daf"
                elif final_code == "FC,ad":
                    canonical_name = "fixed_carbon_ad"
                elif final_code == "FC,d":
                    canonical_name = "fixed_carbon_d"
                elif final_code == "FC,daf":
                    canonical_name = "fixed_carbon_daf"
                elif final_code == "St,d":
                    canonical_name = "total_sulfur_d"
                elif final_code == "St,daf":
                    canonical_name = "total_sulfur_daf"
                elif final_code == "Qgr,d":
                    canonical_name = "calorific_value_d"
                elif final_code == "Qgr,daf":
                    canonical_name = "calorific_value_daf"
                elif final_code == "Qnet,ar":
                    canonical_name = "qnet_ar"
                # (!!! ШИНЭЧИЛЛЭЛ)
                elif final_code == "TRD,ad":
                    canonical_name = "relative_density"
                elif final_code == "TRD,d":
                    canonical_name = "relative_density_d"
                # (/!!! ШИНЭЧИЛЛЭЛ)
                elif final_code == "H,d":
                    canonical_name = "hydrogen_d"
                elif final_code == "P,d":
                    canonical_name = "phosphorus_d"
                elif final_code == "F,d":
                    canonical_name = "total_fluorine_d"
                elif final_code == "Cl,d":
                    canonical_name = "total_chlorine_d"

                details = PARAMETER_DEFINITIONS.get(canonical_name)
                display_name = final_code
                if details and details.get("display_name"):
                    display_name = details["display_name"]

                # Fake объект – зөвхөн code/name хэрэгтэй
                fake_analysis_type = type(
                    "FakeType", (object,), {"code": final_code, "name": display_name}
                )()
                final_analysis_types.append(fake_analysis_type)

        return render_template(
            "sample_summary.html",
            title="Дээжний нэгтгэл",
            samples=samples,
            analysis_types=final_analysis_types,
            results_map=results_map,
            analysis_dates_map=analysis_dates_map,
            pagination=pagination,
            show_archived=show_archived,
        )

    # -----------------------------------------------------------
    # 3) ДЭЭЖНИЙ ТАЙЛАН
    # -----------------------------------------------------------
    @bp.route("/sample_report/<int:sample_id>")
    @login_required
    def sample_report(sample_id):
        sample = Sample.query.get_or_404(sample_id)
        report_date = now_local()

        raw_results = (
            AnalysisResult.query.filter(
                AnalysisResult.sample_id == sample_id,
                AnalysisResult.status.in_(["approved", "pending_review"]),
            ).all()
        )

        raw_canonical_data = {}
        for r in raw_results:
            canonical_name = get_canonical_name(r.analysis_code)
            if canonical_name:
                raw_canonical_data[canonical_name] = {
                    "value": r.final_result,
                    "id": r.id,
                    "status": r.status,
                }

        try:
            sample_calcs = calculate_all_conversions(
                raw_canonical_data, PARAMETER_DEFINITIONS
            )
        except Exception as e:
            flash(
                f"Тооцоолол хийхэд алдаа гарлаа: {e}. Шаардлагатай (MT, Mad) утгууд орсон эсэхийг шалгана уу.",
                "danger",
            )
            return redirect(request.referrer or url_for("api.sample_summary"))

        return render_template(
            "report.html",
            title=f"Тайлан: {sample.sample_code}",
            sample=sample,
            calcs=sample_calcs,  # Энэ бол тооцоолсон бүх утгатай dict
            report_date=report_date,
        )

    # -----------------------------------------------------------
    # 4) ДЭЭЖНИЙ ТҮҮХ
    # -----------------------------------------------------------
    @bp.route("/sample_history/<int:sample_id>")
    @login_required
    def sample_history(sample_id):
        sample = Sample.query.get_or_404(sample_id)
        results = (
            AnalysisResult.query.filter_by(sample_id=sample_id)
            .order_by(AnalysisResult.created_at.desc())
            .all()
        )
        logs = (
            AnalysisResultLog.query.filter_by(sample_id=sample_id)
            .order_by(AnalysisResultLog.timestamp.desc())
            .all()
        )
        return render_template(
            "sample_history.html",
            title=f"Түүх: {sample.sample_code}",  # ✅ sample_code болгосон
            sample=sample,
            results=results,
            logs=logs,
        )
