# app/routes/settings_routes.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, abort
from flask_login import login_required, current_user
from datetime import datetime
import json
import os
import re

from app import db
from app.utils.database import safe_commit
from app.utils.repeatability_loader import load_limit_rules, clear_cache
from app.models import Bottle, BottleConstant, SystemSetting  # моделууд models.py дотор байгаа хувилбар
from app.utils.datetime import now_local as now_mn  # ✅ Монгол цагийн функц

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


# -----------------------
# Natural sorting helper
# -----------------------
def _natural_sort_key(serial_no: str):
    """
    Natural sorting key for bottle serial numbers.
    "PY-1", "PY-2", "PY-10" → correctly sorted as 1, 2, 10
    """
    if not serial_no:
        return []
    # Split string into text and number parts
    parts = re.split(r'(\d+)', serial_no)
    # Convert numeric parts to integers for proper sorting
    return [int(p) if p.isdigit() else p.lower() for p in parts]

# -----------------------
# Эрхийн шалгалтын helper
# -----------------------


def _is_admin() -> bool:
    return getattr(current_user, "role", "") == "admin"


def _is_senior_or_admin() -> bool:
    return getattr(current_user, "role", "") in ("senior", "admin")


# ================================
# 1) ЖАГСААЛТ  (Химич: зөвхөн харах)
# ================================
@settings_bp.route("/bottles", methods=["GET"])
@login_required
def bottles_index():
    """Бортого бүрийн хамгийн сүүлийн тогтмолын мөрийг хавсаргаж харуулна."""
    # Natural sorting: PY-1, PY-2, ..., PY-10 (not PY-1, PY-10, PY-2)
    bottles = Bottle.query.all()
    bottles.sort(key=lambda b: _natural_sort_key(b.serial_no or ""))

    latest_by_bottle: dict[int, BottleConstant] = {}
    if bottles:
        ids = [b.id for b in bottles]
        rows = (
            BottleConstant.query
            .filter(BottleConstant.bottle_id.in_(ids))
            .order_by(
                BottleConstant.bottle_id.asc(),
                BottleConstant.effective_from.desc(),
                BottleConstant.created_at.desc(),
            )
            .all()
        )
        for bc in rows:
            if bc.bottle_id not in latest_by_bottle:
                latest_by_bottle[bc.bottle_id] = bc

    return render_template(
        "settings/bottles_index.html",
        title="Бортого тогтмол — жагсаалт",
        bottles=bottles,
        latest_by_bottle=latest_by_bottle,
        can_create=_is_senior_or_admin(),
        can_edit_delete=_is_senior_or_admin(),  # химичид товчнууд харагдахгүй
    )


# ==================================
# 2) ШИНЭ ТОГТМОЛ ОРУУЛАХ (ахлах/админ)
# ==================================
@settings_bp.route("/bottles/constants/new", methods=["GET", "POST"])
@login_required
def bottles_constants_new():
    if not _is_senior_or_admin():
        flash("Зөвхөн ахлах/админ хэрэглэгч энэ хэсэгт хандах боломжтой.", "danger")
        return redirect(url_for("settings.bottles_index"))

    if request.method == "POST":
        serial_no = (request.form.get("serial_no") or "").strip()

        # t1, t2 заавал; t3 сонголттой
        try:
            t1 = float(request.form.get("trial_1") or "nan")
            t2 = float(request.form.get("trial_2") or "nan")
        except Exception:
            flash("Туршилт 1, 2 тоон утга шаардлагатай.", "danger")
            return redirect(url_for("settings.bottles_constants_new"))

        t3_raw = request.form.get("trial_3")
        t3 = float(t3_raw) if t3_raw not in (None, "",) else None

        # температур (optional, default 20 °C)
        try:
            temperature_c = float(request.form.get("temperature_c") or 20.0)
        except Exception:
            temperature_c = 20.0

        remarks = (request.form.get("remarks") or "").strip()

        if not serial_no:
            flash("Бортогоны дугаар (serial_no) шаардлагатай.", "danger")
            return redirect(url_for("settings.bottles_constants_new"))

        # Bottle хайх/үүсгэх
        bottle = Bottle.query.filter_by(serial_no=serial_no).first()
        if not bottle:
            bottle = Bottle(
                serial_no=serial_no,
                is_active=True,
                created_by_id=getattr(current_user, "id", None),
                created_at=now_mn(),
            )
            db.session.add(bottle)
            db.session.flush()
        else:
            bottle.is_active = True

        # 0.0015 тохирцын дүрэм
        try:
            avg_value, used_pair = _avg_with_tolerance(t1, t2, t3)
        except ValueError as e:
            flash(str(e), "danger")
            return render_template(
                "settings/bottles_constants_new.html",
                title="Бортого тогтмол — шинэ",
                preview=None,
            )

        # Хадгалалт
        const = BottleConstant(
            bottle_id=bottle.id,
            trial_1=t1,
            trial_2=t2,
            trial_3=t3,  # nullable
            avg_value=avg_value,
            temperature_c=temperature_c,
            remarks=remarks,
            created_by_id=getattr(current_user, "id", None),
            created_at=now_mn(),
            effective_from=now_mn(),
        )
        db.session.add(const)
        if not safe_commit(
            f"Хадгалагдлаа. Дундаж m₂ = {avg_value:.5f} (ашигласан хос: {used_pair})",
            "Тогтмол хадгалахад алдаа гарлаа"
        ):
            return redirect(url_for("settings.bottles_constants_new"))

        return redirect(url_for("settings.bottles_index"))

    # GET
    return render_template(
        "settings/bottles_constants_new.html",
        title="Бортого тогтмол — шинэ",
    )


# ==================================
# 2b) BULK ТОГТМОЛ ОРУУЛАХ (ахлах/админ)
# ==================================
@settings_bp.route("/bottles/constants/bulk", methods=["GET"])
@login_required
def bottles_constants_bulk():
    """Олон бортогод нэг дор тогтмол оруулах хуудас"""
    if not _is_senior_or_admin():
        flash("Зөвхөн ахлах/админ хэрэглэгч энэ хэсэгт хандах боломжтой.", "danger")
        return redirect(url_for("settings.bottles_index"))

    # Идэвхтэй бортогуудыг natural sorting-ээр харуулах
    bottles = Bottle.query.filter_by(is_active=True).all()
    bottles.sort(key=lambda b: _natural_sort_key(b.serial_no or ""))

    return render_template(
        "settings/bottle_constants_bulk.html",
        title="Бортого тогтмол — bulk оруулалт",
        bottles=bottles,
    )


@settings_bp.route("/bottles/constants/bulk/save", methods=["POST"])
@login_required
def bottles_constants_bulk_save():
    """Bulk хадгалалт API"""
    from flask import jsonify

    if not _is_senior_or_admin():
        return jsonify({"success": False, "error": "Хандах эрхгүй"}), 403

    data = request.get_json(silent=True) or {}
    rows = data.get("rows", [])

    if not rows:
        return jsonify({"success": False, "error": "Хадгалах өгөгдөл байхгүй"}), 400

    created = 0
    errors = []

    for row in rows:
        serial = (row.get("serial") or "").strip()
        t1 = row.get("trial_1")
        t2 = row.get("trial_2")
        t3 = row.get("trial_3")
        temp_c = row.get("temperature_c", 20.0)
        eff_from_str = row.get("effective_from")
        remarks = row.get("remarks", "")

        if not serial or t1 is None or t2 is None:
            errors.append({"serial": serial, "error": "serial, trial_1, trial_2 шаардлагатай"})
            continue

        # Бортого хайх/үүсгэх
        bottle = Bottle.query.filter_by(serial_no=serial).first()
        if not bottle:
            bottle = Bottle(
                serial_no=serial,
                is_active=True,
                created_by_id=getattr(current_user, "id", None),
                created_at=now_mn(),
            )
            db.session.add(bottle)
            db.session.flush()
        else:
            bottle.is_active = True

        # Дундаж тооцоолол
        try:
            avg_value, used_pair = _avg_with_tolerance(float(t1), float(t2), float(t3) if t3 is not None else None)
        except ValueError as e:
            errors.append({"serial": serial, "error": str(e)})
            continue

        # Effective from parse
        eff_from = None
        if eff_from_str:
            try:
                eff_from = datetime.fromisoformat(eff_from_str)
            except Exception:
                eff_from = now_mn()
        else:
            eff_from = now_mn()

        const = BottleConstant(
            bottle_id=bottle.id,
            trial_1=float(t1),
            trial_2=float(t2),
            trial_3=float(t3) if t3 is not None else None,
            avg_value=avg_value,
            temperature_c=float(temp_c) if temp_c else 20.0,
            remarks=remarks,
            created_by_id=getattr(current_user, "id", None),
            created_at=now_mn(),
            effective_from=eff_from,
        )
        db.session.add(const)
        created += 1

    if not safe_commit():
        return jsonify({"success": False, "error": "Хадгалахад алдаа гарлаа"}), 500
    return jsonify({"success": True, "data": {"created": created, "errors": errors}})


# ============================
# 3) БОРТОГО ЗАСАХ (ахлах/админ)
# ============================
@settings_bp.route("/bottles/<int:bottle_id>/edit", methods=["GET", "POST"])
@login_required
def bottle_edit(bottle_id: int):
    if not _is_senior_or_admin():
        flash("Зөвхөн ахлах/админ хэрэглэгч энэ хэсэгт хандах боломжтой.", "danger")
        return redirect(url_for("settings.bottles_index"))

    bottle = Bottle.query.get_or_404(bottle_id)

    if request.method == "POST":
        serial_no = (request.form.get("serial_no") or "").strip()
        is_active = True if request.form.get("is_active") == "1" else False

        if not serial_no:
            flash("Бортогоны дугаар хоосон байж болохгүй.", "danger")
            return redirect(url_for("settings.bottle_edit", bottle_id=bottle.id))

        # serial_no давхцахгүй байх шалгалт (өөрөөс нь бусадтай)
        dup = Bottle.query.filter(Bottle.serial_no == serial_no, Bottle.id != bottle.id).first()
        if dup:
            flash("Ижил дугаартай бортого аль хэдийн бүртгэгдсэн байна.", "danger")
            return redirect(url_for("settings.bottle_edit", bottle_id=bottle.id))

        bottle.serial_no = serial_no
        bottle.is_active = is_active
        db.session.add(bottle)
        if not safe_commit("Бортогоны мэдээлэл шинэчлэгдлээ.", "Бортого засахад алдаа гарлаа"):
            return redirect(url_for("settings.bottle_edit", bottle_id=bottle.id))
        return redirect(url_for("settings.bottles_index"))

    # GET
    return render_template(
        "settings/bottle_form.html",
        title="Бортого — засах",
        bottle=bottle,
    )


# ==============================
# 4) БОРТОГО УСТГАХ (ахлах/админ)
# ==============================
@settings_bp.route("/bottles/<int:bottle_id>/delete", methods=["POST"])
@login_required
def bottle_delete(bottle_id: int):
    if not _is_senior_or_admin():
        return ("", 403)

    bottle = Bottle.query.get_or_404(bottle_id)
    serial = bottle.serial_no
    db.session.delete(bottle)  # cascade → constants устна
    safe_commit(f"Бортого {serial} бүртгэлээс устгагдлаа.", "Бортого устгахад алдаа гарлаа")
    return redirect(url_for("settings.bottles_index"))


# ==========================
# 5) Тохирцын helper функц
# ==========================
from app.constants import BOTTLE_TOLERANCE
TOL = BOTTLE_TOLERANCE  # хоосон тодорхойлолтын тохирц (грамм)


def _avg_with_tolerance(t1: float, t2: float, t3: float | None):
    """
    Дүрэм:
      1) |t1 - t2| ≤ 0.0015  →  avg = (t1 + t2)/2  (used='1-2')
      2) Хэрэв зөрүү > 0.0015 бол t3 заавал. Хосуудаас хамгийн бага зөрүүтэйг сонгоно,
         тэр хосын дундажийг авна. Хамгийн бага зөрүү нь 0.0015-аас их байвал алдаа.
    Return: (avg_value: float, used_pair: str)
    """
    if t1 is None or t2 is None:
        raise ValueError("Туршилт 1, 2 заавал.")

    d12 = abs(t1 - t2)
    if d12 <= TOL:
        return (t1 + t2) / 2.0, "1-2"

    if t3 is None:
        raise ValueError(f"|t1 - t2| = {d12:.5f} (> {TOL}) байна. 3 дахь туршилтаа оруулна уу.")

    d13 = abs(t1 - t3)
    d23 = abs(t2 - t3)
    pairs = {"1-2": d12, "1-3": d13, "2-3": d23}
    used = min(pairs, key=pairs.get)
    best = pairs[used]

    if best > TOL:
        raise ValueError(f"Ядаж хоёр туршилтын зөрүү {TOL:g}-аас дотроо байх ёстой. Дахин тогтмолжуулна уу.")

    if used == "1-3":
        return (t1 + t3) / 2.0, used
    elif used == "2-3":
        return (t2 + t3) / 2.0, used
    else:
        return (t1 + t2) / 2.0, used

# --- Бортого идэвхтэй тогтмол татах API ---


@settings_bp.route("/api/bottle/<serial_no>/active", methods=["GET"])
@login_required
def api_bottle_active(serial_no):
    # Зөвхөн ахлах/админ бус—химич ч үзэж болно (шинжилгээнд хэрэгтэй)
    bottle = Bottle.query.filter_by(serial_no=serial_no).first()
    if not bottle:
        return {"success": False, "error": "not_found"}, 404
    const = (
        BottleConstant.query
        .filter_by(bottle_id=bottle.id)
        .order_by(BottleConstant.effective_from.desc(), BottleConstant.created_at.desc())
        .first()
    )
    if not const:
        return {"success": False, "error": "no_constant"}, 404
    return {
        "success": True,
        "data": {
            "avg_value": float(const.avg_value),
            "temperature_c": float(const.temperature_c or 20.0),
            "effective_from": const.effective_from.isoformat() if const.effective_from else None,
        }
    }


# ==================================
# 3) Repeatability limits settings (Senior, Manager, Admin)
# ==================================
@settings_bp.route("/repeatability", methods=["GET", "POST"])
@login_required
def repeatability_limits():
    if not _is_senior_or_admin():
        flash("Зөвхөн ахлах түвшний хэрэглэгч засах эрхтэй.", "danger")
        return redirect(url_for("settings.bottles_index"))

    current_rules = load_limit_rules()
    if request.method == "POST":
        raw_json = request.form.get("limits_json") or ""
        try:
            parsed = json.loads(raw_json)
            if not isinstance(parsed, dict):
                raise ValueError("JSON обьект байх ёстой.")
        except Exception as e:
            flash(f"JSON задлах алдаа: {e}", "danger")
            return render_template(
                "settings/repeatability_limits.html",
                title="Repeatability лимитүүд",
                limits_json=raw_json,
            )

        setting = SystemSetting.query.filter_by(category="repeatability", key="limits").first()
        if not setting:
            setting = SystemSetting(category="repeatability", key="limits")
            db.session.add(setting)
        setting.value = json.dumps(parsed, ensure_ascii=False)
        if safe_commit("Лимитүүд амжилттай хадгалагдлаа.", "Лимит хадгалахад алдаа гарлаа"):
            clear_cache()
            current_rules = parsed

    pretty = json.dumps(current_rules, ensure_ascii=False, indent=2)
    return render_template(
        "settings/repeatability_limits.html",
        title="Repeatability лимитүүд",
        limits_json=pretty,
        rules=current_rules,
    )


# ==================================
# 4) Notification Settings (admin only)
# ==================================
@settings_bp.route("/notifications", methods=["GET", "POST"])
@login_required
def notification_settings():
    """Email мэдэгдлийн тохиргоо"""
    if not _is_admin():
        flash("Зөвхөн админ засах эрхтэй.", "danger")
        return redirect(url_for("settings.bottles_index"))

    notification_types = [
        {"key": "qc_alert", "label": "QC Alert (Westgard)", "desc": "Westgard дүрэм зөрчигдсөн үед"},
        {"key": "sample_status", "label": "Sample Status", "desc": "Дээжийн статус өөрчлөгдсөн үед"},
        {"key": "equipment", "label": "Equipment Calibration", "desc": "Калибровкийн хугацаа дөхсөн үед"},
    ]

    current_settings = {}
    for nt in notification_types:
        setting = SystemSetting.query.filter_by(
            category="notifications",
            key=f"{nt['key']}_recipients"
        ).first()
        current_settings[nt['key']] = setting.value if setting else ""

    if request.method == "POST":
        for nt in notification_types:
            recipients = request.form.get(f"{nt['key']}_recipients", "").strip()

            setting = SystemSetting.query.filter_by(
                category="notifications",
                key=f"{nt['key']}_recipients"
            ).first()

            if not setting:
                setting = SystemSetting(
                    category="notifications",
                    key=f"{nt['key']}_recipients"
                )
                db.session.add(setting)

            setting.value = recipients

        safe_commit("Мэдэгдлийн тохиргоо хадгалагдлаа.", "Мэдэгдлийн тохиргоо хадгалахад алдаа гарлаа")

        # Reload
        for nt in notification_types:
            setting = SystemSetting.query.filter_by(
                category="notifications",
                key=f"{nt['key']}_recipients"
            ).first()
            current_settings[nt['key']] = setting.value if setting else ""

    return render_template(
        "settings/notification_settings.html",
        title="Мэдэгдлийн тохиргоо",
        notification_types=notification_types,
        current_settings=current_settings,
    )


# ==================================
# 5) Report Email Settings (admin only)
# ==================================
@settings_bp.route("/email-recipients", methods=["GET", "POST"])
@login_required
def email_recipients():
    """Тайлан илгээх имэйл хаягийн тохиргоо (TO, CC)"""
    if not _is_admin():
        flash("Зөвхөн админ засах эрхтэй.", "danger")
        return redirect(url_for("settings.bottles_index"))

    # Одоогийн тохиргоог авах
    to_setting = SystemSetting.query.filter_by(
        category="email",
        key="report_recipients_to"
    ).first()
    cc_setting = SystemSetting.query.filter_by(
        category="email",
        key="report_recipients_cc"
    ).first()

    current_to = to_setting.value if to_setting else ""
    current_cc = cc_setting.value if cc_setting else ""

    if request.method == "POST":
        new_to = request.form.get("recipients_to", "").strip()
        new_cc = request.form.get("recipients_cc", "").strip()

        # TO хаягуудыг хадгалах
        if not to_setting:
            to_setting = SystemSetting(category="email", key="report_recipients_to")
            db.session.add(to_setting)
        to_setting.value = new_to
        to_setting.is_active = True

        # CC хаягуудыг хадгалах
        if not cc_setting:
            cc_setting = SystemSetting(category="email", key="report_recipients_cc")
            db.session.add(cc_setting)
        cc_setting.value = new_cc
        cc_setting.is_active = True

        if safe_commit("Имэйл хаягууд хадгалагдлаа.", "Имэйл хаяг хадгалахад алдаа гарлаа"):
            current_to = new_to
            current_cc = new_cc

    return render_template(
        "settings/email_recipients.html",
        title="Тайлан илгээх имэйл хаяг",
        current_to=current_to,
        current_cc=current_cc,
    )


# ==================================
# 6) Стандартын лавлах (SOP / Standards Reference)
# ==================================

# SOP файлуудын mapping - шинжилгээ тус бүрт холбогдох файлууд
SOP_MAPPING = {
    # Техникийн анализ
    "MT": {
        "name": "Нийт чийг (MT)",
        "mns": ["2. MNS ISO 589-2003 Нийт чийгийг тодорхойлох.pdf"],
        "sop": ["LAB.07.02 Нийт чийг тодорхойлох.docx"],
    },
    "Mad": {
        "name": "Дотоод чийг (Mad)",
        "mns": ["3. MNS GBT 212-2015 Нүүрсний техникийн шинжилгээний арга.pdf"],
        "sop": ["LAB.07.03 Дотоод чийг тодорхойлох.docx"],
    },
    "Aad": {
        "name": "Үнслэг (Aad)",
        "mns": ["3. MNS GBT 212-2015 Нүүрсний техникийн шинжилгээний арга.pdf"],
        "sop": ["LAB.07.05 Үнслэгийн гарц тодорхойлох.docx"],
    },
    "Vad": {
        "name": "Дэгдэмхий бодис (Vad)",
        "mns": ["3. MNS GBT 212-2015 Нүүрсний техникийн шинжилгээний арга.pdf"],
        "sop": ["LAB.07.04 Дэгдэмхий бодисын гарц тодорхойлох.docx"],
    },
    "CV": {
        "name": "Илчлэг (CV)",
        "mns": ["13. MNS GB-T 213-2024 Нүүрсний илчлэгийг тодорхойлох арга.pdf"],
        "sop": ["LAB.07.13 Нүүрсний илчлэг тодорхойлох арга.docx"],
    },
    # Элементийн анализ
    "TS": {
        "name": "Нийт хүхэр (TS)",
        "mns": ["8. MNS ISO 19579-2014 Нил улаан туяаны спектрометрээр хатуу түлшний хүхрийн хэмжээг тодорхойлох.pdf"],
        "sop": ["LAB.07.08 Нил улаан туяаны спектрометрээр хатуу түлшний хүхрийн хэмжээг тодорхойлох.docx"],
    },
    "P": {
        "name": "Фосфор (P)",
        "mns": [
            "11. MNS 7057-2024 Нүүрсэнд агуулагдах хүхэр, фосфор, хүнцэл болон "
            "хлорын агуулгыг тодорхойлох рентген флюресценцийн спектрометрийн арга.pdf"
        ],
        "sop": [
            "LAB.07.09 Нүүрсэнд агуулагдах фосфор, хлорын агуулгыг тодорхойлох "
            "рентген флюресценцийн спектрометрийн арга.docx"
        ],
    },
    "F": {
        "name": "Фтор (F)",
        "mns": ["10. MNS GB-T 4633-2024 Нүүрсэнд фторын агуулга тодорхойлох арга.pdf"],
        "sop": ["LAB.07.10 Нүүрсэнд фторын агуулга тодорхойлох арга.docx"],
    },
    "Cl": {
        "name": "Хлор (Cl)",
        "mns": [
            "11. MNS 7057-2024 Нүүрсэнд агуулагдах хүхэр, фосфор, хүнцэл болон "
            "хлорын агуулгыг тодорхойлох рентген флюресценцийн спектрометрийн арга.pdf"
        ],
        "sop": [
            "LAB.07.09 Нүүрсэнд агуулагдах фосфор, хлорын агуулгыг тодорхойлох "
            "рентген флюресценцийн спектрометрийн арга.docx"
        ],
    },
    # Коксжих чанар
    "CSN": {
        "name": "Хөөлтийн зэрэг (CSN)",
        "mns": ["6. MNS ISO 501-2003 Тигелийн аргаар хөөлтийн зэргийг тодорхойлох.pdf"],
        "sop": ["LAB.07.06 Хөөлтийн зэрэг тодорхойлох.docx"],
    },
    "Gi": {
        "name": "Барьцалдах чанар (Gi)",
        "mns": ["7. MNS ISO 15585-2014 Хатуу нүүрс. Барьцалдах (бөсөх) чанар тодорхойлох.pdf"],
        "sop": ["LAB.07.07 Барьцалдах чанар тодорхойлох.docx"],
    },
    "X": {
        "name": "Пластометр - X",
        "mns": ["14. Битумжсан нүүрсний пластометрийн үзүүлэлтийг тодорхойлох арга.pdf"],
        "sop": ["LAB.07.14 Нүүрсний Пластометрийн үзүүлэлт тодорхойлох арга.docx"],
    },
    "Y": {
        "name": "Пластометр - Y",
        "mns": ["14. Битумжсан нүүрсний пластометрийн үзүүлэлтийг тодорхойлох арга.pdf"],
        "sop": ["LAB.07.14 Нүүрсний Пластометрийн үзүүлэлт тодорхойлох арга.docx"],
    },
    # Бусад
    "TRD": {
        "name": "Харьцангуй нягт (TRD)",
        "mns": ["12. MNS GBT 217-2015 Нүүрсний харьцангуй нягт тодорхойлох арга.pdf"],
        "sop": ["LAB.07.12 Нүүрсний харьцангуй нягт тодорхойлох арга.docx"],
    },
    "FM": {
        "name": "Чөлөөт чийг / Дээж бэлтгэл (FM)",
        "mns": ["1. MNS GB-T 474-2015 Нүүрсний дээж бэлтгэх арга.pdf"],
        "sop": ["LAB.07.01 Нүүрсний дээж бэлтгэх арга.docx"],
    },
    "Solid": {
        "name": "Хатуу үлдэгдэл / Дээж бэлтгэл (Solid)",
        "mns": ["1. MNS GB-T 474-2015 Нүүрсний дээж бэлтгэх арга.pdf"],
        "sop": ["LAB.07.01 Нүүрсний дээж бэлтгэх арга.docx"],
    },
}

# Ангиллуудыг тодорхойлох
SOP_CATEGORIES = {
    "tech": {
        "name": "Техникийн анализ",
        "icon": "bi-thermometer-half",
        "codes": ["MT", "Mad", "Aad", "Vad", "CV"],
    },
    "element": {
        "name": "Элементийн анализ",
        "icon": "bi-circle-half",
        "codes": ["TS", "P", "F", "Cl"],
    },
    "coking": {
        "name": "Коксжих чанар",
        "icon": "bi-fire",
        "codes": ["CSN", "Gi", "X", "Y"],
    },
    "other": {
        "name": "Бусад",
        "icon": "bi-box",
        "codes": ["TRD", "FM", "Solid"],
    },
}


@settings_bp.route("/standards", methods=["GET"])
@login_required
def standards_reference():
    """Стандартын лавлах хуудас - SOP болон MNS стандартууд"""
    from flask import current_app

    # SOP фолдерт байгаа файлуудыг шалгах
    sop_folder = os.path.join(current_app.root_path, "..", "SOP")
    sop_folder = os.path.abspath(sop_folder)

    available_files = set()
    if os.path.exists(sop_folder):
        available_files = set(os.listdir(sop_folder))

    # Ангиллуудад файлуудын байгаа эсэхийг нэмэх
    categories_data = {}
    for cat_key, cat_info in SOP_CATEGORIES.items():
        cat_data = {
            "name": cat_info["name"],
            "icon": cat_info["icon"],
            "analyses": [],
        }
        for code in cat_info["codes"]:
            if code in SOP_MAPPING:
                analysis = SOP_MAPPING[code].copy()
                analysis["code"] = code
                # Файлууд байгаа эсэхийг шалгах
                analysis["mns_available"] = [f for f in analysis.get("mns", []) if f in available_files]
                analysis["sop_available"] = [f for f in analysis.get("sop", []) if f in available_files]
                cat_data["analyses"].append(analysis)
        categories_data[cat_key] = cat_data

    return render_template(
        "settings/standards_reference.html",
        title="Стандартын лавлах",
        categories=categories_data,
    )


@settings_bp.route("/standards/view/<path:filename>")
@login_required
def view_standard_file(filename):
    """SOP/Стандарт файл үзэх"""
    from flask import current_app

    sop_folder = os.path.join(current_app.root_path, "..", "SOP")
    sop_folder = os.path.abspath(sop_folder)

    # Аюулгүй байдлын шалгалт - path traversal
    requested_path = os.path.abspath(os.path.join(sop_folder, filename))
    if not requested_path.startswith(sop_folder):
        abort(403)

    if not os.path.exists(requested_path):
        abort(404)

    # Файлын төрөл тодорхойлох
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return send_from_directory(sop_folder, filename, mimetype="application/pdf")
    elif ext == ".docx":
        return send_from_directory(
            sop_folder,
            filename,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True
        )
    else:
        abort(400)
