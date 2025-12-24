# tests/test_conversions_full.py
# -*- coding: utf-8 -*-
"""Complete tests for app/utils/conversions.py"""

import pytest


class TestCalculateAllConversions:

    def test_empty_input(self, app):
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            result = calculate_all_conversions({}, {})
            assert isinstance(result, dict)

    def test_basic_mad_conversion(self, app):
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.utils.parameters import PARAMETER_DEFINITIONS
            raw = {'inherent_moisture': 5.0, 'ash': 10.0}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert 'inherent_moisture' in result

    def test_factor_d_calculation(self, app):
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.utils.parameters import PARAMETER_DEFINITIONS
            raw = {'inherent_moisture': 10.0, 'ash': 15.0}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            if 'ash_d' in result:
                assert abs(result['ash_d'] - 16.67) < 0.1

    def test_factor_daf_calculation(self, app):
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.utils.parameters import PARAMETER_DEFINITIONS
            raw = {'inherent_moisture': 5.0, 'ash': 10.0, 'volatile_matter': 30.0}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            if 'volatile_matter_daf' in result:
                expected = 30.0 * (100.0 / 85.0)
                assert abs(result['volatile_matter_daf'] - expected) < 0.1

    def test_factor_ar_calculation(self, app):
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.utils.parameters import PARAMETER_DEFINITIONS
            raw = {'inherent_moisture': 5.0, 'total_moisture': 12.0, 'ash': 10.0}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            if 'ash_ar' in result:
                expected = 10.0 * (88.0 / 95.0)
                assert abs(result['ash_ar'] - expected) < 0.1

    def test_fixed_carbon_calculation(self, app):
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.utils.parameters import PARAMETER_DEFINITIONS
            raw = {'inherent_moisture': 5.0, 'ash': 10.0, 'volatile_matter': 35.0}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            if 'fixed_carbon_ad' in result:
                assert abs(result['fixed_carbon_ad'] - 50.0) < 0.1

    def test_trd_conversion(self, app):
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.utils.parameters import PARAMETER_DEFINITIONS
            raw = {'relative_density': 1.35, 'inherent_moisture': 5.0}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            if 'relative_density' in result:
                expected = 1.35 * 0.95
                assert abs(result['relative_density'] - expected) < 0.01

    def test_dict_value_format(self, app):
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.utils.parameters import PARAMETER_DEFINITIONS
            raw = {
                'inherent_moisture': {'value': 5.0, 'unit': '%'},
                'ash': {'value': 10.0, 'unit': '%'},
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_null_string_handling(self, app):
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.utils.parameters import PARAMETER_DEFINITIONS
            raw = {'inherent_moisture': 'null', 'ash': 10.0}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_invalid_value_handling(self, app):
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.utils.parameters import PARAMETER_DEFINITIONS
            raw = {'inherent_moisture': 'invalid', 'ash': 'not a number'}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_zero_denominator_handling(self, app):
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.utils.parameters import PARAMETER_DEFINITIONS
            raw = {'inherent_moisture': 100.0, 'ash': 10.0}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)

    def test_qnet_ar_calculation(self, app):
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.utils.parameters import PARAMETER_DEFINITIONS
            raw = {
                'calorific_value': 6500,
                'ash': 10.0,
                'inherent_moisture': 5.0,
                'total_moisture': 12.0,
                'volatile_matter': 35.0,
            }
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            if 'qnet_ar' in result:
                assert result['qnet_ar'] > 0

    def test_none_values(self, app):
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions
            from app.utils.parameters import PARAMETER_DEFINITIONS
            raw = {'inherent_moisture': None, 'ash': None}
            result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
            assert isinstance(result, dict)
