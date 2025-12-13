# tests/unit/test_forms_comprehensive.py
# -*- coding: utf-8 -*-
"""
Forms comprehensive tests
"""

import pytest
from app.forms import AddSampleForm, LoginForm


class TestAddSampleForm:
    """AddSampleForm тестүүд"""

    def test_form_creation(self, app):
        """Form үүсгэх"""
        with app.app_context():
            form = AddSampleForm()
            assert form is not None

    def test_form_has_client_name(self, app):
        """Form has client_name field"""
        with app.app_context():
            form = AddSampleForm()
            assert hasattr(form, 'client_name')

    def test_form_has_sample_type(self, app):
        """Form has sample_type field"""
        with app.app_context():
            form = AddSampleForm()
            assert hasattr(form, 'sample_type')

    def test_form_client_choices(self, app):
        """Form client choices"""
        with app.app_context():
            form = AddSampleForm()
            # Set choices
            form.client_name.choices = [
                ('CHPP', 'CHPP'),
                ('QC', 'QC'),
                ('WTL', 'WTL')
            ]
            assert len(form.client_name.choices) == 3


class TestLoginForm:
    """LoginForm тестүүд"""

    def test_login_form_creation(self, app):
        """Login form үүсгэх"""
        with app.app_context():
            form = LoginForm()
            assert form is not None

    def test_login_form_has_fields(self, app):
        """Login form has fields"""
        with app.app_context():
            form = LoginForm()
            assert hasattr(form, 'username')
            assert hasattr(form, 'password')
