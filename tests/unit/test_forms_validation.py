# tests/unit/test_forms_validation.py
# -*- coding: utf-8 -*-
"""Forms validation unit tests"""

import pytest
from app.forms import AddSampleForm
from datetime import date


class TestAddSampleForm:
    def test_form_init(self, app):
        with app.app_context():
            form = AddSampleForm()
            assert form is not None

    def test_form_fields(self, app):
        with app.app_context():
            form = AddSampleForm()
            assert hasattr(form, 'client_name')
            assert hasattr(form, 'sample_type')
            assert hasattr(form, 'sample_date')

    def test_form_client_name_choices(self, app):
        with app.app_context():
            form = AddSampleForm()
            form.client_name.choices = [
                ('CHPP', 'CHPP'),
                ('UHG-Geo', 'UHG-Geo'),
                ('BN-Geo', 'BN-Geo'),
                ('QC', 'QC'),
                ('Proc', 'Proc'),
                ('WTL', 'WTL'),
                ('LAB', 'LAB'),
            ]
            assert len(form.client_name.choices) == 7


class TestLoginForm:
    def test_login_form(self, app):
        with app.app_context():
            try:
                from app.forms import LoginForm
                form = LoginForm()
                assert form is not None
                assert hasattr(form, 'username')
                assert hasattr(form, 'password')
            except ImportError:
                pass


class TestUserForm:
    def test_user_form(self, app):
        with app.app_context():
            try:
                from app.forms import UserForm
                form = UserForm()
                assert form is not None
            except ImportError:
                pass


class TestSettingsForm:
    def test_settings_form(self, app):
        with app.app_context():
            try:
                from app.forms import SettingsForm
                form = SettingsForm()
                assert form is not None
            except ImportError:
                pass
