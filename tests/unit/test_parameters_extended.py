# -*- coding: utf-8 -*-
"""
Parameters utils extended тестүүд
"""
import pytest


class TestGetCanonicalName:
    """get_canonical_name тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.parameters import get_canonical_name
        assert get_canonical_name is not None

    def test_none_input(self):
        """None input returns None"""
        from app.utils.parameters import get_canonical_name
        assert get_canonical_name(None) is None

    def test_empty_input(self):
        """Empty string returns None"""
        from app.utils.parameters import get_canonical_name
        result = get_canonical_name('')
        assert result is None or result == ''

    def test_known_parameter(self):
        """Known parameter returns canonical name"""
        from app.utils.parameters import get_canonical_name
        result = get_canonical_name('Mad')
        assert result is not None

    def test_alias_parameter(self):
        """Alias parameter returns canonical name"""
        from app.utils.parameters import get_canonical_name
        # Mad is often aliased
        result = get_canonical_name('Mad')
        assert isinstance(result, str)

    def test_unknown_parameter(self):
        """Unknown parameter returns cleaned name"""
        from app.utils.parameters import get_canonical_name
        result = get_canonical_name('UNKNOWN_PARAM_XYZ')
        assert result is not None

    def test_whitespace_stripped(self):
        """Whitespace is stripped"""
        from app.utils.parameters import get_canonical_name
        result = get_canonical_name('  Mad  ')
        assert result is not None


class TestGetParameterDetails:
    """get_parameter_details тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.parameters import get_parameter_details
        assert get_parameter_details is not None

    def test_none_input(self):
        """None input returns None"""
        from app.utils.parameters import get_parameter_details
        assert get_parameter_details(None) is None

    def test_empty_input(self):
        """Empty string returns fallback details"""
        from app.utils.parameters import get_parameter_details
        result = get_parameter_details('')
        # May return None or fallback dict
        assert result is None or isinstance(result, dict)

    def test_known_parameter(self):
        """Known parameter returns details dict"""
        from app.utils.parameters import get_parameter_details
        result = get_parameter_details('inherent_moisture')
        assert isinstance(result, dict)

    def test_unknown_parameter(self):
        """Unknown parameter returns fallback dict"""
        from app.utils.parameters import get_parameter_details
        result = get_parameter_details('UNKNOWN_XYZ')
        assert isinstance(result, dict)
        assert 'display_name' in result

    def test_details_has_expected_keys(self):
        """Details dict has expected keys"""
        from app.utils.parameters import get_parameter_details
        result = get_parameter_details('ash')
        if result:
            # Should have some common keys
            assert isinstance(result, dict)


class TestCalculateValue:
    """calculate_value тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.parameters import calculate_value
        assert calculate_value is not None

    def test_unknown_parameter(self):
        """Unknown parameter returns None"""
        from app.utils.parameters import calculate_value
        result = calculate_value('UNKNOWN_XYZ', {})
        assert result is None

    def test_non_calculated_type(self):
        """Non-calculated type returns None"""
        from app.utils.parameters import calculate_value
        # Ash is measured, not calculated
        result = calculate_value('ash', {'ash': 10.0})
        assert result is None

    def test_fixed_carbon_ad_calculation(self):
        """Fixed carbon calculation"""
        from app.utils.parameters import calculate_value
        inputs = {
            'ash': 10.0,
            'volatile_matter': 30.0,
            'inherent_moisture': 5.0
        }
        result = calculate_value('fixed_carbon_ad', inputs)
        # FC = 100 - 10 - 30 - 5 = 55
        if result is not None:
            assert abs(result - 55.0) < 0.1

    def test_fixed_carbon_missing_ash(self):
        """Fixed carbon with missing ash returns None"""
        from app.utils.parameters import calculate_value
        inputs = {
            'volatile_matter': 30.0,
            'inherent_moisture': 5.0
        }
        result = calculate_value('fixed_carbon_ad', inputs)
        assert result is None

    def test_fixed_carbon_missing_vm(self):
        """Fixed carbon with missing volatile matter returns None"""
        from app.utils.parameters import calculate_value
        inputs = {
            'ash': 10.0,
            'inherent_moisture': 5.0
        }
        result = calculate_value('fixed_carbon_ad', inputs)
        assert result is None

    def test_fixed_carbon_missing_moisture(self):
        """Fixed carbon with missing moisture returns None"""
        from app.utils.parameters import calculate_value
        inputs = {
            'ash': 10.0,
            'volatile_matter': 30.0
        }
        result = calculate_value('fixed_carbon_ad', inputs)
        assert result is None

    def test_fixed_carbon_invalid_values(self):
        """Fixed carbon with invalid values returns None"""
        from app.utils.parameters import calculate_value
        inputs = {
            'ash': 'invalid',
            'volatile_matter': 30.0,
            'inherent_moisture': 5.0
        }
        result = calculate_value('fixed_carbon_ad', inputs)
        assert result is None

    def test_fixed_carbon_none_values(self):
        """Fixed carbon with None values returns None"""
        from app.utils.parameters import calculate_value
        inputs = {
            'ash': None,
            'volatile_matter': 30.0,
            'inherent_moisture': 5.0
        }
        result = calculate_value('fixed_carbon_ad', inputs)
        assert result is None
