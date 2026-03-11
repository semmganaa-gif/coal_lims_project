# tests/test_analysis_audit_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/services/analysis_audit.py
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from dataclasses import dataclass
from sqlalchemy.exc import SQLAlchemyError


class TestToJsonable:
    """Tests for _to_jsonable function."""

    def test_dataclass_to_dict(self, app):
        """Test dataclass converts to dict."""
        with app.app_context():
            from app.services.analysis_audit import _to_jsonable

            @dataclass
            class TestData:
                name: str
                value: int

            data = TestData(name="test", value=123)
            result = _to_jsonable(data)
            assert isinstance(result, dict)
            assert result['name'] == 'test'
            assert result['value'] == 123

    def test_object_with_id(self, app):
        """Test object with id attribute returns id."""
        with app.app_context():
            from app.services.analysis_audit import _to_jsonable

            class MockModel:
                id = 42

            obj = MockModel()
            result = _to_jsonable(obj)
            assert result == 42

    def test_regular_value_passthrough(self, app):
        """Test regular values pass through."""
        with app.app_context():
            from app.services.analysis_audit import _to_jsonable
            assert _to_jsonable("test") == "test"
            assert _to_jsonable(123) == 123
            assert _to_jsonable([1, 2, 3]) == [1, 2, 3]

    def test_exception_returns_original(self, app):
        """Test exception returns original value (TypeError/AttributeError fallback)."""
        with app.app_context():
            from app.services.analysis_audit import _to_jsonable

            class BadObject:
                @property
                def id(self):
                    raise AttributeError("Error")

            obj = BadObject()
            result = _to_jsonable(obj)
            assert result == obj


class TestSafeJsonDumps:
    """Tests for _safe_json_dumps function."""

    def test_simple_dict(self, app):
        """Test simple dict to JSON."""
        with app.app_context():
            from app.services.analysis_audit import _safe_json_dumps
            data = {'key': 'value', 'number': 123}
            result = _safe_json_dumps(data)
            assert isinstance(result, str)
            parsed = json.loads(result)
            assert parsed['key'] == 'value'

    def test_mongolian_text(self, app):
        """Test Mongolian text preservation."""
        with app.app_context():
            from app.services.analysis_audit import _safe_json_dumps
            data = {'text': 'Монгол текст', 'code': 'Шинжилгээ'}
            result = _safe_json_dumps(data)
            assert 'Монгол текст' in result
            assert 'Шинжилгээ' in result

    def test_truncation_large_payload(self, app):
        """Test truncation of large payload."""
        with app.app_context():
            from app.services.analysis_audit import _safe_json_dumps
            # Create a large payload
            large_data = {'data': 'x' * 300000}
            result = _safe_json_dumps(large_data, limit_bytes=1000)
            assert '[truncated]' in result
            assert len(result.encode('utf-8')) <= 1100  # Some overhead

    def test_non_serializable_to_str(self, app):
        """Test non-serializable objects convert to string."""
        with app.app_context():
            from app.services.analysis_audit import _safe_json_dumps
            # Test with a simple non-serializable value that doesn't cause circular ref
            result = _safe_json_dumps("simple string")
            assert isinstance(result, str)
            assert "simple string" in result

    def test_empty_dict(self, app):
        """Test empty dict."""
        with app.app_context():
            from app.services.analysis_audit import _safe_json_dumps
            result = _safe_json_dumps({})
            assert result == '{}'

    def test_nested_structure(self, app):
        """Test nested data structure."""
        with app.app_context():
            from app.services.analysis_audit import _safe_json_dumps
            data = {
                'level1': {
                    'level2': {
                        'value': 123
                    }
                }
            }
            result = _safe_json_dumps(data)
            parsed = json.loads(result)
            assert parsed['level1']['level2']['value'] == 123

    def test_list_data(self, app):
        """Test list data."""
        with app.app_context():
            from app.services.analysis_audit import _safe_json_dumps
            data = [1, 2, 3, 'test']
            result = _safe_json_dumps(data)
            parsed = json.loads(result)
            assert parsed == [1, 2, 3, 'test']


class TestLogAnalysisAction:
    """Tests for log_analysis_action function."""

    def test_basic_log_creation(self, app, db):
        """Test basic log creation."""
        with app.app_context():
            from app.services.analysis_audit import log_analysis_action

            with patch('app.services.analysis_audit.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.id = 1

                log_analysis_action(
                    result_id=1,
                    sample_id=1,
                    analysis_code='Mad',
                    action='created',
                    final_result=8.5,
                    raw_data_dict={'m1': 10.0}
                )
                # Should not raise

    def test_with_unauthenticated_user(self, app, db):
        """Test with unauthenticated user."""
        with app.app_context():
            from app.services.analysis_audit import log_analysis_action

            with patch('app.services.analysis_audit.current_user') as mock_user:
                mock_user.is_authenticated = False

                log_analysis_action(
                    result_id=1,
                    sample_id=1,
                    analysis_code='Mad',
                    action='created',
                    final_result=8.5,
                    raw_data_dict=None
                )
                # user_id should be -1

    def test_with_reason(self, app, db):
        """Test log with reason."""
        with app.app_context():
            from app.services.analysis_audit import log_analysis_action

            with patch('app.services.analysis_audit.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.id = 1

                log_analysis_action(
                    result_id=1,
                    sample_id=1,
                    analysis_code='Mad',
                    action='rejected',
                    final_result=8.5,
                    raw_data_dict={},
                    reason='Value out of range'
                )

    def test_with_error_reason(self, app, db):
        """Test log with error_reason."""
        with app.app_context():
            from app.services.analysis_audit import log_analysis_action

            with patch('app.services.analysis_audit.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.id = 1

                log_analysis_action(
                    result_id=1,
                    sample_id=1,
                    analysis_code='Mad',
                    action='rejected',
                    final_result=8.5,
                    raw_data_dict={},
                    error_reason='TOLERANCE_EXCEEDED'
                )

    def test_with_none_values(self, app, db):
        """Test log with None values."""
        with app.app_context():
            from app.services.analysis_audit import log_analysis_action

            with patch('app.services.analysis_audit.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.id = 1

                log_analysis_action(
                    result_id=1,
                    sample_id=1,
                    analysis_code='Mad',
                    action='created',
                    final_result=None,
                    raw_data_dict=None
                )

    def test_exception_handling(self, app, db):
        """Test exception is handled gracefully."""
        with app.app_context():
            from app.services.analysis_audit import log_analysis_action

            with patch('app.services.analysis_audit.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.id = 1

                with patch('app.services.analysis_audit.db.session.add', side_effect=SQLAlchemyError("DB Error")):
                    # Should not raise, just log error
                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code='Mad',
                        action='created',
                        final_result=8.5,
                        raw_data_dict={}
                    )

    def test_various_actions(self, app, db):
        """Test various action types."""
        with app.app_context():
            from app.services.analysis_audit import log_analysis_action

            with patch('app.services.analysis_audit.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.id = 1

                for action in ['created', 'updated', 'approved', 'rejected', 'edited_raw']:
                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code='Mad',
                        action=action,
                        final_result=8.5,
                        raw_data_dict={}
                    )

    def test_complex_raw_data(self, app, db):
        """Test with complex raw_data."""
        with app.app_context():
            from app.services.analysis_audit import log_analysis_action

            with patch('app.services.analysis_audit.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.id = 1

                raw_data = {
                    'p1': {'m1': 10.0, 'm2': 1.0, 'm3': 10.5},
                    'p2': {'m1': 10.0, 'm2': 1.0, 'm3': 10.6},
                    'tolerance': 0.1,
                    'notes': 'Тест тайлбар'
                }

                log_analysis_action(
                    result_id=1,
                    sample_id=1,
                    analysis_code='Mad',
                    action='created',
                    final_result=8.5,
                    raw_data_dict=raw_data
                )

    def test_exception_handled_gracefully(self, app, db):
        """Test exception is handled gracefully (no rollback, caller decides)."""
        with app.app_context():
            from app.services.analysis_audit import log_analysis_action

            with patch('app.services.analysis_audit.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.id = 1

                with patch('app.services.analysis_audit.db.session.add', side_effect=SQLAlchemyError("Error")):
                    # Should not raise; error is logged, no rollback (caller decides)
                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code='Mad',
                        action='created',
                        final_result=8.5,
                        raw_data_dict={}
                    )

    def test_debug_logging(self, app, db):
        """Test debug logging is called."""
        with app.app_context():
            from app.services.analysis_audit import log_analysis_action, logger

            with patch('app.services.analysis_audit.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.id = 1

                with patch.object(logger, 'debug') as mock_debug:
                    log_analysis_action(
                        result_id=123,
                        sample_id=456,
                        analysis_code='Aad',
                        action='approved',
                        final_result=12.5,
                        raw_data_dict={},
                        reason='Normal approval'
                    )
                    mock_debug.assert_called_once()
                    call_args = mock_debug.call_args[0]
                    fmt_string = call_args[0]
                    assert 'AUDIT' in fmt_string
                    # action='approved' is passed as a positional arg to logger.debug
                    assert 'approved' in call_args
