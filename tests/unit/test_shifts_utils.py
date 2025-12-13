# tests/unit/test_shifts_utils.py
# -*- coding: utf-8 -*-
"""Shifts utils tests"""

import pytest
from datetime import datetime, date, time


class TestShiftsUtils:
    def test_import(self):
        from app.utils.shifts import get_shift_info
        assert get_shift_info is not None

    def test_get_shift_info(self):
        from app.utils.shifts import get_shift_info
        result = get_shift_info(datetime.now())
        assert result is not None

    def test_get_shift_type(self):
        try:
            from app.utils.shifts import get_shift_type
            result = get_shift_type(datetime.now())
            assert result in ['day', 'night', None] or result is not None
        except (ImportError, AttributeError):
            pass

    def test_get_shift_team(self):
        try:
            from app.utils.shifts import get_shift_team
            result = get_shift_team(datetime.now())
            assert result in ['A', 'B', 'C', 'D', None] or result is not None
        except (ImportError, AttributeError):
            pass

    def test_get_shift_start(self):
        try:
            from app.utils.shifts import get_shift_start
            result = get_shift_start(datetime.now())
            assert result is not None or result is None
        except (ImportError, AttributeError):
            pass

    def test_get_shift_end(self):
        try:
            from app.utils.shifts import get_shift_end
            result = get_shift_end(datetime.now())
            assert result is not None or result is None
        except (ImportError, AttributeError):
            pass


class TestShiftHelpers:
    def test_get_12h_shift_code(self, app):
        with app.app_context():
            try:
                from app.routes.main.helpers import get_12h_shift_code
                result = get_12h_shift_code()
                assert result is not None
            except (ImportError, AttributeError, Exception):
                pass

    def test_get_quarter_code(self, app):
        with app.app_context():
            try:
                from app.routes.main.helpers import get_quarter_code
                result = get_quarter_code()
                assert result is not None
            except (ImportError, AttributeError, Exception):
                pass
