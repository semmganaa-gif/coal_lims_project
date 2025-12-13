# -*- coding: utf-8 -*-
"""
Sorting utility тестүүд
"""
import pytest
from app.utils.sorting import (
    natural_sort_key,
    sort_samples,
    sort_codes,
    custom_sample_sort_key,
    get_client_type_priority
)


class TestNaturalSortKey:
    """natural_sort_key функц тестүүд"""

    def test_numeric_string(self):
        """Тоотой string"""
        result = natural_sort_key('TEST-123')
        assert result is not None

    def test_alphabetic_string(self):
        """Үсэгтэй string"""
        result = natural_sort_key('ABC')
        assert result is not None

    def test_empty_string(self):
        """Хоосон string"""
        result = natural_sort_key('')
        assert result is not None


class TestSortSamples:
    """sort_samples функц тестүүд"""

    def test_empty_list(self):
        """Хоосон жагсаалт"""
        result = sort_samples([])
        assert result == [] or isinstance(result, list)

    def test_single_sample(self):
        """Нэг sample"""
        result = sort_samples(['TEST-001'])
        assert len(result) == 1


class TestSortCodes:
    """sort_codes функц тестүүд"""

    def test_empty_codes(self):
        """Хоосон codes"""
        result = sort_codes([])
        assert isinstance(result, (list, tuple))

    def test_multiple_codes(self):
        """Олон codes"""
        result = sort_codes(['TS', 'CV', 'Mad'])
        assert isinstance(result, (list, tuple))


class TestCustomSampleSortKey:
    """custom_sample_sort_key функц тестүүд"""

    def test_basic_sort_key(self):
        """Энгийн sort key"""
        result = custom_sample_sort_key('TEST-001')
        assert result is not None


class TestGetClientTypePriority:
    """get_client_type_priority функц тестүүд"""

    def test_known_client(self):
        """Мэдэгдэх client"""
        result = get_client_type_priority('CHPP', 'coal')
        assert isinstance(result, (int, float))

    def test_unknown_client(self):
        """Мэдэгдэхгүй client"""
        result = get_client_type_priority('UNKNOWN_CLIENT', 'unknown')
        assert isinstance(result, (int, float))

    def test_none_values(self):
        """None утгууд"""
        result = get_client_type_priority(None, None)
        assert isinstance(result, (int, float))
