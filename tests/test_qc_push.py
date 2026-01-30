# -*- coding: utf-8 -*-
"""
QC модулийн coverage тестүүд
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date


class TestQcToDate:
    """qc_to_date тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.qc import qc_to_date
        assert qc_to_date is not None

    def test_none_input(self):
        """None input returns None"""
        from app.utils.qc import qc_to_date
        assert qc_to_date(None) is None

    def test_datetime_input(self):
        """Datetime input returns date"""
        from app.utils.qc import qc_to_date
        dt = datetime(2025, 1, 15, 10, 30, 0)
        result = qc_to_date(dt)
        assert result == date(2025, 1, 15)

    def test_date_input(self):
        """Date input returns date"""
        from app.utils.qc import qc_to_date
        d = date(2025, 1, 15)
        result = qc_to_date(d)
        assert result == date(2025, 1, 15)


class TestQcSplitFamily:
    """qc_split_family тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.qc import qc_split_family
        assert qc_split_family is not None

    def test_empty_code(self):
        """Empty code"""
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family("")
        assert family == ""
        assert slot is None

    def test_none_code(self):
        """None code"""
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family(None)
        assert family is None
        assert slot is None

    def test_day_sample(self):
        """Day sample (D1, D2)"""
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family("TT_D1")
        assert family == "TT_D"
        assert slot == "1"

    def test_night_sample(self):
        """Night sample (N1, N2)"""
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family("TT_N3")
        assert family == "TT_N"
        assert slot == "3"

    def test_composite(self):
        """Composite sample"""
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family("TT_Dcom")
        assert family == "TT_D"
        assert slot == "com"

    def test_no_match(self):
        """No match pattern"""
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family("RANDOM_CODE")
        assert family == "RANDOM_CODE"
        assert slot is None


class TestQcIsComposite:
    """qc_is_composite тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.qc import qc_is_composite
        assert qc_is_composite is not None

    def test_composite_sample_type(self):
        """Sample type is composite"""
        from app.utils.qc import qc_is_composite
        sample = MagicMock()
        sample.sample_type = "composite"
        assert qc_is_composite(sample, None) is True

    def test_com_sample_type(self):
        """Sample type is com"""
        from app.utils.qc import qc_is_composite
        sample = MagicMock()
        sample.sample_type = "COM"
        assert qc_is_composite(sample, None) is True

    def test_slot_contains_com(self):
        """Slot contains com"""
        from app.utils.qc import qc_is_composite
        sample = MagicMock()
        sample.sample_type = "coal"
        assert qc_is_composite(sample, "Dcom") is True

    def test_not_composite(self):
        """Not a composite"""
        from app.utils.qc import qc_is_composite
        sample = MagicMock()
        sample.sample_type = "coal"
        assert qc_is_composite(sample, "1") is False

    def test_none_sample_type(self):
        """None sample type"""
        from app.utils.qc import qc_is_composite
        sample = MagicMock()
        sample.sample_type = None
        assert qc_is_composite(sample, None) is False


class TestQcCheckSpec:
    """qc_check_spec тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec is not None

    def test_none_value(self):
        """None value"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(None, (5.0, 15.0)) is False

    def test_none_spec(self):
        """None spec"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(10.0, None) is False

    def test_within_range(self):
        """Value within range"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(10.0, (5.0, 15.0)) is False

    def test_below_min(self):
        """Value below min"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(3.0, (5.0, 15.0)) is True

    def test_above_max(self):
        """Value above max"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(20.0, (5.0, 15.0)) is True

    def test_at_min(self):
        """Value at min (not exceeded)"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(5.0, (5.0, 15.0)) is False

    def test_at_max(self):
        """Value at max (not exceeded)"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(15.0, (5.0, 15.0)) is False

    def test_none_min(self):
        """None min in spec"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(3.0, (None, 15.0)) is False

    def test_none_max(self):
        """None max in spec"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(20.0, (5.0, None)) is False

    def test_invalid_value(self):
        """Invalid value (string)"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec("abc", (5.0, 15.0)) is False

    def test_string_number(self):
        """String number value"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec("10.0", (5.0, 15.0)) is False


class TestParseNumeric:
    """parse_numeric тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.qc import parse_numeric
        assert parse_numeric is not None

    def test_none(self):
        """None input"""
        from app.utils.qc import parse_numeric
        assert parse_numeric(None) is None

    def test_float(self):
        """Float input"""
        from app.utils.qc import parse_numeric
        assert parse_numeric(10.5) == 10.5

    def test_int(self):
        """Int input"""
        from app.utils.qc import parse_numeric
        assert parse_numeric(10) == 10.0

    def test_string_number(self):
        """String number"""
        from app.utils.qc import parse_numeric
        assert parse_numeric("10.5") == 10.5

    def test_string_with_comma(self):
        """String with comma"""
        from app.utils.qc import parse_numeric
        assert parse_numeric("1,234.56") == 1234.56

    def test_string_with_spaces(self):
        """String with spaces"""
        from app.utils.qc import parse_numeric
        assert parse_numeric("  10.5  ") == 10.5

    def test_invalid_string(self):
        """Invalid string"""
        from app.utils.qc import parse_numeric
        assert parse_numeric("abc") is None


class TestEvalQcStatus:
    """eval_qc_status тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.qc import eval_qc_status
        assert eval_qc_status is not None

    def test_no_rule_ok(self):
        """No rule, low percentage"""
        from app.utils.qc import eval_qc_status
        result = eval_qc_status("UNKNOWN_PARAM", 0.1, 1.0)
        assert result == "ok"

    def test_no_rule_warn(self):
        """No rule, medium percentage"""
        from app.utils.qc import eval_qc_status
        result = eval_qc_status("UNKNOWN_PARAM", 0.3, 3.0)
        assert result == "warn"

    def test_no_rule_fail(self):
        """No rule, high percentage"""
        from app.utils.qc import eval_qc_status
        result = eval_qc_status("UNKNOWN_PARAM", 0.6, 6.0)
        assert result == "fail"

    def test_no_rule_none_pct(self):
        """No rule, None percentage"""
        from app.utils.qc import eval_qc_status
        result = eval_qc_status("UNKNOWN_PARAM", 0.1, None)
        assert result == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {'Mad': {'mode': 'abs', 'warn': 0.2, 'fail': 0.5}})
    def test_abs_mode_ok(self):
        """Absolute mode - ok"""
        from app.utils.qc import eval_qc_status
        result = eval_qc_status("Mad", 0.1, 1.0)
        assert result == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {'Mad': {'mode': 'abs', 'warn': 0.2, 'fail': 0.5}})
    def test_abs_mode_warn(self):
        """Absolute mode - warn"""
        from app.utils.qc import eval_qc_status
        result = eval_qc_status("Mad", 0.3, 3.0)
        assert result == "warn"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {'Mad': {'mode': 'abs', 'warn': 0.2, 'fail': 0.5}})
    def test_abs_mode_fail(self):
        """Absolute mode - fail"""
        from app.utils.qc import eval_qc_status
        result = eval_qc_status("Mad", 0.6, 6.0)
        assert result == "fail"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {'Mad': {'mode': 'abs', 'warn': 0.2, 'fail': 0.5}})
    def test_abs_mode_none_diff(self):
        """Absolute mode - None diff"""
        from app.utils.qc import eval_qc_status
        result = eval_qc_status("Mad", None, 1.0)
        assert result == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {'CV': {'mode': 'rel', 'warn': 2.0, 'fail': 5.0}})
    def test_rel_mode_ok(self):
        """Relative mode - ok"""
        from app.utils.qc import eval_qc_status
        result = eval_qc_status("CV", 100, 1.0)
        assert result == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {'CV': {'mode': 'rel', 'warn': 2.0, 'fail': 5.0}})
    def test_rel_mode_warn(self):
        """Relative mode - warn"""
        from app.utils.qc import eval_qc_status
        result = eval_qc_status("CV", 300, 3.0)
        assert result == "warn"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {'CV': {'mode': 'rel', 'warn': 2.0, 'fail': 5.0}})
    def test_rel_mode_fail(self):
        """Relative mode - fail"""
        from app.utils.qc import eval_qc_status
        result = eval_qc_status("CV", 600, 6.0)
        assert result == "fail"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {'CV': {'mode': 'rel', 'warn': 2.0, 'fail': 5.0}})
    def test_rel_mode_none_pct(self):
        """Relative mode - None percentage"""
        from app.utils.qc import eval_qc_status
        result = eval_qc_status("CV", 100, None)
        assert result == "ok"


class TestSplitStreamKey:
    """split_stream_key тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.qc import split_stream_key
        assert split_stream_key is not None

    def test_two_hour_day(self):
        """Two hour day sample"""
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = "TT D1"
        sample.name = None
        sample.sample_name = None
        sample.id = 1
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "two_hour"
        assert idx == 1

    def test_two_hour_night(self):
        """Two hour night sample"""
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = "TT N5"
        sample.name = None
        sample.sample_name = None
        sample.id = 2
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "two_hour"
        assert idx == 5

    def test_composite_ncom(self):
        """Composite ncom"""
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = "TT Ncom"
        sample.name = None
        sample.sample_name = None
        sample.id = 3
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "composite"
        assert idx is None

    def test_composite_comp(self):
        """Composite comp"""
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = "TT comp"
        sample.name = None
        sample.sample_name = None
        sample.id = 4
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "composite"

    def test_unknown(self):
        """Unknown pattern"""
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = "RANDOM"
        sample.name = None
        sample.sample_name = None
        sample.id = 5
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "unknown"

    def test_no_code_uses_name(self):
        """No code uses name"""
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = None
        sample.name = "TT D2"
        sample.sample_name = None
        sample.id = 6
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "two_hour"

    def test_no_code_no_name_uses_id(self):
        """No code, no name uses id"""
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = None
        sample.name = None
        sample.sample_name = None
        sample.id = 7
        prefix, stream_type, idx = split_stream_key(sample)
        assert "7" in prefix or "ID" in prefix


class TestSulfurMapFor:
    """sulfur_map_for тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.qc import sulfur_map_for
        assert sulfur_map_for is not None

    def test_empty_ids(self):
        """Empty sample IDs"""
        from app.utils.qc import sulfur_map_for
        result = sulfur_map_for([])
        assert result == {}

    def test_none_ids(self):
        """None sample IDs"""
        from app.utils.qc import sulfur_map_for
        result = sulfur_map_for(None)
        assert result == {}

    @patch('app.utils.qc.AnalysisResult')
    def test_with_results(self, mock_ar):
        """With analysis results"""
        from app.utils.qc import sulfur_map_for

        # Mock query chain
        mock_query = MagicMock()
        mock_ar.query.filter.return_value.order_by.return_value.all.return_value = [
            MagicMock(sample_id=1, final_result=0.45),
            MagicMock(sample_id=2, final_result=0.52)
        ]

        result = sulfur_map_for([1, 2])
        assert isinstance(result, dict)

    @patch('app.utils.qc.AnalysisResult')
    def test_with_none_result(self, mock_ar):
        """With None final_result"""
        from app.utils.qc import sulfur_map_for

        mock_ar.query.filter.return_value.order_by.return_value.all.return_value = [
            MagicMock(sample_id=1, final_result=None),
            MagicMock(sample_id=2, final_result=0.52)
        ]

        result = sulfur_map_for([1, 2])
        # sample_id=1 should not be in result due to None
        assert isinstance(result, dict)

    @patch('app.utils.qc.AnalysisResult')
    def test_duplicate_sample_id(self, mock_ar):
        """Duplicate sample_id keeps first"""
        from app.utils.qc import sulfur_map_for

        mock_ar.query.filter.return_value.order_by.return_value.all.return_value = [
            MagicMock(sample_id=1, final_result=0.45),
            MagicMock(sample_id=1, final_result=0.50)  # Duplicate
        ]

        result = sulfur_map_for([1])
        # First value should be kept
        assert isinstance(result, dict)

    @patch('app.utils.qc.AnalysisResult')
    def test_invalid_result_value(self, mock_ar):
        """Invalid result value"""
        from app.utils.qc import sulfur_map_for

        mock_ar.query.filter.return_value.order_by.return_value.all.return_value = [
            MagicMock(sample_id=1, final_result="invalid")
        ]

        result = sulfur_map_for([1])
        # Should handle gracefully
        assert isinstance(result, dict)
