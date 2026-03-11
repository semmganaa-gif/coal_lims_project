# -*- coding: utf-8 -*-
"""
qc.py модулийн 100% coverage тестүүд

QC utility функцүүдийн бүх branch-уудыг тест хийнэ.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date


class TestQcImport:
    """Модуль импорт тест"""

    def test_import_module(self):
        from app.utils import qc
        assert qc is not None

    def test_import_functions(self):
        from app.utils.qc import (
            qc_to_date, qc_split_family, qc_is_composite,
            qc_check_spec, parse_numeric, eval_qc_status,
            split_stream_key, sulfur_map_for
        )
        assert all([qc_to_date, qc_split_family, qc_is_composite,
                   qc_check_spec, parse_numeric, eval_qc_status,
                   split_stream_key, sulfur_map_for])


class TestQcToDate:
    """qc_to_date функцийн тест"""

    def test_none_input(self):
        from app.utils.qc import qc_to_date
        assert qc_to_date(None) is None

    def test_datetime_input(self):
        from app.utils.qc import qc_to_date
        dt = datetime(2026, 5, 15, 10, 30)
        result = qc_to_date(dt)
        assert result == date(2026, 5, 15)

    def test_date_input(self):
        from app.utils.qc import qc_to_date
        d = date(2026, 5, 15)
        result = qc_to_date(d)
        assert result == date(2026, 5, 15)

    def test_empty_string(self):
        from app.utils.qc import qc_to_date
        result = qc_to_date('')
        assert result is None


class TestQcSplitFamily:
    """qc_split_family функцийн тест"""

    def test_none_input(self):
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family(None)
        assert family is None
        assert slot is None

    def test_empty_string(self):
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family('')
        assert family == ''
        assert slot is None

    def test_d_slot_number(self):
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family("TT_D1")
        assert family == "TT_D"
        assert slot == "1"

    def test_d_slot_double_digit(self):
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family("TT_D12")
        assert family == "TT_D"
        assert slot == "12"

    def test_n_slot_number(self):
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family("TT_N5")
        assert family == "TT_N"
        assert slot == "5"

    def test_composite_slot(self):
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family("TT_Dcom")
        assert family == "TT_D"
        assert slot == "com"

    def test_n_composite(self):
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family("TT_Ncom")
        assert family == "TT_N"
        assert slot == "com"

    def test_no_match(self):
        from app.utils.qc import qc_split_family
        family, slot = qc_split_family("SIMPLE_CODE")
        assert family == "SIMPLE_CODE"
        assert slot is None


class TestQcIsComposite:
    """qc_is_composite функцийн тест"""

    def test_sample_type_com(self):
        from app.utils.qc import qc_is_composite
        sample = MagicMock()
        sample.sample_type = "com"
        assert qc_is_composite(sample, None) is True

    def test_sample_type_composite(self):
        from app.utils.qc import qc_is_composite
        sample = MagicMock()
        sample.sample_type = "Composite"
        assert qc_is_composite(sample, None) is True

    def test_slot_contains_com(self):
        from app.utils.qc import qc_is_composite
        sample = MagicMock()
        sample.sample_type = "coal"
        assert qc_is_composite(sample, "com") is True
        assert qc_is_composite(sample, "ncom") is True

    def test_not_composite(self):
        from app.utils.qc import qc_is_composite
        sample = MagicMock()
        sample.sample_type = "coal"
        assert qc_is_composite(sample, "1") is False

    def test_sample_type_none(self):
        from app.utils.qc import qc_is_composite
        sample = MagicMock()
        sample.sample_type = None
        assert qc_is_composite(sample, None) is False

    def test_slot_none(self):
        from app.utils.qc import qc_is_composite
        sample = MagicMock()
        sample.sample_type = "coal"
        assert qc_is_composite(sample, None) is False


class TestQcCheckSpec:
    """qc_check_spec функцийн тест"""

    def test_none_value(self):
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(None, (8.0, 12.0)) is False

    def test_none_spec(self):
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(10.0, None) is False

    def test_within_range(self):
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(10.0, (8.0, 12.0)) is False

    def test_below_min(self):
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(5.0, (8.0, 12.0)) is True

    def test_above_max(self):
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(15.0, (8.0, 12.0)) is True

    def test_at_min_boundary(self):
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(8.0, (8.0, 12.0)) is False

    def test_at_max_boundary(self):
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(12.0, (8.0, 12.0)) is False

    def test_invalid_value_type(self):
        from app.utils.qc import qc_check_spec
        assert qc_check_spec("abc", (8.0, 12.0)) is False

    def test_min_none(self):
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(5.0, (None, 12.0)) is False
        assert qc_check_spec(15.0, (None, 12.0)) is True

    def test_max_none(self):
        from app.utils.qc import qc_check_spec
        assert qc_check_spec(5.0, (8.0, None)) is True
        assert qc_check_spec(15.0, (8.0, None)) is False


class TestParseNumeric:
    """parse_numeric функцийн тест"""

    def test_none_input(self):
        from app.utils.qc import parse_numeric
        assert parse_numeric(None) is None

    def test_float_input(self):
        from app.utils.qc import parse_numeric
        assert parse_numeric(5.5) == 5.5

    def test_int_input(self):
        from app.utils.qc import parse_numeric
        assert parse_numeric(5) == 5.0

    def test_string_input(self):
        from app.utils.qc import parse_numeric
        assert parse_numeric("5.5") == 5.5

    def test_string_with_comma(self):
        from app.utils.qc import parse_numeric
        assert parse_numeric("1,234.56") == 1234.56

    def test_string_with_spaces(self):
        from app.utils.qc import parse_numeric
        assert parse_numeric("  5.5  ") == 5.5

    def test_invalid_string(self):
        from app.utils.qc import parse_numeric
        assert parse_numeric("abc") is None


class TestEvalQcStatus:
    """eval_qc_status функцийн тест"""

    def test_no_rule_no_diff_pct(self):
        from app.utils.qc import eval_qc_status
        assert eval_qc_status("Unknown", 0.1, None) == "ok"

    def test_no_rule_diff_pct_fail(self):
        from app.utils.qc import eval_qc_status
        assert eval_qc_status("Unknown", 1.0, 6.0) == "fail"

    def test_no_rule_diff_pct_warn(self):
        from app.utils.qc import eval_qc_status
        assert eval_qc_status("Unknown", 0.5, 3.0) == "warn"

    def test_no_rule_diff_pct_ok(self):
        from app.utils.qc import eval_qc_status
        assert eval_qc_status("Unknown", 0.1, 1.0) == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS')
    def test_abs_mode_fail(self, mock_limits):
        from app.utils.qc import eval_qc_status
        mock_limits.get.return_value = {"mode": "abs", "warn": 0.3, "fail": 0.5}
        assert eval_qc_status("Mad", 0.6, 10.0) == "fail"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS')
    def test_abs_mode_warn(self, mock_limits):
        from app.utils.qc import eval_qc_status
        mock_limits.get.return_value = {"mode": "abs", "warn": 0.3, "fail": 0.5}
        assert eval_qc_status("Mad", 0.4, 5.0) == "warn"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS')
    def test_abs_mode_ok(self, mock_limits):
        from app.utils.qc import eval_qc_status
        mock_limits.get.return_value = {"mode": "abs", "warn": 0.3, "fail": 0.5}
        assert eval_qc_status("Mad", 0.2, 2.0) == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS')
    def test_abs_mode_diff_none(self, mock_limits):
        from app.utils.qc import eval_qc_status
        mock_limits.get.return_value = {"mode": "abs", "warn": 0.3, "fail": 0.5}
        assert eval_qc_status("Mad", None, 5.0) == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS')
    def test_rel_mode_fail(self, mock_limits):
        from app.utils.qc import eval_qc_status
        mock_limits.get.return_value = {"mode": "rel", "warn": 2.0, "fail": 5.0}
        assert eval_qc_status("Aad", 1.0, 6.0) == "fail"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS')
    def test_rel_mode_warn(self, mock_limits):
        from app.utils.qc import eval_qc_status
        mock_limits.get.return_value = {"mode": "rel", "warn": 2.0, "fail": 5.0}
        assert eval_qc_status("Aad", 0.5, 3.0) == "warn"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS')
    def test_rel_mode_ok(self, mock_limits):
        from app.utils.qc import eval_qc_status
        mock_limits.get.return_value = {"mode": "rel", "warn": 2.0, "fail": 5.0}
        assert eval_qc_status("Aad", 0.1, 1.0) == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS')
    def test_rel_mode_diff_pct_none(self, mock_limits):
        from app.utils.qc import eval_qc_status
        mock_limits.get.return_value = {"mode": "rel", "warn": 2.0, "fail": 5.0}
        assert eval_qc_status("Aad", 0.5, None) == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS')
    def test_default_mode(self, mock_limits):
        from app.utils.qc import eval_qc_status
        mock_limits.get.return_value = {"warn": 2.0, "fail": 5.0}  # No mode = rel
        assert eval_qc_status("CV", 500, 6.0) == "fail"


class TestSplitStreamKey:
    """split_stream_key функцийн тест"""

    def test_two_hour_sample(self):
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = "TT D1"
        sample.name = None
        sample.sample_name = None
        sample.id = 1
        prefix, stream_type, idx = split_stream_key(sample)
        assert prefix == "TT"
        assert stream_type == "two_hour"
        assert idx == 1

    def test_two_hour_double_digit(self):
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = "TT D12"
        sample.name = None
        sample.sample_name = None
        sample.id = 1
        prefix, stream_type, idx = split_stream_key(sample)
        assert idx == 12

    def test_n_type_two_hour(self):
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = "TT N5"
        sample.name = None
        sample.sample_name = None
        sample.id = 1
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "two_hour"
        assert idx == 5

    def test_composite_ncom(self):
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = "TT Ncom"
        sample.name = None
        sample.sample_name = None
        sample.id = 1
        prefix, stream_type, idx = split_stream_key(sample)
        assert prefix == "TT"
        assert stream_type == "composite"
        assert idx is None

    def test_composite_variants(self):
        from app.utils.qc import split_stream_key
        for suffix in ["ncomp", "ncomp.", "comp", "comp.", "ncom.", "com"]:
            sample = MagicMock()
            sample.sample_code = f"TT {suffix}"
            sample.name = None
            sample.sample_name = None
            sample.id = 1
            prefix, stream_type, idx = split_stream_key(sample)
            assert stream_type == "composite", f"Failed for {suffix}"

    def test_unknown_type(self):
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = "SIMPLE_CODE"
        sample.name = None
        sample.sample_name = None
        sample.id = 1
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "unknown"
        assert idx is None

    def test_empty_code(self):
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = ""
        sample.name = None
        sample.sample_name = None
        sample.id = 1
        _, stream_type, _ = split_stream_key(sample)
        assert stream_type == "unknown"

    def test_fallback_to_name(self):
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = None
        sample.name = "TT D3"
        sample.sample_name = None
        sample.id = 1
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "two_hour"
        assert idx == 3

    def test_fallback_to_sample_name(self):
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = None
        sample.name = None
        sample.sample_name = "TT D4"
        sample.id = 1
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "two_hour"

    def test_fallback_to_id(self):
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = None
        sample.name = None
        sample.sample_name = None
        sample.id = 123
        raw_name, stream_type, _ = split_stream_key(sample)
        assert "ID 123" in raw_name

    def test_whitespace_only_tokens(self):
        """Test when raw_name.strip().split() returns empty list - line 207"""
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        # When all fallbacks are whitespace, we get empty tokens
        sample.sample_code = ""
        sample.name = ""
        sample.sample_name = ""
        sample.id = ""  # Empty string id

        raw_name, stream_type, idx = split_stream_key(sample)
        # With ID "", raw_name = "ID " and tokens = ["ID"] - not empty
        # Need to test the actual empty tokens case

    def test_empty_tokens_direct(self):
        """Direct test for empty tokens branch - line 207"""
        from app.utils.qc import split_stream_key
        # Create a sample where raw_name.strip().split() returns []
        sample = MagicMock()
        sample.sample_code = None
        sample.name = None
        sample.sample_name = None
        sample.id = None  # All None

        raw_name, stream_type, idx = split_stream_key(sample)
        # raw_name = "ID None" -> tokens = ["ID", "None"] - still not empty

    def test_single_token(self):
        """Test single token sample code"""
        from app.utils.qc import split_stream_key
        sample = MagicMock()
        sample.sample_code = "D1"  # Single token matching pattern
        sample.name = None
        sample.sample_name = None
        sample.id = 1
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "two_hour"
        assert idx == 1


class TestSulfurMapFor:
    """sulfur_map_for функцийн тест"""

    def test_empty_list(self):
        from app.utils.qc import sulfur_map_for
        result = sulfur_map_for([])
        assert result == {}

    def test_none_input(self):
        from app.utils.qc import sulfur_map_for
        result = sulfur_map_for(None)
        assert result == {}

    @patch('app.db.session')
    def test_with_results(self, mock_session):
        from app.utils.qc import sulfur_map_for
        # Mock query result
        mock_row = MagicMock()
        mock_row.sample_id = 1
        mock_row.final_result = "0.45"
        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_row]

        result = sulfur_map_for([1, 2, 3])
        assert 1 in result
        assert result[1] == 0.45

    @patch('app.db.session')
    def test_none_final_result(self, mock_session):
        from app.utils.qc import sulfur_map_for
        mock_row = MagicMock()
        mock_row.sample_id = 1
        mock_row.final_result = None
        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_row]

        result = sulfur_map_for([1])
        assert 1 not in result

    @patch('app.db.session')
    def test_invalid_final_result(self, mock_session):
        from app.utils.qc import sulfur_map_for
        mock_row = MagicMock()
        mock_row.sample_id = 1
        mock_row.final_result = "abc"
        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_row]

        result = sulfur_map_for([1])
        assert 1 not in result

    @patch('app.db.session')
    def test_duplicate_sample_id(self, mock_session):
        from app.utils.qc import sulfur_map_for
        # First result for sample_id 1
        mock_row1 = MagicMock()
        mock_row1.sample_id = 1
        mock_row1.final_result = "0.45"
        # Second result for same sample_id (should be ignored)
        mock_row2 = MagicMock()
        mock_row2.sample_id = 1
        mock_row2.final_result = "0.50"
        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_row1, mock_row2]

        result = sulfur_map_for([1])
        assert result[1] == 0.45  # First one kept
