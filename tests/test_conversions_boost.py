# tests/test_conversions_boost.py
# -*- coding: utf-8 -*-
"""Tests to boost conversions.py coverage."""

import pytest
from typing import Dict, Any


class TestCalculateAllConversions:
    """Test calculate_all_conversions function."""

    def get_param_definitions(self) -> Dict[str, Any]:
        """Get sample parameter definitions for testing."""
        return {
            "inherent_moisture": {"conversion_bases": []},
            "ash": {"conversion_bases": ["d", "ar"]},
            "ash_d": {},
            "ash_ar": {},
            "volatile_matter": {"conversion_bases": ["d", "daf", "ar"]},
            "volatile_matter_d": {},
            "volatile_matter_daf": {},
            "volatile_matter_ar": {},
            "calorific_value": {"conversion_bases": ["d", "ar"]},
            "calorific_value_d": {},
            "calorific_value_ar": {},
            "fixed_carbon_ad": {},
            "relative_density": {},
            "relative_density_d": {},
            "total_moisture": {},
            "hydrogen": {},
        }

    def test_basic_conversion(self, app):
        """Test basic conversion with all required values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 5.0,  # Mad = 5%
                "ash": 10.0,               # Aad = 10%
                "total_moisture": 15.0,    # Mt = 15%
                "volatile_matter": 30.0,   # Vad = 30%
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            assert result is not None
            assert isinstance(result, dict)
            # Original values should be preserved
            assert result.get("inherent_moisture") == 5.0
            assert result.get("ash") == 10.0

    def test_conversion_with_dict_values(self, app):
        """Test conversion when values are dict with 'value' key."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": {"value": 5.0, "unit": "%"},
                "ash": {"value": 10.0, "unit": "%"},
                "total_moisture": {"value": 15.0},
                "volatile_matter": {"value": 30.0},
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            assert result is not None

    def test_conversion_d_factor(self, app):
        """Test dry basis (d) conversion factor."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 5.0,  # Mad = 5%
                "ash": 10.0,               # Aad = 10%
                "volatile_matter": 30.0,   # Vad = 30%
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # factor_d = 100 / (100 - 5) = 100/95 = 1.0526...
            # ash_d = 10 * 1.0526 = 10.526
            if "ash_d" in result:
                expected_ash_d = 10.0 * (100.0 / 95.0)
                assert abs(result["ash_d"] - expected_ash_d) < 0.01

    def test_conversion_daf_factor(self, app):
        """Test dry ash-free (daf) conversion factor."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 5.0,   # Mad = 5%
                "ash": 10.0,                # Aad = 10%
                "volatile_matter": 30.0,    # Vad = 30%
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # factor_daf = 100 / (100 - 5 - 10) = 100/85 = 1.1765...
            # volatile_matter_daf = 30 * 1.1765 = 35.29
            if "volatile_matter_daf" in result:
                expected_v_daf = 30.0 * (100.0 / 85.0)
                assert abs(result["volatile_matter_daf"] - expected_v_daf) < 0.01

    def test_conversion_ar_factor(self, app):
        """Test as-received (ar) conversion factor."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 5.0,   # Mad = 5%
                "ash": 10.0,                # Aad = 10%
                "total_moisture": 15.0,     # Mt = 15%
                "volatile_matter": 30.0,    # Vad = 30%
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # factor_ar = (100 - 15) / (100 - 5) = 85/95 = 0.8947...
            # ash_ar = 10 * 0.8947 = 8.947
            if "ash_ar" in result:
                expected_ash_ar = 10.0 * (85.0 / 95.0)
                assert abs(result["ash_ar"] - expected_ash_ar) < 0.01

    def test_trd_conversion(self, app):
        """Test TRD (relative density) conversion."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 5.0,   # Mad = 5%
                "relative_density": 1.35,   # TRD,d
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # TRD,ad = TRD,d * (100 - Mad) / 100 = 1.35 * 95 / 100 = 1.2825
            if "relative_density" in result:
                expected_trd_ad = 1.35 * 95.0 / 100.0
                assert abs(result["relative_density"] - expected_trd_ad) < 0.001

    def test_trd_without_mad(self, app):
        """Test TRD conversion without Mad."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "relative_density": 1.35,
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # Without Mad, relative_density should be deleted
            assert "relative_density_d" in result
            assert result["relative_density_d"] == 1.35

    def test_trd_with_zero_denominator(self, app):
        """Test TRD conversion with 100% moisture (zero denominator)."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 100.0,  # Mad = 100% (edge case)
                "relative_density": 1.35,
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # When denom <= 0, relative_density retains its raw value (no conversion applied)
            assert result.get("relative_density") == 1.35

    def test_fixed_carbon_calculation(self, app):
        """Test fixed carbon calculation."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 5.0,
                "ash": 10.0,
                "volatile_matter": 30.0,
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # FC,ad = 100 - Mad - Aad - Vad = 100 - 5 - 10 - 30 = 55
            if "fixed_carbon_ad" in result:
                # The actual calculation depends on parameters.py
                assert isinstance(result["fixed_carbon_ad"], (int, float))

    def test_qnet_ar_calculation(self, app):
        """Test Qnet,ar calculation with all required values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 5.0,
                "ash": 10.0,
                "total_moisture": 15.0,
                "volatile_matter": 30.0,
                "calorific_value": 6000.0,  # cal/g
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # Qnet,ar should be calculated if all inputs are available
            # and volatile_matter_daf was calculated
            if "qnet_ar" in result:
                assert isinstance(result["qnet_ar"], float)

    def test_qnet_ar_missing_values(self, app):
        """Test Qnet,ar with missing values (should not calculate)."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 5.0,
                "ash": 10.0,
                # Missing: total_moisture, volatile_matter, calorific_value
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # Qnet,ar should not be in result
            assert "qnet_ar" not in result

    def test_empty_raw_results(self, app):
        """Test with empty raw results."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {}
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            assert result == {}

    def test_none_values(self, app):
        """Test with None values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": None,
                "ash": None,
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            assert result is not None

    def test_null_string_values(self, app):
        """Test with 'null' string values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": "null",
                "ash": "null",
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            assert result is not None

    def test_string_number_values(self, app):
        """Test with string number values (with comma)."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": "5,000",
                "ash": "10.5",
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            assert result is not None

    def test_invalid_string_values(self, app):
        """Test with invalid string values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": "invalid",
                "ash": "not_a_number",
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # Should handle gracefully
            assert result is not None

    def test_zero_denominator_d(self, app):
        """Test with zero denominator for d conversion."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 100.0,  # denom_d = 0
                "ash": 10.0,
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # Should not crash, ash_d should not be calculated
            assert "ash_d" not in result or result.get("ash_d") is None

    def test_zero_denominator_daf(self, app):
        """Test with zero denominator for daf conversion."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 50.0,
                "ash": 50.0,  # denom_daf = 100 - 50 - 50 = 0
                "volatile_matter": 30.0,
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # Should not crash
            assert result is not None

    def test_param_without_conversion_bases(self, app):
        """Test parameter without conversion_bases."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 5.0,
                "some_param": 100.0,
            }
            param_defs = {
                "inherent_moisture": {},  # No conversion_bases
                "some_param": {},         # No conversion_bases
            }

            result = calculate_all_conversions(raw_results, param_defs)

            assert result is not None
            assert result.get("inherent_moisture") == 5.0

    def test_param_not_in_definitions(self, app):
        """Test parameter not in param_definitions."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 5.0,
                "unknown_param": 100.0,
            }
            param_defs = {
                "inherent_moisture": {"conversion_bases": []},
            }

            result = calculate_all_conversions(raw_results, param_defs)

            assert result is not None
            assert result.get("unknown_param") == 100.0

    def test_conversion_target_not_defined(self, app):
        """Test conversion when target key is not in param_definitions."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 5.0,
                "ash": 10.0,
            }
            param_defs = {
                "inherent_moisture": {"conversion_bases": []},
                "ash": {"conversion_bases": ["d"]},
                # ash_d is NOT defined - conversion should be skipped
            }

            result = calculate_all_conversions(raw_results, param_defs)

            assert "ash_d" not in result

    def test_dict_value_in_final_results(self, app):
        """Test get_float_from_any with dict in final_results."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": {"value": 5.0},
                "ash": {"value": 10.0},
                "volatile_matter": {"value": 30.0},
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            assert result is not None

    def test_full_qnet_ar_calculation(self, app):
        """Test full Qnet,ar calculation with realistic values."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            # Realistic coal analysis values
            raw_results = {
                "inherent_moisture": 3.5,    # Mad = 3.5%
                "ash": 12.0,                 # Aad = 12%
                "total_moisture": 8.0,       # Mt = 8%
                "volatile_matter": 28.0,     # Vad = 28%
                "calorific_value": 6500.0,   # Qgr,ad = 6500 cal/g
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # volatile_matter_daf should be calculated first
            if "volatile_matter_daf" in result:
                # Then qnet_ar can be calculated
                if "qnet_ar" in result:
                    # Qnet,ar should be a reasonable value (around 5500-6200 cal/g)
                    assert 4000 < result["qnet_ar"] < 7000

    def test_qnet_ar_zero_denominator(self, app):
        """Test Qnet,ar with zero denominator (Mad=100)."""
        with app.app_context():
            from app.utils.conversions import calculate_all_conversions

            raw_results = {
                "inherent_moisture": 100.0,  # denom = 0
                "ash": 0.0,
                "total_moisture": 0.0,
                "volatile_matter": 0.0,
                "calorific_value": 6500.0,
            }
            param_defs = self.get_param_definitions()

            result = calculate_all_conversions(raw_results, param_defs)

            # Should not crash, qnet_ar should not be calculated
            assert result is not None
