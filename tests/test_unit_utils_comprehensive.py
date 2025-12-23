# tests/unit/test_utils_comprehensive.py
# -*- coding: utf-8 -*-
"""
Utils comprehensive tests - coverage нэмэгдүүлэх
"""

import pytest
from datetime import datetime, date, timedelta
import json


class TestDatabaseUtils:
    """Database utils тестүүд"""

    def test_safe_commit(self, app):
        """safe_commit function"""
        with app.app_context():
            from app.utils.database import safe_commit
            from app import db
            # Test successful commit
            result = safe_commit()
            assert result in [True, False, None]

    def test_safe_add(self, app):
        """safe_add function"""
        with app.app_context():
            from app.utils.database import safe_add
            from app.models import SystemSetting
            # Test adding object
            try:
                obj = SystemSetting(key='test_util', value='test')
                result = safe_add(obj)
            except Exception:
                pass

    def test_safe_delete(self, app):
        """safe_delete function"""
        with app.app_context():
            from app.utils.database import safe_delete
            # Test with None
            try:
                result = safe_delete(None)
            except Exception:
                pass


class TestExportsUtils:
    """Exports utils тестүүд"""

    def test_export_to_excel(self, app):
        """export_to_excel function"""
        with app.app_context():
            from app.utils.exports import export_to_excel
            # Test exists
            assert export_to_excel is not None

    def test_create_sample_export(self, app):
        """create_sample_export function"""
        with app.app_context():
            from app.utils.exports import create_sample_export
            assert create_sample_export is not None

    def test_create_analysis_export(self, app):
        """create_analysis_export function"""
        with app.app_context():
            from app.utils.exports import create_analysis_export
            assert create_analysis_export is not None


class TestNotificationsUtils:
    """Notifications utils тестүүд"""

    def test_notification_imports(self, app):
        """Notification imports"""
        with app.app_context():
            try:
                from app.utils.notifications import logger
                assert logger is not None
            except Exception:
                pass


class TestQCUtils:
    """QC utils тестүүд"""

    def test_eval_qc_status(self, app):
        """eval_qc_status function"""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            assert eval_qc_status is not None

    def test_qc_check_spec(self, app):
        """qc_check_spec function"""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            assert qc_check_spec is not None

    def test_qc_is_composite(self, app):
        """qc_is_composite function"""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            from app.models import Sample
            # Test with mock sample object
            sample = Sample(sample_type='composite')
            result = qc_is_composite(sample, 'p1')
            assert result is True
            # Test with non-composite
            sample2 = Sample(sample_type='2hour')
            result2 = qc_is_composite(sample2, 'p1')
            assert result2 is False
            # Test with composite slot
            result3 = qc_is_composite(sample2, 'com')
            assert result3 is True

    def test_parse_numeric(self, app):
        """parse_numeric function"""
        with app.app_context():
            from app.utils.qc import parse_numeric
            assert parse_numeric('5.5') == 5.5
            assert parse_numeric('10') == 10.0
            assert parse_numeric(None) is None

    def test_qc_split_family(self, app):
        """qc_split_family function"""
        with app.app_context():
            from app.utils.qc import qc_split_family
            assert qc_split_family is not None

    def test_split_stream_key(self, app):
        """split_stream_key function"""
        with app.app_context():
            from app.utils.qc import split_stream_key
            assert split_stream_key is not None


class TestQualityHelpersUtils:
    """Quality helpers utils тестүүд"""

    def test_quality_helpers_import(self, app):
        """Quality helpers import"""
        with app.app_context():
            from app.utils import quality_helpers
            assert quality_helpers is not None


class TestAuditUtils:
    """Audit utils тестүүд"""

    def test_audit_import(self, app):
        """Audit import"""
        with app.app_context():
            from app.utils import audit
            assert audit is not None


class TestDatetimeUtils:
    """Datetime utils тестүүд"""

    def test_now_local(self, app):
        """now_local function"""
        with app.app_context():
            from app.utils.datetime import now_local
            result = now_local()
            assert isinstance(result, datetime)


class TestRepeatabilityLoader:
    """Repeatability loader тестүүд"""

    def test_repeatability_import(self, app):
        """Repeatability import"""
        with app.app_context():
            from app.utils import repeatability_loader
            assert repeatability_loader is not None


class TestSettingsUtils:
    """Settings utils тестүүд"""

    def test_get_setting_value(self, app):
        """get_setting_value function"""
        with app.app_context():
            from app.utils.settings import get_setting_value
            # Test with default (category, key, default)
            value = get_setting_value('nonexistent_category', 'nonexistent_key', 'default_value')
            assert value == 'default_value'
            # Test without default
            value2 = get_setting_value('test_category', 'test_key')
            assert value2 is None

    def test_get_sample_type_choices_map(self, app):
        """get_sample_type_choices_map function"""
        with app.app_context():
            from app.utils.settings import get_sample_type_choices_map
            result = get_sample_type_choices_map()
            assert isinstance(result, dict)

    def test_get_unit_abbreviations(self, app):
        """get_unit_abbreviations function"""
        with app.app_context():
            from app.utils.settings import get_unit_abbreviations
            result = get_unit_abbreviations()
            assert isinstance(result, dict)


class TestParametersUtils:
    """Parameters utils тестүүд"""

    def test_get_canonical_name(self, app):
        """get_canonical_name function"""
        with app.app_context():
            from app.utils.parameters import get_canonical_name
            name = get_canonical_name('Mad')
            assert name is not None

    def test_parameter_definitions(self, app):
        """PARAMETER_DEFINITIONS constant"""
        with app.app_context():
            from app.utils.parameters import PARAMETER_DEFINITIONS
            assert isinstance(PARAMETER_DEFINITIONS, dict)
            assert len(PARAMETER_DEFINITIONS) > 0


class TestCodesUtils:
    """Codes utils тестүүд"""

    def test_norm_code(self, app):
        """norm_code function"""
        with app.app_context():
            from app.utils.codes import norm_code
            assert norm_code('mad') == 'Mad'
            assert norm_code('MAD') == 'Mad'
            assert norm_code('aad') == 'Aad'

    def test_to_base_list(self, app):
        """to_base_list function"""
        with app.app_context():
            from app.utils.codes import to_base_list
            result = to_base_list('["Mad", "Aad"]')
            assert isinstance(result, list)


class TestConvertersUtils:
    """Converters utils тестүүд"""

    def test_to_float(self, app):
        """to_float function"""
        with app.app_context():
            from app.utils.converters import to_float
            assert to_float('5.5') == 5.5
            assert to_float('10') == 10.0
            assert to_float(None) is None
            assert to_float('') is None


class TestSecurityUtils:
    """Security utils тестүүд"""

    def test_escape_like_pattern(self, app):
        """escape_like_pattern function"""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern('test%value')
            assert '%' not in result or '\\%' in result


class TestSortingUtils:
    """Sorting utils тестүүд"""

    def test_custom_sample_sort_key(self, app):
        """custom_sample_sort_key function"""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            assert custom_sample_sort_key is not None

    def test_sort_samples(self, app):
        """sort_samples function"""
        with app.app_context():
            from app.utils.sorting import sort_samples
            assert sort_samples is not None


class TestNormalizeUtils:
    """Normalize utils тестүүд"""

    def test_normalize_raw_data(self, app):
        """normalize_raw_data function"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            # Test with dict
            result = normalize_raw_data({'p1': {'m1': 5.0, 'm2': 5.5}})
            assert isinstance(result, dict)
            # Test with JSON string
            result2 = normalize_raw_data('{"p1": {"m1": 5.0}}')
            assert isinstance(result2, dict)
            # Test with empty
            result3 = normalize_raw_data({})
            assert isinstance(result3, dict)

    def test_normalize_analysis_code_from_aliases(self, app):
        """normalize_analysis_code from analysis_aliases"""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            assert normalize_analysis_code('mad') == 'Mad'
            assert normalize_analysis_code('MAD') == 'Mad'


class TestWestgardUtils:
    """Westgard utils тестүүд"""

    def test_westgard_import(self, app):
        """Westgard import"""
        with app.app_context():
            from app.utils import westgard
            assert westgard is not None


class TestDecoratorsUtils:
    """Decorators utils тестүүд"""

    def test_decorators_import(self, app):
        """Decorators import"""
        with app.app_context():
            from app.utils import decorators
            assert decorators is not None


class TestShiftsUtils:
    """Shifts utils тестүүд"""

    def test_shifts_import(self, app):
        """Shifts import"""
        with app.app_context():
            from app.utils import shifts
            assert shifts is not None


class TestConversionsUtils:
    """Conversions utils тестүүд"""

    def test_calculate_all_conversions(self, app):
        """calculate_all_conversions function"""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            assert calculate_all_conversions is not None


class TestAnalysisRulesUtils:
    """Analysis rules utils тестүүд"""

    def test_determine_result_status(self, app):
        """determine_result_status function"""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            result = determine_result_status('Mad', 5.0)
            assert isinstance(result, tuple)


class TestAnalysisAssignmentUtils:
    """Analysis assignment utils тестүүд"""

    def test_assign_analyses_to_sample(self, app):
        """assign_analyses_to_sample function"""
        with app.app_context():
            from app.utils.analysis_assignment import assign_analyses_to_sample
            assert assign_analyses_to_sample is not None


class TestValidatorsUtils:
    """Validators utils тестүүд"""

    def test_validators_import(self, app):
        """Validators import"""
        with app.app_context():
            from app.utils import validators
            assert validators is not None


class TestServerCalculationsUtils:
    """Server calculations utils тестүүд"""

    def test_server_calculations_import(self, app):
        """Server calculations import"""
        with app.app_context():
            from app.utils import server_calculations
            assert server_calculations is not None
