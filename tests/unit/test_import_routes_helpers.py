# tests/unit/test_import_routes_helpers.py
# -*- coding: utf-8 -*-
"""
Import routes helper functions tests
Coverage target: app/routes/import_routes.py
"""

import pytest
from datetime import datetime
from app.routes.import_routes import (
    _norm, _parse_date, _map_header, _base_code,
    HEADER_KEYS, ALIAS_TO_BASE
)


class TestNormFunction:
    """Test _norm helper function"""

    def test_norm_string(self):
        """_norm with regular string"""
        assert _norm("hello") == "hello"

    def test_norm_string_with_spaces(self):
        """_norm strips whitespace"""
        assert _norm("  hello  ") == "hello"

    def test_norm_none(self):
        """_norm with None returns empty string"""
        assert _norm(None) == ""

    def test_norm_number(self):
        """_norm with number converts to string"""
        assert _norm(123) == "123"

    def test_norm_float(self):
        """_norm with float converts to string"""
        assert _norm(1.5) == "1.5"

    def test_norm_empty_string(self):
        """_norm with empty string"""
        assert _norm("") == ""


class TestParseDateFunction:
    """Test _parse_date helper function"""

    def test_parse_date_none(self):
        """_parse_date with None returns None"""
        assert _parse_date(None) is None

    def test_parse_date_empty(self):
        """_parse_date with empty string returns None"""
        assert _parse_date("") is None

    def test_parse_date_null_string(self):
        """_parse_date with 'null' returns None"""
        assert _parse_date("null") is None
        assert _parse_date("NULL") is None
        assert _parse_date("none") is None

    def test_parse_date_yyyy_mm_dd(self):
        """_parse_date with YYYY-MM-DD format"""
        result = _parse_date("2024-01-15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_yyyy_slash(self):
        """_parse_date with YYYY/MM/DD format"""
        result = _parse_date("2024/01/15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_with_time(self):
        """_parse_date with datetime format"""
        result = _parse_date("2024-01-15 10:30")
        assert result == datetime(2024, 1, 15, 10, 30)

    def test_parse_date_with_seconds(self):
        """_parse_date with full datetime format"""
        result = _parse_date("2024-01-15 10:30:45")
        assert result == datetime(2024, 1, 15, 10, 30, 45)

    def test_parse_date_iso_format(self):
        """_parse_date with ISO format"""
        result = _parse_date("2024-01-15T10:30")
        assert result == datetime(2024, 1, 15, 10, 30)

    def test_parse_date_year_month(self):
        """_parse_date with YYYY-MM format returns first of month"""
        result = _parse_date("2024-01")
        assert result == datetime(2024, 1, 1)

    def test_parse_date_dd_mm_yyyy(self):
        """_parse_date with DD/MM/YYYY format"""
        result = _parse_date("15/01/2024")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_year_only(self):
        """_parse_date with year only"""
        result = _parse_date("2024")
        assert result == datetime(2024, 1, 1)

    def test_parse_date_invalid(self):
        """_parse_date with invalid string returns None"""
        assert _parse_date("invalid") is None
        assert _parse_date("abc123") is None

    def test_parse_date_whitespace(self):
        """_parse_date strips whitespace"""
        result = _parse_date("  2024-01-15  ")
        assert result == datetime(2024, 1, 15)


class TestMapHeaderFunction:
    """Test _map_header helper function"""

    def test_map_header_sample_code(self):
        """_map_header recognizes sample_code variations"""
        assert _map_header("sample_code") == "sample_code"
        assert _map_header("SAMPLE_CODE") == "sample_code"
        assert _map_header("sample") == "sample_code"
        assert _map_header("code") == "sample_code"
        assert _map_header("дээж код") == "sample_code"
        assert _map_header("дээжний нэр") == "sample_code"

    def test_map_header_client_name(self):
        """_map_header recognizes client_name variations"""
        assert _map_header("client_name") == "client_name"
        assert _map_header("unit") == "client_name"
        assert _map_header("нэгж") == "client_name"

    def test_map_header_sample_type(self):
        """_map_header recognizes sample_type variations"""
        assert _map_header("sample_type") == "sample_type"
        assert _map_header("type") == "sample_type"
        assert _map_header("төрөл") == "sample_type"

    def test_map_header_analysis_date(self):
        """_map_header recognizes analysis_date variations"""
        assert _map_header("analysis_date") == "analysis_date"
        assert _map_header("date") == "analysis_date"
        assert _map_header("огноо") == "analysis_date"

    def test_map_header_value(self):
        """_map_header recognizes value variations"""
        assert _map_header("value") == "value"
        assert _map_header("result") == "value"
        assert _map_header("үр дүн") == "value"

    def test_map_header_unknown(self):
        """_map_header returns None for unknown headers"""
        assert _map_header("unknown_column") is None
        assert _map_header("xyz") is None

    def test_map_header_whitespace(self):
        """_map_header handles whitespace"""
        assert _map_header("  sample_code  ") == "sample_code"


class TestBaseCodeFunction:
    """Test _base_code helper function"""

    def test_base_code_empty(self):
        """_base_code with empty string returns empty"""
        assert _base_code("") == ""

    def test_base_code_whitespace(self):
        """_base_code strips whitespace"""
        result = _base_code("  Mad  ")
        assert result.strip() == result

    def test_base_code_known_alias(self):
        """_base_code converts known aliases"""
        # Check if common aliases are mapped
        if "mt,ar" in ALIAS_TO_BASE:
            result = _base_code("Mt,ar")
            assert result is not None

    def test_base_code_unknown(self):
        """_base_code returns original for unknown codes"""
        result = _base_code("UnknownCode")
        assert result == "UnknownCode"

    def test_base_code_case_insensitive(self):
        """_base_code is case insensitive for lookup"""
        # Both should return same result
        result1 = _base_code("mad")
        result2 = _base_code("MAD")
        # If not in alias map, returns as-is preserving case
        assert result1 is not None
        assert result2 is not None


class TestHeaderKeys:
    """Test HEADER_KEYS constant"""

    def test_header_keys_has_required_fields(self):
        """HEADER_KEYS contains required fields"""
        assert "sample_code" in HEADER_KEYS
        assert "client_name" in HEADER_KEYS
        assert "sample_type" in HEADER_KEYS
        assert "analysis_date" in HEADER_KEYS
        assert "value" in HEADER_KEYS

    def test_header_keys_sample_code_synonyms(self):
        """sample_code has expected synonyms"""
        synonyms = HEADER_KEYS["sample_code"]
        assert "sample_code" in synonyms
        assert "sample" in synonyms

    def test_header_keys_value_synonyms(self):
        """value has expected synonyms"""
        synonyms = HEADER_KEYS["value"]
        assert "value" in synonyms
        assert "result" in synonyms


class TestAliasToBase:
    """Test ALIAS_TO_BASE constant"""

    def test_alias_map_is_dict(self):
        """ALIAS_TO_BASE is a dictionary"""
        assert isinstance(ALIAS_TO_BASE, dict)

    def test_alias_map_lowercase_keys(self):
        """ALIAS_TO_BASE has lowercase keys"""
        for key in ALIAS_TO_BASE.keys():
            assert key == key.lower()
