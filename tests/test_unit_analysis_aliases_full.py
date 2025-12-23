# tests/unit/test_analysis_aliases_full.py
# -*- coding: utf-8 -*-
"""
Analysis aliases utility tests
"""
import pytest
from app.utils.analysis_aliases import (
    ALIAS_TO_BASE,
    normalize_analysis_code,
    get_all_aliases_for_base,
)


class TestAliasToBase:
    """ALIAS_TO_BASE dictionary тестүүд"""

    def test_alias_to_base_not_empty(self):
        assert len(ALIAS_TO_BASE) > 0

    def test_common_aliases_exist(self):
        assert "ts" in ALIAS_TO_BASE
        assert "cv" in ALIAS_TO_BASE
        assert "mad" in ALIAS_TO_BASE
        assert "mt" in ALIAS_TO_BASE
        assert "fm" in ALIAS_TO_BASE
        assert "aad" in ALIAS_TO_BASE
        assert "vad" in ALIAS_TO_BASE

    def test_ts_aliases(self):
        assert ALIAS_TO_BASE["ts"] == "TS"
        assert ALIAS_TO_BASE["st,ad"] == "TS"
        assert ALIAS_TO_BASE["s"] == "TS"
        assert ALIAS_TO_BASE["sulfur"] == "TS"

    def test_cv_aliases(self):
        assert ALIAS_TO_BASE["cv"] == "CV"
        assert ALIAS_TO_BASE["qgr,ad"] == "CV"
        assert ALIAS_TO_BASE["qnet,ar"] == "CV"

    def test_moisture_aliases(self):
        assert ALIAS_TO_BASE["mad"] == "Mad"
        assert ALIAS_TO_BASE["mt"] == "MT"
        assert ALIAS_TO_BASE["fm"] == "FM"

    def test_ash_aliases(self):
        assert ALIAS_TO_BASE["aad"] == "Aad"
        assert ALIAS_TO_BASE["ash"] == "Aad"

    def test_volatile_aliases(self):
        assert ALIAS_TO_BASE["vad"] == "Vad"
        assert ALIAS_TO_BASE["vm"] == "Vad"

    def test_element_aliases(self):
        assert ALIAS_TO_BASE["c"] == "C"
        assert ALIAS_TO_BASE["h"] == "H"
        assert ALIAS_TO_BASE["n"] == "N"
        assert ALIAS_TO_BASE["o"] == "O"
        assert ALIAS_TO_BASE["p"] == "P"
        assert ALIAS_TO_BASE["f"] == "F"
        assert ALIAS_TO_BASE["cl"] == "Cl"

    def test_ash_fusion_aliases(self):
        assert ALIAS_TO_BASE["idt"] == "IDT"
        assert ALIAS_TO_BASE["st"] == "ST"
        assert ALIAS_TO_BASE["ht"] == "HT"
        assert ALIAS_TO_BASE["ft"] == "FT"


class TestNormalizeAnalysisCode:
    """normalize_analysis_code() функцийн тестүүд"""

    def test_empty_code_returns_empty(self):
        assert normalize_analysis_code("") == ""
        assert normalize_analysis_code(None) is None

    def test_known_alias_normalizes(self):
        assert normalize_analysis_code("ts") == "TS"
        assert normalize_analysis_code("cv") == "CV"
        assert normalize_analysis_code("mad") == "Mad"

    def test_case_insensitive(self):
        assert normalize_analysis_code("TS") == "TS"
        assert normalize_analysis_code("Ts") == "TS"
        assert normalize_analysis_code("tS") == "TS"

    def test_strips_whitespace(self):
        assert normalize_analysis_code("  ts  ") == "TS"
        assert normalize_analysis_code(" cv ") == "CV"

    def test_unknown_code_returns_original(self):
        assert normalize_analysis_code("unknown") == "unknown"
        assert normalize_analysis_code("XYZ123") == "XYZ123"

    def test_long_aliases(self):
        assert normalize_analysis_code("total sulfur") == "TS"
        assert normalize_analysis_code("air dried moisture") == "Mad"

    def test_mongolian_aliases(self):
        assert normalize_analysis_code("хүхэр") == "TS"
        assert normalize_analysis_code("үнс") == "Aad"


class TestGetAllAliasesForBase:
    """get_all_aliases_for_base() функцийн тестүүд"""

    def test_ts_has_multiple_aliases(self):
        aliases = get_all_aliases_for_base("TS")
        assert "ts" in aliases
        assert "sulfur" in aliases
        assert len(aliases) >= 5

    def test_cv_has_multiple_aliases(self):
        aliases = get_all_aliases_for_base("CV")
        assert "cv" in aliases
        assert "qgr,ad" in aliases
        assert len(aliases) >= 5

    def test_unknown_base_returns_empty(self):
        aliases = get_all_aliases_for_base("UNKNOWN_CODE")
        assert aliases == []

    def test_case_sensitive_base(self):
        """Base codes are case-sensitive"""
        ts_aliases = get_all_aliases_for_base("TS")
        ts_lower_aliases = get_all_aliases_for_base("ts")
        assert len(ts_aliases) > 0
        assert len(ts_lower_aliases) == 0  # "ts" is not a base code

    def test_returns_list(self):
        result = get_all_aliases_for_base("Mad")
        assert isinstance(result, list)
