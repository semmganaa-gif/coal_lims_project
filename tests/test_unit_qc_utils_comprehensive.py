# -*- coding: utf-8 -*-
"""
QC Utils - бүрэн unit тестүүд
"""
import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch
from app.utils.qc import (
    qc_to_date,
    qc_split_family,
    qc_is_composite,
    qc_check_spec,
    parse_numeric,
    eval_qc_status,
    split_stream_key,
    sulfur_map_for,
)


class TestQcToDate:
    """qc_to_date function tests"""

    def test_datetime_to_date(self):
        """Convert datetime to date"""
        dt = datetime(2024, 12, 18, 10, 30, 0)
        result = qc_to_date(dt)
        assert result == date(2024, 12, 18)

    def test_date_unchanged(self):
        """Date returns unchanged"""
        d = date(2024, 12, 18)
        result = qc_to_date(d)
        assert result == d

    def test_none_returns_none(self):
        """None returns None"""
        assert qc_to_date(None) is None

    def test_falsy_returns_none(self):
        """Empty/falsy returns None"""
        assert qc_to_date('') is None
        assert qc_to_date(0) is None


class TestQcSplitFamily:
    """qc_split_family function tests"""

    def test_day_shift_sample(self):
        """Split day shift sample code"""
        family, slot = qc_split_family("TT_D1")
        assert family == "TT_D"
        assert slot == "1"

    def test_night_shift_sample(self):
        """Split night shift sample code"""
        family, slot = qc_split_family("TT_N2")
        assert family == "TT_N"
        assert slot == "2"

    def test_composite_sample(self):
        """Split composite sample code"""
        family, slot = qc_split_family("TT_Dcom")
        assert family == "TT_D"
        assert slot == "com"

    def test_multi_digit_slot(self):
        """Split sample with multi-digit slot"""
        family, slot = qc_split_family("SC20251205_D12")
        assert family == "SC20251205_D"
        assert slot == "12"

    def test_no_match(self):
        """Non-matching code returns original"""
        family, slot = qc_split_family("OTHER_CODE")
        assert family == "OTHER_CODE"
        assert slot is None

    def test_empty_code(self):
        """Empty code returns empty"""
        family, slot = qc_split_family("")
        assert family == ""
        assert slot is None

    def test_none_code(self):
        """None code returns None"""
        family, slot = qc_split_family(None)
        assert family is None
        assert slot is None


class TestQcIsComposite:
    """qc_is_composite function tests"""

    def test_composite_by_sample_type(self):
        """Detect composite by sample type"""
        sample = MagicMock(sample_type="COM")
        assert qc_is_composite(sample, None) is True

        sample2 = MagicMock(sample_type="composite")
        assert qc_is_composite(sample2, "1") is True

    def test_composite_by_slot(self):
        """Detect composite by slot"""
        sample = MagicMock(sample_type="2H")
        assert qc_is_composite(sample, "com") is True
        assert qc_is_composite(sample, "Ncom") is True

    def test_not_composite(self):
        """Non-composite samples"""
        sample = MagicMock(sample_type="2H")
        assert qc_is_composite(sample, "1") is False
        assert qc_is_composite(sample, "2") is False

    def test_empty_sample_type(self):
        """Handle empty sample type"""
        sample = MagicMock(sample_type="")
        assert qc_is_composite(sample, "1") is False

    def test_none_sample_type(self):
        """Handle None sample type"""
        sample = MagicMock(sample_type=None)
        assert qc_is_composite(sample, "1") is False


class TestQcCheckSpec:
    """qc_check_spec function tests"""

    def test_within_spec(self):
        """Value within specification"""
        assert qc_check_spec(10.0, (8.0, 12.0)) is False
        assert qc_check_spec(8.0, (8.0, 12.0)) is False
        assert qc_check_spec(12.0, (8.0, 12.0)) is False

    def test_below_min(self):
        """Value below minimum"""
        assert qc_check_spec(7.0, (8.0, 12.0)) is True
        assert qc_check_spec(0, (8.0, 12.0)) is True

    def test_above_max(self):
        """Value above maximum"""
        assert qc_check_spec(15.0, (8.0, 12.0)) is True
        assert qc_check_spec(100, (8.0, 12.0)) is True

    def test_none_value(self):
        """None value returns False"""
        assert qc_check_spec(None, (8.0, 12.0)) is False

    def test_none_spec(self):
        """None spec returns False"""
        assert qc_check_spec(10.0, None) is False

    def test_invalid_value(self):
        """Invalid value returns False"""
        assert qc_check_spec("invalid", (8.0, 12.0)) is False
        assert qc_check_spec("abc", (8.0, 12.0)) is False

    def test_string_numeric_value(self):
        """String numeric value works"""
        assert qc_check_spec("10.0", (8.0, 12.0)) is False
        assert qc_check_spec("15.0", (8.0, 12.0)) is True

    def test_partial_spec(self):
        """Spec with one limit None"""
        assert qc_check_spec(5.0, (None, 10.0)) is False  # Below max
        assert qc_check_spec(15.0, (None, 10.0)) is True  # Above max
        assert qc_check_spec(5.0, (10.0, None)) is True   # Below min
        assert qc_check_spec(15.0, (10.0, None)) is False # Above min


class TestParseNumeric:
    """parse_numeric function tests"""

    def test_simple_float(self):
        """Parse simple float string"""
        assert parse_numeric("123.45") == 123.45

    def test_with_comma(self):
        """Parse with comma as thousands separator"""
        assert parse_numeric("1,234.56") == 1234.56
        assert parse_numeric("1,000,000") == 1000000

    def test_integer(self):
        """Parse integer string"""
        assert parse_numeric("100") == 100.0

    def test_float_input(self):
        """Float input returns float"""
        assert parse_numeric(100.5) == 100.5

    def test_int_input(self):
        """Int input returns float"""
        assert parse_numeric(100) == 100.0

    def test_none_input(self):
        """None returns None"""
        assert parse_numeric(None) is None

    def test_invalid_string(self):
        """Invalid string returns None"""
        assert parse_numeric("abc") is None
        assert parse_numeric("not a number") is None

    def test_whitespace(self):
        """Whitespace is stripped"""
        assert parse_numeric("  100.5  ") == 100.5


class TestEvalQcStatus:
    """eval_qc_status function tests"""

    def test_default_ok(self):
        """Default rule - OK status"""
        assert eval_qc_status("UNKNOWN", 0.5, 1.0) == "ok"

    def test_default_warn(self):
        """Default rule - WARN status (2-5%)"""
        assert eval_qc_status("UNKNOWN", 2.0, 3.0) == "warn"
        assert eval_qc_status("UNKNOWN", 2.5, 4.9) == "warn"

    def test_default_fail(self):
        """Default rule - FAIL status (>5%)"""
        assert eval_qc_status("UNKNOWN", 5.0, 6.0) == "fail"
        assert eval_qc_status("UNKNOWN", 10.0, 10.0) == "fail"

    def test_none_diff_pct_default(self):
        """None diff_pct returns ok for default"""
        assert eval_qc_status("UNKNOWN", 1.0, None) == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'Mad': {'mode': 'abs', 'warn': 0.3, 'fail': 0.5}
    })
    def test_abs_mode_ok(self):
        """Absolute mode - OK"""
        assert eval_qc_status("Mad", 0.1, 1.0) == "ok"
        assert eval_qc_status("Mad", 0.29, 5.0) == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'Mad': {'mode': 'abs', 'warn': 0.3, 'fail': 0.5}
    })
    def test_abs_mode_warn(self):
        """Absolute mode - WARN"""
        assert eval_qc_status("Mad", 0.35, 1.0) == "warn"
        assert eval_qc_status("Mad", 0.49, 1.0) == "warn"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'Mad': {'mode': 'abs', 'warn': 0.3, 'fail': 0.5}
    })
    def test_abs_mode_fail(self):
        """Absolute mode - FAIL"""
        assert eval_qc_status("Mad", 0.6, 1.0) == "fail"
        assert eval_qc_status("Mad", 1.0, 1.0) == "fail"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'Mad': {'mode': 'abs', 'warn': 0.3, 'fail': 0.5}
    })
    def test_abs_mode_none_diff(self):
        """Absolute mode - None diff returns ok"""
        assert eval_qc_status("Mad", None, 1.0) == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'Aad': {'mode': 'rel', 'warn': 3.0, 'fail': 5.0}
    })
    def test_rel_mode_ok(self):
        """Relative mode - OK"""
        assert eval_qc_status("Aad", 0.5, 2.0) == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'Aad': {'mode': 'rel', 'warn': 3.0, 'fail': 5.0}
    })
    def test_rel_mode_warn(self):
        """Relative mode - WARN"""
        assert eval_qc_status("Aad", 1.0, 4.0) == "warn"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'Aad': {'mode': 'rel', 'warn': 3.0, 'fail': 5.0}
    })
    def test_rel_mode_fail(self):
        """Relative mode - FAIL"""
        assert eval_qc_status("Aad", 2.0, 6.0) == "fail"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'Aad': {'mode': 'rel', 'warn': 3.0, 'fail': 5.0}
    })
    def test_rel_mode_none_diff_pct(self):
        """Relative mode - None diff_pct returns ok"""
        assert eval_qc_status("Aad", 1.0, None) == "ok"


class TestSplitStreamKey:
    """split_stream_key function tests"""

    def test_day_two_hour_sample(self):
        """Split day two-hour sample"""
        sample = MagicMock(sample_code="TT D1", name=None, sample_name=None, id=1)
        prefix, stream_type, idx = split_stream_key(sample)
        assert prefix == "TT"
        assert stream_type == "two_hour"
        assert idx == 1

    def test_night_two_hour_sample(self):
        """Split night two-hour sample"""
        sample = MagicMock(sample_code="TT N3", name=None, sample_name=None, id=2)
        prefix, stream_type, idx = split_stream_key(sample)
        assert prefix == "TT"
        assert stream_type == "two_hour"
        assert idx == 3

    def test_composite_sample_ncom(self):
        """Split composite sample - Ncom"""
        sample = MagicMock(sample_code="SC Ncom", name=None, sample_name=None, id=3)
        prefix, stream_type, idx = split_stream_key(sample)
        assert prefix == "SC"
        assert stream_type == "composite"
        assert idx is None

    def test_composite_sample_comp(self):
        """Split composite sample - comp"""
        sample = MagicMock(sample_code="PF211 comp", name=None, sample_name=None, id=4)
        prefix, stream_type, idx = split_stream_key(sample)
        assert prefix == "PF211"
        assert stream_type == "composite"
        assert idx is None

    def test_unknown_sample(self):
        """Split unknown sample format"""
        sample = MagicMock(sample_code="UNKNOWN_FORMAT", name=None, sample_name=None, id=5)
        prefix, stream_type, idx = split_stream_key(sample)
        assert prefix == "UNKNOWN_FORMAT"
        assert stream_type == "unknown"
        assert idx is None

    def test_fallback_to_name(self):
        """Fallback to name when sample_code is None"""
        from types import SimpleNamespace
        sample = SimpleNamespace(sample_code=None, name="TT D2", sample_name=None, id=6)
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "two_hour"
        assert idx == 2

    def test_fallback_to_sample_name(self):
        """Fallback to sample_name when others are None"""
        from types import SimpleNamespace
        sample = SimpleNamespace(sample_code=None, name=None, sample_name="SC N1", id=7)
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "two_hour"

    def test_fallback_to_id(self):
        """Fallback to ID when all names are None"""
        from types import SimpleNamespace
        sample = SimpleNamespace(sample_code=None, name=None, sample_name=None, id=8)
        prefix, stream_type, idx = split_stream_key(sample)
        assert "8" in prefix
        assert stream_type == "unknown"

    def test_empty_tokens(self):
        """Handle sample with empty code"""
        sample = MagicMock(sample_code="", name=None, sample_name=None, id=9)
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "unknown"


class TestSulfurMapFor:
    """sulfur_map_for function tests"""

    def test_empty_list(self):
        """Empty list returns empty dict"""
        result = sulfur_map_for([])
        assert result == {}

    def test_none_list(self):
        """None list returns empty dict"""
        result = sulfur_map_for(None)
        assert result == {}

    @patch('app.db')
    def test_with_results(self, mock_db):
        """Returns sulfur values from results"""
        mock_result1 = MagicMock(sample_id=1, final_result=0.45)
        mock_result2 = MagicMock(sample_id=2, final_result=0.52)
        mock_exec = MagicMock()
        mock_exec.scalars.return_value.all.return_value = [mock_result1, mock_result2]
        mock_db.session.execute.return_value = mock_exec

        result = sulfur_map_for([1, 2])
        assert result == {1: 0.45, 2: 0.52}

    @patch('app.db')
    def test_ignores_none_results(self, mock_db):
        """Ignores results with None final_result"""
        mock_result1 = MagicMock(sample_id=1, final_result=0.45)
        mock_result2 = MagicMock(sample_id=2, final_result=None)
        mock_exec = MagicMock()
        mock_exec.scalars.return_value.all.return_value = [mock_result1, mock_result2]
        mock_db.session.execute.return_value = mock_exec

        result = sulfur_map_for([1, 2])
        assert result == {1: 0.45}

    @patch('app.db')
    def test_first_result_wins(self, mock_db):
        """First result for sample_id wins"""
        mock_result1 = MagicMock(sample_id=1, final_result=0.45)
        mock_result2 = MagicMock(sample_id=1, final_result=0.50)  # Same sample_id
        mock_exec = MagicMock()
        mock_exec.scalars.return_value.all.return_value = [mock_result1, mock_result2]
        mock_db.session.execute.return_value = mock_exec

        result = sulfur_map_for([1])
        assert result == {1: 0.45}

    @patch('app.db')
    def test_handles_invalid_float(self, mock_db):
        """Handles invalid float conversion"""
        mock_result1 = MagicMock(sample_id=1, final_result="invalid")
        mock_exec = MagicMock()
        mock_exec.scalars.return_value.all.return_value = [mock_result1]
        mock_db.session.execute.return_value = mock_exec

        result = sulfur_map_for([1])
        assert result == {}

    @patch('app.db')
    def test_no_results(self, mock_db):
        """No results returns empty dict"""
        mock_exec = MagicMock()
        mock_exec.scalars.return_value.all.return_value = []
        mock_db.session.execute.return_value = mock_exec

        result = sulfur_map_for([1, 2, 3])
        assert result == {}
