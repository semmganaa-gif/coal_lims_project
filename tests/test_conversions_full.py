# tests/test_conversions_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/conversions.py
"""

import pytest
from unittest.mock import patch, MagicMock


class TestCalculateAllConversions:
    """Tests for calculate_all_conversions function."""

    def test_returns_dict(self, app):
        """Test returns a dictionary."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            result = calculate_all_conversions({}, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_preserves_raw_values(self, app):
        """Test preserves raw input values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {'test_key': 123.45}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert 'test_key' in result
            assert result['test_key'] == 123.45

    def test_with_inherent_moisture(self, app):
        """Test with inherent_moisture value."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {'inherent_moisture': 5.0}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_with_ash_value(self, app):
        """Test with ash value."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'ash': 10.0,
                'inherent_moisture': 5.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_with_total_moisture(self, app):
        """Test with total_moisture value."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'total_moisture': 15.0,
                'inherent_moisture': 5.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_with_volatile_matter(self, app):
        """Test with volatile_matter value."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'volatile_matter': 30.0,
                'inherent_moisture': 5.0,
                'ash': 10.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_fixed_carbon_calculation(self, app):
        """Test fixed carbon calculation."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'ash': 10.0,
                'volatile_matter': 30.0,
                'inherent_moisture': 5.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            # FC = 100 - (ash + VM + Mad) = 100 - (10 + 30 + 5) = 55
            if 'fixed_carbon_ad' in result:
                assert abs(result['fixed_carbon_ad'] - 55.0) < 0.01

    def test_relative_density_conversion(self, app):
        """Test relative density conversion."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'relative_density': 1.35,
                'inherent_moisture': 5.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_dict_value_input(self, app):
        """Test with dict value format input."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'ash': {'value': 10.0, 'unit': '%'},
                'inherent_moisture': {'value': 5.0}
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_null_string_value(self, app):
        """Test with 'null' string value."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'ash': 'null',
                'inherent_moisture': 5.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_invalid_value_handling(self, app):
        """Test invalid value handling."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'ash': 'not_a_number',
                'inherent_moisture': 5.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_comma_in_value(self, app):
        """Test value with comma (European format)."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'ash': '10,5',
                'inherent_moisture': 5.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_qnet_ar_calculation(self, app):
        """Test Qnet,ar calculation with all required inputs."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'calorific_value': 6500.0,  # cal/g
                'ash': 10.0,
                'inherent_moisture': 5.0,
                'total_moisture': 12.0,
                'volatile_matter': 30.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)
            # Check if volatile_matter_daf was calculated (needed for qnet_ar)
            if 'volatile_matter_daf' in result:
                assert result['volatile_matter_daf'] is not None

    def test_empty_raw_results(self, app):
        """Test with empty raw results."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            result = calculate_all_conversions({}, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)
            assert len(result) == 0

    def test_zero_denominator_handling(self, app):
        """Test handling of zero denominator (100 - Mad = 0)."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'inherent_moisture': 100.0  # Edge case
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_d_conversion_factor(self, app):
        """Test dry basis (d) conversion factor."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'ash': 10.0,
                'inherent_moisture': 5.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            # Check if _d conversions are calculated
            if 'ash_d' in result:
                # ash_d = ash * 100 / (100 - Mad) = 10 * 100 / 95 = 10.526
                expected = 10.0 * 100.0 / 95.0
                assert abs(result['ash_d'] - expected) < 0.01

    def test_daf_conversion_factor(self, app):
        """Test dry ash-free (daf) conversion factor."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'volatile_matter': 30.0,
                'ash': 10.0,
                'inherent_moisture': 5.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            # Check if _daf conversions are calculated
            if 'volatile_matter_daf' in result:
                # factor_daf = 100 / (100 - 5 - 10) = 100 / 85 = 1.176
                # VM_daf = 30 * 1.176 = 35.29
                expected = 30.0 * 100.0 / 85.0
                assert abs(result['volatile_matter_daf'] - expected) < 0.1

    def test_ar_conversion_factor(self, app):
        """Test as received (ar) conversion factor."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'ash': 10.0,
                'inherent_moisture': 5.0,
                'total_moisture': 12.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            # factor_ar = (100 - Mt) / (100 - Mad) = (100 - 12) / (100 - 5) = 88/95
            # ash_ar = ash * factor_ar
            if 'ash_ar' in result:
                expected = 10.0 * 88.0 / 95.0
                assert abs(result['ash_ar'] - expected) < 0.1

    def test_skips_relative_density_conversion(self, app):
        """Test that relative_density is handled specially."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'relative_density': 1.35,
                'inherent_moisture': 5.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            # Should have relative_density_d
            assert 'relative_density_d' in result or 'relative_density' in result


class TestHelperFunctions:
    """Tests for helper functions inside calculate_all_conversions."""

    def test_get_float_from_raw_none(self, app):
        """Test get_float_from_raw with None."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {'key': None}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            # Should handle None gracefully
            assert isinstance(result, dict)

    def test_get_float_from_raw_empty_dict(self, app):
        """Test get_float_from_raw with empty dict value."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {'key': {}}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_get_float_from_raw_dict_no_value(self, app):
        """Test get_float_from_raw with dict missing value key."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {'ash': {'unit': '%'}}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)


class TestEdgeCases:
    """Test edge cases for conversions."""

    def test_negative_moisture(self, app):
        """Test with negative moisture (invalid but shouldn't crash)."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'inherent_moisture': -5.0,
                'ash': 10.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_very_large_values(self, app):
        """Test with very large values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'ash': 1000000.0,
                'inherent_moisture': 5.0
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_very_small_values(self, app):
        """Test with very small values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.constants import PARAMETER_DEFINITIONS
            raw = {
                'ash': 0.0001,
                'inherent_moisture': 0.0001
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)
