# tests/unit/test_qc.py
# -*- coding: utf-8 -*-
"""
QC (Quality Control) утилити функцүүдийн тест
"""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch

from app.utils.qc import (
    qc_to_date,
    qc_split_family,
    qc_is_composite,
    qc_check_spec,
    parse_numeric,
    eval_qc_status,
    split_stream_key,
)


class TestQcToDate:
    """qc_to_date() функцийн тест"""

    def test_datetime_to_date(self):
        """datetime объект -> date"""
        dt = datetime(2025, 12, 11, 10, 30)
        result = qc_to_date(dt)
        assert result == date(2025, 12, 11)

    def test_date_unchanged(self):
        """date объект хувиршгүй"""
        d = date(2025, 12, 11)
        result = qc_to_date(d)
        assert result == d

    def test_none_returns_none(self):
        """None -> None"""
        result = qc_to_date(None)
        assert result is None

    def test_false_returns_none(self):
        """False -> None"""
        result = qc_to_date(False)
        assert result is None


class TestQcSplitFamily:
    """qc_split_family() функцийн тест"""

    def test_day_sample(self):
        """Өдрийн дээж: TT_D1 -> (TT_D, 1)"""
        family, slot = qc_split_family("TT_D1")
        assert family == "TT_D"
        assert slot == "1"

    def test_night_sample(self):
        """Шөнийн дээж: TT_N5 -> (TT_N, 5)"""
        family, slot = qc_split_family("TT_N5")
        assert family == "TT_N"
        assert slot == "5"

    def test_composite_day(self):
        """Composite өдрийн: TT_Dcom -> (TT_D, com)"""
        family, slot = qc_split_family("TT_Dcom")
        assert family == "TT_D"
        assert slot == "com"

    def test_composite_night(self):
        """Composite шөнийн: TT_Ncom -> (TT_N, com)"""
        family, slot = qc_split_family("TT_Ncom")
        assert family == "TT_N"
        assert slot == "com"

    def test_double_digit(self):
        """Хоёр оронтой дугаар: TT_D12 -> (TT_D, 12)"""
        family, slot = qc_split_family("TT_D12")
        assert family == "TT_D"
        assert slot == "12"

    def test_no_match(self):
        """Pattern-д таарахгүй"""
        family, slot = qc_split_family("InvalidCode")
        assert family == "InvalidCode"
        assert slot is None

    def test_empty_string(self):
        """Хоосон string"""
        family, slot = qc_split_family("")
        assert family == ""
        assert slot is None

    def test_none_input(self):
        """None утга"""
        family, slot = qc_split_family(None)
        assert family is None
        assert slot is None


class TestQcIsComposite:
    """qc_is_composite() функцийн тест"""

    def test_sample_type_com(self):
        """sample_type == 'com'"""
        sample = Mock(sample_type="com")
        assert qc_is_composite(sample, None) is True

    def test_sample_type_composite(self):
        """sample_type == 'composite'"""
        sample = Mock(sample_type="composite")
        assert qc_is_composite(sample, None) is True

    def test_sample_type_composite_uppercase(self):
        """sample_type == 'Composite' (case insensitive)"""
        sample = Mock(sample_type="Composite")
        assert qc_is_composite(sample, None) is True

    def test_slot_has_com(self):
        """slot == 'com'"""
        sample = Mock(sample_type="2hour")
        assert qc_is_composite(sample, "com") is True

    def test_slot_has_ncom(self):
        """slot == 'Ncom' (case insensitive)"""
        sample = Mock(sample_type="2hour")
        assert qc_is_composite(sample, "Ncom") is True

    def test_not_composite(self):
        """Composite биш"""
        sample = Mock(sample_type="2hour")
        assert qc_is_composite(sample, "1") is False

    def test_sample_type_none(self):
        """sample_type = None"""
        sample = Mock(sample_type=None)
        assert qc_is_composite(sample, "1") is False


class TestQcCheckSpec:
    """qc_check_spec() функцийн тест"""

    def test_within_range(self):
        """Хязгаар дотор - False"""
        assert qc_check_spec(10.0, (8.0, 12.0)) is False

    def test_below_min(self):
        """Min-ээс бага - True"""
        assert qc_check_spec(5.0, (8.0, 12.0)) is True

    def test_above_max(self):
        """Max-аас их - True"""
        assert qc_check_spec(15.0, (8.0, 12.0)) is True

    def test_at_min_boundary(self):
        """Яг min дээр - False"""
        assert qc_check_spec(8.0, (8.0, 12.0)) is False

    def test_at_max_boundary(self):
        """Яг max дээр - False"""
        assert qc_check_spec(12.0, (8.0, 12.0)) is False

    def test_none_value(self):
        """value=None - False"""
        assert qc_check_spec(None, (8.0, 12.0)) is False

    def test_none_spec(self):
        """spec=None - False"""
        assert qc_check_spec(10.0, None) is False

    def test_string_value(self):
        """String утга - хөрвүүлэгдэнэ"""
        assert qc_check_spec("10.0", (8.0, 12.0)) is False

    def test_invalid_string_value(self):
        """Хөрвүүлж болохгүй string - False"""
        assert qc_check_spec("abc", (8.0, 12.0)) is False

    def test_min_only(self):
        """Зөвхөн min хязгаар"""
        assert qc_check_spec(5.0, (8.0, None)) is True
        assert qc_check_spec(10.0, (8.0, None)) is False

    def test_max_only(self):
        """Зөвхөн max хязгаар"""
        assert qc_check_spec(15.0, (None, 12.0)) is True
        assert qc_check_spec(10.0, (None, 12.0)) is False


class TestParseNumeric:
    """parse_numeric() функцийн тест"""

    def test_simple_float(self):
        """Энгийн float string"""
        assert parse_numeric("123.45") == 123.45

    def test_with_comma_thousand(self):
        """Мянгатын таслал"""
        assert parse_numeric("1,234.56") == 1234.56

    def test_integer_string(self):
        """Integer string"""
        assert parse_numeric("100") == 100.0

    def test_with_spaces(self):
        """Хоосон зайтай"""
        assert parse_numeric("  123.45  ") == 123.45

    def test_none_input(self):
        """None -> None"""
        assert parse_numeric(None) is None

    def test_invalid_string(self):
        """Хөрвүүлж болохгүй string"""
        assert parse_numeric("abc") is None

    def test_float_input(self):
        """Float утга шууд"""
        assert parse_numeric(123.45) == 123.45

    def test_int_input(self):
        """Integer утга"""
        assert parse_numeric(100) == 100.0


class TestEvalQcStatus:
    """eval_qc_status() функцийн тест"""

    def test_default_rule_ok(self):
        """Default rule (no config) - <2% = ok"""
        result = eval_qc_status("UnknownParam", 0.5, 1.5)
        assert result == "ok"

    def test_default_rule_warn(self):
        """Default rule - 2-5% = warn"""
        result = eval_qc_status("UnknownParam", 1.0, 3.5)
        assert result == "warn"

    def test_default_rule_fail(self):
        """Default rule - >5% = fail"""
        result = eval_qc_status("UnknownParam", 2.0, 7.0)
        assert result == "fail"

    def test_default_rule_none_pct(self):
        """Default rule - diff_pct=None = ok"""
        result = eval_qc_status("UnknownParam", 1.0, None)
        assert result == "ok"

    def test_diff_pct_negative(self):
        """Сөрөг хувь - abs авна"""
        result = eval_qc_status("UnknownParam", 2.0, -7.0)
        assert result == "fail"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'TestParam': {'mode': 'abs', 'warn': 0.5, 'fail': 1.0}
    })
    def test_abs_mode_ok(self):
        """Absolute mode - ok"""
        result = eval_qc_status("TestParam", 0.3, 10.0)
        assert result == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'TestParam': {'mode': 'abs', 'warn': 0.5, 'fail': 1.0}
    })
    def test_abs_mode_warn(self):
        """Absolute mode - warn"""
        result = eval_qc_status("TestParam", 0.7, 10.0)
        assert result == "warn"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'TestParam': {'mode': 'abs', 'warn': 0.5, 'fail': 1.0}
    })
    def test_abs_mode_fail(self):
        """Absolute mode - fail"""
        result = eval_qc_status("TestParam", 1.5, 10.0)
        assert result == "fail"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'TestParam': {'mode': 'rel', 'warn': 2.0, 'fail': 5.0}
    })
    def test_rel_mode_ok(self):
        """Relative (%) mode - ok"""
        result = eval_qc_status("TestParam", 0.1, 1.5)
        assert result == "ok"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'TestParam': {'mode': 'rel', 'warn': 2.0, 'fail': 5.0}
    })
    def test_rel_mode_warn(self):
        """Relative (%) mode - warn"""
        result = eval_qc_status("TestParam", 0.5, 3.0)
        assert result == "warn"

    @patch('app.utils.qc.COMPOSITE_QC_LIMITS', {
        'TestParam': {'mode': 'rel', 'warn': 2.0, 'fail': 5.0}
    })
    def test_rel_mode_fail(self):
        """Relative (%) mode - fail"""
        result = eval_qc_status("TestParam", 1.0, 6.0)
        assert result == "fail"


class TestSplitStreamKey:
    """split_stream_key() функцийн тест"""

    def test_two_hour_day_sample(self):
        """2-цагийн өдрийн дээж: TT D1"""
        sample = Mock(sample_code="TT D1", name=None, sample_name=None, id=1)
        prefix, stream_type, idx = split_stream_key(sample)
        assert prefix == "TT"
        assert stream_type == "two_hour"
        assert idx == 1

    def test_two_hour_night_sample(self):
        """2-цагийн шөнийн дээж: TT N5"""
        sample = Mock(sample_code="TT N5", name=None, sample_name=None, id=1)
        prefix, stream_type, idx = split_stream_key(sample)
        assert prefix == "TT"
        assert stream_type == "two_hour"
        assert idx == 5

    def test_composite_ncom(self):
        """Composite дээж: TT Ncom"""
        sample = Mock(sample_code="TT Ncom", name=None, sample_name=None, id=1)
        prefix, stream_type, idx = split_stream_key(sample)
        assert prefix == "TT"
        assert stream_type == "composite"
        assert idx is None

    def test_composite_comp(self):
        """Composite дээж: TT comp"""
        sample = Mock(sample_code="TT comp", name=None, sample_name=None, id=1)
        prefix, stream_type, idx = split_stream_key(sample)
        assert prefix == "TT"
        assert stream_type == "composite"
        assert idx is None

    def test_unknown_suffix(self):
        """Тодорхойгүй suffix: TT XYZ"""
        sample = Mock(sample_code="TT XYZ", name=None, sample_name=None, id=1)
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "unknown"
        assert idx is None

    def test_fallback_to_name(self):
        """sample_code байхгүй үед name ашиглах"""
        sample = Mock()
        sample.sample_code = ""
        sample.name = "TT D1"
        sample.sample_name = ""
        sample.id = 1
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "two_hour"
        assert idx == 1

    def test_fallback_to_sample_name(self):
        """name байхгүй үед sample_name ашиглах"""
        sample = Mock()
        sample.sample_code = ""
        sample.name = ""
        sample.sample_name = "TT N3"
        sample.id = 1
        prefix, stream_type, idx = split_stream_key(sample)
        assert stream_type == "two_hour"
        assert idx == 3

    def test_fallback_to_id(self):
        """Бүх нэр байхгүй үед ID ашиглах"""
        sample = Mock()
        sample.sample_code = ""
        sample.name = ""
        sample.sample_name = ""
        sample.id = 123
        prefix, stream_type, idx = split_stream_key(sample)
        assert "ID 123" in prefix
        assert stream_type == "unknown"

    def test_multi_word_prefix(self):
        """Олон үгтэй prefix: TT UHG D1"""
        sample = Mock(sample_code="TT UHG D1", name=None, sample_name=None, id=1)
        prefix, stream_type, idx = split_stream_key(sample)
        assert prefix == "TT UHG"
        assert stream_type == "two_hour"
        assert idx == 1
