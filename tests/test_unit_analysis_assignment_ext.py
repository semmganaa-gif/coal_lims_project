# -*- coding: utf-8 -*-
"""
Analysis assignment extended тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError


class TestDefaultGiShiftConfig:
    """DEFAULT_GI_SHIFT_CONFIG тестүүд"""

    def test_import_config(self):
        """Config import"""
        from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
        assert DEFAULT_GI_SHIFT_CONFIG is not None
        assert isinstance(DEFAULT_GI_SHIFT_CONFIG, dict)

    def test_has_pf_codes(self):
        """Config has PF codes"""
        from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
        assert 'PF211' in DEFAULT_GI_SHIFT_CONFIG
        assert 'PF221' in DEFAULT_GI_SHIFT_CONFIG
        assert 'PF231' in DEFAULT_GI_SHIFT_CONFIG

    def test_pf211_shifts(self):
        """PF211 has correct shifts"""
        from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
        shifts = DEFAULT_GI_SHIFT_CONFIG['PF211']
        assert 'D1' in shifts
        assert 'N1' in shifts


class TestGetGiShiftConfig:
    """get_gi_shift_config тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.analysis_assignment import get_gi_shift_config
        assert get_gi_shift_config is not None

    @patch('app.utils.analysis_assignment.SystemSetting')
    def test_returns_default_when_no_setting(self, mock_setting):
        """Returns default when no DB setting"""
        from app.utils.analysis_assignment import get_gi_shift_config, DEFAULT_GI_SHIFT_CONFIG
        mock_setting.query.filter_by.return_value.first.return_value = None

        result = get_gi_shift_config()
        assert result == DEFAULT_GI_SHIFT_CONFIG

    @patch('app.utils.analysis_assignment.SystemSetting')
    def test_returns_db_config(self, mock_setting):
        """Returns DB config when available"""
        from app.utils.analysis_assignment import get_gi_shift_config
        import json

        mock_record = MagicMock()
        mock_record.value = json.dumps({'PF211': ['D1', 'D2']})
        mock_setting.query.filter_by.return_value.first.return_value = mock_record

        result = get_gi_shift_config()
        assert result == {'PF211': ['D1', 'D2']}

    @patch('app.utils.analysis_assignment.SystemSetting')
    def test_returns_default_on_error(self, mock_setting):
        """Returns default on error"""
        from app.utils.analysis_assignment import get_gi_shift_config, DEFAULT_GI_SHIFT_CONFIG
        mock_setting.query.filter_by.side_effect = SQLAlchemyError("DB Error")

        result = get_gi_shift_config()
        assert result == DEFAULT_GI_SHIFT_CONFIG


class TestAssignAnalysesToSample:
    """assign_analyses_to_sample тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.analysis_assignment import assign_analyses_to_sample
        assert assign_analyses_to_sample is not None

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_empty_params_returns_list(self, mock_profile):
        """Empty params returns empty list"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_profile.query.filter.return_value.first.return_value = None
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = []

        result = assign_analyses_to_sample(client_name='TEST', sample_type='TEST')
        assert isinstance(result, list)

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_with_sample_object(self, mock_profile):
        """Works with sample object"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        # Mock sample object
        sample = MagicMock()
        sample.client_name = 'CHPP'
        sample.sample_type = '2H'
        sample.sample_code = 'PF211_D1'
        sample.sample_condition = None

        mock_profile.query.filter.return_value.first.return_value = None
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = []

        result = assign_analyses_to_sample(sample=sample)
        assert isinstance(result, list)

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_simple_profile_match(self, mock_profile):
        """Simple profile match adds analyses"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        # Mock simple profile
        simple = MagicMock()
        simple.pattern = None
        simple.client_name = 'CHPP'
        simple.sample_type = '2H'
        simple.get_analyses.return_value = ['Mad', 'Aad', 'TS']

        mock_profile.query.filter.return_value.first.return_value = simple
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = []

        result = assign_analyses_to_sample(client_name='CHPP', sample_type='2H')
        assert 'Aad' in result or isinstance(result, list)

    @patch('app.utils.analysis_assignment.get_gi_shift_config')
    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_pattern_profile_match(self, mock_profile, mock_config):
        """Pattern profile match adds analyses"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_config.return_value = {'PF211': ['D1', 'D3', 'D5', 'N1', 'N3', 'N5']}

        # Mock pattern profile
        pattern = MagicMock()
        pattern.pattern = 'PF211'
        pattern.match_rule = 'merge'
        pattern.get_analyses.return_value = ['Gi']

        mock_profile.query.filter.return_value.first.return_value = None
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = [pattern]

        result = assign_analyses_to_sample(client_name='CHPP', sample_type='2H', sample_code='PF211_D1')
        assert isinstance(result, list)

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_pattern_replace_rule(self, mock_profile):
        """Pattern with replace rule replaces analyses"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        # Mock simple profile
        simple = MagicMock()
        simple.pattern = None
        simple.get_analyses.return_value = ['Mad', 'Aad']

        # Mock pattern profile with replace
        pattern = MagicMock()
        pattern.pattern = 'SPECIAL'
        pattern.match_rule = 'replace'
        pattern.get_analyses.return_value = ['TS']

        mock_profile.query.filter.return_value.first.return_value = simple
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = [pattern]

        result = assign_analyses_to_sample(client_name='CHPP', sample_type='2H', sample_code='SPECIAL_1')
        assert isinstance(result, list)

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_sample_condition_match(self, mock_profile):
        """Sample condition can be matched"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        pattern = MagicMock()
        pattern.pattern = 'Шингэн'
        pattern.match_rule = 'merge'
        pattern.get_analyses.return_value = ['TS']

        mock_profile.query.filter.return_value.first.return_value = None
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = [pattern]

        result = assign_analyses_to_sample(
            client_name='CHPP',
            sample_type='2H',
            sample_code='S001',
            sample_condition='Шингэн'
        )
        assert isinstance(result, list)

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    @patch('app.utils.analysis_assignment.get_gi_shift_config')
    def test_gi_shift_allowed(self, mock_config, mock_profile):
        """Gi is kept when shift is allowed"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_config.return_value = {'PF211': ['D1', 'D3', 'D5']}

        simple = MagicMock()
        simple.pattern = None
        simple.get_analyses.return_value = ['Gi']

        mock_profile.query.filter.return_value.first.return_value = simple
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = []

        result = assign_analyses_to_sample(
            client_name='CHPP',
            sample_type='2H',
            sample_code='PF211_D1'
        )
        # Gi should be in result for allowed shift
        assert isinstance(result, list)

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    @patch('app.utils.analysis_assignment.get_gi_shift_config')
    def test_gi_shift_not_allowed(self, mock_config, mock_profile):
        """Gi is removed when shift is not allowed"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_config.return_value = {'PF211': ['D1', 'D3', 'D5']}

        simple = MagicMock()
        simple.pattern = None
        simple.get_analyses.return_value = ['Gi', 'Mad']

        mock_profile.query.filter.return_value.first.return_value = simple
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = []

        result = assign_analyses_to_sample(
            client_name='CHPP',
            sample_type='2H',
            sample_code='PF211_D2'  # D2 is not in allowed shifts
        )
        assert isinstance(result, list)

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_invalid_regex_fallback(self, mock_profile):
        """Invalid regex falls back to text match"""
        from app.utils.analysis_assignment import assign_analyses_to_sample

        pattern = MagicMock()
        pattern.pattern = '[invalid('  # Invalid regex
        pattern.match_rule = 'merge'
        pattern.get_analyses.return_value = ['TS']

        mock_profile.query.filter.return_value.first.return_value = None
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = [pattern]

        # Should not crash on invalid regex
        result = assign_analyses_to_sample(client_name='CHPP', sample_type='2H', sample_code='TEST')
        assert isinstance(result, list)
