# tests/test_utils_remaining.py
# -*- coding: utf-8 -*-
"""
Complete tests for remaining low-coverage utility files:
- normalize.py
- database.py
- audit.py
"""

import pytest
from unittest.mock import patch, MagicMock
import json


# ============================================================================
# NORMALIZE.PY TESTS
# ============================================================================

class TestPick:
    """Tests for _pick function."""

    def test_first_key(self, app):
        """Test returns first matching key."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {"num": "123", "box_no": "456"}
            assert _pick(d, ["num", "box_no"]) == "123"

    def test_second_key(self, app):
        """Test returns second key if first missing."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {"box_no": "456"}
            assert _pick(d, ["num", "box_no"]) == "456"

    def test_no_match(self, app):
        """Test returns None if no match."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {"other": "value"}
            assert _pick(d, ["num", "box_no"]) is None

    def test_empty_dict(self, app):
        """Test with empty dict."""
        with app.app_context():
            from app.utils.normalize import _pick
            assert _pick({}, ["num"]) is None

    def test_none_value(self, app):
        """Test skips None values."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {"num": None, "box_no": "456"}
            assert _pick(d, ["num", "box_no"]) == "456"

    def test_empty_string(self, app):
        """Test skips empty string."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {"num": "", "box_no": "456"}
            assert _pick(d, ["num", "box_no"]) == "456"


class TestNormParallel:
    """Tests for _norm_parallel function."""

    def test_basic(self, app):
        """Test with basic input."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {"num": "123", "m1": 10.5, "m2": 15.3}
            result = _norm_parallel(raw)
            assert result["num"] == "123"
            assert result["m1"] == 10.5

    def test_aliases(self, app):
        """Test with alias keys."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {"box_no": "123", "tare": 10.5}
            result = _norm_parallel(raw)
            assert result["num"] == "123"
            assert result["m1"] == 10.5

    def test_empty(self, app):
        """Test with empty dict."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            assert _norm_parallel({}) == {}

    def test_not_dict(self, app):
        """Test with non-dict."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            assert _norm_parallel("not a dict") == {}

    def test_string_to_float(self, app):
        """Test converts string to float."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {"m1": "10.5"}
            result = _norm_parallel(raw)
            assert result["m1"] == 10.5

    def test_invalid_float(self, app):
        """Test with invalid float string."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {"m1": "invalid"}
            result = _norm_parallel(raw)
            assert "m1" in result

    def test_weight_alias(self, app):
        """Test weight alias from m1."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {"m1": 10.5}
            result = _norm_parallel(raw)
            assert result.get("weight") == 10.5


class TestNormalizeRawData:
    """Tests for normalize_raw_data function."""

    def test_dict_input(self, app):
        """Test with dict input."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {"p1": {"num": "123", "m1": 10.5}}
            result = normalize_raw_data(raw)
            assert "p1" in result
            assert "_schema" in result

    def test_json_string(self, app):
        """Test with JSON string input."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = json.dumps({"p1": {"num": "123"}})
            result = normalize_raw_data(raw)
            assert isinstance(result, dict)

    def test_empty_dict(self, app):
        """Test with empty dict."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            result = normalize_raw_data({})
            assert isinstance(result, dict)

    def test_none(self, app):
        """Test with None."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            result = normalize_raw_data(None)
            assert isinstance(result, dict)

    def test_p1_p2(self, app):
        """Test with p1 and p2."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                "p1": {"num": "1", "m1": 10},
                "p2": {"num": "2", "m1": 11}
            }
            result = normalize_raw_data(raw)
            assert "parallels" in result

    def test_csn_analysis(self, app):
        """Test with CSN analysis."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {"v1": 2, "v2": 2.5, "v3": 2}
            result = normalize_raw_data(raw, analysis_code="CSN")
            assert "_schema" in result

    def test_diff_avg(self, app):
        """Test diff and avg preserved."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {"diff": 0.5, "avg": 10.0}
            result = normalize_raw_data(raw)
            assert result.get("diff") == 0.5
            assert result.get("avg") == 10.0

    def test_common_value_aliases(self, app):
        """Test common value aliases (A, B, C)."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {"A": 100, "B": 50}
            result = normalize_raw_data(raw)
            assert result.get("A") == 100

    def test_preserve_keys(self, app):
        """Test preserve keys (FM, CV fields)."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {"tray_g": 10, "fm_pct": 5.5}
            result = normalize_raw_data(raw)
            assert result.get("tray_g") == 10
            assert result.get("fm_pct") == 5.5

    def test_cv_fields(self, app):
        """Test CV-specific fields."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {"p1": {"m": 1.0, "delta_t": 2.5}}
            result = normalize_raw_data(raw)
            assert result["p1"].get("m") == 1.0

    def test_trd_fields(self, app):
        """Test TRD-specific fields."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {"mad_used": 5.0, "temp_c": 25, "kt_used": 1.1}
            result = normalize_raw_data(raw)
            assert result.get("mad_used") == 5.0

    def test_invalid_json(self, app):
        """Test with invalid JSON string."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            result = normalize_raw_data("not valid json")
            assert isinstance(result, dict)


class TestPickNumeric:
    """Tests for _pick_numeric function."""

    def test_float_value(self, app):
        """Test with float value."""
        with app.app_context():
            from app.utils.normalize import _pick_numeric
            d = {"A": 10.5}
            assert _pick_numeric(d, ["A"]) == 10.5

    def test_string_value(self, app):
        """Test with string value converted to float."""
        with app.app_context():
            from app.utils.normalize import _pick_numeric
            d = {"A": "10.5"}
            assert _pick_numeric(d, ["A"]) == 10.5

    def test_invalid_string(self, app):
        """Test with invalid string."""
        with app.app_context():
            from app.utils.normalize import _pick_numeric
            d = {"A": "invalid"}
            assert _pick_numeric(d, ["A"]) == "invalid"


# ============================================================================
# DATABASE.PY TESTS
# ============================================================================

class TestSafeCommit:
    """Tests for safe_commit function."""

    def test_success(self, app, db):
        """Test successful commit."""
        with app.test_request_context('/'):
            from app.utils.database import safe_commit
            with patch('app.utils.database.flash'):
                result = safe_commit(None, "Error")
                assert result is True

    def test_with_message(self, app, db):
        """Test with success message."""
        with app.test_request_context('/'):
            from app.utils.database import safe_commit
            with patch('app.utils.database.flash') as mock_flash:
                result = safe_commit("Success!", "Error")
                assert result is True
                mock_flash.assert_called_once()

    def test_integrity_error(self, app, db):
        """Test handles IntegrityError."""
        with app.test_request_context('/'):
            from app.utils.database import safe_commit
            from app import db as database
            from sqlalchemy.exc import IntegrityError

            with patch.object(database.session, 'commit', side_effect=IntegrityError('', '', '')):
                with patch('app.utils.database.flash'):
                    result = safe_commit("Success", "Integrity Error")
                    assert result is False

    def test_general_exception(self, app, db):
        """Test handles general Exception."""
        with app.test_request_context('/'):
            from app.utils.database import safe_commit
            from app import db as database

            from sqlalchemy.exc import SQLAlchemyError
            with patch.object(database.session, 'commit', side_effect=SQLAlchemyError('Test')):
                with patch('app.utils.database.flash'):
                    result = safe_commit("Success", "Error")
                    assert result is False


class TestSafeDelete:
    """Tests for safe_delete function."""

    def test_success(self, app, db):
        """Test successful delete."""
        with app.test_request_context('/'):
            from app.utils.database import safe_delete
            from app.models import Sample

            sample = Sample(
                sample_code='DELETE_TEST',
                client_name='CHPP',
                sample_type='2H',
                user_id=1
            )
            db.session.add(sample)
            db.session.commit()

            with patch('app.utils.database.flash'):
                result = safe_delete(sample, "Deleted", "Error")
                assert result is True

    def test_exception(self, app, db):
        """Test handles exception."""
        with app.test_request_context('/'):
            from app.utils.database import safe_delete
            from app import db as database

            mock_obj = MagicMock()
            from sqlalchemy.exc import SQLAlchemyError
            with patch.object(database.session, 'delete', side_effect=SQLAlchemyError('Test')):
                with patch('app.utils.database.flash'):
                    result = safe_delete(mock_obj, "Deleted", "Error")
                    assert result is False


class TestSafeAdd:
    """Tests for safe_add function."""

    def test_single(self, app, db):
        """Test with single object."""
        with app.test_request_context('/'):
            from app.utils.database import safe_add
            from app.models import Sample

            sample = Sample(
                sample_code='ADD_SINGLE',
                client_name='CHPP',
                sample_type='2H',
                user_id=1
            )

            with patch('app.utils.database.flash'):
                result = safe_add(sample, "Added", "Error")
                assert result is True

    def test_list(self, app, db):
        """Test with list of objects."""
        with app.test_request_context('/'):
            from app.utils.database import safe_add
            from app.models import Sample

            samples = [
                Sample(sample_code='ADD_A', client_name='CHPP', sample_type='2H', user_id=1),
                Sample(sample_code='ADD_B', client_name='CHPP', sample_type='2H', user_id=1)
            ]

            with patch('app.utils.database.flash'):
                result = safe_add(samples, "Added", "Error")
                assert result is True

    def test_integrity_error(self, app, db):
        """Test handles IntegrityError."""
        with app.test_request_context('/'):
            from app.utils.database import safe_add
            from app import db as database
            from sqlalchemy.exc import IntegrityError

            mock_obj = MagicMock()
            with patch.object(database.session, 'add', side_effect=IntegrityError('', '', '')):
                with patch('app.utils.database.flash'):
                    result = safe_add(mock_obj, "Added", "Error")
                    assert result is False

    def test_general_exception(self, app, db):
        """Test handles general exception."""
        with app.test_request_context('/'):
            from app.utils.database import safe_add
            from app import db as database

            mock_obj = MagicMock()
            from sqlalchemy.exc import SQLAlchemyError
            with patch.object(database.session, 'add', side_effect=SQLAlchemyError('Test')):
                with patch('app.utils.database.flash'):
                    result = safe_add(mock_obj, "Added", "Error")
                    assert result is False


# ============================================================================
# AUDIT.PY TESTS
# ============================================================================

class TestLogAudit:
    """Tests for log_audit function."""

    def test_basic_log(self, app, db):
        """Test basic audit log."""
        with app.test_request_context('/'):
            from app.utils.audit import log_audit
            with patch('flask_login.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.id = 1
                log_audit('test_action')
                # Should not raise

    def test_with_all_params(self, app, db):
        """Test with all parameters."""
        with app.test_request_context('/'):
            from app.utils.audit import log_audit
            with patch('flask_login.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.id = 1
                log_audit(
                    'test_action',
                    resource_type='Sample',
                    resource_id=123,
                    details={'key': 'value'}
                )

    def test_unauthenticated(self, app, db):
        """Test with unauthenticated user."""
        with app.test_request_context('/'):
            from app.utils.audit import log_audit
            with patch('flask_login.current_user') as mock_user:
                mock_user.is_authenticated = False
                log_audit('anonymous_action')

    def test_commit_error(self, app, db):
        """Test handles commit error."""
        with app.test_request_context('/'):
            from app.utils.audit import log_audit
            from app import db as database

            with patch('flask_login.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.id = 1
                from sqlalchemy.exc import SQLAlchemyError
                with patch.object(database.session, 'commit', side_effect=SQLAlchemyError('Test')):
                    log_audit('test_action')  # Should not raise


class TestGetRecentAuditLogs:
    """Tests for get_recent_audit_logs function."""

    def test_returns_list(self, app, db):
        """Test returns a list."""
        with app.app_context():
            from app.utils.audit import get_recent_audit_logs
            result = get_recent_audit_logs()
            assert isinstance(result, list)

    def test_with_limit(self, app, db):
        """Test with custom limit."""
        with app.app_context():
            from app.utils.audit import get_recent_audit_logs
            result = get_recent_audit_logs(limit=10)
            assert len(result) <= 10

    def test_filter_by_action(self, app, db):
        """Test filtering by action."""
        with app.app_context():
            from app.utils.audit import get_recent_audit_logs
            result = get_recent_audit_logs(action='login')
            assert isinstance(result, list)


class TestGetUserAuditLogs:
    """Tests for get_user_audit_logs function."""

    def test_returns_list(self, app, db):
        """Test returns a list."""
        with app.app_context():
            from app.utils.audit import get_user_audit_logs
            result = get_user_audit_logs(user_id=1)
            assert isinstance(result, list)

    def test_with_limit(self, app, db):
        """Test with custom limit."""
        with app.app_context():
            from app.utils.audit import get_user_audit_logs
            result = get_user_audit_logs(user_id=1, limit=5)
            assert len(result) <= 5


class TestGetResourceAuditLogs:
    """Tests for get_resource_audit_logs function."""

    def test_returns_list(self, app, db):
        """Test returns a list."""
        with app.app_context():
            from app.utils.audit import get_resource_audit_logs
            result = get_resource_audit_logs('Sample', 123)
            assert isinstance(result, list)

    def test_with_limit(self, app, db):
        """Test with custom limit."""
        with app.app_context():
            from app.utils.audit import get_resource_audit_logs
            result = get_resource_audit_logs('Sample', 123, limit=10)
            assert len(result) <= 10


# ============================================================================
# ALIASES TESTS
# ============================================================================

class TestNormalizeAliases:
    """Tests for alias constants in normalize.py."""

    def test_num_aliases(self, app):
        """Test NUM_ALIASES exists."""
        with app.app_context():
            from app.utils.normalize import NUM_ALIASES
            assert isinstance(NUM_ALIASES, list)
            assert "num" in NUM_ALIASES

    def test_m1_aliases(self, app):
        """Test M1_ALIASES exists."""
        with app.app_context():
            from app.utils.normalize import M1_ALIASES
            assert isinstance(M1_ALIASES, list)
            assert "m1" in M1_ALIASES

    def test_m2_aliases(self, app):
        """Test M2_ALIASES exists."""
        with app.app_context():
            from app.utils.normalize import M2_ALIASES
            assert isinstance(M2_ALIASES, list)
            assert "m2" in M2_ALIASES

    def test_m3_aliases(self, app):
        """Test M3_ALIASES exists."""
        with app.app_context():
            from app.utils.normalize import M3_ALIASES
            assert isinstance(M3_ALIASES, list)
            assert "m3" in M3_ALIASES

    def test_result_aliases(self, app):
        """Test RESULT_ALIASES exists."""
        with app.app_context():
            from app.utils.normalize import RESULT_ALIASES
            assert isinstance(RESULT_ALIASES, list)
            assert "result" in RESULT_ALIASES

    def test_common_value_aliases(self, app):
        """Test COMMON_VALUE_ALIASES exists."""
        with app.app_context():
            from app.utils.normalize import COMMON_VALUE_ALIASES
            assert isinstance(COMMON_VALUE_ALIASES, dict)
            assert "A" in COMMON_VALUE_ALIASES
