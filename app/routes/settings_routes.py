# app/routes/settings_routes.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import json

from app import db
from app.utils.repeatability_loader import load_limit_rules, clear_cache
from app.models import Bottle, BottleConstant, SystemSetting  # моделууд models.py дотор байгаа хувилбар
from app.utils.datetime import now_local as now_mn  # ✅ Монгол цагийн функц

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")

# -----------------------
# Эрхийн шалгалтын helper
# -----------------------
def _is_admin() -> bool:
    return getattr(current_user, "role", "") == "admin"

def _is_ahlah_or_admin() -> bool:
    return getattr(current_user, "role", "") in ("ahlah", "admin")


# ================================
# 1) ЖАГСААЛТ  (Химич: зөвхөн харах)
# ================================
@settings_bp.route("/bottles", methods=["GET"])
@login_required
def bottles_index():
    """Бортого бүрийн хамгийн сүүлийн тогтмолын мөрийг хавсаргаж харуулна."""
    bottles = Bottle.query.order_by(Bottle.serial_no.asc()).all()

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
        can_create=_is_ahlah_or_admin(),
        can_edit_delete=_is_ahlah_or_admin(),  # химичид товчнууд харагдахгүй
    )


# ==================================
# 2) ШИНЭ ТОГТМОЛ ОРУУЛАХ (ахлах/админ)
# ==================================
@settings_bp.route("/bottles/constants/new", methods=["GET", "POST"])
@login_required
def bottles_constants_new():
    if not _is_ahlah_or_admin():
        flash("Энэ хэсэгт зөвхөн ахлах/админ нэвтрэнэ.", "danger")
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
            flash("Бортогын дугаар (serial_no) шаардлагатай.", "danger")
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
        db.session.commit()

        flash(f"Хадгаллаа. Дундаж m₂ = {avg_value:.5f} (ашигласан хос: {used_pair})", "success")
        return redirect(url_for("settings.bottles_index"))

    # GET
    return render_template(
        "settings/bottles_constants_new.html",
        title="Бортого тогтмол — шинэ",
    )


# ============================
# 3) БОРТОГО ЗАСАХ (ахлах/админ)
# ============================
@settings_bp.route("/bottles/<int:bottle_id>/edit", methods=["GET", "POST"])
@login_required
def bottle_edit(bottle_id: int):
    if not _is_ahlah_or_admin():
        flash("Энэ хэсэгт зөвхөн ахлах/админ нэвтрэнэ.", "danger")
        return redirect(url_for("settings.bottles_index"))

    bottle = Bottle.query.get_or_404(bottle_id)

    if request.method == "POST":
        serial_no = (request.form.get("serial_no") or "").strip()
        is_active = True if request.form.get("is_active") == "1" else False

        if not serial_no:
            flash("Бортогын дугаар хоосон байж болохгүй.", "danger")
            return redirect(url_for("settings.bottle_edit", bottle_id=bottle.id))

        # serial_no давхцахгүй байх шалгалт (өөрөөс нь бусадтай)
        dup = Bottle.query.filter(Bottle.serial_no == serial_no, Bottle.id != bottle.id).first()
        if dup:
            flash("Ижил дугаартай бортого бүртгэлтэй байна.", "danger")
            return redirect(url_for("settings.bottle_edit", bottle_id=bottle.id))

        bottle.serial_no = serial_no
        bottle.is_active = is_active
        db.session.add(bottle)
        db.session.commit()
        flash("Бортогын мэдээлэл шинэчлэгдлээ.", "success")
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
    if not _is_ahlah_or_admin():
        return ("", 403)

    bottle = Bottle.query.get_or_404(bottle_id)
    serial = bottle.serial_no
    db.session.delete(bottle)  # cascade → constants устна
    db.session.commit()
    flash(f"Бортого {serial} бүртгэлээс устлаа.", "success")
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
        return {"ok": False, "error": "not_found"}, 404
    const = (
        BottleConstant.query
        .filter_by(bottle_id=bottle.id)
        .order_by(BottleConstant.effective_from.desc(), BottleConstant.created_at.desc())
        .first()
    )
    if not const:
        return {"ok": False, "error": "no_constant"}, 404
    return {
        "ok": True,
        "avg_value": float(const.avg_value),
        "temperature_c": float(const.temperature_c or 20.0),
        "effective_from": const.effective_from.isoformat() if const.effective_from else None,
    }




# ==================================
# 3) Repeatability limits settings (admin only)
# ==================================
@settings_bp.route("/repeatability", methods=["GET", "POST"])
@login_required
def repeatability_limits():
    if not _is_admin():
        flash("Зөвхөн админ засварлана.", "danger")
        return redirect(url_for("settings.bottles_index"))

    current_rules = load_limit_rules()
    if request.method == "POST":
        raw_json = request.form.get("limits_json") or ""
        try:
            parsed = json.loads(raw_json)
            if not isinstance(parsed, dict):
                raise ValueError("JSON нь объект байх ёстой.")
        except Exception as e:
            flash(f"JSON уншихад алдаа: {e}", "danger")
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
        db.session.commit()
        clear_cache()
        flash("Лимитүүд амжилттай хадгаллаа.", "success")
        current_rules = parsed

    pretty = json.dumps(current_rules, ensure_ascii=False, indent=2)
    return render_template(
        "settings/repeatability_limits.html",
        title="Repeatability лимитүүд",
        limits_json=pretty,
        rules=current_rules,
    )



