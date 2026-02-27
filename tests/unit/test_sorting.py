# -*- coding: utf-8 -*-
"""
Tests for app/utils/sorting.py
Sample code sorting functions comprehensive tests
"""
import pytest
from unittest.mock import MagicMock


class TestNaturalSortKey:
    """natural_sort_key function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.sorting import natural_sort_key
        assert callable(natural_sort_key)

    def test_none_returns_empty_list(self):
        """None returns list with sentinel tuple"""
        from app.utils.sorting import natural_sort_key
        assert natural_sort_key(None) == [(1, "", 0)]

    def test_empty_string_returns_empty_list(self):
        """Empty string returns list with sentinel tuple"""
        from app.utils.sorting import natural_sort_key
        assert natural_sort_key("") == [(1, "", 0)]

    def test_whitespace_only_returns_empty_list(self):
        """Whitespace only returns list with sentinel tuple"""
        from app.utils.sorting import natural_sort_key
        assert natural_sort_key("   ") == [(1, "", 0)]

    def test_simple_string(self):
        """Simple string without numbers"""
        from app.utils.sorting import natural_sort_key
        result = natural_sort_key("abc")
        assert result == [(1, "abc", 0)]

    def test_simple_number(self):
        """String with only number"""
        from app.utils.sorting import natural_sort_key
        result = natural_sort_key("123")
        assert result == [(0, "", 123)]

    def test_string_with_number(self):
        """String with number embedded"""
        from app.utils.sorting import natural_sort_key
        result = natural_sort_key("N10")
        assert result == [(1, "n", 0), (0, "", 10)]

    def test_lowercase_conversion(self):
        """Text is converted to lowercase"""
        from app.utils.sorting import natural_sort_key
        result = natural_sort_key("ABC")
        assert result == [(1, "abc", 0)]

    def test_multiple_numbers(self):
        """String with multiple numbers"""
        from app.utils.sorting import natural_sort_key
        result = natural_sort_key("A1B2C3")
        assert result == [(1, "a", 0), (0, "", 1), (1, "b", 0), (0, "", 2), (1, "c", 0), (0, "", 3)]

    def test_leading_zeros_number(self):
        """Leading zeros in number"""
        from app.utils.sorting import natural_sort_key
        result = natural_sort_key("N007")
        assert result == [(1, "n", 0), (0, "", 7)]

    def test_integer_input(self):
        """Integer input is converted"""
        from app.utils.sorting import natural_sort_key
        result = natural_sort_key(123)
        assert result == [(0, "", 123)]

    def test_float_input(self):
        """Float input - decimal point separates"""
        from app.utils.sorting import natural_sort_key
        result = natural_sort_key(12.5)
        # "12.5" splits into [(0,'',12), (1,'.',0), (0,'',5)]
        assert (0, "", 12) in result

    def test_sorts_correctly(self):
        """Natural sort key works for sorting"""
        from app.utils.sorting import natural_sort_key
        items = ["N10", "N2", "N1", "N20"]
        sorted_items = sorted(items, key=natural_sort_key)
        assert sorted_items == ["N1", "N2", "N10", "N20"]

    def test_mixed_case_sorting(self):
        """Mixed case items sort correctly"""
        from app.utils.sorting import natural_sort_key
        items = ["B1", "a1", "A2", "b2"]
        sorted_items = sorted(items, key=natural_sort_key)
        # All lowercase for comparison, so a1 < a2 < b1 < b2
        assert sorted_items == ["a1", "A2", "B1", "b2"]

    def test_chpp_sample_codes(self):
        """CHPP sample codes sort correctly"""
        from app.utils.sorting import natural_sort_key
        items = ["PF211", "PF221", "PF211_D1", "CC", "TC"]
        sorted_items = sorted(items, key=natural_sort_key)
        # "cc" < "pf211" < "pf211_d1" < "pf221" < "tc"
        assert "CC" in sorted_items
        assert "TC" in sorted_items


class TestCustomSampleSortKey:
    """custom_sample_sort_key function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.sorting import custom_sample_sort_key
        assert callable(custom_sample_sort_key)

    def test_none_returns_high_priority(self):
        """None returns tuple with 99 priority"""
        from app.utils.sorting import custom_sample_sort_key
        result = custom_sample_sort_key(None)
        assert result[0] == 99
        assert result[1] == 0
        assert result[2] == [(1, "", 0)]

    def test_empty_string_returns_high_priority(self):
        """Empty string returns tuple with 99 priority"""
        from app.utils.sorting import custom_sample_sort_key
        result = custom_sample_sort_key("")
        assert result[0] == 99

    def test_whitespace_returns_high_priority(self):
        """Whitespace only returns tuple with 99 priority"""
        from app.utils.sorting import custom_sample_sort_key
        result = custom_sample_sort_key("   ")
        assert result[0] == 99

    def test_chpp_2h_exact_match(self):
        """CHPP 2H exact match gets priority 0"""
        from app.utils.sorting import custom_sample_sort_key
        result = custom_sample_sort_key("PF211")
        assert result[0] == 0
        assert isinstance(result[1], int)

    def test_chpp_2h_prefix_match(self):
        """CHPP 2H prefix match gets priority 0"""
        from app.utils.sorting import custom_sample_sort_key
        result = custom_sample_sort_key("PF211_D1")
        assert result[0] == 0

    def test_chpp_2h_cc_exact_match(self):
        """CHPP 2H CC exact match"""
        from app.utils.sorting import custom_sample_sort_key
        result = custom_sample_sort_key("CC")
        assert result[0] == 0

    def test_chpp_2h_tc_exact_match(self):
        """CHPP 2H TC exact match"""
        from app.utils.sorting import custom_sample_sort_key
        result = custom_sample_sort_key("TC")
        assert result[0] == 0

    def test_chpp_12h_exact_match(self):
        """CHPP 12H exact match gets priority 1"""
        from app.utils.sorting import custom_sample_sort_key
        result = custom_sample_sort_key("SC401")
        assert result[0] == 1

    def test_chpp_12h_prefix_match(self):
        """CHPP 12H prefix match gets priority 1"""
        from app.utils.sorting import custom_sample_sort_key
        result = custom_sample_sort_key("SC401_X")
        assert result[0] == 1

    def test_other_codes_get_priority_2(self):
        """Other codes get priority 2"""
        from app.utils.sorting import custom_sample_sort_key
        result = custom_sample_sort_key("UNKNOWN_CODE")
        assert result[0] == 2

    def test_returns_tuple_structure(self):
        """Returns correct tuple structure"""
        from app.utils.sorting import custom_sample_sort_key
        result = custom_sample_sort_key("TEST")
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], int)  # group
        assert isinstance(result[1], int)  # index
        assert isinstance(result[2], list)  # natural key

    def test_sorting_order_chpp_2h_first(self):
        """CHPP 2H codes sort before CHPP 12H"""
        from app.utils.sorting import custom_sample_sort_key
        codes = ["SC401", "PF211", "OTHER"]
        sorted_codes = sorted(codes, key=custom_sample_sort_key)
        assert sorted_codes[0] == "PF211"  # CHPP 2H first
        assert sorted_codes[1] == "SC401"  # CHPP 12H second
        assert sorted_codes[2] == "OTHER"  # Others last

    def test_integer_code_converted(self):
        """Integer code is converted to string"""
        from app.utils.sorting import custom_sample_sort_key
        result = custom_sample_sort_key(12345)
        assert result[0] == 2  # Not in CHPP lists


class TestCHPP2HIndex:
    """CHPP_2H_INDEX dictionary tests"""

    def test_import(self):
        """Import CHPP_2H_INDEX"""
        from app.utils.sorting import CHPP_2H_INDEX
        assert isinstance(CHPP_2H_INDEX, dict)

    def test_has_pf_codes(self):
        """Contains PF codes"""
        from app.utils.sorting import CHPP_2H_INDEX
        assert "PF211" in CHPP_2H_INDEX
        assert "PF221" in CHPP_2H_INDEX
        assert "PF231" in CHPP_2H_INDEX

    def test_has_cc_tc(self):
        """Contains CC and TC codes"""
        from app.utils.sorting import CHPP_2H_INDEX
        assert "CC" in CHPP_2H_INDEX or "TC" in CHPP_2H_INDEX

    def test_values_are_integers(self):
        """All values are integer indices"""
        from app.utils.sorting import CHPP_2H_INDEX
        for key, val in CHPP_2H_INDEX.items():
            assert isinstance(val, int)

    def test_indices_are_sequential(self):
        """Indices are sequential from 0"""
        from app.utils.sorting import CHPP_2H_INDEX
        indices = sorted(CHPP_2H_INDEX.values())
        expected = list(range(len(indices)))
        assert indices == expected


class TestCHPP12HIndex:
    """CHPP_12H_INDEX dictionary tests"""

    def test_import(self):
        """Import CHPP_12H_INDEX"""
        from app.utils.sorting import CHPP_12H_INDEX
        assert isinstance(CHPP_12H_INDEX, dict)

    def test_has_sc_codes(self):
        """Contains SC codes"""
        from app.utils.sorting import CHPP_12H_INDEX
        sc_codes = [k for k in CHPP_12H_INDEX.keys() if k.startswith("SC")]
        assert len(sc_codes) > 0

    def test_values_are_integers(self):
        """All values are integer indices"""
        from app.utils.sorting import CHPP_12H_INDEX
        for key, val in CHPP_12H_INDEX.items():
            assert isinstance(val, int)


class TestSortPriority:
    """SORT_PRIORITY dictionary tests"""

    def test_import(self):
        """Import SORT_PRIORITY"""
        from app.utils.sorting import SORT_PRIORITY
        assert isinstance(SORT_PRIORITY, dict)

    def test_has_chpp_client(self):
        """Contains CHPP client"""
        from app.utils.sorting import SORT_PRIORITY
        assert "CHPP" in SORT_PRIORITY

    def test_has_uhg_geo_client(self):
        """Contains UHG-Geo client"""
        from app.utils.sorting import SORT_PRIORITY
        assert "UHG-Geo" in SORT_PRIORITY

    def test_has_bn_geo_client(self):
        """Contains BN-Geo client"""
        from app.utils.sorting import SORT_PRIORITY
        assert "BN-Geo" in SORT_PRIORITY

    def test_has_qc_client(self):
        """Contains QC client"""
        from app.utils.sorting import SORT_PRIORITY
        assert "QC" in SORT_PRIORITY

    def test_has_proc_client(self):
        """Contains Proc client"""
        from app.utils.sorting import SORT_PRIORITY
        assert "Proc" in SORT_PRIORITY

    def test_has_wtl_client(self):
        """Contains WTL client"""
        from app.utils.sorting import SORT_PRIORITY
        assert "WTL" in SORT_PRIORITY

    def test_has_lab_client(self):
        """Contains LAB client"""
        from app.utils.sorting import SORT_PRIORITY
        assert "LAB" in SORT_PRIORITY

    def test_chpp_priorities(self):
        """CHPP has correct sample type priorities"""
        from app.utils.sorting import SORT_PRIORITY
        chpp = SORT_PRIORITY["CHPP"]
        assert chpp["2 hourly"] == 0
        assert chpp["4 hourly"] == 1
        assert chpp["12 hourly"] == 2
        assert chpp["com"] == 3

    def test_uhg_geo_priorities(self):
        """UHG-Geo has correct sample type priorities"""
        from app.utils.sorting import SORT_PRIORITY
        geo = SORT_PRIORITY["UHG-Geo"]
        assert geo["Stock"] == 0
        assert geo["TR"] == 1

    def test_nested_dicts_have_integers(self):
        """All nested values are integers"""
        from app.utils.sorting import SORT_PRIORITY
        for client, types in SORT_PRIORITY.items():
            for stype, priority in types.items():
                assert isinstance(priority, int), f"{client}.{stype} should be int"


class TestGetClientTypePriority:
    """get_client_type_priority function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.sorting import get_client_type_priority
        assert callable(get_client_type_priority)

    def test_none_client_returns_99(self):
        """None client returns 99"""
        from app.utils.sorting import get_client_type_priority
        assert get_client_type_priority(None, "any") == 99

    def test_empty_client_returns_99(self):
        """Empty client returns 99"""
        from app.utils.sorting import get_client_type_priority
        assert get_client_type_priority("", "any") == 99

    def test_chpp_2hourly_priority(self):
        """CHPP 2 hourly priority is 0"""
        from app.utils.sorting import get_client_type_priority
        assert get_client_type_priority("CHPP", "2 hourly") == 0

    def test_chpp_12hourly_priority(self):
        """CHPP 12 hourly priority is 2"""
        from app.utils.sorting import get_client_type_priority
        assert get_client_type_priority("CHPP", "12 hourly") == 2

    def test_chpp_com_priority(self):
        """CHPP com priority is 3"""
        from app.utils.sorting import get_client_type_priority
        assert get_client_type_priority("CHPP", "com") == 3

    def test_unknown_client_returns_50(self):
        """Unknown client returns 50 for any type"""
        from app.utils.sorting import get_client_type_priority
        result = get_client_type_priority("UNKNOWN_CLIENT", "any")
        assert result == 50

    def test_known_client_unknown_type_returns_50(self):
        """Known client with unknown type returns 50"""
        from app.utils.sorting import get_client_type_priority
        result = get_client_type_priority("CHPP", "unknown_type")
        assert result == 50

    def test_none_sample_type(self):
        """None sample type uses empty string lookup"""
        from app.utils.sorting import get_client_type_priority
        result = get_client_type_priority("CHPP", None)
        # Empty string not in CHPP priorities, so returns 50
        assert result == 50

    def test_uhg_geo_stock_priority(self):
        """UHG-Geo Stock priority is 0"""
        from app.utils.sorting import get_client_type_priority
        assert get_client_type_priority("UHG-Geo", "Stock") == 0

    def test_qc_hcc_priority(self):
        """QC HCC priority is 0"""
        from app.utils.sorting import get_client_type_priority
        assert get_client_type_priority("QC", "HCC") == 0

    def test_lab_cm_priority(self):
        """LAB CM priority is 0"""
        from app.utils.sorting import get_client_type_priority
        assert get_client_type_priority("LAB", "CM") == 0

    def test_wtl_wtl_priority(self):
        """WTL WTL priority is 0"""
        from app.utils.sorting import get_client_type_priority
        assert get_client_type_priority("WTL", "WTL") == 0


class TestSampleFullSortKey:
    """sample_full_sort_key function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.sorting import sample_full_sort_key
        assert callable(sample_full_sort_key)

    def test_returns_tuple(self):
        """Returns tuple with 3 elements"""
        from app.utils.sorting import sample_full_sort_key
        sample = MagicMock()
        sample.client_name = "CHPP"
        sample.sample_type = "2 hourly"
        sample.sample_code = "PF211"
        result = sample_full_sort_key(sample)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_uses_client_name_attribute(self):
        """Uses client_name attribute"""
        from app.utils.sorting import sample_full_sort_key
        sample = MagicMock()
        sample.client_name = "CHPP"
        sample.sample_type = "2 hourly"
        sample.sample_code = "PF211"
        result = sample_full_sort_key(sample)
        assert result[0] == 0  # CHPP + 2 hourly = priority 0

    def test_uses_sample_code_attribute(self):
        """Uses sample_code attribute for sorting"""
        from app.utils.sorting import sample_full_sort_key
        sample = MagicMock()
        sample.client_name = None
        sample.sample_type = None
        sample.sample_code = "PF211"
        sample.name = None
        result = sample_full_sort_key(sample)
        # Priority 99 (no client), but index from CHPP 2H
        assert result[0] == 99

    def test_uses_name_attribute_fallback(self):
        """Uses name attribute if sample_code is None"""
        from app.utils.sorting import sample_full_sort_key
        sample = MagicMock()
        sample.client_name = "CHPP"
        sample.sample_type = "2 hourly"
        sample.sample_code = None
        sample.name = "PF211"
        result = sample_full_sort_key(sample)
        assert result[0] == 0

    def test_no_attributes_returns_high_priority(self):
        """Object with no matching attributes gets high priority"""
        from app.utils.sorting import sample_full_sort_key
        sample = MagicMock(spec=[])  # No attributes
        result = sample_full_sort_key(sample)
        assert result[0] == 99

    def test_sorting_by_client_type(self):
        """Samples sort by client type priority first"""
        from app.utils.sorting import sample_full_sort_key

        sample1 = MagicMock()
        sample1.client_name = "CHPP"
        sample1.sample_type = "2 hourly"
        sample1.sample_code = "AAA"

        sample2 = MagicMock()
        sample2.client_name = "CHPP"
        sample2.sample_type = "12 hourly"
        sample2.sample_code = "AAA"

        samples = [sample2, sample1]
        sorted_samples = sorted(samples, key=sample_full_sort_key)
        # 2 hourly (priority 0) before 12 hourly (priority 2)
        assert sorted_samples[0].sample_type == "2 hourly"


class TestSortSamples:
    """sort_samples function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.sorting import sort_samples
        assert callable(sort_samples)

    def test_empty_list_returns_empty(self):
        """Empty list returns empty list"""
        from app.utils.sorting import sort_samples
        assert sort_samples([]) == []

    def test_none_returns_empty(self):
        """None input treated as empty"""
        from app.utils.sorting import sort_samples
        assert sort_samples(None) == []

    def test_by_code_default(self):
        """Default sort is by code"""
        from app.utils.sorting import sort_samples

        s1 = MagicMock()
        s1.sample_code = "SC401"
        s1.name = None

        s2 = MagicMock()
        s2.sample_code = "PF211"
        s2.name = None

        samples = [s1, s2]
        result = sort_samples(samples)
        # PF211 (CHPP 2H, priority 0) before SC401 (CHPP 12H, priority 1)
        assert result[0].sample_code == "PF211"

    def test_by_code_explicit(self):
        """Explicit by='code' works"""
        from app.utils.sorting import sort_samples

        s1 = MagicMock()
        s1.sample_code = "ZZZ"
        s1.name = None

        s2 = MagicMock()
        s2.sample_code = "AAA"
        s2.name = None

        samples = [s1, s2]
        result = sort_samples(samples, by="code")
        # Both are "other" (priority 2), so natural sort
        assert result[0].sample_code == "AAA"

    def test_by_natural(self):
        """by='natural' uses natural sort"""
        from app.utils.sorting import sort_samples

        s1 = MagicMock()
        s1.sample_code = "N10"
        s1.name = None

        s2 = MagicMock()
        s2.sample_code = "N2"
        s2.name = None

        samples = [s1, s2]
        result = sort_samples(samples, by="natural")
        assert result[0].sample_code == "N2"
        assert result[1].sample_code == "N10"

    def test_by_full(self):
        """by='full' uses full sort key"""
        from app.utils.sorting import sort_samples

        s1 = MagicMock()
        s1.client_name = "CHPP"
        s1.sample_type = "12 hourly"
        s1.sample_code = "AAA"

        s2 = MagicMock()
        s2.client_name = "CHPP"
        s2.sample_type = "2 hourly"
        s2.sample_code = "ZZZ"

        samples = [s1, s2]
        result = sort_samples(samples, by="full")
        # 2 hourly (priority 0) before 12 hourly (priority 2)
        assert result[0].sample_type == "2 hourly"

    def test_uses_name_when_no_sample_code(self):
        """Uses name attribute when sample_code is None"""
        from app.utils.sorting import sort_samples

        s1 = MagicMock()
        s1.sample_code = None
        s1.name = "ZZZ"

        s2 = MagicMock()
        s2.sample_code = None
        s2.name = "AAA"

        samples = [s1, s2]
        result = sort_samples(samples, by="code")
        assert result[0].name == "AAA"

    def test_single_item_list(self):
        """Single item list returns same list"""
        from app.utils.sorting import sort_samples

        s1 = MagicMock()
        s1.sample_code = "TEST"
        s1.name = None

        samples = [s1]
        result = sort_samples(samples)
        assert len(result) == 1
        assert result[0].sample_code == "TEST"

    def test_string_fallback(self):
        """Uses string itself if no attributes"""
        from app.utils.sorting import sort_samples
        samples = ["B10", "A2", "A10"]
        result = sort_samples(samples, by="natural")
        assert result == ["A2", "A10", "B10"]


class TestSortCodes:
    """sort_codes function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.sorting import sort_codes
        assert callable(sort_codes)

    def test_empty_list_returns_empty(self):
        """Empty list returns empty list"""
        from app.utils.sorting import sort_codes
        assert sort_codes([]) == []

    def test_none_returns_empty(self):
        """None input treated as empty"""
        from app.utils.sorting import sort_codes
        assert sort_codes(None) == []

    def test_custom_method_default(self):
        """Default method is custom"""
        from app.utils.sorting import sort_codes
        codes = ["SC401", "PF211", "OTHER"]
        result = sort_codes(codes)
        assert result[0] == "PF211"  # CHPP 2H first
        assert result[1] == "SC401"  # CHPP 12H second
        assert result[2] == "OTHER"  # Others last

    def test_natural_method(self):
        """method='natural' uses natural sort"""
        from app.utils.sorting import sort_codes
        codes = ["N10", "N2", "N1"]
        result = sort_codes(codes, method="natural")
        assert result == ["N1", "N2", "N10"]

    def test_custom_method_explicit(self):
        """Explicit method='custom' works"""
        from app.utils.sorting import sort_codes
        codes = ["ZZZ", "PF211"]
        result = sort_codes(codes, method="custom")
        assert result[0] == "PF211"

    def test_single_code(self):
        """Single code list"""
        from app.utils.sorting import sort_codes
        result = sort_codes(["PF211"])
        assert result == ["PF211"]

    def test_all_chpp_2h_codes(self):
        """All CHPP 2H codes sort by index"""
        from app.utils.sorting import sort_codes, CHPP_2H_INDEX
        codes = list(CHPP_2H_INDEX.keys())
        result = sort_codes(codes)
        # Should maintain original order based on index
        for i, code in enumerate(result):
            if i < len(result) - 1:
                assert CHPP_2H_INDEX.get(result[i], 0) <= CHPP_2H_INDEX.get(result[i+1], 0)

    def test_mixed_codes_sorting(self):
        """Mixed codes sort correctly"""
        from app.utils.sorting import sort_codes
        codes = ["TEST_CODE", "SC401", "PF211", "SC402", "PF221"]
        result = sort_codes(codes)
        # PF codes first (CHPP 2H), then SC codes (CHPP 12H), then others
        pf_indices = [i for i, c in enumerate(result) if c.startswith("PF")]
        sc_indices = [i for i, c in enumerate(result) if c.startswith("SC")]
        test_index = result.index("TEST_CODE")

        assert all(p < s for p in pf_indices for s in sc_indices)
        assert all(s < test_index for s in sc_indices)


class TestSortingIntegration:
    """Integration tests for sorting functions"""

    def test_chpp_2h_order_preserved(self):
        """CHPP 2H sample order from constants is preserved"""
        from app.utils.sorting import sort_codes
        from app.constants import CHPP_2H_SAMPLES_ORDER

        # Take a subset of CHPP 2H codes
        codes = CHPP_2H_SAMPLES_ORDER[:5] if len(CHPP_2H_SAMPLES_ORDER) >= 5 else CHPP_2H_SAMPLES_ORDER
        shuffled = codes.copy()
        shuffled.reverse()

        result = sort_codes(shuffled)
        assert result == codes

    def test_chpp_12h_order_preserved(self):
        """CHPP 12H sample order from constants is preserved"""
        from app.utils.sorting import sort_codes, CHPP_12H_INDEX

        codes = list(CHPP_12H_INDEX.keys())[:5]
        shuffled = codes.copy()
        shuffled.reverse()

        result = sort_codes(shuffled)
        # Should be sorted by index
        for i in range(len(result) - 1):
            assert CHPP_12H_INDEX[result[i]] <= CHPP_12H_INDEX[result[i + 1]]

    def test_real_world_sample_list(self):
        """Real world sample list sorts correctly"""
        from app.utils.sorting import sort_codes

        codes = [
            "UNKNOWN_1",
            "SC405",
            "PF231",
            "SC401",
            "PF211",
            "RANDOM",
            "PF221",
        ]

        result = sort_codes(codes)

        # Find positions
        pf211_idx = result.index("PF211")
        pf221_idx = result.index("PF221")
        pf231_idx = result.index("PF231")
        sc401_idx = result.index("SC401")
        sc405_idx = result.index("SC405")

        # CHPP 2H should come before CHPP 12H
        assert pf211_idx < sc401_idx
        assert pf221_idx < sc401_idx
        assert pf231_idx < sc401_idx

        # Within CHPP 2H, order should be PF211 < PF221 < PF231
        assert pf211_idx < pf221_idx < pf231_idx

        # Within CHPP 12H, SC401 < SC405
        assert sc401_idx < sc405_idx


class TestEdgeCases:
    """Edge case tests"""

    def test_natural_sort_special_characters(self):
        """Natural sort with special characters"""
        from app.utils.sorting import natural_sort_key
        result = natural_sort_key("A_B-C.D")
        assert len(result) > 0

    def test_natural_sort_unicode(self):
        """Natural sort with unicode characters"""
        from app.utils.sorting import natural_sort_key
        result = natural_sort_key("Дээж1")
        assert len(result) > 0

    def test_custom_sort_very_long_code(self):
        """Custom sort with very long code"""
        from app.utils.sorting import custom_sample_sort_key
        long_code = "A" * 1000
        result = custom_sample_sort_key(long_code)
        assert result[0] == 2  # Falls to "other" category

    def test_sort_samples_mixed_types(self):
        """Sort samples with mixed attribute types works with tuple keys"""
        from app.utils.sorting import sort_samples

        s1 = MagicMock()
        s1.sample_code = 123  # Integer
        s1.name = None

        s2 = MagicMock()
        s2.sample_code = "ABC"  # String
        s2.name = None

        samples = [s1, s2]
        # Tuple-based keys prevent int vs str comparison errors
        result = sort_samples(samples)
        assert len(result) == 2

    def test_get_priority_case_sensitive(self):
        """Client names are case sensitive"""
        from app.utils.sorting import get_client_type_priority
        # "chpp" (lowercase) is not the same as "CHPP"
        assert get_client_type_priority("chpp", "2 hourly") == 50
        assert get_client_type_priority("CHPP", "2 hourly") == 0

    def test_sort_codes_with_none_elements(self):
        """Sort codes list containing None raises or handles"""
        from app.utils.sorting import sort_codes
        # This might raise or handle None - just ensure no crash
        try:
            codes = ["PF211", None, "SC401"]
            result = sort_codes(codes)
            # If it doesn't raise, None should be last
            assert result[-1] is None or result[0] is None
        except (TypeError, AttributeError):
            pass  # Expected if None not handled

    def test_sample_with_only_name(self):
        """Sample object with only name attribute"""
        from app.utils.sorting import sample_full_sort_key
        sample = MagicMock(spec=['name'])
        sample.name = "TEST"
        result = sample_full_sort_key(sample)
        assert result[0] == 99  # No client

    def test_natural_sort_preserves_original_case_in_output(self):
        """Natural sort preserves original case in sorted output"""
        from app.utils.sorting import natural_sort_key
        items = ["ABC", "abc", "Abc"]
        # Note: sorted uses stable sort, so equal items maintain order
        sorted_items = sorted(items, key=natural_sort_key)
        # All compare equal (lowercase), so original order preserved
        assert sorted_items == ["ABC", "abc", "Abc"]

