# tests/test_qc_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/qc.py
"""

import pytest
from datetime import datetime, date
from unittest.mock import MagicMock


class TestQcToDate:
    """Tests for qc_to_date function."""

    def test_qc_to_date_with_datetime(self, app):
        """Test qc_to_date with datetime object."""
        with app.app_context():
            from app.utils.qc import qc_to_date
            dt = datetime(2024, 12, 25, 10, 30, 0)
            result = qc_to_date(dt)
            assert result == date(2024, 12, 25)

    def test_qc_to_date_with_date(self, app):
        """Test qc_to_date with date object."""
        with app.app_context():
            from app.utils.qc import qc_to_date
            d = date(2024, 12, 25)
            result = qc_to_date(d)
            assert result == date(2024, 12, 25)

    def test_qc_to_date_with_none(self, app):
        """Test qc_to_date with None."""
        with app.app_context():
            from app.utils.qc import qc_to_date
            result = qc_to_date(None)
            assert result is None

    def test_qc_to_date_with_empty_string(self, app):
        """Test qc_to_date with empty string."""
        with app.app_context():
            from app.utils.qc import qc_to_date
            result = qc_to_date('')
            assert result is None or result == ''


class TestQcSplitFamily:
    """Tests for qc_split_family function."""

    def test_split_family_two_hour_sample(self, app):
        """Test qc_split_family with 2-hour sample."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            result = qc_split_family("TT_D1")
            assert result == ("TT_D", "1")

    def test_split_family_composite_sample(self, app):
        """Test qc_split_family with composite sample."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            result = qc_split_family("TT_Dcom")
            assert result == ("TT_D", "com")

    def test_split_family_night_shift(self, app):
        """Test qc_split_family with night shift sample."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            result = qc_split_family("PF_N3")
            assert result == ("PF_N", "3")

    def test_split_family_empty_code(self, app):
        """Test qc_split_family with empty code."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            result = qc_split_family("")
            assert result == ("", None)

    def test_split_family_none(self, app):
        """Test qc_split_family with None."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            result = qc_split_family(None)
            assert result == (None, None)

    def test_split_family_no_match(self, app):
        """Test qc_split_family with no matching pattern."""
        with app.app_context():
            from app.utils.qc import qc_split_family
            result = qc_split_family("SAMPLE001")
            assert result == ("SAMPLE001", None)


class TestQcIsComposite:
    """Tests for qc_is_composite function."""

    def test_is_composite_with_com_type(self, app):
        """Test qc_is_composite with COM sample type."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            mock_sample = MagicMock()
            mock_sample.sample_type = "COM"
            result = qc_is_composite(mock_sample, None)
            assert result is True

    def test_is_composite_with_composite_type(self, app):
        """Test qc_is_composite with composite sample type."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            mock_sample = MagicMock()
            mock_sample.sample_type = "composite"
            result = qc_is_composite(mock_sample, None)
            assert result is True

    def test_is_composite_with_com_slot(self, app):
        """Test qc_is_composite with com slot."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            mock_sample = MagicMock()
            mock_sample.sample_type = "2H"
            result = qc_is_composite(mock_sample, "Dcom")
            assert result is True

    def test_is_not_composite(self, app):
        """Test qc_is_composite with non-composite sample."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            mock_sample = MagicMock()
            mock_sample.sample_type = "2H"
            result = qc_is_composite(mock_sample, "1")
            assert result is False

    def test_is_composite_none_type(self, app):
        """Test qc_is_composite with None sample type."""
        with app.app_context():
            from app.utils.qc import qc_is_composite
            mock_sample = MagicMock()
            mock_sample.sample_type = None
            result = qc_is_composite(mock_sample, None)
            assert result is False


class TestQcCheckSpec:
    """Tests for qc_check_spec function."""

    def test_check_spec_within_limits(self, app):
        """Test qc_check_spec with value within limits."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(10.0, (8.0, 12.0))
            assert result is False

    def test_check_spec_above_max(self, app):
        """Test qc_check_spec with value above max."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(15.0, (8.0, 12.0))
            assert result is True

    def test_check_spec_below_min(self, app):
        """Test qc_check_spec with value below min."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(5.0, (8.0, 12.0))
            assert result is True

    def test_check_spec_none_value(self, app):
        """Test qc_check_spec with None value."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(None, (8.0, 12.0))
            assert result is False

    def test_check_spec_none_spec(self, app):
        """Test qc_check_spec with None spec."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(10.0, None)
            assert result is False

    def test_check_spec_invalid_string(self, app):
        """Test qc_check_spec with invalid string value."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec("invalid", (8.0, 12.0))
            assert result is False

    def test_check_spec_only_min_limit(self, app):
        """Test qc_check_spec with only min limit."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(5.0, (8.0, None))
            assert result is True

    def test_check_spec_only_max_limit(self, app):
        """Test qc_check_spec with only max limit."""
        with app.app_context():
            from app.utils.qc import qc_check_spec
            result = qc_check_spec(15.0, (None, 12.0))
            assert result is True


class TestParseNumeric:
    """Tests for parse_numeric function."""

    def test_parse_numeric_simple(self, app):
        """Test parse_numeric with simple number."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric("123.45")
            assert result == 123.45

    def test_parse_numeric_with_comma(self, app):
        """Test parse_numeric with comma."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric("1,234.56")
            assert result == 1234.56

    def test_parse_numeric_with_spaces(self, app):
        """Test parse_numeric with spaces."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric("  123.45  ")
            assert result == 123.45

    def test_parse_numeric_none(self, app):
        """Test parse_numeric with None."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric(None)
            assert result is None

    def test_parse_numeric_invalid(self, app):
        """Test parse_numeric with invalid string."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric("abc")
            assert result is None

    def test_parse_numeric_integer(self, app):
        """Test parse_numeric with integer."""
        with app.app_context():
            from app.utils.qc import parse_numeric
            result = parse_numeric(123)
            assert result == 123.0


class TestEvalQcStatus:
    """Tests for eval_qc_status function."""

    def test_eval_qc_status_ok(self, app):
        """Test eval_qc_status returns ok."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("Unknown_Param", 0.5, 1.0)
            assert result == "ok"

    def test_eval_qc_status_warn(self, app):
        """Test eval_qc_status returns warn."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("Unknown_Param", 2.0, 3.5)
            assert result == "warn"

    def test_eval_qc_status_fail(self, app):
        """Test eval_qc_status returns fail."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("Unknown_Param", 5.0, 7.0)
            assert result == "fail"

    def test_eval_qc_status_none_diff_pct(self, app):
        """Test eval_qc_status with None diff_pct."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            result = eval_qc_status("Unknown_Param", None, None)
            assert result == "ok"

    def test_eval_qc_status_known_param(self, app):
        """Test eval_qc_status with known parameter."""
        with app.app_context():
            from app.utils.qc import eval_qc_status
            # Test with Mad if it exists in COMPOSITE_QC_LIMITS
            result = eval_qc_status("Mad", 0.1, 1.0)
            assert result in ["ok", "warn", "fail"]


class TestSplitStreamKey:
    """Tests for split_stream_key function."""

    def test_split_stream_two_hour(self, app):
        """Test split_stream_key with 2-hour sample."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            mock_sample = MagicMock()
            mock_sample.sample_code = "TT D1"
            mock_sample.name = None
            mock_sample.sample_name = None
            mock_sample.id = 1
            result = split_stream_key(mock_sample)
            assert result[1] == "two_hour"
            assert result[2] == 1

    def test_split_stream_composite(self, app):
        """Test split_stream_key with composite sample."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            mock_sample = MagicMock()
            mock_sample.sample_code = "TT Ncom"
            mock_sample.name = None
            mock_sample.sample_name = None
            mock_sample.id = 1
            result = split_stream_key(mock_sample)
            assert result[1] == "composite"
            assert result[2] is None

    def test_split_stream_unknown(self, app):
        """Test split_stream_key with unknown sample."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            mock_sample = MagicMock()
            mock_sample.sample_code = "RANDOM"
            mock_sample.name = None
            mock_sample.sample_name = None
            mock_sample.id = 1
            result = split_stream_key(mock_sample)
            assert result[1] == "unknown"

    def test_split_stream_no_code(self, app):
        """Test split_stream_key with no sample code."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            mock_sample = MagicMock()
            mock_sample.sample_code = None
            mock_sample.name = "Test Name"
            mock_sample.sample_name = None
            mock_sample.id = 1
            result = split_stream_key(mock_sample)
            assert result is not None

    def test_split_stream_ncomp(self, app):
        """Test split_stream_key with ncomp suffix."""
        with app.app_context():
            from app.utils.qc import split_stream_key
            mock_sample = MagicMock()
            mock_sample.sample_code = "TT ncomp"
            mock_sample.name = None
            mock_sample.sample_name = None
            mock_sample.id = 1
            result = split_stream_key(mock_sample)
            assert result[1] == "composite"


class TestSulfurMapFor:
    """Tests for sulfur_map_for function."""

    def test_sulfur_map_empty_ids(self, app, db):
        """Test sulfur_map_for with empty IDs."""
        with app.app_context():
            from app.utils.qc import sulfur_map_for
            result = sulfur_map_for([])
            assert result == {}

    def test_sulfur_map_none_ids(self, app, db):
        """Test sulfur_map_for with None IDs."""
        with app.app_context():
            from app.utils.qc import sulfur_map_for
            result = sulfur_map_for(None)
            assert result == {}

    def test_sulfur_map_no_results(self, app, db):
        """Test sulfur_map_for with no matching results."""
        with app.app_context():
            from app.utils.qc import sulfur_map_for
            result = sulfur_map_for([99999, 99998])
            assert isinstance(result, dict)
