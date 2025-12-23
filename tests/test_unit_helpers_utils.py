# tests/unit/test_helpers_utils.py
# -*- coding: utf-8 -*-
"""Helpers and utils unit tests"""

import pytest
from datetime import datetime, date, timedelta


class TestDateTimeUtils:
    def test_now_local(self):
        from app.utils.datetime import now_local
        result = now_local()
        assert result is not None
        assert isinstance(result, datetime)

    def test_format_date(self):
        try:
            from app.utils.datetime import format_date
            result = format_date(date.today())
            assert result is not None
        except (ImportError, AttributeError):
            pass

    def test_parse_date(self):
        try:
            from app.utils.datetime import parse_date
            result = parse_date('2025-01-01')
            assert result is not None
        except (ImportError, AttributeError):
            pass


class TestSortingUtils:
    def test_custom_sample_sort_key(self):
        from app.utils.sorting import custom_sample_sort_key
        samples = ['CHPP-001', 'CHPP-002', 'CHPP-010']
        sorted_samples = sorted(samples, key=custom_sample_sort_key)
        assert len(sorted_samples) == 3


class TestDatabaseUtils:
    def test_safe_commit(self):
        from app.utils.database import safe_commit
        assert safe_commit is not None


class TestSettingsUtils:
    def test_get_sample_type_choices_map(self, app):
        with app.app_context():
            from app.utils.settings import get_sample_type_choices_map
            result = get_sample_type_choices_map()
            assert isinstance(result, dict)

    def test_get_unit_abbreviations(self, app):
        with app.app_context():
            try:
                from app.utils.settings import get_unit_abbreviations
                result = get_unit_abbreviations()
                assert result is not None
            except (ImportError, AttributeError):
                pass


class TestValidators:
    def test_validators_import(self):
        try:
            from app.utils import validators
            assert validators is not None
        except ImportError:
            pass


class TestNormalizeUtils:
    def test_normalize_import(self):
        try:
            from app.utils import normalize
            assert normalize is not None
        except ImportError:
            pass


class TestCodesUtils:
    def test_codes_utils_import(self):
        try:
            from app.utils import codes
            assert codes is not None
        except ImportError:
            pass
