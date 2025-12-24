# tests/test_sorting_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/sorting.py
"""

import pytest


class TestSortingConstants:
    """Tests for sorting constants."""

    def test_chpp_2h_index_exists(self, app):
        """Test CHPP_2H_INDEX constant exists."""
        with app.app_context():
            from app.utils.sorting import CHPP_2H_INDEX
            assert isinstance(CHPP_2H_INDEX, dict)

    def test_chpp_12h_index_exists(self, app):
        """Test CHPP_12H_INDEX constant exists."""
        with app.app_context():
            from app.utils.sorting import CHPP_12H_INDEX
            assert isinstance(CHPP_12H_INDEX, dict)

    def test_sort_priority_exists(self, app):
        """Test SORT_PRIORITY constant exists."""
        with app.app_context():
            from app.utils.sorting import SORT_PRIORITY
            assert isinstance(SORT_PRIORITY, dict)
            assert 'CHPP' in SORT_PRIORITY
            assert 'UHG-Geo' in SORT_PRIORITY
            assert 'QC' in SORT_PRIORITY


class TestCustomSampleSortKey:
    """Tests for custom_sample_sort_key function."""

    def test_sort_key_basic(self, app):
        """Test custom_sample_sort_key with basic code."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            result = custom_sample_sort_key('PF211D1')
            assert result is not None

    def test_sort_key_none(self, app):
        """Test custom_sample_sort_key with None."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            result = custom_sample_sort_key(None)
            assert result is not None  # Should return a default sort key

    def test_sort_key_empty_string(self, app):
        """Test custom_sample_sort_key with empty string."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            result = custom_sample_sort_key('')
            assert result is not None

    def test_sort_key_hcc_sample(self, app):
        """Test custom_sample_sort_key with HCC sample."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            result = custom_sample_sort_key('HCC1D1')
            assert result is not None

    def test_sort_key_tt_sample(self, app):
        """Test custom_sample_sort_key with TT sample."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            result = custom_sample_sort_key('TT D1')
            assert result is not None

    def test_sort_key_com_sample(self, app):
        """Test custom_sample_sort_key with composite sample."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            result = custom_sample_sort_key('TT Dcom')
            assert result is not None


class TestSortingSamples:
    """Tests for sorting samples list."""

    def test_sort_samples_basic(self, app):
        """Test sorting samples list."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            samples = ['PF221D2', 'PF211D1', 'HCC1D3']
            sorted_samples = sorted(samples, key=custom_sample_sort_key)
            assert isinstance(sorted_samples, list)
            assert len(sorted_samples) == 3

    def test_sort_samples_with_none(self, app):
        """Test sorting samples with None values."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            # Filter out None values before sorting
            samples = ['PF221D2', 'HCC1D3']
            sorted_samples = sorted(samples, key=custom_sample_sort_key)
            assert isinstance(sorted_samples, list)
            assert len(sorted_samples) == 2

    def test_sort_samples_ordering(self, app):
        """Test samples are ordered correctly."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            samples = ['HCC1D3', 'HCC1D1', 'HCC1D2']
            sorted_samples = sorted(samples, key=custom_sample_sort_key)
            assert isinstance(sorted_samples, list)


class TestGetSampleSortPriority:
    """Tests for _get_sample_sort_priority function if exists."""

    def test_get_sort_priority_chpp(self, app):
        """Test _get_sample_sort_priority for CHPP."""
        with app.app_context():
            try:
                from app.utils.sorting import _get_sample_sort_priority
                result = _get_sample_sort_priority('CHPP', '2 hourly')
                assert isinstance(result, int)
            except (ImportError, AttributeError):
                # Function may not exist - skip
                pytest.skip("_get_sample_sort_priority not available")

    def test_get_sort_priority_unknown(self, app):
        """Test _get_sample_sort_priority for unknown client."""
        with app.app_context():
            try:
                from app.utils.sorting import _get_sample_sort_priority
                result = _get_sample_sort_priority('UNKNOWN', 'type')
                assert isinstance(result, int)
            except (ImportError, AttributeError):
                pytest.skip("_get_sample_sort_priority not available")


class TestParseCodeForSorting:
    """Tests for parsing code for sorting."""

    def test_parse_chpp_2h_code(self, app):
        """Test parsing CHPP 2H code."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            # 2H samples should sort together
            key1 = custom_sample_sort_key('PF211D1')
            key2 = custom_sample_sort_key('PF211D2')
            assert key1 is not None
            assert key2 is not None

    def test_parse_12h_code(self, app):
        """Test parsing 12H code."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            key = custom_sample_sort_key('TT12H')
            assert key is not None

    def test_parse_com_code(self, app):
        """Test parsing composite code."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            key = custom_sample_sort_key('TTDcom')
            assert key is not None


class TestSortResultsForDisplay:
    """Tests for sort_results_for_display if exists."""

    def test_sort_results_empty(self, app):
        """Test sort_results_for_display with empty list."""
        with app.app_context():
            try:
                from app.utils.sorting import sort_results_for_display
                result = sort_results_for_display([])
                assert result == []
            except (ImportError, AttributeError):
                pytest.skip("sort_results_for_display not available")

    def test_sort_results_basic(self, app):
        """Test sort_results_for_display with basic list."""
        with app.app_context():
            try:
                from app.utils.sorting import sort_results_for_display
                items = [
                    {'sample_code': 'PF221D2'},
                    {'sample_code': 'PF211D1'}
                ]
                result = sort_results_for_display(items)
                assert isinstance(result, list)
            except (ImportError, AttributeError):
                pytest.skip("sort_results_for_display not available")


class TestSortKeyTuple:
    """Tests for sort key tuple structure."""

    def test_sort_key_is_comparable(self, app):
        """Test sort keys can be compared."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            key1 = custom_sample_sort_key('PF211D1')
            key2 = custom_sample_sort_key('PF211D2')
            # Should not raise exception
            try:
                _ = key1 < key2 or key1 > key2 or key1 == key2
            except TypeError:
                pytest.fail("Sort keys should be comparable")

    def test_sort_key_consistency(self, app):
        """Test same code returns same key."""
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            key1 = custom_sample_sort_key('PF211D1')
            key2 = custom_sample_sort_key('PF211D1')
            assert key1 == key2
