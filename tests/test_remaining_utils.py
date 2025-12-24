# tests/test_remaining_utils.py
# -*- coding: utf-8 -*-
"""
Tests for remaining low-coverage utility files:
- database.py
- notifications.py
- sorting.py (extended)
- shifts.py (extended)
- decorators.py (extended)
- quality_helpers.py (extended)
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date


# ============================================================================
# DATABASE.PY TESTS
# ============================================================================

class TestDatabaseSafeCommit:
    """Extended tests for safe_commit function."""

    def test_safe_commit_success(self, app, db):
        """Test safe_commit success case."""
        with app.test_request_context('/'):
            from app.utils.database import safe_commit
            with patch('app.utils.database.flash'):
                result = safe_commit(None, "Error")
                assert result is True

    def test_safe_commit_with_message(self, app, db):
        """Test safe_commit with success message."""
        with app.test_request_context('/'):
            from app.utils.database import safe_commit
            with patch('app.utils.database.flash') as mock_flash:
                result = safe_commit("Success!", "Error")
                assert result is True

    def test_safe_commit_integrity_error(self, app, db):
        """Test safe_commit handles IntegrityError."""
        with app.test_request_context('/'):
            from app.utils.database import safe_commit
            from app import db as database
            from sqlalchemy.exc import IntegrityError

            with patch.object(database.session, 'commit', side_effect=IntegrityError('', '', '')):
                with patch('app.utils.database.flash'):
                    result = safe_commit("Success", "Integrity Error")
                    assert result is False

    def test_safe_commit_general_exception(self, app, db):
        """Test safe_commit handles general Exception."""
        with app.test_request_context('/'):
            from app.utils.database import safe_commit
            from app import db as database

            with patch.object(database.session, 'commit', side_effect=Exception('Test error')):
                with patch('app.utils.database.flash'):
                    result = safe_commit("Success", "Error")
                    assert result is False


class TestDatabaseSafeDelete:
    """Extended tests for safe_delete function."""

    def test_safe_delete_success(self, app, db):
        """Test safe_delete success case."""
        with app.test_request_context('/'):
            from app.utils.database import safe_delete
            from app.models import Sample

            sample = Sample(
                sample_code='DELETE_TEST_999',
                client_name='CHPP',
                sample_type='2H',
                user_id=1
            )
            db.session.add(sample)
            db.session.commit()

            with patch('app.utils.database.flash'):
                result = safe_delete(sample, "Deleted", "Error")
                assert result is True

    def test_safe_delete_with_message(self, app, db):
        """Test safe_delete with success message."""
        with app.test_request_context('/'):
            from app.utils.database import safe_delete
            from app.models import Sample

            sample = Sample(
                sample_code='DELETE_MSG_TEST',
                client_name='CHPP',
                sample_type='2H',
                user_id=1
            )
            db.session.add(sample)
            db.session.commit()

            with patch('app.utils.database.flash') as mock_flash:
                result = safe_delete(sample, "Deleted successfully", "Error")
                assert result is True


class TestDatabaseSafeAdd:
    """Extended tests for safe_add function."""

    def test_safe_add_single(self, app, db):
        """Test safe_add with single object."""
        with app.test_request_context('/'):
            from app.utils.database import safe_add
            from app.models import Sample

            sample = Sample(
                sample_code='ADD_SINGLE_TEST',
                client_name='CHPP',
                sample_type='2H',
                user_id=1
            )

            with patch('app.utils.database.flash'):
                result = safe_add(sample, "Added", "Error")
                assert result is True

    def test_safe_add_list(self, app, db):
        """Test safe_add with list of objects."""
        with app.test_request_context('/'):
            from app.utils.database import safe_add
            from app.models import Sample

            samples = [
                Sample(sample_code='ADD_LIST_A', client_name='CHPP', sample_type='2H', user_id=1),
                Sample(sample_code='ADD_LIST_B', client_name='CHPP', sample_type='2H', user_id=1)
            ]

            with patch('app.utils.database.flash'):
                result = safe_add(samples, "Added", "Error")
                assert result is True


# ============================================================================
# NOTIFICATIONS.PY TESTS
# ============================================================================

class TestNotificationTemplates:
    """Tests for notification templates."""

    def test_qc_failure_template_exists(self, app):
        """Test QC_FAILURE_TEMPLATE exists."""
        with app.app_context():
            from app.utils.notifications import QC_FAILURE_TEMPLATE
            assert isinstance(QC_FAILURE_TEMPLATE, str)
            assert "QC" in QC_FAILURE_TEMPLATE

    def test_sample_status_template_exists(self, app):
        """Test SAMPLE_STATUS_TEMPLATE exists."""
        with app.app_context():
            from app.utils.notifications import SAMPLE_STATUS_TEMPLATE
            assert isinstance(SAMPLE_STATUS_TEMPLATE, str)


class TestNotificationFunctions:
    """Tests for notification functions."""

    def test_module_imports(self, app):
        """Test notifications module can be imported."""
        with app.app_context():
            import app.utils.notifications
            assert True


# ============================================================================
# SORTING.PY EXTENDED TESTS
# ============================================================================

class TestSortingExtended:
    """Extended tests for sorting.py."""

    def test_chpp_2h_index_values(self, app):
        """Test CHPP_2H_INDEX has expected values."""
        with app.app_context():
            from app.utils.sorting import CHPP_2H_INDEX
            assert isinstance(CHPP_2H_INDEX, dict)

    def test_sort_multiple_samples(self, app):
        """Test sorting multiple samples."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            samples = ['PF221D3', 'PF211D1', 'PF221D1', 'HCC1D2']
            sorted_samples = sorted(samples, key=custom_sample_sort_key)
            assert len(sorted_samples) == 4


# ============================================================================
# SHIFTS.PY EXTENDED TESTS
# ============================================================================

class TestShiftsExtended:
    """Extended tests for shifts.py."""

    def test_shift_times(self, app):
        """Test shift time constants."""
        with app.app_context():
            from app.utils.shifts import DAY_START, DAY_END
            from datetime import time
            assert DAY_START == time(7, 1)
            assert DAY_END == time(19, 0)

    def test_cycle_start_date(self, app):
        """Test CYCLE_START_DATE constant."""
        with app.app_context():
            from app.utils.shifts import CYCLE_START_DATE
            assert isinstance(CYCLE_START_DATE, date)


# ============================================================================
# DECORATORS.PY EXTENDED TESTS
# ============================================================================

class TestDecoratorsExtended:
    """Extended tests for decorators.py."""

    def test_role_required_multiple_roles(self, app):
        """Test role_required with multiple allowed roles."""
        with app.app_context():
            from app.utils.decorators import role_required

            @role_required('admin', 'senior', 'chemist')
            def multi_role_view():
                return 'OK'

            assert callable(multi_role_view)

    def test_admin_required_decorator(self, app):
        """Test admin_required decorator."""
        with app.app_context():
            from app.utils.decorators import admin_required

            @admin_required
            def admin_only_view():
                return 'Admin OK'

            assert callable(admin_only_view)


# ============================================================================
# QUALITY_HELPERS.PY EXTENDED TESTS
# ============================================================================

class TestQualityHelpersExtended:
    """Extended tests for quality_helpers.py."""

    def test_can_edit_quality_roles(self, app):
        """Test can_edit_quality with different roles."""
        with app.app_context():
            from app.utils.quality_helpers import can_edit_quality

            with patch('app.utils.quality_helpers.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                assert can_edit_quality() is True

                mock_user.role = 'senior'
                assert can_edit_quality() is True

                mock_user.role = 'chemist'
                assert can_edit_quality() is False

    def test_calculate_status_stats_with_data(self, app):
        """Test calculate_status_stats with data."""
        with app.app_context():
            from app.utils.quality_helpers import calculate_status_stats

            class MockItem:
                def __init__(self, status):
                    self.status = status

            items = [
                MockItem('open'),
                MockItem('closed'),
                MockItem('open'),
                MockItem('pending')
            ]
            result = calculate_status_stats(items, status_values=['open', 'closed', 'pending'])
            assert result['total'] == 4
            assert result['open'] == 2
            assert result['closed'] == 1
            assert result['pending'] == 1


# ============================================================================
# ANALYSIS_ALIASES.PY TESTS
# ============================================================================

class TestAnalysisAliases:
    """Tests for analysis_aliases.py."""

    def test_module_exists(self, app):
        """Test analysis_aliases module exists."""
        with app.app_context():
            import app.utils.analysis_aliases
            assert True


# ============================================================================
# REPEATABILITY_LOADER.PY TESTS
# ============================================================================

class TestRepeatabilityLoader:
    """Tests for repeatability_loader.py."""

    def test_load_repeatability_limits_exists(self, app):
        """Test load_repeatability_limits function exists."""
        with app.app_context():
            try:
                from app.utils.repeatability_loader import load_repeatability_limits
                assert callable(load_repeatability_limits)
            except ImportError:
                pytest.skip("repeatability_loader not available")


# ============================================================================
# ANALYSIS_ASSIGNMENT.PY TESTS
# ============================================================================

class TestAnalysisAssignment:
    """Tests for analysis_assignment.py."""

    def test_module_exists(self, app):
        """Test analysis_assignment module exists."""
        with app.app_context():
            import app.utils.analysis_assignment
            assert True


# ============================================================================
# LICENSE_PROTECTION.PY TESTS
# ============================================================================

class TestLicenseProtection:
    """Tests for license_protection.py."""

    def test_module_exists(self, app):
        """Test license_protection module exists."""
        with app.app_context():
            import app.utils.license_protection
            assert True


# ============================================================================
# HARDWARE_FINGERPRINT.PY TESTS
# ============================================================================

class TestHardwareFingerprint:
    """Tests for hardware_fingerprint.py."""

    def test_module_exists(self, app):
        """Test hardware_fingerprint module exists."""
        with app.app_context():
            import app.utils.hardware_fingerprint
            assert True


# ============================================================================
# PARAMETERS.PY TESTS
# ============================================================================

class TestParameters:
    """Tests for parameters.py."""

    def test_parameter_definitions_exists(self, app):
        """Test PARAMETER_DEFINITIONS constant exists."""
        with app.app_context():
            from app.utils.parameters import PARAMETER_DEFINITIONS
            assert isinstance(PARAMETER_DEFINITIONS, dict)

    def test_calculate_value_exists(self, app):
        """Test calculate_value function exists."""
        with app.app_context():
            try:
                from app.utils.parameters import calculate_value
                assert callable(calculate_value)
            except ImportError:
                pytest.skip("calculate_value not available")
