# tests/test_analysis_aliases_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/analysis_aliases.py
"""

import pytest


class TestNormalizeAnalysisCode:
    """Tests for normalize_analysis_code function."""

    def test_known_alias_ts(self, app):
        """Test normalizing known alias 'ts' to 'TS'."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("ts")
            assert result == "TS"

    def test_known_alias_cv(self, app):
        """Test normalizing known alias 'cv' to 'CV'."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("cv")
            assert result == "CV"

    def test_known_alias_mad(self, app):
        """Test normalizing known alias 'mad' to 'Mad'."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("mad")
            assert result == "Mad"

    def test_known_alias_mt(self, app):
        """Test normalizing known alias 'mt' to 'MT'."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("mt")
            assert result == "MT"

    def test_known_alias_aad(self, app):
        """Test normalizing known alias 'aad' to 'Aad'."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("aad")
            assert result == "Aad"

    def test_known_alias_vad(self, app):
        """Test normalizing known alias 'vad' to 'Vad'."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("vad")
            assert result == "Vad"

    def test_known_alias_csn(self, app):
        """Test normalizing known alias 'csn' to 'CSN'."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("csn")
            assert result == "CSN"

    def test_known_alias_sulfur(self, app):
        """Test normalizing 'sulfur' to 'TS'."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("sulfur")
            assert result == "TS"

    def test_known_alias_comma_notation(self, app):
        """Test normalizing comma notation 'st,ad' to 'TS'."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("st,ad")
            assert result == "TS"

    def test_known_alias_dot_notation(self, app):
        """Test normalizing dot notation 'st.ad' to 'TS'."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("st.ad")
            assert result == "TS"

    def test_unknown_alias_returns_original(self, app):
        """Test unknown alias returns original code."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("UNKNOWN_XYZ")
            assert result == "UNKNOWN_XYZ"

    def test_empty_string_returns_empty(self, app):
        """Test empty string returns empty."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("")
            assert result == ""

    def test_none_returns_none(self, app):
        """Test None returns None."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code(None)
            assert result is None

    def test_case_insensitive(self, app):
        """Test case insensitive matching."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            assert normalize_analysis_code("TS") == "TS"
            assert normalize_analysis_code("Ts") == "TS"
            assert normalize_analysis_code("tS") == "TS"

    def test_whitespace_stripped(self, app):
        """Test whitespace is stripped."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("  ts  ")
            assert result == "TS"

    def test_mongolian_alias(self, app):
        """Test Mongolian alias works."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("хүхэр")
            assert result == "TS"

    def test_ash_alias(self, app):
        """Test 'ash' alias."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("ash")
            assert result == "Aad"

    def test_volatile_alias(self, app):
        """Test 'volatile' alias."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("volatile")
            assert result == "Vad"

    def test_fixed_carbon_alias(self, app):
        """Test 'fixed carbon' alias."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("fixed carbon")
            assert result == "FC"

    def test_size_distribution_alias(self, app):
        """Test size distribution alias."""
        with app.app_context():
            from app.utils.analysis_aliases import normalize_analysis_code
            result = normalize_analysis_code("+50mm")
            assert result == "Size_50"


class TestGetAllAliasesForBase:
    """Tests for get_all_aliases_for_base function."""

    def test_get_aliases_for_ts(self, app):
        """Test getting all aliases for 'TS'."""
        with app.app_context():
            from app.utils.analysis_aliases import get_all_aliases_for_base
            result = get_all_aliases_for_base("TS")
            assert isinstance(result, list)
            assert len(result) > 0
            assert "ts" in result
            assert "sulfur" in result

    def test_get_aliases_for_cv(self, app):
        """Test getting all aliases for 'CV'."""
        with app.app_context():
            from app.utils.analysis_aliases import get_all_aliases_for_base
            result = get_all_aliases_for_base("CV")
            assert isinstance(result, list)
            assert len(result) > 0
            assert "cv" in result

    def test_get_aliases_for_unknown(self, app):
        """Test getting aliases for unknown base returns empty list."""
        with app.app_context():
            from app.utils.analysis_aliases import get_all_aliases_for_base
            result = get_all_aliases_for_base("UNKNOWN_BASE")
            assert isinstance(result, list)
            assert len(result) == 0

    def test_get_aliases_for_mt(self, app):
        """Test getting all aliases for 'MT'."""
        with app.app_context():
            from app.utils.analysis_aliases import get_all_aliases_for_base
            result = get_all_aliases_for_base("MT")
            assert isinstance(result, list)
            assert "mt" in result

    def test_get_aliases_for_aad(self, app):
        """Test getting all aliases for 'Aad'."""
        with app.app_context():
            from app.utils.analysis_aliases import get_all_aliases_for_base
            result = get_all_aliases_for_base("Aad")
            assert isinstance(result, list)
            assert "aad" in result
            assert "ash" in result


class TestAliasToBase:
    """Tests for ALIAS_TO_BASE constant."""

    def test_alias_to_base_is_dict(self, app):
        """Test ALIAS_TO_BASE is a dictionary."""
        with app.app_context():
            from app.utils.analysis_aliases import ALIAS_TO_BASE
            assert isinstance(ALIAS_TO_BASE, dict)

    def test_alias_to_base_has_entries(self, app):
        """Test ALIAS_TO_BASE has entries."""
        with app.app_context():
            from app.utils.analysis_aliases import ALIAS_TO_BASE
            assert len(ALIAS_TO_BASE) > 0

    def test_alias_to_base_lowercase_keys(self, app):
        """Test all keys are lowercase."""
        with app.app_context():
            from app.utils.analysis_aliases import ALIAS_TO_BASE
            for key in ALIAS_TO_BASE.keys():
                assert key == key.lower()
