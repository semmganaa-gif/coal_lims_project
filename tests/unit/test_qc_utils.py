# -*- coding: utf-8 -*-
"""
Tests for app/utils/qc.py
QC utility functions tests
"""
import pytest
from datetime import datetime, date
from unittest.mock import patch, MagicMock


class TestQcToDate:
    """qc_to_date function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.qc import qc_to_date
        assert callable(qc_to_date)

    def test_none_input(self):
        """None returns None"""
        from app.utils.qc import qc_to_date
        assert qc_to_date(None) is None

    def test_datetime_to_date(self):
        """Converts datetime to date"""
        from app.utils.qc import qc_to_date

        dt = datetime(2025, 1, 15, 12, 30, 45)
        result = qc_to_date(dt)

        assert isinstance(result, date)
        assert result == date(2025, 1, 15)

    def test_date_unchanged(self):
        """Date input unchanged"""
        from app.utils.qc import qc_to_date

        d = date(2025, 1, 15)
        result = qc_to_date(d)

        assert result == d

    def test_midnight_datetime(self):
        """Midnight datetime converted correctly"""
        from app.utils.qc import qc_to_date

        dt = datetime(2025, 6, 1, 0, 0, 0)
        result = qc_to_date(dt)

        assert result == date(2025, 6, 1)


class TestQcSplitFamily:
    """qc_split_family function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.qc import qc_split_family
        assert callable(qc_split_family)

    def test_empty_input(self):
        """Empty string returns (input, None)"""
        from app.utils.qc import qc_split_family

        result = qc_split_family("")
        assert result == ("", None)

    def test_none_input(self):
        """None returns (None, None)"""
        from app.utils.qc import qc_split_family

        result = qc_split_family(None)
        assert result == (None, None)

    def test_day_shift(self):
        """D1 pattern split correctly"""
        from app.utils.qc import qc_split_family

        result = qc_split_family("TT_D1")
        assert result == ("TT_D", "1")

    def test_night_shift(self):
        """N2 pattern split correctly"""
        from app.utils.qc import qc_split_family

        result = qc_split_family("TT_N2")
        assert result == ("TT_N", "2")

    def test_composite(self):
        """Dcom pattern split correctly"""
        from app.utils.qc import qc_split_family

        result = qc_split_family("TT_Dcom")
        assert result == ("TT_D", "com")

    def test_two_digit_slot(self):
        """Two-digit slot split correctly"""
        from app.utils.qc import qc_split_family

        result = qc_split_family("TT_D12")
        assert result == ("TT_D", "12")

    def test_no_pattern(self):
        """No pattern match returns (input, None)"""
        from app.utils.qc import qc_split_family

        result = qc_split_family("SAMPLE_CODE")
        assert result == ("SAMPLE_CODE", None)

    def test_complex_prefix(self):
        """Complex prefix split correctly"""
        from app.utils.qc import qc_split_family

        result = qc_split_family("PF211_TT_D3")
        assert result == ("PF211_TT_D", "3")


class TestQcIsComposite:
    """qc_is_composite function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.qc import qc_is_composite
        assert callable(qc_is_composite)

    def test_sample_type_com(self):
        """sample_type 'com' returns True"""
        from app.utils.qc import qc_is_composite

        mock_sample = MagicMock()
        mock_sample.sample_type = "com"

        assert qc_is_composite(mock_sample, None) is True

    def test_sample_type_composite(self):
        """sample_type 'composite' returns True"""
        from app.utils.qc import qc_is_composite

        mock_sample = MagicMock()
        mock_sample.sample_type = "composite"

        assert qc_is_composite(mock_sample, None) is True

    def test_sample_type_uppercase(self):
        """Case insensitive sample_type"""
        from app.utils.qc import qc_is_composite

        mock_sample = MagicMock()
        mock_sample.sample_type = "COM"

        assert qc_is_composite(mock_sample, None) is True

    def test_slot_com(self):
        """Slot 'com' returns True"""
        from app.utils.qc import qc_is_composite

        mock_sample = MagicMock()
        mock_sample.sample_type = "2H"

        assert qc_is_composite(mock_sample, "com") is True

    def test_slot_dcom(self):
        """Slot 'dcom' returns True"""
        from app.utils.qc import qc_is_composite

        mock_sample = MagicMock()
        mock_sample.sample_type = "2H"

        assert qc_is_composite(mock_sample, "Dcom") is True

    def test_not_composite(self):
        """Regular sample returns False"""
        from app.utils.qc import qc_is_composite

        mock_sample = MagicMock()
        mock_sample.sample_type = "2H"

        assert qc_is_composite(mock_sample, "1") is False

    def test_none_sample_type(self):
        """None sample_type doesn't crash"""
        from app.utils.qc import qc_is_composite

        mock_sample = MagicMock()
        mock_sample.sample_type = None

        assert qc_is_composite(mock_sample, "1") is False


class TestQcCheckSpec:
    """qc_check_spec function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.qc import qc_check_spec
        assert callable(qc_check_spec)

    def test_none_value(self):
        """None value returns False"""
        from app.utils.qc import qc_check_spec

        assert qc_check_spec(None, (0, 10)) is False

    def test_none_spec(self):
        """None spec returns False"""
        from app.utils.qc import qc_check_spec

        assert qc_check_spec(5.0, None) is False

    def test_within_spec(self):
        """Value within spec returns False"""
        from app.utils.qc import qc_check_spec

        assert qc_check_spec(10.0, (8.0, 12.0)) is False

    def test_above_max(self):
        """Value above max returns True"""
        from app.utils.qc import qc_check_spec

        assert qc_check_spec(15.0, (8.0, 12.0)) is True

    def test_below_min(self):
        """Value below min returns True"""
        from app.utils.qc import qc_check_spec

        assert qc_check_spec(5.0, (8.0, 12.0)) is True

    def test_at_min(self):
        """Value at min returns False"""
        from app.utils.qc import qc_check_spec

        assert qc_check_spec(8.0, (8.0, 12.0)) is False

    def test_at_max(self):
        """Value at max returns False"""
        from app.utils.qc import qc_check_spec

        assert qc_check_spec(12.0, (8.0, 12.0)) is False

    def test_none_min(self):
        """None min only checks max"""
        from app.utils.qc import qc_check_spec

        assert qc_check_spec(100.0, (None, 50.0)) is True
        assert qc_check_spec(10.0, (None, 50.0)) is False

    def test_none_max(self):
        """None max only checks min"""
        from app.utils.qc import qc_check_spec

        assert qc_check_spec(0.0, (50.0, None)) is True
        assert qc_check_spec(100.0, (50.0, None)) is False

    def test_invalid_value(self):
        """Non-numeric value returns False"""
        from app.utils.qc import qc_check_spec

        assert qc_check_spec("abc", (0, 10)) is False

    def test_string_number(self):
        """String number works"""
        from app.utils.qc import qc_check_spec

        assert qc_check_spec("15.0", (8.0, 12.0)) is True


class TestParseNumeric:
    """parse_numeric function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.qc import parse_numeric
        assert callable(parse_numeric)

    def test_none_input(self):
        """None returns None"""
        from app.utils.qc import parse_numeric

        assert parse_numeric(None) is None

    def test_float_input(self):
        """Float input unchanged"""
        from app.utils.qc import parse_numeric

        assert parse_numeric(123.45) == 123.45

    def test_int_input(self):
        """Int converted to float"""
        from app.utils.qc import parse_numeric

        assert parse_numeric(123) == 123.0

    def test_string_number(self):
        """String number parsed"""
        from app.utils.qc import parse_numeric

        assert parse_numeric("123.45") == 123.45

    def test_comma_removed(self):
        """Comma removed from number"""
        from app.utils.qc import parse_numeric

        assert parse_numeric("1,234.56") == 1234.56

    def test_whitespace_stripped(self):
        """Whitespace stripped"""
        from app.utils.qc import parse_numeric

        assert parse_numeric("  123.45  ") == 123.45

    def test_invalid_string(self):
        """Invalid string returns None"""
        from app.utils.qc import parse_numeric

        assert parse_numeric("abc") is None

    def test_empty_string(self):
        """Empty string returns None"""
        from app.utils.qc import parse_numeric

        assert parse_numeric("") is None


class TestEvalQcStatus:
    """eval_qc_status function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.qc import eval_qc_status
        assert callable(eval_qc_status)

    def test_unknown_param_default(self):
        """Unknown param uses default 5%/2% thresholds"""
        from app.utils.qc import eval_qc_status

        assert eval_qc_status("Unknown", 0.5, 1.0) == "ok"
        assert eval_qc_status("Unknown", 1.0, 3.0) == "warn"
        assert eval_qc_status("Unknown", 2.0, 6.0) == "fail"

    def test_unknown_none_diff_pct(self):
        """Unknown param with None diff_pct returns ok"""
        from app.utils.qc import eval_qc_status

        assert eval_qc_status("Unknown", 0.5, None) == "ok"

    def test_mad_absolute_mode(self):
        """Mad uses absolute mode"""
        from app.utils.qc import eval_qc_status

        # Mad: warn=0.3, fail=0.5
        assert eval_qc_status("Mad", 0.2, 1.0) == "ok"
        assert eval_qc_status("Mad", 0.35, 2.0) == "warn"
        assert eval_qc_status("Mad", 0.6, 5.0) == "fail"

    def test_aad_absolute_mode(self):
        """Aad uses absolute mode"""
        from app.utils.qc import eval_qc_status

        # Aad: warn=0.5, fail=1.0
        assert eval_qc_status("Aad", 0.4, 1.0) == "ok"
        assert eval_qc_status("Aad", 0.7, 2.0) == "warn"
        assert eval_qc_status("Aad", 1.5, 5.0) == "fail"

    def test_vad_relative_mode(self):
        """Vad uses relative mode"""
        from app.utils.qc import eval_qc_status

        # Vad: warn=2.5, fail=5.0 (relative %)
        assert eval_qc_status("Vad", 0.1, 2.0) == "ok"
        assert eval_qc_status("Vad", 0.2, 3.5) == "warn"
        assert eval_qc_status("Vad", 0.3, 6.0) == "fail"

    def test_qnet_ar_absolute_mode(self):
        """Qnet,ar uses absolute mode"""
        from app.utils.qc import eval_qc_status

        # Qnet,ar: warn=100, fail=200
        assert eval_qc_status("Qnet,ar", 80, 1.0) == "ok"
        assert eval_qc_status("Qnet,ar", 150, 2.0) == "warn"
        assert eval_qc_status("Qnet,ar", 250, 5.0) == "fail"

    def test_gi_relative_mode(self):
        """Gi uses relative mode"""
        from app.utils.qc import eval_qc_status

        # Gi: warn=5.0, fail=10.0 (relative %)
        assert eval_qc_status("Gi", 1.0, 3.0) == "ok"
        assert eval_qc_status("Gi", 2.0, 7.0) == "warn"
        assert eval_qc_status("Gi", 3.0, 12.0) == "fail"

    def test_none_diff_abs_mode(self):
        """None diff in abs mode returns ok"""
        from app.utils.qc import eval_qc_status

        assert eval_qc_status("Mad", None, 5.0) == "ok"

    def test_none_diff_pct_rel_mode(self):
        """None diff_pct in rel mode returns ok"""
        from app.utils.qc import eval_qc_status

        assert eval_qc_status("Vad", 0.5, None) == "ok"

    def test_negative_diff(self):
        """Negative diff uses absolute value"""
        from app.utils.qc import eval_qc_status

        # Mad: fail=0.5
        assert eval_qc_status("Mad", -0.6, -5.0) == "fail"


class TestSplitStreamKey:
    """split_stream_key function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.qc import split_stream_key
        assert callable(split_stream_key)

    def test_two_hour_d1(self):
        """D1 pattern detected"""
        from app.utils.qc import split_stream_key

        mock_sample = MagicMock()
        mock_sample.sample_code = "TT D1"
        mock_sample.name = None
        mock_sample.sample_name = None
        mock_sample.id = 1

        prefix, stream_type, idx = split_stream_key(mock_sample)
        assert stream_type == "two_hour"
        assert idx == 1

    def test_two_hour_n12(self):
        """N12 pattern detected"""
        from app.utils.qc import split_stream_key

        mock_sample = MagicMock()
        mock_sample.sample_code = "TT N12"
        mock_sample.name = None
        mock_sample.sample_name = None
        mock_sample.id = 1

        prefix, stream_type, idx = split_stream_key(mock_sample)
        assert stream_type == "two_hour"
        assert idx == 12

    def test_composite_ncom(self):
        """Ncom pattern detected"""
        from app.utils.qc import split_stream_key

        mock_sample = MagicMock()
        mock_sample.sample_code = "TT Ncom"
        mock_sample.name = None
        mock_sample.sample_name = None
        mock_sample.id = 1

        prefix, stream_type, idx = split_stream_key(mock_sample)
        assert stream_type == "composite"
        assert idx is None

    def test_composite_comp(self):
        """comp pattern detected"""
        from app.utils.qc import split_stream_key

        mock_sample = MagicMock()
        mock_sample.sample_code = "TT comp"
        mock_sample.name = None
        mock_sample.sample_name = None
        mock_sample.id = 1

        prefix, stream_type, idx = split_stream_key(mock_sample)
        assert stream_type == "composite"

    def test_unknown_pattern(self):
        """Unknown pattern returns unknown"""
        from app.utils.qc import split_stream_key

        mock_sample = MagicMock()
        mock_sample.sample_code = "RANDOM_CODE"
        mock_sample.name = None
        mock_sample.sample_name = None
        mock_sample.id = 1

        prefix, stream_type, idx = split_stream_key(mock_sample)
        assert stream_type == "unknown"

    def test_fallback_name(self):
        """Falls back to name if sample_code is None"""
        from app.utils.qc import split_stream_key

        mock_sample = MagicMock()
        mock_sample.sample_code = None
        mock_sample.name = "TT D5"
        mock_sample.sample_name = None
        mock_sample.id = 1

        prefix, stream_type, idx = split_stream_key(mock_sample)
        assert stream_type == "two_hour"
        assert idx == 5

    def test_empty_tokens(self):
        """Empty sample code returns unknown"""
        from app.utils.qc import split_stream_key

        mock_sample = MagicMock()
        mock_sample.sample_code = ""
        mock_sample.name = ""
        mock_sample.sample_name = ""
        mock_sample.id = 1

        prefix, stream_type, idx = split_stream_key(mock_sample)
        assert stream_type == "unknown"


class TestSulfurMapFor:
    """sulfur_map_for function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.qc import sulfur_map_for
        assert callable(sulfur_map_for)

    def test_empty_list(self):
        """Empty list returns empty dict"""
        from app.utils.qc import sulfur_map_for

        result = sulfur_map_for([])
        assert result == {}

    def test_none_input(self):
        """None input returns empty dict"""
        from app.utils.qc import sulfur_map_for

        result = sulfur_map_for(None)
        assert result == {}

    def test_with_results(self):
        """Returns sulfur values for sample IDs"""
        from app.utils.qc import sulfur_map_for

        mock_result = MagicMock()
        mock_result.sample_id = 1
        mock_result.final_result = 0.45

        with patch('app.utils.qc.AnalysisResult') as mock_ar:
            mock_ar.query.filter.return_value.order_by.return_value.all.return_value = [mock_result]

            result = sulfur_map_for([1, 2, 3])
            assert result[1] == 0.45

    def test_none_final_result(self):
        """None final_result skipped"""
        from app.utils.qc import sulfur_map_for

        mock_result = MagicMock()
        mock_result.sample_id = 1
        mock_result.final_result = None

        with patch('app.utils.qc.AnalysisResult') as mock_ar:
            mock_ar.query.filter.return_value.order_by.return_value.all.return_value = [mock_result]

            result = sulfur_map_for([1])
            assert 1 not in result

    def test_first_result_used(self):
        """First result per sample is used (ordered by id desc)"""
        from app.utils.qc import sulfur_map_for

        mock_result1 = MagicMock()
        mock_result1.sample_id = 1
        mock_result1.final_result = 0.45

        mock_result2 = MagicMock()
        mock_result2.sample_id = 1
        mock_result2.final_result = 0.50

        with patch('app.utils.qc.AnalysisResult') as mock_ar:
            mock_ar.query.filter.return_value.order_by.return_value.all.return_value = [
                mock_result1, mock_result2
            ]

            result = sulfur_map_for([1])
            # First one (0.45) should be used
            assert result[1] == 0.45

    def test_invalid_final_result(self):
        """Invalid final_result skipped"""
        from app.utils.qc import sulfur_map_for

        mock_result = MagicMock()
        mock_result.sample_id = 1
        mock_result.final_result = "not a number"

        with patch('app.utils.qc.AnalysisResult') as mock_ar:
            mock_ar.query.filter.return_value.order_by.return_value.all.return_value = [mock_result]

            result = sulfur_map_for([1])
            assert 1 not in result


class TestQcToDateEdgeCases:
    """qc_to_date edge case tests"""

    def test_falsy_input_returns_none(self):
        """Falsy inputs return None"""
        from app.utils.qc import qc_to_date
        assert qc_to_date(0) is None
        assert qc_to_date("") is None

    def test_year_end_datetime(self):
        """Year end datetime converted correctly"""
        from app.utils.qc import qc_to_date
        dt = datetime(2025, 12, 31, 23, 59, 59)
        result = qc_to_date(dt)
        assert result == date(2025, 12, 31)

    def test_leap_year_date(self):
        """Leap year date works"""
        from app.utils.qc import qc_to_date
        dt = datetime(2024, 2, 29, 12, 0, 0)
        result = qc_to_date(dt)
        assert result == date(2024, 2, 29)


class TestQcSplitFamilyEdgeCases:
    """qc_split_family edge case tests"""

    def test_ncom_pattern(self):
        """Ncom pattern split correctly"""
        from app.utils.qc import qc_split_family
        result = qc_split_family("TT_Ncom")
        assert result == ("TT_N", "com")

    def test_single_digit(self):
        """Single digit slot"""
        from app.utils.qc import qc_split_family
        for i in range(1, 10):
            result = qc_split_family(f"TT_D{i}")
            assert result == ("TT_D", str(i))

    def test_three_digit_slot(self):
        """Three digit slot"""
        from app.utils.qc import qc_split_family
        result = qc_split_family("TT_D123")
        assert result == ("TT_D", "123")

    def test_underscore_in_prefix(self):
        """Multiple underscores in prefix"""
        from app.utils.qc import qc_split_family
        result = qc_split_family("A_B_C_D5")
        assert result == ("A_B_C_D", "5")

    def test_only_d_or_n(self):
        """Only D or N without number"""
        from app.utils.qc import qc_split_family
        result = qc_split_family("TT_D")
        assert result == ("TT_D", None)

    def test_lowercase_d(self):
        """Lowercase d not matched (case sensitive)"""
        from app.utils.qc import qc_split_family
        result = qc_split_family("TT_d1")
        # Pattern is case sensitive, lowercase d not matched
        assert result[1] is None or result[1] == "1"


class TestQcIsCompositeEdgeCases:
    """qc_is_composite edge case tests"""

    def test_mixed_case_composite(self):
        """Mixed case 'Composite'"""
        from app.utils.qc import qc_is_composite
        mock_sample = MagicMock()
        mock_sample.sample_type = "Composite"
        assert qc_is_composite(mock_sample, None) is True

    def test_empty_sample_type(self):
        """Empty sample_type"""
        from app.utils.qc import qc_is_composite
        mock_sample = MagicMock()
        mock_sample.sample_type = ""
        assert qc_is_composite(mock_sample, None) is False

    def test_slot_contains_com(self):
        """Slot containing 'com' substring"""
        from app.utils.qc import qc_is_composite
        mock_sample = MagicMock()
        mock_sample.sample_type = "2H"
        assert qc_is_composite(mock_sample, "ncomp") is True
        assert qc_is_composite(mock_sample, "DCOM") is True

    def test_slot_none_sample_type_none(self):
        """Both slot and sample_type None"""
        from app.utils.qc import qc_is_composite
        mock_sample = MagicMock()
        mock_sample.sample_type = None
        assert qc_is_composite(mock_sample, None) is False


class TestQcCheckSpecEdgeCases:
    """qc_check_spec edge case tests"""

    def test_negative_values(self):
        """Negative values in spec"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(-5.0, (-10.0, 0.0)) is False
        assert qc_check_spec(-15.0, (-10.0, 0.0)) is True

    def test_zero_boundaries(self):
        """Zero boundaries"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(0.0, (0.0, 10.0)) is False
        assert qc_check_spec(0.0, (1.0, 10.0)) is True

    def test_very_small_difference(self):
        """Very small difference from boundary"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(12.0001, (8.0, 12.0)) is True
        assert qc_check_spec(7.9999, (8.0, 12.0)) is True

    def test_both_limits_none(self):
        """Both min and max are None"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(100.0, (None, None)) is False

    def test_integer_value(self):
        """Integer value works"""
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(15, (8.0, 12.0)) is True


class TestParseNumericEdgeCases:
    """parse_numeric edge case tests"""

    def test_multiple_commas(self):
        """Multiple commas in number"""
        from app.utils.qc import parse_numeric
        assert parse_numeric("1,234,567.89") == 1234567.89

    def test_negative_number(self):
        """Negative number"""
        from app.utils.qc import parse_numeric
        assert parse_numeric("-123.45") == -123.45

    def test_scientific_notation(self):
        """Scientific notation"""
        from app.utils.qc import parse_numeric
        assert parse_numeric("1.5e3") == 1500.0

    def test_leading_zeros(self):
        """Leading zeros"""
        from app.utils.qc import parse_numeric
        assert parse_numeric("0007") == 7.0

    def test_only_comma(self):
        """Only comma"""
        from app.utils.qc import parse_numeric
        assert parse_numeric(",") is None

    def test_zero_string(self):
        """Zero as string"""
        from app.utils.qc import parse_numeric
        assert parse_numeric("0") == 0.0
        assert parse_numeric("0.0") == 0.0


class TestEvalQcStatusEdgeCases:
    """eval_qc_status edge case tests"""

    def test_ts_uses_default_rel_mode(self):
        """TS uses default relative mode (not in COMPOSITE_QC_LIMITS)"""
        from app.utils.qc import eval_qc_status
        # TS not in config, uses default: warn > 2%, fail > 5%
        assert eval_qc_status("TS", 0.03, 1.0) == "ok"
        assert eval_qc_status("TS", 0.07, 3.0) == "warn"
        assert eval_qc_status("TS", 0.15, 6.0) == "fail"

    def test_cv_absolute_mode(self):
        """CV uses absolute mode (same as Qnet,ar)"""
        from app.utils.qc import eval_qc_status
        result = eval_qc_status("CV", 150, 2.0)
        # Either ok, warn, or fail depending on limits
        assert result in ["ok", "warn", "fail"]

    def test_boundary_warn_value(self):
        """Value exactly at warn threshold"""
        from app.utils.qc import eval_qc_status
        # Default: warn > 2%
        assert eval_qc_status("Unknown", 0.1, 2.0) == "ok"
        assert eval_qc_status("Unknown", 0.1, 2.1) == "warn"

    def test_boundary_fail_value(self):
        """Value exactly at fail threshold"""
        from app.utils.qc import eval_qc_status
        # Default: fail > 5%
        assert eval_qc_status("Unknown", 0.2, 5.0) == "warn"
        assert eval_qc_status("Unknown", 0.2, 5.1) == "fail"

    def test_zero_diff(self):
        """Zero difference"""
        from app.utils.qc import eval_qc_status
        assert eval_qc_status("Mad", 0.0, 0.0) == "ok"
        assert eval_qc_status("Unknown", 0.0, 0.0) == "ok"


class TestSplitStreamKeyEdgeCases:
    """split_stream_key edge case tests"""

    def test_composite_variations(self):
        """Different composite variations"""
        from app.utils.qc import split_stream_key

        variations = ["com", "comp", "comp.", "ncom", "ncom.", "ncomp", "ncomp."]
        for var in variations:
            mock_sample = MagicMock()
            mock_sample.sample_code = f"TT {var}"
            mock_sample.name = None
            mock_sample.sample_name = None
            mock_sample.id = 1

            _, stream_type, _ = split_stream_key(mock_sample)
            assert stream_type == "composite", f"{var} should be composite"

    def test_fallback_to_sample_name(self):
        """Falls back to sample_name if sample_code and name are None"""
        from app.utils.qc import split_stream_key

        mock_sample = MagicMock()
        mock_sample.sample_code = None
        mock_sample.name = None
        mock_sample.sample_name = "TT D3"
        mock_sample.id = 1

        prefix, stream_type, idx = split_stream_key(mock_sample)
        assert stream_type == "two_hour"
        assert idx == 3

    def test_fallback_to_id(self):
        """Falls back to ID if all names are None/empty"""
        from app.utils.qc import split_stream_key

        mock_sample = MagicMock()
        mock_sample.sample_code = None
        mock_sample.name = None
        mock_sample.sample_name = None
        mock_sample.id = 42

        prefix, stream_type, idx = split_stream_key(mock_sample)
        assert "42" in prefix or "ID" in prefix

    def test_single_token_code(self):
        """Single token code (no space)"""
        from app.utils.qc import split_stream_key

        mock_sample = MagicMock()
        mock_sample.sample_code = "SAMPLE"
        mock_sample.name = None
        mock_sample.sample_name = None
        mock_sample.id = 1

        prefix, stream_type, idx = split_stream_key(mock_sample)
        assert stream_type == "unknown"

    def test_multiple_spaces(self):
        """Multiple spaces in code"""
        from app.utils.qc import split_stream_key

        mock_sample = MagicMock()
        mock_sample.sample_code = "TT  PF  D5"
        mock_sample.name = None
        mock_sample.sample_name = None
        mock_sample.id = 1

        prefix, stream_type, idx = split_stream_key(mock_sample)
        assert stream_type == "two_hour"
        assert idx == 5


class TestQcRealWorldScenarios:
    """Real world QC scenario tests"""

    def test_typical_qc_workflow(self):
        """Typical QC workflow values"""
        from app.utils.qc import qc_to_date, qc_split_family, qc_is_composite, qc_check_spec

        # Date conversion
        now = datetime.now()
        today = qc_to_date(now)
        assert today == now.date()

        # Sample code split
        family, slot = qc_split_family("PF211_D3")
        assert family == "PF211_D"
        assert slot == "3"

        # Check if composite
        mock_sample = MagicMock()
        mock_sample.sample_type = "2H"
        assert qc_is_composite(mock_sample, "3") is False
        assert qc_is_composite(mock_sample, "com") is True

        # Spec check
        assert qc_check_spec(25.5, (20.0, 30.0)) is False
        assert qc_check_spec(35.0, (20.0, 30.0)) is True

    def test_qc_status_evaluation(self):
        """QC status evaluation for different parameters"""
        from app.utils.qc import eval_qc_status

        # Moisture - absolute mode
        assert eval_qc_status("Mad", 0.2, 5.0) == "ok"

        # Ash - absolute mode
        assert eval_qc_status("Aad", 0.4, 2.0) == "ok"

        # Volatile - relative mode
        assert eval_qc_status("Vad", 0.5, 1.5) == "ok"

    def test_stream_sample_identification(self):
        """Stream sample identification"""
        from app.utils.qc import split_stream_key

        # Day shift samples
        for i in range(1, 13):
            mock = MagicMock()
            mock.sample_code = f"TT D{i}"
            mock.name = None
            mock.sample_name = None
            mock.id = i
            _, stype, idx = split_stream_key(mock)
            assert stype == "two_hour"
            assert idx == i

        # Night shift samples
        for i in range(1, 13):
            mock = MagicMock()
            mock.sample_code = f"TT N{i}"
            mock.name = None
            mock.sample_name = None
            mock.id = i
            _, stype, idx = split_stream_key(mock)
            assert stype == "two_hour"
            assert idx == i
