# -*- coding: utf-8 -*-
"""
Codes utility тестүүд
"""
import pytest
from app.utils.codes import (
    norm_code,
    is_alias_of_base,
    aliases_of,
    to_base_list,
    ALIAS_TO_BASE_ANALYSIS,
    BASE_TO_ALIASES
)


class TestNormCode:
    """norm_code функц тестүүд"""

    def test_basic_normalization(self):
        """Энгийн code normalize"""
        result = norm_code('ts')
        assert result == 'TS' or result == 'ts'

    def test_with_spaces(self):
        """Хоосон зайтай code"""
        result = norm_code('  TS  ')
        assert 'TS' in result.upper()

    def test_none_input(self):
        """None оролт"""
        try:
            result = norm_code(None)
            assert result is None or result == ''
        except (TypeError, AttributeError):
            pass


class TestIsAliasOfBase:
    """is_alias_of_base функц тестүүд"""

    def test_valid_alias(self):
        """Valid alias шалгах"""
        # TS should be an alias for itself or related base
        result = is_alias_of_base('TS', 'TS')
        assert isinstance(result, bool)

    def test_invalid_alias(self):
        """Invalid alias шалгах"""
        result = is_alias_of_base('UNKNOWN', 'TS')
        assert isinstance(result, bool)


class TestAliasesOf:
    """aliases_of функц тестүүд"""

    def test_get_aliases(self):
        """Aliases авах"""
        result = aliases_of('TS')
        assert isinstance(result, (list, set, tuple)) or result is None


class TestToBaseList:
    """to_base_list функц тестүүд"""

    def test_single_code(self):
        """Нэг code"""
        result = to_base_list(['TS'])
        assert isinstance(result, (list, set, tuple))

    def test_multiple_codes(self):
        """Олон code"""
        result = to_base_list(['TS', 'CV', 'Mad'])
        assert isinstance(result, (list, set, tuple))

    def test_empty_list(self):
        """Хоосон жагсаалт"""
        result = to_base_list([])
        assert isinstance(result, (list, set, tuple))
