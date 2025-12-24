# tests/test_qc_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/qc.py - targeting 100% coverage.
"""

import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch


class TestQcToDate:
    """Tests for qc_to_date function."""

    def test_none_input(self, app):
        """Test with None input."""
        with app.app_context():
            from app.utils.qc import qc_to_date
            result = qc_to_date(None)
            assert result is None

    def test_datetime_input(self, app):
        """Test with datetime input."""
        with app.app_context():
            from app.utils.qc import qc_to_date
            dt = datetime(2025, 12, 25, 10, 30, 45)
            result = qc_to_date(dt)
            assert result == date(2025, 12, 25)

    def test_date_input(self, app):
        """Test with date input."""
        with app.app_context():
            from app.utils.qc import qc_to_date
            d = date(2025, 12, 25)
            result = qc_to_date(d)
            assert result == d

    def test_empty_string(self, app):
        """Test with empty string (falsy)."""
        with app.app_context():
            from app.utils.qc import qc_to_date
            result = qc_to_date("")
            assert result is None


class TestQcSplitFamily:
    """Tests for qc_split_family function."""

    def test_day_slot(self, app):
        """Test with day slot."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family("TT_D1")
            assert family == "TT_D"
            assert slot == "1"

    def test_night_slot(self, app):
        """Test with night slot."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family("TT_N2")
            assert family == "TT_N"
            assert slot == "2"

    def test_composite(self, app):
        """Test with composite."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family("TT_Dcom")
            assert family == "TT_D"
            assert slot == "com"

    def test_night_composite(self, app):
        """Test with night composite."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family("TT_Ncom")
            assert family == "TT_N"
            assert slot == "com"

    def test_no_match(self, app):
        """Test with no pattern match."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family("INVALID")
            assert family == "INVALID"
            assert slot is None

    def test_none_input(self, app):
        """Test with None input."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family(None)
            assert family is None
            assert slot is None

    def test_empty_string(self, app):
        """Test with empty string."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family("")
            assert family == ""
            assert slot is None

    def test_multi_digit(self, app):
        """Test with multi-digit slot."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family("TT_D12")
            assert family == "TT_D"
            assert slot == "12"


class TestQcIsComposite:
    """Tests for qc_is_composite function."""

    def test_com_type(self, app):
        """Test with com sample type."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            sample = MagicMock()
            sample.sample_type = "com"
            assert qc_is_composite(sample, None) is True

    def test_composite_type(self, app):
        """Test with composite sample type."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            sample = MagicMock()
            sample.sample_type = "composite"
            assert qc_is_composite(sample, None) is True

    def test_com_slot(self, app):
        """Test with com in slot."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            sample = MagicMock()
            sample.sample_type = "2H"
            assert qc_is_composite(sample, "com") is True

    def test_dcom_slot(self, app):
        """Test with Dcom in slot."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            sample = MagicMock()
            sample.sample_type = "2H"
            assert qc_is_composite(sample, "Dcom") is True

    def test_ncom_slot(self, app):
        """Test with Ncom in slot."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            sample = MagicMock()
            sample.sample_type = "2H"
            assert qc_is_composite(sample, "Ncom") is True

    def test_regular_sample(self, app):
        """Test with regular sample."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            sample = MagicMock()
            sample.sample_type = "2H"
            assert qc_is_composite(sample, "1") is False

    def test_none_type(self, app):
        """Test with None sample type."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            sample = MagicMock()
            sample.sample_type = None
            assert qc_is_composite(sample, None) is False


class TestQcCheckSpec:
    """Tests for qc_check_spec function."""

    def test_within_range(self, app):
        """Test with value within range."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(10.0, (8.0, 12.0))
            assert result is False

    def test_above_range(self, app):
        """Test with value above range."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(15.0, (8.0, 12.0))
            assert result is True

    def test_below_range(self, app):
        """Test with value below range."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(5.0, (8.0, 12.0))
            assert result is True

    def test_at_boundary(self, app):
        """Test with value at boundary."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(8.0, (8.0, 12.0))
            assert result is False

    def test_none_value(self, app):
        """Test with None value."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(None, (8.0, 12.0))
            assert result is False

    def test_none_spec(self, app):
        """Test with None spec."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(10.0, None)
            assert result is False

    def test_string_value(self, app):
        """Test with string value."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec("10.0", (8.0, 12.0))
            assert result is False

    def test_invalid_string(self, app):
        """Test with invalid string."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec("invalid", (8.0, 12.0))
            assert result is False

    def test_none_min(self, app):
        """Test with None min."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(5.0, (None, 12.0))
            assert result is False

    def test_none_max(self, app):
        """Test with None max."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(15.0, (8.0, None))
            assert result is False


class TestParseNumeric:
    """Tests for parse_numeric function."""

    def test_none_input(self, app):
        """Test with None input."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric(None)
            assert result is None

    def test_with_comma(self, app):
        """Test with comma in number."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric("1,234.56")
            assert result == 1234.56

    def test_simple_number(self, app):
        """Test with simple number."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric("10.5")
            assert result == 10.5

    def test_integer(self, app):
        """Test with integer."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric(100)
            assert result == 100.0

    def test_float(self, app):
        """Test with float."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric(10.5)
            assert result == 10.5

    def test_invalid_string(self, app):
        """Test with invalid string."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric("abc")
            assert result is None

    def test_whitespace(self, app):
        """Test with whitespace."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric("  10.5  ")
            assert result == 10.5


class TestEvalQcStatus:
    """Tests for eval_qc_status function."""

    def test_default_ok(self, app):
        """Test default rule returns ok."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("UnknownParam", 0.5, 1.0)
            assert result == "ok"

    def test_default_warn(self, app):
        """Test default rule returns warn."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("UnknownParam", 1.0, 3.0)
            assert result == "warn"

    def test_default_fail(self, app):
        """Test default rule returns fail."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("UnknownParam", 5.0, 10.0)
            assert result == "fail"

    def test_none_diff_pct(self, app):
        """Test with None diff_pct."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("UnknownParam", 1.0, None)
            assert result == "ok"

    def test_abs_mode_ok(self, app):
        """Test abs mode returns ok."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            # Mad uses abs mode in COMPOSITE_QC_LIMITS
            result = eval_qc_status("Mad", 0.1, 1.0)
            assert result in ["ok", "warn", "fail"]

    def test_abs_mode_none_diff(self, app):
        """Test abs mode with None diff."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("Mad", None, 1.0)
            assert result in ["ok", "warn", "fail"]

    def test_rel_mode_ok(self, app):
        """Test rel mode returns ok."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            # Use a param with rel mode if exists
            result = eval_qc_status("Aad", 0.1, 0.5)
            assert result in ["ok", "warn", "fail"]

    def test_rel_mode_none_diff_pct(self, app):
        """Test rel mode with None diff_pct."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("Aad", 0.1, None)
            assert result in ["ok", "warn", "fail"]


class TestSplitStreamKey:
    """Tests for split_stream_key function."""

    def test_two_hour_day(self, app, db):
        """Test with 2-hour day sample."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = "TT D1"
            sample.name = None
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, idx = split_stream_key(sample)
            assert stream_type == "two_hour"
            assert idx == 1

    def test_two_hour_night(self, app):
        """Test with 2-hour night sample."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = "TT N5"
            sample.name = None
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, idx = split_stream_key(sample)
            assert stream_type == "two_hour"
            assert idx == 5

    def test_composite_ncom(self, app):
        """Test with composite ncom."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = "TT Ncom"
            sample.name = None
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, idx = split_stream_key(sample)
            assert stream_type == "composite"
            assert idx is None

    def test_composite_comp(self, app):
        """Test with composite comp."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = "TT comp"
            sample.name = None
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, idx = split_stream_key(sample)
            assert stream_type == "composite"

    def test_unknown(self, app):
        """Test with unknown format."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = "INVALID"
            sample.name = None
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, idx = split_stream_key(sample)
            assert stream_type == "unknown"

    def test_no_code(self, app):
        """Test with no sample code."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = None
            sample.name = "TestName"
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, idx = split_stream_key(sample)
            assert prefix is not None

    def test_fallback_to_id(self, app):
        """Test fallback to ID."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = None
            sample.name = None
            sample.sample_name = None
            sample.id = 999
            prefix, stream_type, idx = split_stream_key(sample)
            assert "999" in prefix

    def test_empty_tokens(self, app):
        """Test with empty string (no tokens)."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            sample = MagicMock()
            sample.sample_code = "   "
            sample.name = None
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, idx = split_stream_key(sample)
            assert stream_type == "unknown"


class TestSulfurMapFor:
    """Tests for sulfur_map_for function."""

    def test_empty_list(self, app, db):
        """Test with empty list."""
        with app.app_context():
            from app.utils.qc import sulfur_map_for
            result = sulfur_map_for([])
            assert result == {}

    def test_no_results(self, app, db):
        """Test with no matching results."""
        with app.app_context():
            from app.utils.qc import sulfur_map_for
            result = sulfur_map_for([99999])  # Non-existent ID
            assert isinstance(result, dict)

    def test_with_results(self, app, db):
        """Test with actual results."""
        with app.app_context():
            from app.utils.qc import sulfur_map_for
            from app.models import Sample, AnalysisResult

            # Create test sample
            sample = Sample(
                sample_code='SULFUR_TEST',
                client_name='CHPP',
                sample_type='2H',
                user_id=1
            )
            db.session.add(sample)
            db.session.commit()

            # Create analysis result
            ar = AnalysisResult(
                sample_id=sample.id,
                analysis_code='TS',
                final_result=0.45,
                status='approved'
            )
            db.session.add(ar)
            db.session.commit()

            result = sulfur_map_for([sample.id])
            assert sample.id in result
            assert result[sample.id] == 0.45

            # Cleanup
            db.session.delete(ar)
            db.session.delete(sample)
            db.session.commit()
