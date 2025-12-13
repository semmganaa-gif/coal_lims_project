# -*- coding: utf-8 -*-
"""
Sorting utils extended тестүүд
"""
import pytest


class TestSortingModule:
    """Sorting module тестүүд"""

    def test_import_module(self):
        """Module import"""
        from app.utils import sorting
        assert sorting is not None


class TestNaturalSortKey:
    """natural_sort_key тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.sorting import natural_sort_key
        assert natural_sort_key is not None

    def test_sort_simple(self):
        """Sort simple strings"""
        from app.utils.sorting import natural_sort_key
        items = ['a10', 'a2', 'a1']
        sorted_items = sorted(items, key=natural_sort_key)
        assert sorted_items[0] == 'a1'

    def test_sort_numbers(self):
        """Sort with numbers"""
        from app.utils.sorting import natural_sort_key
        items = ['item10', 'item2', 'item1', 'item20']
        sorted_items = sorted(items, key=natural_sort_key)
        assert sorted_items == ['item1', 'item2', 'item10', 'item20']


class TestSortSamples:
    """sort_samples тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.sorting import sort_samples
        assert sort_samples is not None

    def test_sort_empty(self):
        """Sort empty list"""
        from app.utils.sorting import sort_samples
        result = sort_samples([])
        assert result == []

    def test_sort_single(self):
        """Sort single item"""
        from app.utils.sorting import sort_samples
        result = sort_samples([{'sample_code': 'A001'}])
        assert len(result) == 1


class TestSortCodes:
    """sort_codes тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.sorting import sort_codes
        assert sort_codes is not None

    def test_sort_codes(self):
        """Sort analysis codes"""
        from app.utils.sorting import sort_codes
        codes = ['Vad', 'TS', 'Mad', 'Aad', 'CV']
        sorted_codes = sort_codes(codes)
        assert len(sorted_codes) == 5

    def test_sort_empty(self):
        """Sort empty list"""
        from app.utils.sorting import sort_codes
        result = sort_codes([])
        assert result == []


class TestSampleFullSortKey:
    """sample_full_sort_key тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.sorting import sample_full_sort_key
        assert sample_full_sort_key is not None


class TestCustomSampleSortKey:
    """custom_sample_sort_key тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.sorting import custom_sample_sort_key
        assert custom_sample_sort_key is not None


class TestGetClientTypePriority:
    """get_client_type_priority тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.sorting import get_client_type_priority
        assert get_client_type_priority is not None

    def test_priority_chpp(self):
        """Priority for CHPP"""
        from app.utils.sorting import get_client_type_priority
        result = get_client_type_priority('CHPP', '12H')
        assert isinstance(result, (int, tuple))
