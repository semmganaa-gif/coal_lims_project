# -*- coding: utf-8 -*-
"""
analysis_audit.py модулийн 100% coverage тестүүд
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from dataclasses import dataclass


class TestAnalysisAuditImport:
    """Модуль импорт тест"""

    def test_import_module(self):
        from app.services import analysis_audit
        assert analysis_audit is not None

    def test_import_functions(self):
        from app.services.analysis_audit import (
            _to_jsonable, _safe_json_dumps, log_analysis_action
        )
        assert _to_jsonable is not None
        assert _safe_json_dumps is not None
        assert log_analysis_action is not None


class TestToJsonable:
    """_to_jsonable функцийн тест"""

    def test_dataclass_input(self):
        from app.services.analysis_audit import _to_jsonable

        @dataclass
        class TestData:
            name: str
            value: int

        data = TestData(name="test", value=123)
        result = _to_jsonable(data)
        assert result == {"name": "test", "value": 123}

    def test_object_with_id(self):
        from app.services.analysis_audit import _to_jsonable
        obj = MagicMock()
        obj.id = 42
        result = _to_jsonable(obj)
        assert result == 42

    def test_plain_value(self):
        from app.services.analysis_audit import _to_jsonable
        assert _to_jsonable("test") == "test"
        assert _to_jsonable(123) == 123
        assert _to_jsonable(None) is None

    def test_exception_handling(self):
        from app.services.analysis_audit import _to_jsonable
        # Object that raises exception on asdict
        obj = MagicMock()
        del obj.id  # No id attribute
        result = _to_jsonable(obj)
        assert result == obj


class TestSafeJsonDumps:
    """_safe_json_dumps функцийн тест"""

    def test_simple_dict(self):
        from app.services.analysis_audit import _safe_json_dumps
        result = _safe_json_dumps({"key": "value"})
        assert json.loads(result) == {"key": "value"}

    def test_mongolian_text(self):
        from app.services.analysis_audit import _safe_json_dumps
        result = _safe_json_dumps({"text": "Монгол текст"})
        assert "Монгол" in result

    def test_dataclass_conversion(self):
        from app.services.analysis_audit import _safe_json_dumps

        @dataclass
        class TestData:
            name: str

        data = {"data": TestData(name="test")}
        result = _safe_json_dumps(data)
        assert "test" in result

    @patch('app.services.analysis_audit.json.dumps')
    def test_non_serializable(self, mock_dumps):
        from app.services.analysis_audit import _safe_json_dumps
        # Simulate TypeError from json.dumps to test fallback to str()
        mock_dumps.side_effect = [TypeError("not serializable"), '"test_object"']

        result = _safe_json_dumps({"test": "value"})
        assert isinstance(result, str)
        # Fallback should call json.dumps with str() version
        assert mock_dumps.call_count == 2

    def test_truncation(self):
        from app.services.analysis_audit import _safe_json_dumps
        # Create a large payload
        large_data = {"data": "x" * 300000}
        result = _safe_json_dumps(large_data, limit_bytes=1000)
        assert "truncated" in result
        assert len(result.encode("utf-8")) < 300000

    def test_limit_bytes_parameter(self):
        from app.services.analysis_audit import _safe_json_dumps
        data = {"key": "a" * 500}
        result = _safe_json_dumps(data, limit_bytes=100)
        assert "truncated" in result


class TestLogAnalysisAction:
    """log_analysis_action функцийн тест"""

    @patch('app.services.analysis_audit.db')
    @patch('app.services.analysis_audit.current_user')
    @patch('app.services.analysis_audit.AnalysisResultLog')
    def test_log_with_authenticated_user(self, mock_log_class, mock_user, mock_db):
        from app.services.analysis_audit import log_analysis_action

        mock_user.is_authenticated = True
        mock_user.id = 5
        mock_log_instance = MagicMock()
        mock_log_class.return_value = mock_log_instance

        log_analysis_action(
            result_id=123,
            sample_id=456,
            analysis_code='Mad',
            action='approved',
            final_result=8.5,
            raw_data_dict={'m1': 10.2, 'm2': 10.3},
            reason='Test reason'
        )

        mock_db.session.add.assert_called_once()

    @patch('app.services.analysis_audit.db')
    @patch('app.services.analysis_audit.current_user')
    @patch('app.services.analysis_audit.AnalysisResultLog')
    def test_log_with_unauthenticated_user(self, mock_log_class, mock_user, mock_db):
        from app.services.analysis_audit import log_analysis_action

        mock_user.is_authenticated = False
        mock_log_instance = MagicMock()
        mock_log_class.return_value = mock_log_instance

        log_analysis_action(
            result_id=123,
            sample_id=456,
            analysis_code='CV',
            action='created',
            final_result=6000,
            raw_data_dict=None
        )

        # user_id should be -1
        call_kwargs = mock_log_class.call_args[1]
        assert call_kwargs['user_id'] == -1

    @patch('app.services.analysis_audit.db')
    @patch('app.services.analysis_audit.current_user')
    @patch('app.services.analysis_audit.AnalysisResultLog')
    def test_log_with_error_reason(self, mock_log_class, mock_user, mock_db):
        from app.services.analysis_audit import log_analysis_action

        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_log_instance = MagicMock()
        mock_log_class.return_value = mock_log_instance

        log_analysis_action(
            result_id=1,
            sample_id=2,
            analysis_code='Aad',
            action='rejected',
            final_result=50.0,
            raw_data_dict={'p1': {'result': 50}},
            reason='Failed QC',
            error_reason='measurement_error'
        )

        call_kwargs = mock_log_class.call_args[1]
        assert call_kwargs['error_reason'] == 'measurement_error'

    @patch('app.services.analysis_audit.db')
    @patch('app.services.analysis_audit.current_user')
    @patch('app.services.analysis_audit.AnalysisResultLog')
    def test_log_exception_handling(self, mock_log_class, mock_user, mock_db):
        from app.services.analysis_audit import log_analysis_action

        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_log_class.side_effect = Exception("Database error")

        # Should not raise exception
        log_analysis_action(
            result_id=1,
            sample_id=2,
            analysis_code='TS',
            action='updated',
            final_result=0.5,
            raw_data_dict={}
        )

        # Rollback should be called
        mock_db.session.rollback.assert_called()

    @patch('app.services.analysis_audit.db')
    @patch('app.services.analysis_audit.current_user')
    @patch('app.services.analysis_audit.AnalysisResultLog')
    def test_log_rollback_exception(self, mock_log_class, mock_user, mock_db):
        from app.services.analysis_audit import log_analysis_action

        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_log_class.side_effect = Exception("Database error")
        mock_db.session.rollback.side_effect = Exception("Rollback failed")

        # Should not raise exception even if rollback fails
        log_analysis_action(
            result_id=1,
            sample_id=2,
            analysis_code='Vad',
            action='edited_raw',
            final_result=35.0,
            raw_data_dict={'p1': {}}
        )

    @patch('app.services.analysis_audit.db')
    @patch('app.services.analysis_audit.current_user')
    @patch('app.services.analysis_audit.AnalysisResultLog')
    def test_log_none_raw_data(self, mock_log_class, mock_user, mock_db):
        from app.services.analysis_audit import log_analysis_action

        mock_user.is_authenticated = True
        mock_user.id = 1

        log_analysis_action(
            result_id=1,
            sample_id=2,
            analysis_code='MT',
            action='created',
            final_result=15.0,
            raw_data_dict=None
        )

        mock_db.session.add.assert_called_once()
