# tests/test_sorting_full.py
# -*- coding: utf-8 -*-
"""Complete tests for app/utils/sorting.py"""

import pytest
from unittest.mock import MagicMock


class TestNaturalSortKey:

    def test_simple_strings(self, app):
        with app.app_context():
            from app.utils.sorting import natural_sort_key
            assert natural_sort_key('abc') == [(1, 'abc', 0)]
            assert natural_sort_key('ABC') == [(1, 'abc', 0)]

    def test_strings_with_numbers(self, app):
        with app.app_context():
            from app.utils.sorting import natural_sort_key
            result = natural_sort_key('N10')
            assert result == [(1, 'n', 0), (0, '', 10)]

    def test_none_value(self, app):
        with app.app_context():
            from app.utils.sorting import natural_sort_key
            assert natural_sort_key(None) == [(1, '', 0)]

    def test_empty_string(self, app):
        with app.app_context():
            from app.utils.sorting import natural_sort_key
            assert natural_sort_key('') == [(1, '', 0)]

    def test_numeric_string(self, app):
        with app.app_context():
            from app.utils.sorting import natural_sort_key
            assert natural_sort_key('123') == [(0, '', 123)]

    def test_natural_order(self, app):
        with app.app_context():
            from app.utils.sorting import natural_sort_key
            items = ['N10', 'N2', 'N1', 'N20']
            sorted_items = sorted(items, key=natural_sort_key)
            assert sorted_items == ['N1', 'N2', 'N10', 'N20']


class TestCustomSampleSortKey:

    def test_none_code(self, app):
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            result = custom_sample_sort_key(None)
            assert result == (99, 0, [(1, '', 0)])

    def test_empty_code(self, app):
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            result = custom_sample_sort_key('')
            assert result == (99, 0, [(1, '', 0)])

    def test_chpp_2h_exact_match(self, app):
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key, CHPP_2H_INDEX
            if CHPP_2H_INDEX:
                first_code = list(CHPP_2H_INDEX.keys())[0]
                result = custom_sample_sort_key(first_code)
                assert result[0] == 0

    def test_other_codes(self, app):
        with app.app_context():
            from app.utils.sorting import custom_sample_sort_key
            result = custom_sample_sort_key('RANDOM_CODE_XYZ')
            assert result[0] == 2


class TestGetClientTypePriority:

    def test_chpp_2_hourly(self, app):
        with app.app_context():
            from app.utils.sorting import get_client_type_priority
            result = get_client_type_priority('CHPP', '2 hourly')
            assert result == 0

    def test_chpp_12_hourly(self, app):
        with app.app_context():
            from app.utils.sorting import get_client_type_priority
            result = get_client_type_priority('CHPP', '12 hourly')
            assert result == 2

    def test_none_client(self, app):
        with app.app_context():
            from app.utils.sorting import get_client_type_priority
            result = get_client_type_priority(None, '2 hourly')
            assert result == 99

    def test_unknown_client(self, app):
        with app.app_context():
            from app.utils.sorting import get_client_type_priority
            result = get_client_type_priority('UNKNOWN', 'test')
            assert result == 50

    def test_lab_cm(self, app):
        with app.app_context():
            from app.utils.sorting import get_client_type_priority
            result = get_client_type_priority('LAB', 'CM')
            assert result == 0


class TestSampleFullSortKey:

    def test_sample_object(self, app):
        with app.app_context():
            from app.utils.sorting import sample_full_sort_key
            sample = MagicMock()
            sample.client_name = 'CHPP'
            sample.sample_type = '2 hourly'
            sample.sample_code = 'PF211_D1'
            result = sample_full_sort_key(sample)
            assert isinstance(result, tuple)
            assert len(result) == 3


class TestSortSamples:

    def test_empty_list(self, app):
        with app.app_context():
            from app.utils.sorting import sort_samples
            result = sort_samples([])
            assert result == []

    def test_sort_by_code(self, app):
        with app.app_context():
            from app.utils.sorting import sort_samples
            samples = [
                MagicMock(sample_code='N10'),
                MagicMock(sample_code='N2'),
                MagicMock(sample_code='N1'),
            ]
            result = sort_samples(samples, by='code')
            codes = [s.sample_code for s in result]
            assert codes == ['N1', 'N2', 'N10']

    def test_sort_by_natural(self, app):
        with app.app_context():
            from app.utils.sorting import sort_samples
            samples = [
                MagicMock(sample_code='N10'),
                MagicMock(sample_code='N2'),
                MagicMock(sample_code='N1'),
            ]
            result = sort_samples(samples, by='natural')
            codes = [s.sample_code for s in result]
            assert codes == ['N1', 'N2', 'N10']

    def test_sort_by_full(self, app):
        with app.app_context():
            from app.utils.sorting import sort_samples
            # Use samples with clearly different priorities
            samples = [
                MagicMock(client_name='CHPP', sample_type='com', sample_code='COM_001'),  # priority 3
                MagicMock(client_name='CHPP', sample_type='2 hourly', sample_code='PF211'),  # priority 0
            ]
            result = sort_samples(samples, by='full')
            # 2 hourly (priority 0) should come before com (priority 3)
            assert result[0].sample_type == '2 hourly'


class TestSortCodes:

    def test_empty_list(self, app):
        with app.app_context():
            from app.utils.sorting import sort_codes
            result = sort_codes([])
            assert result == []

    def test_custom_sort(self, app):
        with app.app_context():
            from app.utils.sorting import sort_codes
            codes = ['N10', 'N2', 'N1']
            result = sort_codes(codes, method='custom')
            assert result == ['N1', 'N2', 'N10']

    def test_natural_sort(self, app):
        with app.app_context():
            from app.utils.sorting import sort_codes
            codes = ['N10', 'N2', 'N1']
            result = sort_codes(codes, method='natural')
            assert result == ['N1', 'N2', 'N10']
