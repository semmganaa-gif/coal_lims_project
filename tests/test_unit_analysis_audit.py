# -*- coding: utf-8 -*-
"""
Analysis audit service тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass


class TestToJsonable:
    """_to_jsonable function тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.services.analysis_audit import _to_jsonable
        assert _to_jsonable is not None

    def test_dataclass_conversion(self):
        """Dataclass -> dict"""
        from app.services.analysis_audit import _to_jsonable

        @dataclass
        class TestData:
            value: int
            name: str

        data = TestData(value=10, name="test")
        result = _to_jsonable(data)
        assert isinstance(result, dict)
        assert result['value'] == 10
        assert result['name'] == "test"

    def test_object_with_id(self):
        """Object with id attribute"""
        from app.services.analysis_audit import _to_jsonable

        class FakeModel:
            id = 123

        obj = FakeModel()
        result = _to_jsonable(obj)
        assert result == 123

    def test_regular_value(self):
        """Regular value returns as-is"""
        from app.services.analysis_audit import _to_jsonable
        assert _to_jsonable(10) == 10
        assert _to_jsonable("test") == "test"
        assert _to_jsonable([1, 2, 3]) == [1, 2, 3]

    def test_none_value(self):
        """None value"""
        from app.services.analysis_audit import _to_jsonable
        assert _to_jsonable(None) is None


class TestSafeJsonDumps:
    """_safe_json_dumps function тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.services.analysis_audit import _safe_json_dumps
        assert _safe_json_dumps is not None

    def test_simple_dict(self):
        """Simple dict serialization"""
        from app.services.analysis_audit import _safe_json_dumps
        data = {'key': 'value', 'number': 123}
        result = _safe_json_dumps(data)
        assert 'key' in result
        assert 'value' in result

    def test_mongolian_text(self):
        """Mongolian text serialization"""
        from app.services.analysis_audit import _safe_json_dumps
        data = {'text': 'Монгол текст'}
        result = _safe_json_dumps(data)
        assert 'Монгол текст' in result

    def test_large_payload_truncation(self):
        """Large payload truncation"""
        from app.services.analysis_audit import _safe_json_dumps
        # Create data larger than limit
        large_data = {'data': 'x' * 250000}
        result = _safe_json_dumps(large_data, limit_bytes=1000)
        assert 'truncated' in result

    def test_string_fallback(self):
        """String as input"""
        from app.services.analysis_audit import _safe_json_dumps
        result = _safe_json_dumps("test string")
        assert isinstance(result, str)


class TestLogAnalysisAction:
    """log_analysis_action function тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.services.analysis_audit import log_analysis_action
        assert log_analysis_action is not None

    @patch('app.services.analysis_audit.db')
    @patch('app.services.analysis_audit.current_user')
    def test_with_authenticated_user(self, mock_user, mock_db):
        """Log with authenticated user"""
        from app.services.analysis_audit import log_analysis_action

        mock_user.is_authenticated = True
        mock_user.id = 1

        log_analysis_action(
            result_id=1,
            sample_id=1,
            analysis_code='TS',
            action='created',
            final_result=10.5,
            raw_data_dict={'m1': 10.0}
        )

        assert mock_db.session.add.called

    @patch('app.services.analysis_audit.db')
    @patch('app.services.analysis_audit.current_user')
    def test_with_unauthenticated_user(self, mock_user, mock_db):
        """Log with unauthenticated user"""
        from app.services.analysis_audit import log_analysis_action

        mock_user.is_authenticated = False

        log_analysis_action(
            result_id=1,
            sample_id=1,
            analysis_code='TS',
            action='created',
            final_result=10.5,
            raw_data_dict=None
        )

        assert mock_db.session.add.called

    @patch('app.services.analysis_audit.db')
    @patch('app.services.analysis_audit.current_user')
    def test_with_reason(self, mock_user, mock_db):
        """Log with reason"""
        from app.services.analysis_audit import log_analysis_action

        mock_user.is_authenticated = True
        mock_user.id = 1

        log_analysis_action(
            result_id=1,
            sample_id=1,
            analysis_code='Mad',
            action='rejected',
            final_result=8.5,
            raw_data_dict={'m1': 10.0},
            reason='Value out of range'
        )

        assert mock_db.session.add.called

    @patch('app.services.analysis_audit.db')
    @patch('app.services.analysis_audit.current_user')
    def test_with_error_reason(self, mock_user, mock_db):
        """Log with error_reason"""
        from app.services.analysis_audit import log_analysis_action

        mock_user.is_authenticated = True
        mock_user.id = 1

        log_analysis_action(
            result_id=1,
            sample_id=1,
            analysis_code='CV',
            action='error',
            final_result=None,
            raw_data_dict=None,
            error_reason='REPEATABILITY_ERROR'
        )

        assert mock_db.session.add.called

    @patch('app.services.analysis_audit.db')
    @patch('app.services.analysis_audit.current_user')
    def test_exception_handling(self, mock_user, mock_db):
        """Exception handling in log_analysis_action"""
        from app.services.analysis_audit import log_analysis_action

        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_db.session.add.side_effect = Exception("Database error")

        # Should not raise exception
        log_analysis_action(
            result_id=1,
            sample_id=1,
            analysis_code='TS',
            action='created',
            final_result=10.5,
            raw_data_dict={}
        )

        # Should have called rollback
        assert mock_db.session.rollback.called


class TestMainHelpers:
    """Main helpers тестүүд"""

    def test_get_12h_shift_code_day(self):
        """12H shift code - day"""
        from app.routes.main.helpers import get_12h_shift_code
        from datetime import datetime

        dt_morning = datetime(2024, 1, 1, 7, 0)
        dt_afternoon = datetime(2024, 1, 1, 14, 0)
        dt_evening = datetime(2024, 1, 1, 18, 59)

        assert get_12h_shift_code(dt_morning) == "_D"
        assert get_12h_shift_code(dt_afternoon) == "_D"
        assert get_12h_shift_code(dt_evening) == "_D"

    def test_get_12h_shift_code_night(self):
        """12H shift code - night"""
        from app.routes.main.helpers import get_12h_shift_code
        from datetime import datetime

        dt_night = datetime(2024, 1, 1, 19, 0)
        dt_midnight = datetime(2024, 1, 1, 0, 0)
        dt_early = datetime(2024, 1, 1, 6, 59)

        assert get_12h_shift_code(dt_night) == "_N"
        assert get_12h_shift_code(dt_midnight) == "_N"
        assert get_12h_shift_code(dt_early) == "_N"

    def test_get_quarter_code_q1(self):
        """Quarter code Q1"""
        from app.routes.main.helpers import get_quarter_code
        from datetime import datetime

        assert get_quarter_code(datetime(2024, 1, 1)) == "_Q1"
        assert get_quarter_code(datetime(2024, 2, 15)) == "_Q1"
        assert get_quarter_code(datetime(2024, 3, 31)) == "_Q1"

    def test_get_quarter_code_q2(self):
        """Quarter code Q2"""
        from app.routes.main.helpers import get_quarter_code
        from datetime import datetime

        assert get_quarter_code(datetime(2024, 4, 1)) == "_Q2"
        assert get_quarter_code(datetime(2024, 5, 15)) == "_Q2"
        assert get_quarter_code(datetime(2024, 6, 30)) == "_Q2"

    def test_get_quarter_code_q3(self):
        """Quarter code Q3"""
        from app.routes.main.helpers import get_quarter_code
        from datetime import datetime

        assert get_quarter_code(datetime(2024, 7, 1)) == "_Q3"
        assert get_quarter_code(datetime(2024, 8, 15)) == "_Q3"
        assert get_quarter_code(datetime(2024, 9, 30)) == "_Q3"

    def test_get_quarter_code_q4(self):
        """Quarter code Q4"""
        from app.routes.main.helpers import get_quarter_code
        from datetime import datetime

        assert get_quarter_code(datetime(2024, 10, 1)) == "_Q4"
        assert get_quarter_code(datetime(2024, 11, 15)) == "_Q4"
        assert get_quarter_code(datetime(2024, 12, 31)) == "_Q4"


class TestChatEventsHelpers:
    """Chat events helper тестүүд"""

    def test_get_user_room(self):
        """get_user_room function"""
        from app.routes.chat.events import get_user_room
        assert get_user_room(1) == "user_1"
        assert get_user_room(123) == "user_123"
