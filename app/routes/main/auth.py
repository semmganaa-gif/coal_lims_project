# app/routes/main/auth.py
# -*- coding: utf-8 -*-
"""
Нэвтрэх/Гарах (Authentication) routes
"""

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user
from app import db, limiter
from app.forms import LoginForm
import sqlalchemy as sa

from .helpers import is_safe_url


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # =====================================================================
    # 1. НЭВТРЭХ
    # =====================================================================
    @bp.route("/login", methods=["GET", "POST"])
    @limiter.limit("5 per minute")  # Brute force халдлагаас хамгаалах
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("main.index"))

        from app.models import User
        form = LoginForm()

        if form.validate_on_submit():
            user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
            if user is None or not user.check_password(form.password.data):
                flash("Нэр эсвэл нууц үг буруу байна", "danger")
                return redirect(url_for("main.login"))
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get("next")
            if not next_page or not is_safe_url(next_page):
                next_page = url_for("main.index")
            return redirect(next_page)

        return render_template("login.html", title="Нэвтрэх", form=form)

    # =====================================================================
    # 2. ГАРАХ
    # =====================================================================
    @bp.route("/logout")
    def logout():
        logout_user()
        return redirect(url_for("main.login"))
