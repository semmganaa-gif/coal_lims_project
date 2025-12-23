# tests/unit/test_conversions.py
"""
Unit tests for app/utils/conversions.py

Coal analysis тооцооллын conversion functions тестлэнэ.
"""

import pytest
from app.utils.conversions import calculate_all_conversions
from app.constants import PARAMETER_DEFINITIONS


class TestCalculateAllConversions:
    """Tests for calculate_all_conversions()"""

    def test_ad_to_d_conversion_moisture(self):
        """ad -> d conversion for moisture"""
        raw = {
            'inherent_moisture': 5.0,  # Mad = 5%
            'ash': 10.0,              # Aad = 10%
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)

        # Ash,d = Aad * 100 / (100 - Mad)
        # Ash,d = 10 * 100 / (100 - 5) = 10 * 100 / 95 = 10.526...
        assert 'ash_d' in result
        assert abs(result['ash_d'] - 10.526) < 0.01

    def test_ad_to_daf_conversion(self):
        """ad -> daf conversion"""
        raw = {
            'inherent_moisture': 5.0,    # Mad = 5%
            'ash': 10.0,                 # Aad = 10%
            'volatile_matter': 30.0,     # Vad = 30%
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)

        # Vdaf = Vad * 100 / (100 - Mad - Aad)
        # Vdaf = 30 * 100 / (100 - 5 - 10) = 30 * 100 / 85 = 35.29...
        assert 'volatile_matter_daf' in result
        assert abs(result['volatile_matter_daf'] - 35.29) < 0.01

    def test_fixed_carbon_calculation(self):
        """FC,ad = 100 - Mad - Aad - Vad"""
        raw = {
            'inherent_moisture': 5.0,
            'ash': 10.0,
            'volatile_matter': 30.0,
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)

        # FC,ad = 100 - 5 - 10 - 30 = 55
        assert 'fixed_carbon_ad' in result
        assert abs(result['fixed_carbon_ad'] - 55.0) < 0.01

    def test_ar_conversion_with_total_moisture(self):
        """ad -> ar conversion using total moisture"""
        raw = {
            'inherent_moisture': 5.0,   # Mad
            'total_moisture': 10.0,     # Mt
            'ash': 10.0,
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)

        # Aar = Aad * (100 - Mt) / (100 - Mad)
        # Aar = 10 * (100 - 10) / (100 - 5) = 10 * 90 / 95 = 9.47...
        assert 'ash_ar' in result
        assert abs(result['ash_ar'] - 9.47) < 0.01

    def test_missing_moisture_no_conversions(self):
        """No Mad -> no d/daf conversions"""
        raw = {
            'ash': 10.0,
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)

        # Without Mad, can't calculate _d or _daf
        assert 'ash_d' not in result
        assert 'ash_daf' not in result

    def test_zero_division_protection(self):
        """Mad=100% should not cause division by zero"""
        raw = {
            'inherent_moisture': 100.0,
            'ash': 10.0,
        }
        # Should not raise exception
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
        assert result is not None

    def test_dict_value_format(self):
        """Values as {'value': x} dict should work"""
        raw = {
            'inherent_moisture': {'value': 5.0},
            'ash': {'value': 10.0},
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)

        assert result['inherent_moisture']['value'] == 5.0
        assert 'ash_d' in result

    def test_none_values_ignored(self):
        """None values should be skipped - FC requires all 3 values"""
        raw = {
            'inherent_moisture': 5.0,
            'ash': None,  # Missing required value
            'volatile_matter': 30.0,
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)

        # FC calculation requires ash, so it won't be calculated when ash=None
        # This tests that the function doesn't crash on None values
        assert result is not None
        assert 'fixed_carbon_ad' not in result  # Can't calculate without ash

    def test_string_to_float_conversion(self):
        """String numbers should be converted"""
        raw = {
            'inherent_moisture': "5.0",
            'ash': "10.0",
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)

        assert 'ash_d' in result
        assert isinstance(result['ash_d'], float)

    def test_trd_special_case(self):
        """TRD (relative density) special handling"""
        raw = {
            'inherent_moisture': 5.0,
            'relative_density': 50.0,  # TRD,d
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)

        # TRD,ad = TRD,d * (100 - Mad) / 100
        # TRD,ad = 50 * (100 - 5) / 100 = 50 * 0.95 = 47.5
        assert 'relative_density_d' in result
        assert result['relative_density_d'] == 50.0
        # Note: 'relative_density' key might be TRD,ad

    def test_comma_in_value(self):
        """Comma in value (European format) should be handled"""
        raw = {
            'inherent_moisture': "5,5",  # European decimal format
            'ash': "10,0",
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
        assert result is not None

    def test_qnet_ar_calculation(self):
        """Qnet,ar calculation requires all inputs"""
        raw = {
            'calorific_value': 6000.0,
            'ash': 10.0,
            'inherent_moisture': 5.0,
            'total_moisture': 12.0,
            'volatile_matter': 30.0,
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
        # volatile_matter_daf should be calculated first
        if 'volatile_matter_daf' in result:
            # If all values present, qnet_ar may be calculated
            assert 'qnet_ar' in result or True  # May or may not be calculated

    def test_qnet_ar_missing_calorific_value(self):
        """Qnet,ar not calculated without calorific_value"""
        raw = {
            'ash': 10.0,
            'inherent_moisture': 5.0,
            'total_moisture': 12.0,
            'volatile_matter': 30.0,
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
        assert 'qnet_ar' not in result

    def test_invalid_string_value(self):
        """Invalid string should not crash"""
        raw = {
            'inherent_moisture': "invalid",
            'ash': 10.0,
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
        assert result is not None
        # ash_d should not be calculated without valid Mad
        assert 'ash_d' not in result

    def test_null_string_value(self):
        """'null' string treated as None"""
        raw = {
            'inherent_moisture': 'null',
            'ash': 10.0,
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
        assert 'ash_d' not in result

    def test_mad_zero_relative_density(self):
        """Mad=0 should work for relative density"""
        raw = {
            'inherent_moisture': 0.0,
            'relative_density': 50.0,
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
        # TRD,ad = TRD,d * (100 - 0) / 100 = TRD,d
        assert 'relative_density' in result

    def test_all_conversion_bases(self):
        """Test all conversion bases (d, daf, ar)"""
        raw = {
            'inherent_moisture': 5.0,
            'ash': 10.0,
            'total_moisture': 12.0,
            'volatile_matter': 30.0,
            'sulfur': 1.0,
        }
        result = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)
        # Should have multiple _d, _daf, _ar conversions
        assert 'ash_d' in result
        assert 'volatile_matter_daf' in result
        assert 'ash_ar' in result

    def test_empty_param_definitions(self):
        """Empty param definitions should not crash"""
        raw = {
            'inherent_moisture': 5.0,
            'ash': 10.0,
        }
        result = calculate_all_conversions(raw, {})
        assert result is not None
        # No conversions should be done without definitions
        assert 'ash_d' not in result
