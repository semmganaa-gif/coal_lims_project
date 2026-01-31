# app/routes/main/auth.py
# -*- coding: utf-8 -*-
"""
Нэвтрэх/Гарах (Authentication) routes
"""

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db, limiter
from app.forms import LoginForm
import sqlalchemy as sa

from app.utils.security import is_safe_url
from app.utils.audit import log_audit


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # =====================================================================
    # 1. НЭВТРЭХ
    # =====================================================================
    @bp.route("/login", methods=["GET", "POST"])
    @limiter.limit("5 per minute")  # Brute force халдлагаас хамгаалах
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("main.lab_selector"))

        from app.models import User
        form = LoginForm()

        if form.validate_on_submit():
            user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
            if user is None or not user.check_password(form.password.data):
                flash("Нэр эсвэл нууц үг буруу байна", "danger")
                log_audit(action='login_failed', details={'username': form.username.data})
                return redirect(url_for("main.login"))
            login_user(user, remember=form.remember_me.data)
            log_audit(action='login_success', details={'username': user.username, 'role': user.role})
            next_page = request.args.get("next")
            if not next_page or not is_safe_url(next_page):
                next_page = url_for("main.lab_selector")
            return redirect(next_page)

        return render_template("login.html", title="Нэвтрэх", form=form)

    # =====================================================================
    # 2. ГАРАХ
    # =====================================================================
    @bp.route("/logout")
    @login_required
    def logout():
        if current_user.is_authenticated:
            log_audit(action='logout', details={'username': current_user.username})
        logout_user()
        return redirect(url_for("main.login"))

    # =====================================================================
    # 3. ПРОФАЙЛ ТОХИРГОО (Email Signature)
    # =====================================================================
    @bp.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        """Хэрэглэгчийн профайл тохиргоо - Email signature"""
        from app.forms import UserProfileForm

        form = UserProfileForm()

        if form.validate_on_submit():
            current_user.full_name = form.full_name.data
            current_user.email = form.email.data
            current_user.phone = form.phone.data
            current_user.position = form.position.data
            db.session.commit()

            log_audit(
                action='profile_updated',
                details={
                    'full_name': form.full_name.data,
                    'email': form.email.data,
                    'position': form.position.data
                }
            )

            flash("Профайл амжилттай хадгалагдлаа!", "success")
            return redirect(url_for("main.profile"))

        # Өмнөх утгуудыг form-д оруулах
        if request.method == "GET":
            form.full_name.data = current_user.full_name or ""
            form.email.data = current_user.email or ""
            form.phone.data = current_user.phone or ""
            form.position.data = current_user.position or ""

        return render_template("profile.html", title="Миний профайл", form=form)
