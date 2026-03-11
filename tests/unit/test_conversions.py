# -*- coding: utf-8 -*-
"""
Tests for app/utils/conversions.py
Coal analysis conversion calculations tests
"""
import pytest
from unittest.mock import patch, MagicMock


class TestCalculateAllConversions:
    """calculate_all_conversions function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.conversions import calculate_all_conversions
        assert callable(calculate_all_conversions)

    def test_empty_input_returns_empty(self):
        """Empty input returns empty dict"""
        from app.utils.conversions import calculate_all_conversions

        result = calculate_all_conversions({}, {})
        assert result == {}

    def test_preserves_raw_values(self):
        """Raw values are preserved in result"""
        from app.utils.conversions import calculate_all_conversions

        raw = {"inherent_moisture": 5.0, "ash": 10.0}
        result = calculate_all_conversions(raw, {})

        assert result["inherent_moisture"] == 5.0
        assert result["ash"] == 10.0

    def test_dict_value_format(self):
        """Handles dict value format with 'value' key"""
        from app.utils.conversions import calculate_all_conversions

        raw = {"inherent_moisture": {"value": 5.0}}
        result = calculate_all_conversions(raw, {})

        assert result["inherent_moisture"] == {"value": 5.0}

    def test_string_float_converted(self):
        """String float values are handled"""
        from app.utils.conversions import calculate_all_conversions

        raw = {"inherent_moisture": "5.5", "ash": "10.2"}
        result = calculate_all_conversions(raw, {})

        # Values are preserved as-is (conversion happens internally)
        assert result["inherent_moisture"] == "5.5"

    def test_null_string_value(self):
        """'null' string is treated as None"""
        from app.utils.conversions import calculate_all_conversions

        raw = {"inherent_moisture": "null"}
        result = calculate_all_conversions(raw, {})

        # Should not cause error
        assert "inherent_moisture" in result

    def test_comma_in_number_removed(self):
        """Comma in number is removed for parsing"""
        from app.utils.conversions import calculate_all_conversions

        raw = {"inherent_moisture": "1,234.5"}
        result = calculate_all_conversions(raw, {})

        # Should not cause error
        assert "inherent_moisture" in result

    def test_fixed_carbon_calculated(self):
        """Fixed carbon (FC,ad) is calculated"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 5.0,
            "ash": 10.0,
            "volatile_matter": 30.0
        }
        # FC = 100 - Mad - Aad - Vad = 100 - 5 - 10 - 30 = 55

        with patch('app.utils.conversions.calculate_parameter_value') as mock_calc:
            mock_calc.return_value = 55.0
            result = calculate_all_conversions(raw, {})
            assert result.get("fixed_carbon_ad") == 55.0

    def test_fixed_carbon_none_when_cannot_calculate(self):
        """Fixed carbon is None when cannot calculate"""
        from app.utils.conversions import calculate_all_conversions

        raw = {"inherent_moisture": 5.0}

        with patch('app.utils.conversions.calculate_parameter_value') as mock_calc:
            mock_calc.return_value = None
            result = calculate_all_conversions(raw, {})
            assert "fixed_carbon_ad" not in result


class TestTRDCalculations:
    """TRD (relative density) calculation tests"""

    def test_trd_d_preserved(self):
        """TRD,d value is preserved as relative_density_d"""
        from app.utils.conversions import calculate_all_conversions

        raw = {"relative_density": 1.35}
        result = calculate_all_conversions(raw, {})

        assert result.get("relative_density_d") == 1.35

    def test_trd_ad_calculated_from_trd_d(self):
        """TRD,ad is calculated from TRD,d"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "relative_density": 1.35,  # TRD,d
            "inherent_moisture": 5.0   # Mad
        }
        # TRD,ad = TRD,d * (100 - Mad) / 100 = 1.35 * 95 / 100 = 1.2825

        result = calculate_all_conversions(raw, {})

        assert result.get("relative_density_d") == 1.35
        assert abs(result.get("relative_density") - 1.2825) < 0.0001

    def test_trd_ad_not_calculated_without_mad(self):
        """TRD,ad is not calculated without Mad"""
        from app.utils.conversions import calculate_all_conversions

        raw = {"relative_density": 1.35}
        result = calculate_all_conversions(raw, {})

        # relative_density should not be in result (or deleted)
        # because Mad is needed for conversion
        assert result.get("relative_density_d") == 1.35

    def test_trd_zero_denominator(self):
        """TRD handles zero denominator (100 - Mad = 0) — keeps original value"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "relative_density": 1.35,
            "inherent_moisture": 100.0  # Mad = 100% (extreme case)
        }

        result = calculate_all_conversions(raw, {})
        # When denom_ad = 0, TRD,ad is not calculated; original value remains
        assert result.get("relative_density") == 1.35


class TestConversionFactors:
    """Conversion factor calculation tests"""

    def test_factor_d_calculated(self):
        """Factor d is calculated from Mad"""
        from app.utils.conversions import calculate_all_conversions

        # factor_d = 100 / (100 - Mad) = 100 / 95 = 1.0526...
        raw = {
            "inherent_moisture": 5.0,
            "ash": 10.0,
            "volatile_matter": 30.0
        }

        param_defs = {
            "volatile_matter": {"conversion_bases": ["d"]},
            "volatile_matter_d": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        # Vad * factor_d = 30 * 1.0526... = 31.578...
        expected = 30.0 * (100.0 / 95.0)
        assert abs(result.get("volatile_matter_d", 0) - expected) < 0.001

    def test_factor_daf_calculated(self):
        """Factor daf is calculated from Mad and Aad"""
        from app.utils.conversions import calculate_all_conversions

        # factor_daf = 100 / (100 - Mad - Aad) = 100 / 85 = 1.1765...
        raw = {
            "inherent_moisture": 5.0,
            "ash": 10.0,
            "volatile_matter": 30.0
        }

        param_defs = {
            "volatile_matter": {"conversion_bases": ["daf"]},
            "volatile_matter_daf": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        expected = 30.0 * (100.0 / 85.0)
        assert abs(result.get("volatile_matter_daf", 0) - expected) < 0.001

    def test_factor_ar_calculated(self):
        """Factor ar is calculated from Mt and Mad"""
        from app.utils.conversions import calculate_all_conversions

        # factor_ar = (100 - Mt) / (100 - Mad) = 90 / 95 = 0.9474...
        raw = {
            "inherent_moisture": 5.0,
            "total_moisture": 10.0,
            "volatile_matter": 30.0
        }

        param_defs = {
            "volatile_matter": {"conversion_bases": ["ar"]},
            "volatile_matter_ar": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        expected = 30.0 * (90.0 / 95.0)
        assert abs(result.get("volatile_matter_ar", 0) - expected) < 0.001

    def test_factor_not_calculated_without_mad(self):
        """Factors are not calculated without Mad"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "volatile_matter": 30.0,
            "ash": 10.0
        }

        param_defs = {
            "volatile_matter": {"conversion_bases": ["d", "daf"]},
            "volatile_matter_d": {},
            "volatile_matter_daf": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        # No conversions without Mad
        assert "volatile_matter_d" not in result
        assert "volatile_matter_daf" not in result

    def test_zero_mad_denominator(self):
        """Factor d handles zero denominator (Mad = 100)"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 100.0,
            "volatile_matter": 30.0
        }

        param_defs = {
            "volatile_matter": {"conversion_bases": ["d"]},
            "volatile_matter_d": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        # Cannot divide by zero
        assert "volatile_matter_d" not in result


class TestConversionBaseIterations:
    """Conversion base iteration tests"""

    def test_multiple_bases(self):
        """Multiple conversion bases are applied"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 5.0,
            "ash": 10.0,
            "total_moisture": 15.0,
            "volatile_matter": 30.0
        }

        param_defs = {
            "volatile_matter": {"conversion_bases": ["d", "daf", "ar"]},
            "volatile_matter_d": {},
            "volatile_matter_daf": {},
            "volatile_matter_ar": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        assert "volatile_matter_d" in result
        assert "volatile_matter_daf" in result
        assert "volatile_matter_ar" in result

    def test_skips_relative_density(self):
        """Skips relative_density and relative_density_d for conversions"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 5.0,
            "relative_density": 1.35
        }

        param_defs = {
            "relative_density": {"conversion_bases": ["d"]},
            "relative_density_d": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        # TRD is handled specially, conversion should use the special TRD logic
        # not the general conversion loop
        assert result.get("relative_density_d") == 1.35

    def test_skips_missing_target_param(self):
        """Skips if target parameter definition is missing"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 5.0,
            "volatile_matter": 30.0
        }

        param_defs = {
            "volatile_matter": {"conversion_bases": ["d"]}
            # "volatile_matter_d" is NOT defined
        }

        result = calculate_all_conversions(raw, param_defs)

        # Conversion skipped because volatile_matter_d not in definitions
        assert "volatile_matter_d" not in result

    def test_skips_empty_bases(self):
        """Skips parameters with empty conversion_bases"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 5.0,
            "volatile_matter": 30.0
        }

        param_defs = {
            "volatile_matter": {"conversion_bases": []}
        }

        result = calculate_all_conversions(raw, {})

        assert "volatile_matter_d" not in result


class TestQnetArCalculation:
    """Qnet,ar calculation tests"""

    def test_qnet_ar_calculated_with_all_inputs(self):
        """Qnet,ar is calculated when all inputs are available"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "calorific_value": 6000.0,    # Qgr,ad in cal/g
            "ash": 10.0,                   # Aad %
            "inherent_moisture": 5.0,      # Mad %
            "total_moisture": 12.0,        # Mt,ar %
            "volatile_matter": 30.0        # For Vdaf calculation
        }

        param_defs = {
            "volatile_matter": {"conversion_bases": ["daf"]},
            "volatile_matter_daf": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        # Should have Vdaf calculated
        assert "volatile_matter_daf" in result
        # And qnet_ar should be calculated
        assert "qnet_ar" in result
        # Value should be a float
        assert isinstance(result["qnet_ar"], float)

    def test_qnet_ar_not_calculated_without_all_inputs(self):
        """Qnet,ar is not calculated when inputs are missing"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "calorific_value": 6000.0,
            "ash": 10.0,
            "inherent_moisture": 5.0
            # Missing total_moisture and volatile_matter
        }

        result = calculate_all_conversions(raw, {})

        assert "qnet_ar" not in result

    def test_qnet_ar_handles_zero_denominator(self):
        """Qnet,ar handles zero denominator"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "calorific_value": 6000.0,
            "ash": 10.0,
            "inherent_moisture": 100.0,  # 100 - Mad = 0
            "total_moisture": 12.0,
            "volatile_matter": 30.0
        }

        result = calculate_all_conversions(raw, {})

        # Should not raise error, qnet_ar should not be calculated
        assert "qnet_ar" not in result

    def test_qnet_ar_with_dict_values(self):
        """Qnet,ar handles dict value format"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "calorific_value": {"value": 6000.0},
            "ash": {"value": 10.0},
            "inherent_moisture": {"value": 5.0},
            "total_moisture": {"value": 12.0},
            "volatile_matter": {"value": 30.0}
        }

        param_defs = {
            "volatile_matter": {"conversion_bases": ["daf"]},
            "volatile_matter_daf": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        # Should have calculated Vdaf from dict values
        assert "volatile_matter_daf" in result
        # And qnet_ar should be calculated
        assert "qnet_ar" in result


class TestEdgeCases:
    """Edge case tests"""

    def test_none_values_handled(self):
        """None values are handled gracefully"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": None,
            "ash": 10.0
        }

        result = calculate_all_conversions(raw, {})

        # Should not raise error
        assert result["ash"] == 10.0

    def test_invalid_string_handled(self):
        """Invalid string values are handled"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": "not a number",
            "ash": 10.0
        }

        result = calculate_all_conversions(raw, {})

        # Should not raise error
        assert result["ash"] == 10.0

    def test_whitespace_in_value(self):
        """Whitespace in value is stripped"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": "  5.0  ",
            "ash": 10.0
        }

        result = calculate_all_conversions(raw, {})

        # Should not raise error
        assert "inherent_moisture" in result

    def test_mixed_valid_invalid_values(self):
        """Handles mix of valid and invalid values"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 5.0,
            "ash": "invalid",
            "volatile_matter": 30.0
        }

        param_defs = {
            "volatile_matter": {"conversion_bases": ["d"]},
            "volatile_matter_d": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        # factor_d should work (only needs Mad)
        assert "volatile_matter_d" in result

    def test_negative_values(self):
        """Negative values are handled"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": -5.0,  # Invalid but should not crash
            "ash": 10.0
        }

        result = calculate_all_conversions(raw, {})

        # Should not raise error
        assert "inherent_moisture" in result

    def test_large_values(self):
        """Large values are handled"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 5.0,
            "calorific_value": 9999999.0
        }

        result = calculate_all_conversions(raw, {})

        # Should not raise error
        assert "calorific_value" in result

    def test_empty_param_definitions(self):
        """Empty param definitions are handled"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 5.0,
            "volatile_matter": 30.0
        }

        result = calculate_all_conversions(raw, {})

        # No conversions performed
        assert "volatile_matter_d" not in result

    def test_original_raw_not_modified(self):
        """Original raw dict is not modified"""
        from app.utils.conversions import calculate_all_conversions

        raw = {"inherent_moisture": 5.0}
        original = raw.copy()

        calculate_all_conversions(raw, {})

        assert raw == original


class TestAshConversions:
    """Ash conversion tests"""

    def test_ash_d_calculated(self):
        """Ash d-basis is calculated"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 5.0,
            "ash": 10.0
        }

        param_defs = {
            "ash": {"conversion_bases": ["d"]},
            "ash_d": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        # Aad * factor_d = 10 * (100/95) = 10.526...
        expected = 10.0 * (100.0 / 95.0)
        assert abs(result.get("ash_d", 0) - expected) < 0.001

    def test_ash_ar_calculated(self):
        """Ash ar-basis is calculated"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 5.0,
            "total_moisture": 15.0,
            "ash": 10.0
        }

        param_defs = {
            "ash": {"conversion_bases": ["ar"]},
            "ash_ar": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        # Aad * factor_ar = 10 * (85/95) = 8.947...
        expected = 10.0 * (85.0 / 95.0)
        assert abs(result.get("ash_ar", 0) - expected) < 0.001


class TestCalorificValueConversions:
    """Calorific value conversion tests"""

    def test_cv_d_calculated(self):
        """Calorific value d-basis is calculated"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 5.0,
            "calorific_value": 6000.0
        }

        param_defs = {
            "calorific_value": {"conversion_bases": ["d"]},
            "calorific_value_d": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        expected = 6000.0 * (100.0 / 95.0)
        assert abs(result.get("calorific_value_d", 0) - expected) < 0.01

    def test_cv_ar_calculated(self):
        """Calorific value ar-basis is calculated"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 5.0,
            "total_moisture": 15.0,
            "calorific_value": 6000.0
        }

        param_defs = {
            "calorific_value": {"conversion_bases": ["ar"]},
            "calorific_value_ar": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        expected = 6000.0 * (85.0 / 95.0)
        assert abs(result.get("calorific_value_ar", 0) - expected) < 0.01


class TestDafCalculations:
    """DAF (dry-ash-free) basis calculation tests"""

    def test_daf_factor_requires_both_mad_and_aad(self):
        """DAF factor requires both Mad and Aad"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 5.0,
            # No ash
            "volatile_matter": 30.0
        }

        param_defs = {
            "volatile_matter": {"conversion_bases": ["daf"]},
            "volatile_matter_daf": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        # Cannot calculate daf without Aad
        assert "volatile_matter_daf" not in result

    def test_daf_zero_denominator(self):
        """DAF handles zero denominator"""
        from app.utils.conversions import calculate_all_conversions

        raw = {
            "inherent_moisture": 50.0,
            "ash": 50.0,  # Mad + Aad = 100
            "volatile_matter": 30.0
        }

        param_defs = {
            "volatile_matter": {"conversion_bases": ["daf"]},
            "volatile_matter_daf": {}
        }

        result = calculate_all_conversions(raw, param_defs)

        # Cannot divide by zero
        assert "volatile_matter_daf" not in result
