# tests/unit/test_sorting_comprehensive.py
# -*- coding: utf-8 -*-
"""
Sorting utility comprehensive tests
"""
import pytest
from app.utils.sorting import (
    natural_sort_key,
    custom_sample_sort_key,
    get_client_type_priority,
    sample_full_sort_key,
    sort_samples,
    sort_codes,
)


class TestNaturalSortKey:
    """natural_sort_key() функцийн тестүүд"""

    def test_none_returns_empty_list(self):
        result = natural_sort_key(None)
        assert result == [(1, "", 0)]

    def test_empty_string_returns_empty_list(self):
        result = natural_sort_key("")
        assert result == [(1, "", 0)]

    def test_whitespace_only_returns_empty_list(self):
        result = natural_sort_key("   ")
        assert result == [(1, "", 0)]

    def test_simple_text(self):
        result = natural_sort_key("abc")
        assert result == [(1, "abc", 0)]

    def test_simple_number(self):
        result = natural_sort_key("123")
        assert result == [(0, "", 123)]

    def test_mixed_text_number(self):
        result = natural_sort_key("abc123")
        assert result == [(1, "abc", 0), (0, "", 123)]

    def test_number_text_number(self):
        result = natural_sort_key("12abc34")
        assert result == [(0, "", 12), (1, "abc", 0), (0, "", 34)]

    def test_case_insensitive(self):
        result = natural_sort_key("ABC")
        assert result == [(1, "abc", 0)]


class TestCustomSampleSortKey:
    """custom_sample_sort_key() функцийн тестүүд"""

    def test_none_returns_default(self):
        result = custom_sample_sort_key(None)
        assert result == (99, 0, [(1, "", 0)])

    def test_empty_string_returns_default(self):
        result = custom_sample_sort_key("")
        assert result == (99, 0, [(1, "", 0)])

    def test_whitespace_returns_default(self):
        result = custom_sample_sort_key("   ")
        assert result == (99, 0, [(1, "", 0)])

    def test_chpp_2h_code(self):
        """CHPP 2H codes should have group 0"""
        result = custom_sample_sort_key("PF211")
        assert result[0] == 0  # Group 0 for 2H

    def test_unknown_code_returns_group_2(self):
        """Unknown codes should have group 2 (others)"""
        result = custom_sample_sort_key("UNKNOWN_CODE")
        assert result[0] == 2


class TestGetClientTypePriority:
    """get_client_type_priority() функцийн тестүүд"""

    def test_none_client_returns_99(self):
        assert get_client_type_priority(None, None) == 99

    def test_empty_client_returns_99(self):
        assert get_client_type_priority("", None) == 99

    def test_unknown_client_returns_50(self):
        """Unknown client returns default priority 50"""
        result = get_client_type_priority("UNKNOWN", "some_type")
        assert result == 50


class MockSample:
    """Mock sample object for testing"""
    def __init__(self, client_name=None, sample_type=None, sample_code=None):
        self.client_name = client_name
        self.sample_type = sample_type
        self.sample_code = sample_code


class TestSampleFullSortKey:
    """sample_full_sort_key() функцийн тестүүд"""

    def test_sample_with_all_attributes(self):
        sample = MockSample("CHPP", "2 hourly", "PF211")
        result = sample_full_sort_key(sample)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_sample_with_no_attributes(self):
        sample = MockSample()
        result = sample_full_sort_key(sample)
        assert isinstance(result, tuple)


class TestSortSamples:
    """sort_samples() функцийн тестүүд"""

    def test_empty_list_returns_empty(self):
        assert sort_samples([]) == []

    def test_none_returns_empty(self):
        assert sort_samples(None) == []

    def test_sort_by_code_default(self):
        samples = [
            MockSample(sample_code="Z"),
            MockSample(sample_code="A"),
        ]
        result = sort_samples(samples)
        assert result[0].sample_code == "A"
        assert result[1].sample_code == "Z"

    def test_sort_by_full(self):
        samples = [
            MockSample("CHPP", "2 hourly", "PF211"),
            MockSample("CHPP", "2 hourly", "PF212"),
        ]
        result = sort_samples(samples, by="full")
        assert len(result) == 2

    def test_sort_by_natural(self):
        samples = [
            MockSample(sample_code="item10"),
            MockSample(sample_code="item2"),
        ]
        result = sort_samples(samples, by="natural")
        assert result[0].sample_code == "item2"
        assert result[1].sample_code == "item10"


class TestSortCodes:
    """sort_codes() функцийн тестүүд"""

    def test_empty_list_returns_empty(self):
        assert sort_codes([]) == []

    def test_none_returns_empty(self):
        assert sort_codes(None) == []

    def test_natural_sort(self):
        codes = ["item10", "item2", "item1"]
        result = sort_codes(codes, method="natural")
        assert result == ["item1", "item2", "item10"]

    def test_custom_sort(self):
        codes = ["Z", "A", "M"]
        result = sort_codes(codes, method="custom")
        assert result[0] == "A"
        assert result[-1] == "Z"

    def test_default_is_custom(self):
        codes = ["B", "A"]
        result = sort_codes(codes)
        assert result == sort_codes(codes, method="custom")
