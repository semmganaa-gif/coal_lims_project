# tests/test_qc_utils_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/qc.py
"""

import pytest
from datetime import datetime, date
from unittest.mock import patch, MagicMock


class TestQcToDate:
    """Tests for qc_to_date function."""

    def test_datetime_to_date(self, app):
        """Test datetime converts to date."""
        with app.app_context():
            from app.utils.qc import qc_to_date
            dt = datetime(2025, 1, 15, 10, 30, 0)
            result = qc_to_date(dt)
            assert result == date(2025, 1, 15)

    def test_date_passthrough(self, app):
        """Test date passes through unchanged."""
        with app.app_context():
            from app.utils.qc import qc_to_date
            d = date(2025, 1, 15)
            result = qc_to_date(d)
            assert result == date(2025, 1, 15)

    def test_none_returns_none(self, app):
        """Test None returns None."""
        with app.app_context():
            from app.utils.qc import qc_to_date
            result = qc_to_date(None)
            assert result is None

    def test_falsy_returns_none(self, app):
        """Test falsy value returns None."""
        with app.app_context():
            from app.utils.qc import qc_to_date
            result = qc_to_date(0)
            assert result is None


class TestQcSplitFamily:
    """Tests for qc_split_family function."""

    def test_two_hour_day_sample(self, app):
        """Test 2-hour day sample split."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family("TT_D1")
            assert family == "TT_D"
            assert slot == "1"

    def test_two_hour_night_sample(self, app):
        """Test 2-hour night sample split."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family("TT_N2")
            assert family == "TT_N"
            assert slot == "2"

    def test_composite_sample(self, app):
        """Test composite sample split."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family("TT_Dcom")
            assert family == "TT_D"
            assert slot == "com"

    def test_no_match(self, app):
        """Test sample code without pattern match."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family("RANDOM_CODE")
            assert family == "RANDOM_CODE"
            assert slot is None

    def test_none_input(self, app):
        """Test None input."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family(None)
            assert family is None
            assert slot is None

    def test_empty_string(self, app):
        """Test empty string input."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family("")
            assert family == ""
            assert slot is None

    def test_double_digit_slot(self, app):
        """Test double digit slot number."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family("TT_D12")
            assert family == "TT_D"
            assert slot == "12"


class TestQcIsComposite:
    """Tests for qc_is_composite function."""

    def test_composite_by_sample_type(self, app, db):
        """Test composite by sample_type."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            sample = MagicMock()
            sample.sample_type = "composite"
            result = qc_is_composite(sample, None)
            assert result is True

    def test_composite_by_sample_type_com(self, app, db):
        """Test composite by sample_type 'com'."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            sample = MagicMock()
            sample.sample_type = "com"
            result = qc_is_composite(sample, None)
            assert result is True

    def test_composite_by_slot(self, app, db):
        """Test composite by slot containing 'com'."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            sample = MagicMock()
            sample.sample_type = "2H"
            result = qc_is_composite(sample, "com")
            assert result is True

    def test_composite_by_slot_ncom(self, app, db):
        """Test composite by slot 'ncom'."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            sample = MagicMock()
            sample.sample_type = "2H"
            result = qc_is_composite(sample, "Ncom")
            assert result is True

    def test_not_composite(self, app, db):
        """Test not composite."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            sample = MagicMock()
            sample.sample_type = "2H"
            result = qc_is_composite(sample, "1")
            assert result is False

    def test_none_sample_type(self, app, db):
        """Test None sample_type."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            sample = MagicMock()
            sample.sample_type = None
            result = qc_is_composite(sample, "1")
            assert result is False


class TestQcCheckSpec:
    """Tests for qc_check_spec function."""

    def test_value_within_spec(self, app):
        """Test value within specification."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(10.0, (8.0, 12.0))
            assert result is False

    def test_value_below_min(self, app):
        """Test value below minimum."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(5.0, (8.0, 12.0))
            assert result is True

    def test_value_above_max(self, app):
        """Test value above maximum."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(15.0, (8.0, 12.0))
            assert result is True

    def test_value_at_min(self, app):
        """Test value at minimum (edge case)."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(8.0, (8.0, 12.0))
            assert result is False

    def test_value_at_max(self, app):
        """Test value at maximum (edge case)."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(12.0, (8.0, 12.0))
            assert result is False

    def test_none_value(self, app):
        """Test None value."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(None, (8.0, 12.0))
            assert result is False

    def test_none_spec(self, app):
        """Test None specification."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(10.0, None)
            assert result is False

    def test_invalid_value_string(self, app):
        """Test invalid value (string)."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec("abc", (8.0, 12.0))
            assert result is False

    def test_none_min_value(self, app):
        """Test None minimum in spec."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(10.0, (None, 12.0))
            assert result is False

    def test_none_max_value(self, app):
        """Test None maximum in spec."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(10.0, (8.0, None))
            assert result is False


class TestParseNumeric:
    """Tests for parse_numeric function."""

    def test_valid_float(self, app):
        """Test valid float."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric(5.5)
            assert result == 5.5

    def test_valid_int(self, app):
        """Test valid integer."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric(5)
            assert result == 5.0

    def test_valid_string(self, app):
        """Test valid string number."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric("5.5")
            assert result == 5.5

    def test_string_with_comma(self, app):
        """Test string with comma separator."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric("1,234.56")
            assert result == 1234.56

    def test_none_returns_none(self, app):
        """Test None returns None."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric(None)
            assert result is None

    def test_invalid_string(self, app):
        """Test invalid string returns None."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric("abc")
            assert result is None

    def test_string_with_spaces(self, app):
        """Test string with spaces."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric("  5.5  ")
            assert result == 5.5


class TestEvalQcStatus:
    """Tests for eval_qc_status function."""

    def test_ok_status(self, app):
        """Test OK status when within limits."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("Mad", 0.1, 1.0)
            assert result == "ok"

    def test_warn_status(self, app):
        """Test warn status."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("UNKNOWN_CODE", 0.1, 3.5)  # > 2% but < 5%
            assert result == "warn"

    def test_fail_status(self, app):
        """Test fail status."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("UNKNOWN_CODE", 0.5, 6.0)  # > 5%
            assert result == "fail"

    def test_none_diff_pct(self, app):
        """Test None diff_pct for unknown code."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("UNKNOWN_CODE", 0.1, None)
            assert result == "ok"

    def test_with_known_param(self, app):
        """Test with known parameter code."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            # Test a known param - behavior depends on COMPOSITE_QC_LIMITS
            result = eval_qc_status("Mad", 0.01, 0.5)
            assert result in ["ok", "warn", "fail"]

    def test_abs_mode_fail(self, app):
        """Test absolute mode fail."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            # Need to mock COMPOSITE_QC_LIMITS with abs mode
            with patch('app.utils.qc.COMPOSITE_QC_LIMITS', {'TEST': {'mode': 'abs', 'warn': 1.0, 'fail': 2.0}}):
                result = eval_qc_status("TEST", 3.0, 10.0)
                assert result == "fail"

    def test_abs_mode_warn(self, app):
        """Test absolute mode warn."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            with patch('app.utils.qc.COMPOSITE_QC_LIMITS', {'TEST': {'mode': 'abs', 'warn': 1.0, 'fail': 2.0}}):
                result = eval_qc_status("TEST", 1.5, 5.0)
                assert result == "warn"

    def test_abs_mode_ok(self, app):
        """Test absolute mode ok."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            with patch('app.utils.qc.COMPOSITE_QC_LIMITS', {'TEST': {'mode': 'abs', 'warn': 1.0, 'fail': 2.0}}):
                result = eval_qc_status("TEST", 0.5, 2.0)
                assert result == "ok"

    def test_abs_mode_none_diff(self, app):
        """Test absolute mode with None diff."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            with patch('app.utils.qc.COMPOSITE_QC_LIMITS', {'TEST': {'mode': 'abs', 'warn': 1.0, 'fail': 2.0}}):
                result = eval_qc_status("TEST", None, 5.0)
                assert result == "ok"


class TestSplitStreamKey:
    """Tests for split_stream_key function."""

    def test_two_hour_day_sample(self, app, db):
        """Test 2-hour day sample."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = "TT D1"
            sample.name = None
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, index = split_stream_key(sample)
            assert prefix == "TT"
            assert stream_type == "two_hour"
            assert index == 1

    def test_two_hour_night_sample(self, app, db):
        """Test 2-hour night sample."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = "TT N6"
            sample.name = None
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, index = split_stream_key(sample)
            assert stream_type == "two_hour"
            assert index == 6

    def test_composite_ncom(self, app, db):
        """Test composite sample (Ncom)."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = "TT Ncom"
            sample.name = None
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, index = split_stream_key(sample)
            assert stream_type == "composite"
            assert index is None

    def test_composite_comp(self, app, db):
        """Test composite sample (comp)."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = "TT comp"
            sample.name = None
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, index = split_stream_key(sample)
            assert stream_type == "composite"

    def test_unknown_format(self, app, db):
        """Test unknown format."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = "RANDOM"
            sample.name = None
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, index = split_stream_key(sample)
            assert stream_type == "unknown"

    def test_empty_sample_code(self, app, db):
        """Test empty sample_code uses id."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = None
            sample.name = None
            sample.sample_name = None
            sample.id = 123
            prefix, stream_type, index = split_stream_key(sample)
            assert "ID 123" in prefix

    def test_fallback_to_name(self, app, db):
        """Test fallback to name field."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = None
            sample.name = "TT D1"
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, index = split_stream_key(sample)
            assert stream_type == "two_hour"


class TestSulfurMapFor:
    """Tests for sulfur_map_for function."""

    def test_empty_list(self, app, db):
        """Test with empty list."""
        with app.app_context():
            from app.utils.qc import sulfur_map_for
            result = sulfur_map_for([])
            assert result == {}

    def test_none_input(self, app, db):
        """Test with None input."""
        with app.app_context():
            from app.utils.qc import sulfur_map_for
            result = sulfur_map_for(None)
            assert result == {}

    def test_with_sample_ids(self, app, db):
        """Test with sample IDs (may return empty if no data)."""
        with app.app_context():
            from app.utils.qc import sulfur_map_for
            result = sulfur_map_for([1, 2, 3])
            assert isinstance(result, dict)
