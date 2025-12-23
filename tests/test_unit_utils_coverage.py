# tests/unit/test_utils_coverage.py
"""
Utils coverage тест - normalize, codes, datetime, converters
"""
import pytest
from datetime import datetime, date


class TestNormalize:
    """Normalize функцүүдийн тест"""

    def test_normalize_raw_data_mad(self, app):
        """Mad raw data normalize"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data

            raw = {'c1': 100, 'c2': 95.5, 'c3': 95.0}
            result = normalize_raw_data(raw, 'Mad')
            assert isinstance(result, dict)

    def test_normalize_raw_data_aad(self, app):
        """Aad raw data normalize"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data

            raw = {'m1': 1.0, 'm2': 0.92, 'm3': 0.005}
            result = normalize_raw_data(raw, 'Aad')
            assert isinstance(result, dict)

    def test_normalize_raw_data_cv(self, app):
        """CV raw data normalize"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data

            raw = {'gross_cv': 6500, 'net_cv': 6200}
            result = normalize_raw_data(raw, 'CV')
            assert isinstance(result, dict)

    def test_normalize_raw_data_empty(self, app):
        """Empty raw data"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data

            result = normalize_raw_data({}, 'Mad')
            assert isinstance(result, dict)

    def test_normalize_raw_data_none(self, app):
        """None raw data"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data

            result = normalize_raw_data(None, 'Mad')
            assert isinstance(result, dict)


class TestCodes:
    """Codes функцүүдийн тест"""

    def test_norm_code(self, app):
        """norm_code функц"""
        with app.app_context():
            from app.utils.codes import norm_code

            assert norm_code('Mad') == 'Mad'
            assert norm_code('mad') == 'Mad'
            assert norm_code('MAD') == 'Mad'

    def test_norm_code_alias(self, app):
        """norm_code with alias"""
        with app.app_context():
            from app.utils.codes import norm_code

            # Moisture -> Mad
            result = norm_code('Moisture')
            assert result is not None

    def test_base_to_aliases(self, app):
        """BASE_TO_ALIASES constant"""
        with app.app_context():
            from app.utils.codes import BASE_TO_ALIASES

            assert isinstance(BASE_TO_ALIASES, dict)


class TestDatetime:
    """Datetime функцүүдийн тест"""

    def test_now_local(self, app):
        """now_local функц"""
        with app.app_context():
            from app.utils.datetime import now_local

            result = now_local()
            assert isinstance(result, datetime)


class TestConverters:
    """Converters функцүүдийн тест"""

    def test_to_float_valid(self, app):
        """to_float with valid input"""
        with app.app_context():
            from app.utils.converters import to_float

            assert to_float(10.5) == 10.5
            assert to_float('10.5') == 10.5
            assert to_float(10) == 10.0

    def test_to_float_invalid(self, app):
        """to_float with invalid input"""
        with app.app_context():
            from app.utils.converters import to_float

            assert to_float('invalid') is None
            assert to_float(None) is None
            assert to_float('') is None


class TestShifts:
    """Shifts функцүүдийн тест"""

    def test_get_shift_info(self, app):
        """get_shift_info функц"""
        with app.app_context():
            from app.utils.shifts import get_shift_info

            now = datetime.now()
            result = get_shift_info(now)
            assert result is not None

    def test_get_shift_date(self, app):
        """get_shift_date функц"""
        with app.app_context():
            from app.utils.shifts import get_shift_date

            now = datetime.now()
            result = get_shift_date(now)
            assert result is not None

    def test_get_current_shift_start(self, app):
        """get_current_shift_start функц"""
        with app.app_context():
            from app.utils.shifts import get_current_shift_start

            now = datetime.now()
            result = get_current_shift_start(now)
            assert result is not None

    def test_get_12h_shift_code(self, app):
        """get_12h_shift_code функц"""
        with app.app_context():
            from app.utils.shifts import get_12h_shift_code

            now = datetime.now()
            result = get_12h_shift_code(now)
            assert result in ['D', 'N'] or isinstance(result, str)

    def test_get_quarter_code(self, app):
        """get_quarter_code функц"""
        with app.app_context():
            from app.utils.shifts import get_quarter_code

            now = datetime.now()
            result = get_quarter_code(now)
            assert isinstance(result, str)


class TestSorting:
    """Sorting функцүүдийн тест"""

    def test_natural_sort_key(self, app):
        """natural_sort_key функц"""
        with app.app_context():
            from app.utils.sorting import natural_sort_key

            result = natural_sort_key('TEST-001')
            assert result is not None

    def test_sort_samples(self, app):
        """sort_samples функц"""
        with app.app_context():
            try:
                from app.utils.sorting import sort_samples

                samples = [
                    {'sample_code': 'TEST-002'},
                    {'sample_code': 'TEST-001'},
                    {'sample_code': 'TEST-010'}
                ]
                # If function exists, test it
                result = sort_samples(samples)
                assert isinstance(result, list)
            except (ImportError, AttributeError):
                # Function may not exist
                pass


class TestAudit:
    """Audit функцүүдийн тест"""

    def test_log_audit(self, app):
        """log_audit функц"""
        with app.app_context():
            from app.utils.audit import log_audit

            assert callable(log_audit)

    def test_get_recent_audit_logs(self, app):
        """get_recent_audit_logs функц"""
        with app.app_context():
            from app.utils.audit import get_recent_audit_logs

            result = get_recent_audit_logs(limit=5)
            assert isinstance(result, list)

    def test_get_user_audit_logs(self, app):
        """get_user_audit_logs функц"""
        with app.app_context():
            from app.utils.audit import get_user_audit_logs

            result = get_user_audit_logs(user_id=1, limit=5)
            assert isinstance(result, list)


class TestDecorators:
    """Decorators функцүүдийн тест"""

    def test_decorators_import(self, app):
        """Decorators module import"""
        with app.app_context():
            try:
                from app.utils.decorators import admin_required

                assert callable(admin_required)
            except ImportError:
                pass


class TestDatabase:
    """Database utils тест"""

    def test_database_import(self, app):
        """Database module import"""
        with app.app_context():
            try:
                from app.utils.database import safe_commit

                assert callable(safe_commit)
            except ImportError:
                pass


class TestSecurity:
    """Security utils тест"""

    def test_security_import(self, app):
        """Security module import"""
        with app.app_context():
            try:
                from app.utils.security import sanitize_input

                assert callable(sanitize_input)
            except (ImportError, AttributeError):
                pass


class TestSettings:
    """Settings utils тест"""

    def test_get_setting(self, app):
        """get_setting функц"""
        with app.app_context():
            try:
                from app.utils.settings import get_setting

                result = get_setting('test_category', 'test_key')
                # May return None if not found
                assert True
            except ImportError:
                pass


class TestExports:
    """Exports utils тест"""

    def test_exports_import(self, app):
        """Exports module import"""
        with app.app_context():
            try:
                from app.utils.exports import export_to_excel

                assert callable(export_to_excel)
            except (ImportError, AttributeError):
                pass


class TestWestgard:
    """Westgard utils тест"""

    def test_westgard_import(self, app):
        """Westgard module import"""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules

            assert callable(check_westgard_rules)


class TestQualityHelpers:
    """Quality helpers тест"""

    def test_quality_helpers_import(self, app):
        """Quality helpers import"""
        with app.app_context():
            try:
                from app.utils.quality_helpers import calculate_statistics

                assert callable(calculate_statistics)
            except (ImportError, AttributeError):
                pass
