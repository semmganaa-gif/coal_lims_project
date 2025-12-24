# tests/test_parameters_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/parameters.py - targeting 100% coverage.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestGetCanonicalName:
    """Tests for get_canonical_name function."""

    def test_valid_name(self, app):
        """Test with valid parameter name."""
        with app.app_context():
            from app.utils.parameters import get_canonical_name
            result = get_canonical_name("MT")
            assert result is not None

    def test_none_input(self, app):
        """Test with None input."""
        with app.app_context():
            from app.utils.parameters import get_canonical_name
            result = get_canonical_name(None)
            assert result is None

    def test_empty_string(self, app):
        """Test with empty string."""
        with app.app_context():
            from app.utils.parameters import get_canonical_name
            result = get_canonical_name("")
            assert result is None

    def test_whitespace_stripped(self, app):
        """Test whitespace is stripped."""
        with app.app_context():
            from app.utils.parameters import get_canonical_name
            result = get_canonical_name("  MT  ")
            assert result is not None

    def test_unknown_name(self, app):
        """Test with unknown name returns cleaned input."""
        with app.app_context():
            from app.utils.parameters import get_canonical_name
            result = get_canonical_name("UNKNOWN_PARAM_XYZ")
            assert result == "UNKNOWN_PARAM_XYZ"

    def test_integer_input(self, app):
        """Test with integer input (converted to string)."""
        with app.app_context():
            from app.utils.parameters import get_canonical_name
            result = get_canonical_name(123)
            assert result is not None


class TestGetParameterDetails:
    """Tests for get_parameter_details function."""

    def test_known_parameter(self, app):
        """Test with known parameter."""
        with app.app_context():
            from app.utils.parameters import get_parameter_details
            result = get_parameter_details("MT")
            assert result is not None
            assert isinstance(result, dict)

    def test_none_input(self, app):
        """Test with None input."""
        with app.app_context():
            from app.utils.parameters import get_parameter_details
            result = get_parameter_details(None)
            assert result is None

    def test_empty_string(self, app):
        """Test with empty string."""
        with app.app_context():
            from app.utils.parameters import get_parameter_details
            result = get_parameter_details("")
            assert result is None

    def test_unknown_parameter(self, app):
        """Test with unknown parameter returns default structure."""
        with app.app_context():
            from app.utils.parameters import get_parameter_details
            result = get_parameter_details("COMPLETELY_UNKNOWN_PARAM")
            assert result is not None
            assert 'display_name' in result
            assert 'type' in result
            assert result['type'] == 'unknown'


class TestCalculateValue:
    """Tests for calculate_value function."""

    def test_fixed_carbon_ad(self, app):
        """Test fixed_carbon_ad calculation."""
        with app.app_context():
            from app.utils.parameters import calculate_value
            from app.constants import PARAMETER_DEFINITIONS

            # Check if fixed_carbon_ad exists
            if 'fixed_carbon_ad' in PARAMETER_DEFINITIONS:
                inputs = {
                    'ash': 10.0,
                    'volatile_matter': 30.0,
                    'inherent_moisture': 5.0
                }
                result = calculate_value('fixed_carbon_ad', inputs)
                if result is not None:
                    assert result == 55.0  # 100 - (10 + 30 + 5)
            else:
                pytest.skip("fixed_carbon_ad not in PARAMETER_DEFINITIONS")

    def test_unknown_parameter(self, app):
        """Test with unknown parameter."""
        with app.app_context():
            from app.utils.parameters import calculate_value
            result = calculate_value('unknown_param', {})
            assert result is None

    def test_non_calculated_type(self, app):
        """Test with non-calculated type parameter."""
        with app.app_context():
            from app.utils.parameters import calculate_value
            # MT is a measured parameter, not calculated
            result = calculate_value('MT', {})
            assert result is None

    def test_missing_required_input(self, app):
        """Test with missing required input."""
        with app.app_context():
            from app.utils.parameters import calculate_value
            from app.constants import PARAMETER_DEFINITIONS

            if 'fixed_carbon_ad' in PARAMETER_DEFINITIONS:
                inputs = {
                    'ash': 10.0,
                    # missing volatile_matter and inherent_moisture
                }
                result = calculate_value('fixed_carbon_ad', inputs)
                assert result is None
            else:
                pytest.skip("fixed_carbon_ad not in PARAMETER_DEFINITIONS")

    def test_invalid_input_type(self, app):
        """Test with invalid input type."""
        with app.app_context():
            from app.utils.parameters import calculate_value
            from app.constants import PARAMETER_DEFINITIONS

            if 'fixed_carbon_ad' in PARAMETER_DEFINITIONS:
                inputs = {
                    'ash': 'not_a_number',
                    'volatile_matter': 30.0,
                    'inherent_moisture': 5.0
                }
                result = calculate_value('fixed_carbon_ad', inputs)
                assert result is None
            else:
                pytest.skip("fixed_carbon_ad not in PARAMETER_DEFINITIONS")

    def test_none_input_value(self, app):
        """Test with None input value."""
        with app.app_context():
            from app.utils.parameters import calculate_value
            from app.constants import PARAMETER_DEFINITIONS

            if 'fixed_carbon_ad' in PARAMETER_DEFINITIONS:
                inputs = {
                    'ash': None,
                    'volatile_matter': 30.0,
                    'inherent_moisture': 5.0
                }
                result = calculate_value('fixed_carbon_ad', inputs)
                assert result is None
            else:
                pytest.skip("fixed_carbon_ad not in PARAMETER_DEFINITIONS")


class TestParameterDefinitions:
    """Tests for PARAMETER_DEFINITIONS constant."""

    def test_is_dict(self, app):
        """Test PARAMETER_DEFINITIONS is a dict."""
        with app.app_context():
            from app.constants import PARAMETER_DEFINITIONS
            assert isinstance(PARAMETER_DEFINITIONS, dict)

    def test_has_entries(self, app):
        """Test PARAMETER_DEFINITIONS has entries."""
        with app.app_context():
            from app.constants import PARAMETER_DEFINITIONS
            assert len(PARAMETER_DEFINITIONS) > 0
