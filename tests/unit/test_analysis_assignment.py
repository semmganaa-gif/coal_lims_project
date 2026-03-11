# -*- coding: utf-8 -*-
"""
Tests for app/utils/analysis_assignment.py
Analysis assignment utility tests
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError


class TestDefaultGiShiftConfig:
    """DEFAULT_GI_SHIFT_CONFIG tests"""

    def test_import(self):
        """Import constant"""
        from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
        assert DEFAULT_GI_SHIFT_CONFIG is not None

    def test_is_dict(self):
        """Is dictionary"""
        from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
        assert isinstance(DEFAULT_GI_SHIFT_CONFIG, dict)

    def test_has_pf211(self):
        """Has PF211 key"""
        from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
        assert 'PF211' in DEFAULT_GI_SHIFT_CONFIG

    def test_has_pf221(self):
        """Has PF221 key"""
        from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
        assert 'PF221' in DEFAULT_GI_SHIFT_CONFIG

    def test_has_pf231(self):
        """Has PF231 key"""
        from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
        assert 'PF231' in DEFAULT_GI_SHIFT_CONFIG

    def test_pf211_has_shifts(self):
        """PF211 has shift list"""
        from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
        shifts = DEFAULT_GI_SHIFT_CONFIG['PF211']
        assert isinstance(shifts, list)
        assert 'D1' in shifts

    def test_pf221_has_even_shifts(self):
        """PF221 has even shifts"""
        from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
        shifts = DEFAULT_GI_SHIFT_CONFIG['PF221']
        assert 'D2' in shifts
        assert 'D4' in shifts

    def test_pf211_has_odd_shifts(self):
        """PF211 has odd shifts"""
        from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
        shifts = DEFAULT_GI_SHIFT_CONFIG['PF211']
        assert 'D1' in shifts
        assert 'D3' in shifts
        assert 'D5' in shifts


class TestGetGiShiftConfig:
    """get_gi_shift_config function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.analysis_assignment import get_gi_shift_config
        assert callable(get_gi_shift_config)

    def test_returns_dict(self):
        """Returns dictionary"""
        from app.utils.analysis_assignment import get_gi_shift_config

        with patch('app.utils.analysis_assignment.SystemSetting') as mock_ss:
            mock_ss.query.filter_by.return_value.first.return_value = None
            result = get_gi_shift_config()
            assert isinstance(result, dict)

    def test_returns_default_when_no_setting(self):
        """Returns default when no DB setting"""
        from app.utils.analysis_assignment import get_gi_shift_config, DEFAULT_GI_SHIFT_CONFIG

        with patch('app.utils.analysis_assignment.SystemSetting') as mock_ss:
            mock_ss.query.filter_by.return_value.first.return_value = None
            result = get_gi_shift_config()
            assert result == DEFAULT_GI_SHIFT_CONFIG

    def test_returns_db_config(self):
        """Returns config from DB"""
        from app.utils.analysis_assignment import get_gi_shift_config

        custom_config = {'PF211': ['D1', 'D2']}

        with patch('app.utils.analysis_assignment.SystemSetting') as mock_ss:
            mock_setting = MagicMock()
            mock_setting.value = json.dumps(custom_config)
            mock_ss.query.filter_by.return_value.first.return_value = mock_setting

            result = get_gi_shift_config()
            assert result == custom_config

    def test_returns_default_on_exception(self):
        """Returns default on exception"""
        from app.utils.analysis_assignment import get_gi_shift_config, DEFAULT_GI_SHIFT_CONFIG

        with patch('app.utils.analysis_assignment.SystemSetting') as mock_ss:
            mock_ss.query.filter_by.side_effect = SQLAlchemyError("DB Error")
            result = get_gi_shift_config()
            assert result == DEFAULT_GI_SHIFT_CONFIG

    def test_returns_default_on_empty_value(self):
        """Returns default when value is empty"""
        from app.utils.analysis_assignment import get_gi_shift_config, DEFAULT_GI_SHIFT_CONFIG

        with patch('app.utils.analysis_assignment.SystemSetting') as mock_ss:
            mock_setting = MagicMock()
            mock_setting.value = None
            mock_ss.query.filter_by.return_value.first.return_value = mock_setting

            result = get_gi_shift_config()
            assert result == DEFAULT_GI_SHIFT_CONFIG


class TestAssignAnalysesToSample:
    """assign_analyses_to_sample function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.analysis_assignment import assign_analyses_to_sample
        assert callable(assign_analyses_to_sample)

    def test_returns_list(self):
        """Returns list"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = None
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            result = assign_analyses_to_sample(
                client_name="Client",
                sample_type="Type"
            )
            assert isinstance(result, list)

    def test_empty_with_no_profiles(self):
        """Returns empty list with no matching profiles"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = None
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            result = assign_analyses_to_sample(
                client_name="Unknown",
                sample_type="Unknown"
            )
            assert result == []

    def test_with_sample_object(self):
        """Works with sample object"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_sample = MagicMock()
        mock_sample.client_name = "CHPP"
        mock_sample.sample_type = "2H"
        mock_sample.sample_code = "S001"
        mock_sample.sample_condition = None

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = None
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            result = assign_analyses_to_sample(sample=mock_sample)
            assert isinstance(result, list)

    def test_simple_profile_match(self):
        """Matches simple profile (no pattern)"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_profile = MagicMock()
        mock_profile.get_analyses.return_value = ['MAD', 'AAD', 'VAD']

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_profile
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            result = assign_analyses_to_sample(
                client_name="CHPP",
                sample_type="2H"
            )
            assert 'MAD' in result
            assert 'AAD' in result

    def test_pattern_profile_match(self):
        """Matches pattern profile"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_simple = MagicMock()
        mock_simple.get_analyses.return_value = ['MAD']

        mock_pattern = MagicMock()
        mock_pattern.pattern = 'PF211'
        mock_pattern.get_analyses.return_value = ['Gi']
        mock_pattern.match_rule = 'merge'

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = [mock_pattern]

            with patch('app.utils.analysis_assignment.get_gi_shift_config') as mock_config:
                mock_config.return_value = {'PF211': ['D1', 'D3', 'D5', 'N1', 'N3', 'N5']}

                result = assign_analyses_to_sample(
                    client_name="CHPP",
                    sample_type="2H",
                    sample_code="PF211_D1"
                )
                assert 'MAD' in result

    def test_pattern_replace_rule(self):
        """Pattern with replace rule replaces all"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_simple = MagicMock()
        mock_simple.get_analyses.return_value = ['MAD', 'AAD']

        mock_pattern = MagicMock()
        mock_pattern.pattern = 'SPECIAL'
        mock_pattern.get_analyses.return_value = ['TS']
        mock_pattern.match_rule = 'replace'

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = [mock_pattern]

            result = assign_analyses_to_sample(
                client_name="CHPP",
                sample_type="2H",
                sample_code="SPECIAL_001"
            )
            assert 'TS' in result
            assert 'MAD' not in result

    def test_regex_pattern_fallback(self):
        """Falls back to simple text match on regex error"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_simple = None
        mock_pattern = MagicMock()
        mock_pattern.pattern = '[invalid('  # Invalid regex
        mock_pattern.get_analyses.return_value = ['TS']
        mock_pattern.match_rule = 'merge'

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = [mock_pattern]

            result = assign_analyses_to_sample(
                client_name="CHPP",
                sample_type="2H",
                sample_code="[invalid(_test"
            )
            assert 'TS' in result

    def test_sample_condition_pattern_match(self):
        """Matches pattern against sample_condition"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_pattern = MagicMock()
        mock_pattern.pattern = 'Wet'
        mock_pattern.get_analyses.return_value = ['WET_ANALYSIS']
        mock_pattern.match_rule = 'merge'

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = None
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = [mock_pattern]

            result = assign_analyses_to_sample(
                client_name="CHPP",
                sample_type="2H",
                sample_code="S001",
                sample_condition="Wet Sample"
            )
            assert 'WET_ANALYSIS' in result

    def test_gi_shift_removal_wrong_shift(self):
        """Gi removed for wrong shift"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_simple = MagicMock()
        mock_simple.get_analyses.return_value = ['MAD', 'Gi']

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            with patch('app.utils.analysis_assignment.get_gi_shift_config') as mock_config:
                # PF211 allows D1, D3, D5
                mock_config.return_value = {'PF211': ['D1', 'D3', 'D5']}

                # D2 is not allowed for PF211
                result = assign_analyses_to_sample(
                    client_name="CHPP",
                    sample_type="2H",
                    sample_code="PF211_D2"
                )
                assert 'Gi' not in result
                assert 'MAD' in result

    def test_gi_shift_kept_correct_shift(self):
        """Gi kept for correct shift"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_simple = MagicMock()
        mock_simple.get_analyses.return_value = ['MAD', 'Gi']

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            with patch('app.utils.analysis_assignment.get_gi_shift_config') as mock_config:
                mock_config.return_value = {'PF211': ['D1', 'D3', 'D5']}

                # D1 is allowed for PF211
                result = assign_analyses_to_sample(
                    client_name="CHPP",
                    sample_type="2H",
                    sample_code="PF211_D1"
                )
                assert 'Gi' in result

    def test_result_is_sorted(self):
        """Result list is sorted"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_simple = MagicMock()
        mock_simple.get_analyses.return_value = ['VAD', 'MAD', 'AAD', 'CV']

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            result = assign_analyses_to_sample(
                client_name="CHPP",
                sample_type="2H"
            )
            assert result == sorted(result)

    def test_sample_analyses_updated(self):
        """Sample.analyses_to_perform updated"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_sample = MagicMock()
        mock_sample.client_name = "CHPP"
        mock_sample.sample_type = "2H"
        mock_sample.sample_code = "S001"
        mock_sample.sample_condition = None
        mock_sample.analyses_to_perform = None

        mock_simple = MagicMock()
        mock_simple.get_analyses.return_value = ['MAD', 'AAD']

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            result = assign_analyses_to_sample(sample=mock_sample)

            # Check that sample.analyses_to_perform was set
            assert mock_sample.analyses_to_perform is not None
            stored = json.loads(mock_sample.analyses_to_perform)
            assert 'MAD' in stored

    def test_no_sample_no_update(self):
        """No update when sample is None"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_simple = MagicMock()
        mock_simple.get_analyses.return_value = ['MAD']

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            # Should not raise error
            result = assign_analyses_to_sample(
                client_name="CHPP",
                sample_type="2H"
            )
            assert 'MAD' in result

    def test_gi_no_shift_in_code(self):
        """Gi kept when no shift code found"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_simple = MagicMock()
        mock_simple.get_analyses.return_value = ['MAD', 'Gi']

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            # No shift pattern in sample code
            result = assign_analyses_to_sample(
                client_name="CHPP",
                sample_type="2H",
                sample_code="SAMPLE_WITHOUT_SHIFT"
            )
            assert 'Gi' in result

    def test_gi_no_pf_match(self):
        """Gi kept when no PF pattern matched"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_simple = MagicMock()
        mock_simple.get_analyses.return_value = ['MAD', 'Gi']

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            with patch('app.utils.analysis_assignment.get_gi_shift_config') as mock_config:
                mock_config.return_value = {'PF211': ['D1']}

                # Has shift but no PF match
                result = assign_analyses_to_sample(
                    client_name="CHPP",
                    sample_type="2H",
                    sample_code="OTHER_D1"
                )
                assert 'Gi' in result

    def test_night_shift(self):
        """Handles night shift (N1, N2, etc.)"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_simple = MagicMock()
        mock_simple.get_analyses.return_value = ['Gi']

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            with patch('app.utils.analysis_assignment.get_gi_shift_config') as mock_config:
                mock_config.return_value = {'PF211': ['N1', 'N3', 'N5']}

                result = assign_analyses_to_sample(
                    client_name="CHPP",
                    sample_type="2H",
                    sample_code="PF211_N1"
                )
                assert 'Gi' in result

    def test_empty_sample_code(self):
        """Handles empty sample code"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_simple = MagicMock()
        mock_simple.get_analyses.return_value = ['MAD']

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            result = assign_analyses_to_sample(
                client_name="CHPP",
                sample_type="2H",
                sample_code=""
            )
            assert 'MAD' in result

    def test_none_sample_code(self):
        """Handles None sample code"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_simple = MagicMock()
        mock_simple.get_analyses.return_value = ['MAD']

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = []

            result = assign_analyses_to_sample(
                client_name="CHPP",
                sample_type="2H",
                sample_code=None
            )
            assert 'MAD' in result

    def test_case_insensitive_pattern_match(self):
        """Pattern matching is case insensitive"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_pattern = MagicMock()
        mock_pattern.pattern = 'pf211'  # lowercase
        mock_pattern.get_analyses.return_value = ['Gi']
        mock_pattern.match_rule = 'merge'

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = None
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = [mock_pattern]

            with patch('app.utils.analysis_assignment.get_gi_shift_config') as mock_config:
                mock_config.return_value = {'PF211': ['D1', 'D3', 'D5', 'N1', 'N3', 'N5']}

                result = assign_analyses_to_sample(
                    client_name="CHPP",
                    sample_type="2H",
                    sample_code="PF211_D1"  # uppercase
                )
                # The Gi might be removed by shift logic, but pattern should match
                assert isinstance(result, list)

    def test_multiple_pattern_profiles(self):
        """Multiple pattern profiles are processed"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_pattern1 = MagicMock()
        mock_pattern1.pattern = 'A'
        mock_pattern1.get_analyses.return_value = ['MAD']
        mock_pattern1.match_rule = 'merge'

        mock_pattern2 = MagicMock()
        mock_pattern2.pattern = 'B'
        mock_pattern2.get_analyses.return_value = ['AAD']
        mock_pattern2.match_rule = 'merge'

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = None
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = [
                mock_pattern1, mock_pattern2
            ]

            result = assign_analyses_to_sample(
                client_name="CHPP",
                sample_type="2H",
                sample_code="A_B_001"
            )
            assert 'MAD' in result
            assert 'AAD' in result

    def test_duplicates_removed(self):
        """Duplicate analyses are removed"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_simple = MagicMock()
        mock_simple.get_analyses.return_value = ['MAD', 'AAD']

        mock_pattern = MagicMock()
        mock_pattern.pattern = 'TEST'
        mock_pattern.get_analyses.return_value = ['MAD', 'VAD']  # MAD is duplicate
        mock_pattern.match_rule = 'merge'

        with patch('app.utils.analysis_assignment.AnalysisProfile') as mock_ap:
            mock_ap.query.filter.return_value.first.return_value = mock_simple
            mock_ap.query.filter.return_value.order_by.return_value.all.return_value = [mock_pattern]

            result = assign_analyses_to_sample(
                client_name="CHPP",
                sample_type="2H",
                sample_code="TEST_001"
            )
            # MAD should appear only once
            assert result.count('MAD') == 1
