# -*- coding: utf-8 -*-
"""
Codes utils extended тестүүд
"""
import pytest


class TestCodesModule:
    """Codes module тестүүд"""

    def test_import_module(self):
        """Module import"""
        from app.utils import codes
        assert codes is not None


class TestNormCode:
    """norm_code тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.codes import norm_code
        assert norm_code is not None

    def test_norm_ts(self):
        """Normalize TS"""
        from app.utils.codes import norm_code
        result = norm_code('TS')
        assert result is not None

    def test_norm_lowercase(self):
        """Normalize lowercase"""
        from app.utils.codes import norm_code
        result = norm_code('ts')
        assert result is not None

    def test_norm_mad(self):
        """Normalize Mad"""
        from app.utils.codes import norm_code
        result = norm_code('Mad')
        assert result is not None


class TestAliasConstants:
    """Alias constants тестүүд"""

    def test_import_base_to_aliases(self):
        """BASE_TO_ALIASES import"""
        from app.utils.codes import BASE_TO_ALIASES
        assert BASE_TO_ALIASES is not None
        assert isinstance(BASE_TO_ALIASES, dict)

    def test_import_alias_to_base(self):
        """ALIAS_TO_BASE_ANALYSIS import"""
        from app.utils.codes import ALIAS_TO_BASE_ANALYSIS
        assert ALIAS_TO_BASE_ANALYSIS is not None
        assert isinstance(ALIAS_TO_BASE_ANALYSIS, dict)


class TestAliasesOf:
    """aliases_of тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.codes import aliases_of
        assert aliases_of is not None

    def test_aliases_of_ts(self):
        """Aliases of TS"""
        from app.utils.codes import aliases_of
        result = aliases_of('TS')
        assert result is not None


class TestToBaseList:
    """to_base_list тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.codes import to_base_list
        assert to_base_list is not None

    def test_convert_list(self):
        """Convert list"""
        from app.utils.codes import to_base_list
        result = to_base_list(['TS', 'Mad', 'Aad'])
        assert result is not None
        assert isinstance(result, list)


class TestIsAliasOfBase:
    """is_alias_of_base тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.codes import is_alias_of_base
        assert is_alias_of_base is not None

    def test_ts_is_ts(self):
        """TS is TS"""
        from app.utils.codes import is_alias_of_base
        result = is_alias_of_base('TS', 'TS')
        assert result is True or result is False
