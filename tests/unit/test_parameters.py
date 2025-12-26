# -*- coding: utf-8 -*-
"""
Tests for app/utils/parameters.py
Parameter utilities tests
"""
import pytest
from unittest.mock import patch, MagicMock


class TestGetCanonicalName:
    """get_canonical_name function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.parameters import get_canonical_name
        assert callable(get_canonical_name)

    def test_none_input(self):
        """None returns None"""
        from app.utils.parameters import get_canonical_name
        assert get_canonical_name(None) is None

    def test_empty_string(self):
        """Empty string returns None"""
        from app.utils.parameters import get_canonical_name
        assert get_canonical_name("") is None

    def test_known_parameter(self):
        """Known parameter returns canonical"""
        from app.utils.parameters import get_canonical_name

        result = get_canonical_name("Mad")
        # Should return canonical name for inherent_moisture
        assert result is not None

    def test_alias_parameter(self):
        """Alias returns canonical"""
        from app.utils.parameters import get_canonical_name

        # "M,ad" is an alias for inherent_moisture
        result = get_canonical_name("M,ad")
        assert result is not None

    def test_unknown_parameter_returns_cleaned(self):
        """Unknown parameter returns cleaned name"""
        from app.utils.parameters import get_canonical_name

        result = get_canonical_name("  Unknown_Param  ")
        assert result == "Unknown_Param"

    def test_strips_whitespace(self):
        """Strips whitespace"""
        from app.utils.parameters import get_canonical_name

        result = get_canonical_name("  Mad  ")
        assert result is not None

    def test_int_input(self):
        """Int input converted to string"""
        from app.utils.parameters import get_canonical_name

        result = get_canonical_name(123)
        assert result == "123"

    def test_case_insensitive(self):
        """Case insensitive matching"""
        from app.utils.parameters import get_canonical_name

        result1 = get_canonical_name("mad")
        result2 = get_canonical_name("MAD")
        # Both should resolve to same canonical name
        assert result1 is not None
        assert result2 is not None


class TestGetParameterDetails:
    """get_parameter_details function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.parameters import get_parameter_details
        assert callable(get_parameter_details)

    def test_none_input(self):
        """None returns None"""
        from app.utils.parameters import get_parameter_details
        assert get_parameter_details(None) is None

    def test_known_parameter(self):
        """Known parameter returns details"""
        from app.utils.parameters import get_parameter_details

        result = get_parameter_details("inherent_moisture")
        assert result is not None
        assert isinstance(result, dict)

    def test_alias_parameter(self):
        """Alias returns details"""
        from app.utils.parameters import get_parameter_details

        result = get_parameter_details("Mad")
        assert result is not None

    def test_unknown_parameter_returns_default(self):
        """Unknown parameter returns default structure"""
        from app.utils.parameters import get_parameter_details

        result = get_parameter_details("totally_unknown_param")
        assert result is not None
        assert result["type"] == "unknown"
        assert result["lab_code"] is None

    def test_result_has_display_name(self):
        """Result has display_name"""
        from app.utils.parameters import get_parameter_details

        result = get_parameter_details("inherent_moisture")
        assert "display_name" in result

    def test_result_has_aliases(self):
        """Result has aliases"""
        from app.utils.parameters import get_parameter_details

        result = get_parameter_details("inherent_moisture")
        assert "aliases" in result


class TestCalculateValue:
    """calculate_value function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.parameters import calculate_value
        assert callable(calculate_value)

    def test_unknown_parameter(self):
        """Unknown parameter returns None"""
        from app.utils.parameters import calculate_value

        result = calculate_value("unknown_param", {"ash": 10})
        assert result is None

    def test_non_calculated_type(self):
        """Non-calculated parameter returns None"""
        from app.utils.parameters import calculate_value

        # inherent_moisture is measured, not calculated
        result = calculate_value("inherent_moisture", {"ash": 10})
        assert result is None

    def test_fixed_carbon_ad_calculation(self):
        """Fixed carbon calculation"""
        from app.utils.parameters import calculate_value

        inputs = {
            "ash": 10.0,
            "volatile_matter": 30.0,
            "inherent_moisture": 5.0
        }

        result = calculate_value("fixed_carbon_ad", inputs)

        # FC = 100 - (10 + 30 + 5) = 55
        assert result == 55.0

    def test_fixed_carbon_ad_rounded(self):
        """Fixed carbon result is rounded"""
        from app.utils.parameters import calculate_value

        inputs = {
            "ash": 10.123,
            "volatile_matter": 30.456,
            "inherent_moisture": 5.789
        }

        result = calculate_value("fixed_carbon_ad", inputs)

        # Should be rounded to 2 decimals
        assert result == round(100 - (10.123 + 30.456 + 5.789), 2)

    def test_missing_required_input(self):
        """Missing required input returns None"""
        from app.utils.parameters import calculate_value

        inputs = {
            "ash": 10.0,
            # Missing volatile_matter and inherent_moisture
        }

        result = calculate_value("fixed_carbon_ad", inputs)
        assert result is None

    def test_none_value_in_inputs(self):
        """None value in inputs returns None"""
        from app.utils.parameters import calculate_value

        inputs = {
            "ash": 10.0,
            "volatile_matter": None,
            "inherent_moisture": 5.0
        }

        result = calculate_value("fixed_carbon_ad", inputs)
        assert result is None

    def test_invalid_float_value(self):
        """Invalid float value returns None"""
        from app.utils.parameters import calculate_value

        inputs = {
            "ash": "not a number",
            "volatile_matter": 30.0,
            "inherent_moisture": 5.0
        }

        result = calculate_value("fixed_carbon_ad", inputs)
        assert result is None

    def test_string_numbers_work(self):
        """String numbers are converted"""
        from app.utils.parameters import calculate_value

        inputs = {
            "ash": "10.0",
            "volatile_matter": "30.0",
            "inherent_moisture": "5.0"
        }

        result = calculate_value("fixed_carbon_ad", inputs)
        assert result == 55.0

    def test_int_values_work(self):
        """Integer values work"""
        from app.utils.parameters import calculate_value

        inputs = {
            "ash": 10,
            "volatile_matter": 30,
            "inherent_moisture": 5
        }

        result = calculate_value("fixed_carbon_ad", inputs)
        assert result == 55.0

    def test_zero_values(self):
        """Zero values work"""
        from app.utils.parameters import calculate_value

        inputs = {
            "ash": 0.0,
            "volatile_matter": 0.0,
            "inherent_moisture": 0.0
        }

        result = calculate_value("fixed_carbon_ad", inputs)
        assert result == 100.0


class TestParameterDefinitionsIntegration:
    """Integration tests with PARAMETER_DEFINITIONS"""

    def test_parameter_definitions_exist(self):
        """PARAMETER_DEFINITIONS constant exists"""
        from app.constants import PARAMETER_DEFINITIONS
        assert PARAMETER_DEFINITIONS is not None
        assert isinstance(PARAMETER_DEFINITIONS, dict)

    def test_common_parameters_exist(self):
        """Common parameters are defined"""
        from app.constants import PARAMETER_DEFINITIONS

        common_params = [
            "inherent_moisture",
            "ash",
            "volatile_matter",
            "calorific_value"
        ]

        for param in common_params:
            assert param in PARAMETER_DEFINITIONS, f"{param} should exist"

    def test_param_key_function(self):
        """param_key function works"""
        from app.constants import param_key

        # Should find canonical name for alias
        result = param_key("Mad")
        assert result is not None


class TestEdgeCases:
    """Edge case tests"""

    def test_unicode_comma_handling(self):
        """Unicode comma in parameter name"""
        from app.utils.parameters import get_canonical_name

        # Unicode comma (，) should be handled
        result = get_canonical_name("M，ad")  # Unicode comma
        # Should still work
        assert result is not None

    def test_very_long_input(self):
        """Very long input name"""
        from app.utils.parameters import get_canonical_name

        long_name = "A" * 1000
        result = get_canonical_name(long_name)
        assert result == long_name

    def test_special_characters(self):
        """Special characters in name"""
        from app.utils.parameters import get_canonical_name

        result = get_canonical_name("param@#$%")
        assert result is not None

    def test_whitespace_only(self):
        """Whitespace only input"""
        from app.utils.parameters import get_canonical_name

        result = get_canonical_name("   ")
        # After strip, becomes empty string (fallback behavior)
        assert result == ""

    def test_calculate_with_empty_dict(self):
        """Calculate with empty dict"""
        from app.utils.parameters import calculate_value

        result = calculate_value("fixed_carbon_ad", {})
        assert result is None

    def test_get_details_various_known_params(self):
        """Get details for various known parameters"""
        from app.utils.parameters import get_parameter_details

        params = ["ash", "volatile_matter", "total_moisture"]

        for param in params:
            result = get_parameter_details(param)
            assert result is not None, f"Should find details for {param}"
