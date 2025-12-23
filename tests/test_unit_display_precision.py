# -*- coding: utf-8 -*-
"""
Display Precision - unit тестүүд
"""
import pytest
from app.config.display_precision import (
    DECIMAL_PLACES,
    DEFAULT_DECIMAL_PLACES,
    PRECISION_GROUPS,
    get_decimal_places,
    format_result,
    get_precision_summary,
    validate_precision_config,
)


class TestDecimalPlacesConfig:
    """DECIMAL_PLACES config tests"""

    def test_decimal_places_is_dict(self):
        """DECIMAL_PLACES is a dictionary"""
        assert isinstance(DECIMAL_PLACES, dict)
        assert len(DECIMAL_PLACES) > 0

    def test_common_codes_exist(self):
        """Common analysis codes exist"""
        common_codes = ['MT', 'Mad', 'Aad', 'Vad', 'TS', 'CV', 'P', 'Gi']
        for code in common_codes:
            assert code in DECIMAL_PLACES

    def test_decimal_values_are_integers(self):
        """All decimal places are integers"""
        for code, places in DECIMAL_PLACES.items():
            assert isinstance(places, int), f"{code} should have int decimal places"
            assert 0 <= places <= 10, f"{code} decimal places should be 0-10"

    def test_default_decimal_places(self):
        """Default decimal places is set"""
        assert DEFAULT_DECIMAL_PLACES == 2


class TestGetDecimalPlaces:
    """get_decimal_places function tests"""

    def test_exact_match(self):
        """Get decimal places for exact code match"""
        assert get_decimal_places('Aad') == 2
        assert get_decimal_places('P') == 3
        assert get_decimal_places('CV') == 0
        assert get_decimal_places('MT') == 1

    def test_empty_code(self):
        """Get default for empty code"""
        assert get_decimal_places('') == DEFAULT_DECIMAL_PLACES
        assert get_decimal_places(None) == DEFAULT_DECIMAL_PLACES

    def test_unknown_code(self):
        """Get default for unknown code"""
        assert get_decimal_places('UNKNOWN') == DEFAULT_DECIMAL_PLACES
        assert get_decimal_places('XYZ123') == DEFAULT_DECIMAL_PLACES

    def test_case_insensitive(self):
        """Case insensitive lookup works"""
        # These should find matches via case-insensitive search
        assert get_decimal_places('aad') == 2
        assert get_decimal_places('AAD') == 2
        assert get_decimal_places('cv') == 0
        assert get_decimal_places('CV') == 0

    def test_base_code_lookup(self):
        """Base code lookup for comma-separated codes"""
        # St,ad should find St
        assert get_decimal_places('St,ad') == 2
        # Unknown base
        assert get_decimal_places('UNKNOWN,ad') == DEFAULT_DECIMAL_PLACES

    def test_whitespace_handling(self):
        """Whitespace is trimmed"""
        assert get_decimal_places(' Aad ') == 2
        assert get_decimal_places('  CV  ') == 0


class TestFormatResult:
    """format_result function tests"""

    def test_format_with_code(self):
        """Format result with analysis code"""
        assert format_result(10.256, 'Aad') == '10.26'
        assert format_result(0.0156, 'P') == '0.016'
        assert format_result(25432.8, 'CV') == '25433'
        assert format_result(5.55, 'CSN') == '5.5'

    def test_format_none_value(self):
        """Format None returns dash"""
        assert format_result(None, 'Aad') == '-'
        assert format_result(None) == '-'

    def test_format_without_code(self):
        """Format without code uses default precision"""
        result = format_result(10.256)
        assert result == '10.26'  # Default 2 decimal places

    def test_format_integer_result(self):
        """Format integer result"""
        assert format_result(100, 'CV') == '100'
        assert format_result(25000.0, 'CV') == '25000'

    def test_format_rounding(self):
        """Format applies correct rounding"""
        assert format_result(10.255, 'Aad') == '10.26'  # Round up
        assert format_result(10.254, 'Aad') == '10.25'  # Round down

    def test_format_zero(self):
        """Format zero value"""
        assert format_result(0, 'Aad') == '0.00'
        assert format_result(0.0, 'CV') == '0'

    def test_format_negative(self):
        """Format negative value"""
        assert format_result(-10.25, 'Aad') == '-10.25'

    def test_format_small_value(self):
        """Format very small values"""
        assert format_result(0.001, 'P') == '0.001'
        assert format_result(0.0001, 'P') == '0.000'


class TestGetPrecisionSummary:
    """get_precision_summary function tests"""

    def test_summary_structure(self):
        """Summary has correct structure"""
        summary = get_precision_summary()
        assert 'total_codes' in summary
        assert 'default_precision' in summary
        assert 'groups' in summary
        assert 'by_precision' in summary

    def test_total_codes(self):
        """Total codes matches DECIMAL_PLACES"""
        summary = get_precision_summary()
        assert summary['total_codes'] == len(DECIMAL_PLACES)

    def test_default_precision(self):
        """Default precision is included"""
        summary = get_precision_summary()
        assert summary['default_precision'] == DEFAULT_DECIMAL_PLACES

    def test_groups_included(self):
        """Groups are included"""
        summary = get_precision_summary()
        assert summary['groups'] == PRECISION_GROUPS

    def test_by_precision_grouping(self):
        """Codes are grouped by precision"""
        summary = get_precision_summary()
        by_precision = summary['by_precision']

        # Check some expected groupings
        assert isinstance(by_precision, dict)
        # CV should be in 0 decimal places
        if 0 in by_precision:
            assert 'CV' in by_precision[0]
        # Aad should be in 2 decimal places
        if 2 in by_precision:
            assert 'Aad' in by_precision[2]


class TestValidatePrecisionConfig:
    """validate_precision_config function tests"""

    def test_valid_config(self):
        """Current config is valid"""
        # Should not raise
        validate_precision_config()

    def test_validates_successfully(self):
        """Validation passes for current config"""
        try:
            validate_precision_config()
            assert True
        except ValueError:
            pytest.fail("Validation should pass for current config")


class TestPrecisionGroups:
    """PRECISION_GROUPS tests"""

    def test_groups_structure(self):
        """Groups have correct structure"""
        for group_name, group_data in PRECISION_GROUPS.items():
            assert 'name' in group_data
            assert 'codes' in group_data
            assert 'example' in group_data
            assert isinstance(group_data['codes'], list)

    def test_zero_decimals_group(self):
        """0 decimals group contains expected codes"""
        group = PRECISION_GROUPS.get('0_decimals')
        if group:
            assert 'CV' in group['codes']

    def test_three_decimals_group(self):
        """3 decimals group contains trace elements"""
        group = PRECISION_GROUPS.get('3_decimals')
        if group:
            assert 'P' in group['codes']


class TestEdgeCases:
    """Edge case tests"""

    def test_very_large_value(self):
        """Handle very large values"""
        result = format_result(999999.999, 'Aad')
        assert result == '1000000.00'

    def test_scientific_notation_input(self):
        """Handle scientific notation"""
        result = format_result(1.5e-3, 'P')
        assert result == '0.002'

    def test_float_precision_issues(self):
        """Handle float precision edge cases"""
        # 0.1 + 0.2 = 0.30000000000000004 in float
        result = format_result(0.1 + 0.2, 'P')
        assert result == '0.300'

    def test_all_codes_have_valid_precision(self):
        """All defined codes return valid precision"""
        for code in DECIMAL_PLACES.keys():
            places = get_decimal_places(code)
            assert isinstance(places, int)
            assert 0 <= places <= 10
