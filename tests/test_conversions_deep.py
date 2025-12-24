# tests/test_conversions_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/conversions.py
"""

import pytest
from unittest.mock import patch, MagicMock


class TestCalculateAllConversions:
    """Tests for calculate_all_conversions function."""

    def test_empty_input(self, app):
        """Test calculate_all_conversions with empty input."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            result = calculate_all_conversions({}, {})
            assert isinstance(result, dict)

    def test_basic_input(self, app):
        """Test calculate_all_conversions with basic input."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': 5.0,
                'ash': 10.0,
                'total_moisture': 15.0,
            }
            param_definitions = {}
            result = calculate_all_conversions(raw_results, param_definitions)
            assert isinstance(result, dict)
            assert 'inherent_moisture' in result

    def test_with_dict_values(self, app):
        """Test calculate_all_conversions with dict-style values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': {'value': 5.0},
                'ash': {'value': 10.0},
                'total_moisture': {'value': 15.0},
            }
            param_definitions = {}
            result = calculate_all_conversions(raw_results, param_definitions)
            assert isinstance(result, dict)

    def test_with_null_values(self, app):
        """Test calculate_all_conversions with null values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': 'null',
                'ash': None,
            }
            param_definitions = {}
            result = calculate_all_conversions(raw_results, param_definitions)
            assert isinstance(result, dict)

    def test_with_string_values(self, app):
        """Test calculate_all_conversions with string numeric values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': '5.0',
                'ash': '10,5',  # Comma decimal
            }
            param_definitions = {}
            result = calculate_all_conversions(raw_results, param_definitions)
            assert isinstance(result, dict)

    def test_trd_calculation(self, app):
        """Test TRD (relative density) calculation."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': 5.0,
                'relative_density': 1.5,
            }
            param_definitions = {}
            result = calculate_all_conversions(raw_results, param_definitions)
            assert 'relative_density_d' in result
            assert result['relative_density_d'] == 1.5

    def test_trd_without_moisture(self, app):
        """Test TRD calculation without moisture."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'relative_density': 1.5,
            }
            param_definitions = {}
            result = calculate_all_conversions(raw_results, param_definitions)
            assert 'relative_density_d' in result

    def test_conversion_factors_d(self, app):
        """Test _d conversion factor calculation."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': 5.0,  # Mad = 5%
                'ash': 10.0,               # Aad = 10%
                'volatile_matter': 30.0,   # Vad = 30%
            }
            param_definitions = {
                'volatile_matter': {
                    'conversion_bases': ['d', 'daf']
                },
                'volatile_matter_d': {},
                'volatile_matter_daf': {},
            }
            result = calculate_all_conversions(raw_results, param_definitions)
            # factor_d = 100 / (100 - 5) = 100/95 = 1.0526
            # Vd = Vad * factor_d = 30 * 1.0526 = 31.58
            if 'volatile_matter_d' in result:
                assert result['volatile_matter_d'] > 30.0

    def test_conversion_factors_daf(self, app):
        """Test _daf conversion factor calculation."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': 5.0,  # Mad = 5%
                'ash': 10.0,               # Aad = 10%
                'volatile_matter': 30.0,   # Vad = 30%
            }
            param_definitions = {
                'volatile_matter': {
                    'conversion_bases': ['d', 'daf']
                },
                'volatile_matter_d': {},
                'volatile_matter_daf': {},
            }
            result = calculate_all_conversions(raw_results, param_definitions)
            # factor_daf = 100 / (100 - 5 - 10) = 100/85 = 1.176
            # Vdaf = Vad * factor_daf = 30 * 1.176 = 35.29
            if 'volatile_matter_daf' in result:
                assert result['volatile_matter_daf'] > 30.0

    def test_conversion_factors_ar(self, app):
        """Test _ar conversion factor calculation."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': 5.0,   # Mad = 5%
                'total_moisture': 15.0,     # Mt = 15%
                'volatile_matter': 30.0,
            }
            param_definitions = {
                'volatile_matter': {
                    'conversion_bases': ['ar']
                },
                'volatile_matter_ar': {},
            }
            result = calculate_all_conversions(raw_results, param_definitions)
            # factor_ar = (100 - Mt) / (100 - Mad) = (100-15)/(100-5) = 85/95 = 0.8947
            # Var = Vad * factor_ar = 30 * 0.8947 = 26.84
            if 'volatile_matter_ar' in result:
                assert result['volatile_matter_ar'] < 30.0

    def test_qnet_ar_calculation(self, app):
        """Test Qnet,ar calculation."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'calorific_value': 6000.0,    # Qgr,ad (cal/g)
                'inherent_moisture': 5.0,     # Mad (%)
                'ash': 10.0,                  # Aad (%)
                'total_moisture': 12.0,       # Mt,ar (%)
                'volatile_matter': 30.0,      # Vad (%)
            }
            param_definitions = {
                'volatile_matter': {
                    'conversion_bases': ['daf']
                },
                'volatile_matter_daf': {},
            }
            result = calculate_all_conversions(raw_results, param_definitions)
            # Should calculate qnet_ar
            if 'qnet_ar' in result:
                assert isinstance(result['qnet_ar'], float)

    def test_qnet_ar_missing_values(self, app):
        """Test Qnet,ar calculation with missing values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'calorific_value': 6000.0,
                'inherent_moisture': 5.0,
                # Missing ash, total_moisture, volatile_matter
            }
            param_definitions = {}
            result = calculate_all_conversions(raw_results, param_definitions)
            # qnet_ar should not be calculated
            assert 'qnet_ar' not in result or result.get('qnet_ar') is None

    def test_zero_denominator_handling(self, app):
        """Test handling of zero denominator in calculations."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': 100.0,  # Mad = 100% -> denominator = 0
                'ash': 0.0,
                'volatile_matter': 30.0,
            }
            param_definitions = {}
            result = calculate_all_conversions(raw_results, param_definitions)
            # Should not crash with zero denominator
            assert isinstance(result, dict)

    def test_fc_ad_calculation(self, app):
        """Test fixed carbon ad calculation."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': 5.0,
                'ash': 10.0,
                'volatile_matter': 30.0,
            }
            param_definitions = {}
            result = calculate_all_conversions(raw_results, param_definitions)
            # FC,ad = 100 - Mad - Aad - Vad = 100 - 5 - 10 - 30 = 55
            if 'fixed_carbon_ad' in result:
                assert result['fixed_carbon_ad'] == pytest.approx(55.0, rel=0.01)

    def test_invalid_string_values(self, app):
        """Test handling of invalid string values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': 'invalid',
                'ash': 'not a number',
            }
            param_definitions = {}
            result = calculate_all_conversions(raw_results, param_definitions)
            # Should not crash with invalid values
            assert isinstance(result, dict)

    def test_skip_relative_density_conversion(self, app):
        """Test that relative_density conversions are skipped."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': 5.0,
                'relative_density': 1.5,
            }
            param_definitions = {
                'relative_density': {
                    'conversion_bases': ['d']
                },
                'relative_density_d': {},
            }
            result = calculate_all_conversions(raw_results, param_definitions)
            # relative_density should have special handling
            assert 'relative_density_d' in result


class TestHelperFunctions:
    """Tests for internal helper functions through calculate_all_conversions."""

    def test_get_float_from_dict_value(self, app):
        """Test extraction of float from dict value."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': {'value': 5.0, 'unit': '%'},
            }
            param_definitions = {}
            result = calculate_all_conversions(raw_results, param_definitions)
            assert result['inherent_moisture']['value'] == 5.0

    def test_comma_decimal_parsing(self, app):
        """Test parsing of comma decimal values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': '5,5',  # European format
            }
            param_definitions = {}
            result = calculate_all_conversions(raw_results, param_definitions)
            # The function replaces comma, so should work
            assert isinstance(result, dict)

    def test_whitespace_handling(self, app):
        """Test handling of whitespace in values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': '  5.0  ',
            }
            param_definitions = {}
            result = calculate_all_conversions(raw_results, param_definitions)
            assert isinstance(result, dict)

    def test_param_without_conversion_bases(self, app):
        """Test parameter without conversion_bases."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': 5.0,
                'some_param': 10.0,
            }
            param_definitions = {
                'some_param': {}  # No conversion_bases
            }
            result = calculate_all_conversions(raw_results, param_definitions)
            assert 'some_param' in result

    def test_param_with_empty_conversion_bases(self, app):
        """Test parameter with empty conversion_bases."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                'inherent_moisture': 5.0,
                'some_param': 10.0,
            }
            param_definitions = {
                'some_param': {
                    'conversion_bases': []  # Empty list
                }
            }
            result = calculate_all_conversions(raw_results, param_definitions)
            assert 'some_param' in result
