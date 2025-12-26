# -*- coding: utf-8 -*-
"""
Tests for app/services/analysis_audit.py
Analysis result audit logging service tests
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from dataclasses import dataclass


class TestToJsonable:
    """_to_jsonable function tests"""

    def test_import(self):
        """Import function"""
        from app.services.analysis_audit import _to_jsonable
        assert callable(_to_jsonable)

    def test_dataclass_converted_to_dict(self):
        """Dataclass is converted to dict"""
        from app.services.analysis_audit import _to_jsonable

        @dataclass
        class Sample:
            id: int
            name: str

        obj = Sample(id=1, name="test")
        result = _to_jsonable(obj)
        assert result == {"id": 1, "name": "test"}

    def test_object_with_id_returns_id(self):
        """Object with id attribute returns the id"""
        from app.services.analysis_audit import _to_jsonable

        class MockModel:
            id = 123

        result = _to_jsonable(MockModel())
        assert result == 123

    def test_object_without_id_returns_as_is(self):
        """Object without id returns as-is"""
        from app.services.analysis_audit import _to_jsonable

        obj = {"key": "value"}
        result = _to_jsonable(obj)
        assert result == {"key": "value"}

    def test_string_returns_as_is(self):
        """String returns as-is"""
        from app.services.analysis_audit import _to_jsonable
        assert _to_jsonable("test") == "test"

    def test_int_returns_as_is(self):
        """Int returns as-is"""
        from app.services.analysis_audit import _to_jsonable
        assert _to_jsonable(123) == 123

    def test_float_returns_as_is(self):
        """Float returns as-is"""
        from app.services.analysis_audit import _to_jsonable
        assert _to_jsonable(10.5) == 10.5

    def test_none_returns_as_is(self):
        """None returns as-is"""
        from app.services.analysis_audit import _to_jsonable
        assert _to_jsonable(None) is None

    def test_list_returns_as_is(self):
        """List returns as-is"""
        from app.services.analysis_audit import _to_jsonable
        assert _to_jsonable([1, 2, 3]) == [1, 2, 3]

    def test_nested_dataclass(self):
        """Nested dataclass is converted"""
        from app.services.analysis_audit import _to_jsonable

        @dataclass
        class Inner:
            value: int

        @dataclass
        class Outer:
            inner: Inner

        obj = Outer(inner=Inner(value=42))
        result = _to_jsonable(obj)
        assert result == {"inner": {"value": 42}}


class TestSafeJsonDumps:
    """_safe_json_dumps function tests"""

    def test_import(self):
        """Import function"""
        from app.services.analysis_audit import _safe_json_dumps
        assert callable(_safe_json_dumps)

    def test_dict_to_json(self):
        """Dict is converted to JSON string"""
        from app.services.analysis_audit import _safe_json_dumps

        result = _safe_json_dumps({"key": "value"})
        assert result == '{"key": "value"}'

    def test_list_to_json(self):
        """List is converted to JSON string"""
        from app.services.analysis_audit import _safe_json_dumps

        result = _safe_json_dumps([1, 2, 3])
        assert result == "[1, 2, 3]"

    def test_mongolian_text_preserved(self):
        """Mongolian text is preserved (ensure_ascii=False)"""
        from app.services.analysis_audit import _safe_json_dumps

        result = _safe_json_dumps({"text": "Монгол текст"})
        assert "Монгол текст" in result
        # Should not be escaped like \u041c...
        assert "\\u" not in result

    def test_int_to_json(self):
        """Int is converted to JSON string"""
        from app.services.analysis_audit import _safe_json_dumps

        result = _safe_json_dumps(123)
        assert result == "123"

    def test_float_to_json(self):
        """Float is converted to JSON string"""
        from app.services.analysis_audit import _safe_json_dumps

        result = _safe_json_dumps(10.5)
        assert result == "10.5"

    def test_none_to_json(self):
        """None is converted to null"""
        from app.services.analysis_audit import _safe_json_dumps

        result = _safe_json_dumps(None)
        assert result == "null"

    def test_string_to_json(self):
        """String is quoted in JSON"""
        from app.services.analysis_audit import _safe_json_dumps

        result = _safe_json_dumps("test")
        assert result == '"test"'

    def test_dataclass_converted(self):
        """Dataclass is converted via default handler"""
        from app.services.analysis_audit import _safe_json_dumps

        @dataclass
        class TestClass:
            value: int

        result = _safe_json_dumps(TestClass(value=42))
        parsed = json.loads(result)
        assert parsed == {"value": 42}

    def test_large_payload_truncated(self):
        """Large payload is truncated"""
        from app.services.analysis_audit import _safe_json_dumps

        # Create large string (over 200KB)
        large_data = {"data": "x" * 300000}
        result = _safe_json_dumps(large_data, limit_bytes=1000)
        assert "[truncated]" in result
        # Should be much shorter than original
        assert len(result) < len(json.dumps(large_data))

    def test_small_payload_not_truncated(self):
        """Small payload is not truncated"""
        from app.services.analysis_audit import _safe_json_dumps

        small_data = {"key": "value"}
        result = _safe_json_dumps(small_data)
        assert "[truncated]" not in result
        assert result == '{"key": "value"}'

    def test_non_serializable_converted_to_string(self):
        """Non-serializable objects converted to string"""
        from app.services.analysis_audit import _safe_json_dumps

        class CustomClass:
            def __str__(self):
                return "CustomObject"

            @property
            def id(self):
                return 999

        # Object with id attribute returns the id
        result = _safe_json_dumps(CustomClass())
        assert result == "999"

    def test_empty_dict(self):
        """Empty dict is converted"""
        from app.services.analysis_audit import _safe_json_dumps

        result = _safe_json_dumps({})
        assert result == "{}"

    def test_nested_dict(self):
        """Nested dict is converted"""
        from app.services.analysis_audit import _safe_json_dumps

        data = {"outer": {"inner": {"deep": 123}}}
        result = _safe_json_dumps(data)
        parsed = json.loads(result)
        assert parsed["outer"]["inner"]["deep"] == 123


class TestLogAnalysisAction:
    """log_analysis_action function tests"""

    def test_import(self):
        """Import function"""
        from app.services.analysis_audit import log_analysis_action
        assert callable(log_analysis_action)

    def test_function_signature(self):
        """Function has expected parameters"""
        from app.services.analysis_audit import log_analysis_action
        import inspect

        sig = inspect.signature(log_analysis_action)
        params = list(sig.parameters.keys())
        assert "result_id" in params
        assert "sample_id" in params
        assert "analysis_code" in params
        assert "action" in params
        assert "final_result" in params
        assert "raw_data_dict" in params
        assert "reason" in params
        assert "error_reason" in params

    def test_creates_log_entry(self, app):
        """Creates AnalysisResultLog entry"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = True
                    mock_user.id = 1

                    log_analysis_action(
                        result_id=123,
                        sample_id=456,
                        analysis_code="Mad",
                        action="approved",
                        final_result=8.5,
                        raw_data_dict={"m1": 10.0, "m2": 10.1}
                    )

                    mock_add.assert_called_once()

    def test_anonymous_user_gets_minus_one(self, app):
        """Anonymous user gets user_id=-1"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = False

                    log_analysis_action(
                        result_id=123,
                        sample_id=456,
                        analysis_code="Aad",
                        action="created",
                        final_result=5.5,
                        raw_data_dict={}
                    )

                    # Check that log was created
                    mock_add.assert_called_once()
                    log_entry = mock_add.call_args[0][0]
                    assert log_entry.user_id == -1

    def test_handles_none_raw_data(self, app):
        """Handles None raw_data_dict"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = False

                    # Should not raise exception
                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code="TS",
                        action="updated",
                        final_result=0.5,
                        raw_data_dict=None
                    )

                    mock_add.assert_called_once()

    def test_handles_none_final_result(self, app):
        """Handles None final_result"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = False

                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code="Vad",
                        action="created",
                        final_result=None,
                        raw_data_dict={"m1": 10.0}
                    )

                    mock_add.assert_called_once()

    def test_reason_passed_to_log(self, app):
        """Reason is passed to log entry"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = False

                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code="CV",
                        action="rejected",
                        final_result=None,
                        raw_data_dict={},
                        reason="Quality issue"
                    )

                    log_entry = mock_add.call_args[0][0]
                    assert log_entry.reason == "Quality issue"

    def test_error_reason_passed_to_log(self, app):
        """Error reason is passed to log entry"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = False

                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code="Gi",
                        action="rejected",
                        final_result=None,
                        raw_data_dict={},
                        error_reason="T_EXCEEDED"
                    )

                    log_entry = mock_add.call_args[0][0]
                    assert log_entry.error_reason == "T_EXCEEDED"

    def test_exception_handled_gracefully(self, app):
        """Exception during logging is handled gracefully"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add', side_effect=Exception("DB Error")):
                with patch.object(db.session, 'rollback') as mock_rollback:
                    with patch('app.services.analysis_audit.current_user') as mock_user:
                        mock_user.is_authenticated = False

                        # Should not raise exception
                        log_analysis_action(
                            result_id=1,
                            sample_id=1,
                            analysis_code="TRD",
                            action="created",
                            final_result=1.0,
                            raw_data_dict={}
                        )

                        # Rollback should be called
                        mock_rollback.assert_called()

    def test_does_not_commit(self, app):
        """Function does not commit - caller is responsible"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit') as mock_commit:
                    with patch('app.services.analysis_audit.current_user') as mock_user:
                        mock_user.is_authenticated = False

                        log_analysis_action(
                            result_id=1,
                            sample_id=1,
                            analysis_code="FCad",
                            action="approved",
                            final_result=50.0,
                            raw_data_dict={}
                        )

                        # Commit should NOT be called
                        mock_commit.assert_not_called()

    def test_analysis_code_set(self, app):
        """Analysis code is set on log entry"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = False

                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code="CSN",
                        action="created",
                        final_result=5.0,
                        raw_data_dict={}
                    )

                    log_entry = mock_add.call_args[0][0]
                    assert log_entry.analysis_code == "CSN"

    def test_action_set(self, app):
        """Action is set on log entry"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = False

                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code="HGI",
                        action="edited_raw",
                        final_result=45,
                        raw_data_dict={}
                    )

                    log_entry = mock_add.call_args[0][0]
                    assert log_entry.action == "edited_raw"

    def test_result_id_set(self, app):
        """Result ID is set on log entry"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = False

                    log_analysis_action(
                        result_id=999,
                        sample_id=1,
                        analysis_code="Aad",
                        action="created",
                        final_result=5.0,
                        raw_data_dict={}
                    )

                    log_entry = mock_add.call_args[0][0]
                    assert log_entry.analysis_result_id == 999

    def test_sample_id_set(self, app):
        """Sample ID is set on log entry"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = False

                    log_analysis_action(
                        result_id=1,
                        sample_id=888,
                        analysis_code="Mad",
                        action="approved",
                        final_result=8.0,
                        raw_data_dict={}
                    )

                    log_entry = mock_add.call_args[0][0]
                    assert log_entry.sample_id == 888


class TestEdgeCases:
    """Edge case tests"""

    def test_empty_raw_data_dict(self, app):
        """Empty raw_data_dict works"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = False

                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code="Vad",
                        action="created",
                        final_result=30.0,
                        raw_data_dict={}
                    )

                    log_entry = mock_add.call_args[0][0]
                    assert log_entry.raw_data_snapshot == "{}"

    def test_complex_raw_data(self, app):
        """Complex raw_data_dict is serialized"""
        from app.services.analysis_audit import log_analysis_action
        from app import db
        import json

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = False

                    raw_data = {
                        "p1": {"m1": 10.0, "m2": 10.5, "m3": 10.2},
                        "p2": {"m1": 10.1, "m2": 10.6, "m3": 10.3},
                        "avg": 10.25,
                        "diff": 0.05
                    }

                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code="Mad",
                        action="approved",
                        final_result=10.25,
                        raw_data_dict=raw_data
                    )

                    log_entry = mock_add.call_args[0][0]
                    parsed = json.loads(log_entry.raw_data_snapshot)
                    assert parsed["p1"]["m1"] == 10.0
                    assert parsed["avg"] == 10.25

    def test_mongolian_reason(self, app):
        """Mongolian text in reason is preserved"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = False

                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code="CV",
                        action="rejected",
                        final_result=None,
                        raw_data_dict={},
                        reason="Чанар хангахгүй"
                    )

                    log_entry = mock_add.call_args[0][0]
                    assert log_entry.reason == "Чанар хангахгүй"

    def test_string_final_result(self, app):
        """String final_result is serialized"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = False

                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code="CSN",
                        action="created",
                        final_result="A1",
                        raw_data_dict={}
                    )

                    log_entry = mock_add.call_args[0][0]
                    assert '"A1"' in log_entry.final_result_snapshot

    def test_rollback_failure_handled(self, app):
        """Rollback failure is handled"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add', side_effect=Exception("Add Error")):
                with patch.object(db.session, 'rollback', side_effect=Exception("Rollback Error")):
                    with patch('app.services.analysis_audit.current_user') as mock_user:
                        mock_user.is_authenticated = False

                        # Should not raise exception even with rollback failure
                        log_analysis_action(
                            result_id=1,
                            sample_id=1,
                            analysis_code="Mad",
                            action="created",
                            final_result=5.0,
                            raw_data_dict={}
                        )

    def test_authenticated_user_id_used(self, app):
        """Authenticated user's ID is used"""
        from app.services.analysis_audit import log_analysis_action
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch('app.services.analysis_audit.current_user') as mock_user:
                    mock_user.is_authenticated = True
                    mock_user.id = 42

                    log_analysis_action(
                        result_id=1,
                        sample_id=1,
                        analysis_code="Aad",
                        action="approved",
                        final_result=5.0,
                        raw_data_dict={}
                    )

                    log_entry = mock_add.call_args[0][0]
                    assert log_entry.user_id == 42
