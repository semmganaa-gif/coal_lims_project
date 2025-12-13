# -*- coding: utf-8 -*-
"""
Datetime utils тестүүд
"""
import pytest
from datetime import datetime


class TestDatetimeModule:
    """Datetime module тестүүд"""

    def test_import_module(self):
        """Module import"""
        from app.utils import datetime as dt_utils
        assert dt_utils is not None

    def test_now_local_import(self):
        """now_local function import"""
        from app.utils.datetime import now_local
        assert now_local is not None

    def test_now_local_returns_datetime(self):
        """now_local returns datetime"""
        from app import create_app
        from app.utils.datetime import now_local

        app = create_app()
        with app.app_context():
            result = now_local()
            assert isinstance(result, datetime)

    def test_now_local_year(self):
        """now_local returns current year"""
        from app import create_app
        from app.utils.datetime import now_local

        app = create_app()
        with app.app_context():
            result = now_local()
            # Should be current year
            assert result.year >= 2024
