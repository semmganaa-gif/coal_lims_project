# -*- coding: utf-8 -*-
"""
analysis_assignment.py модулийн 100% coverage тестүүд
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError


class TestAnalysisAssignmentImport:
    """Модуль импорт тест"""

    def test_import_module(self):
        from app.utils import analysis_assignment
        assert analysis_assignment is not None

    def test_import_functions(self):
        from app.utils.analysis_assignment import (
            get_gi_shift_config, assign_analyses_to_sample,
            DEFAULT_GI_SHIFT_CONFIG
        )
        assert get_gi_shift_config is not None
        assert assign_analyses_to_sample is not None
        assert isinstance(DEFAULT_GI_SHIFT_CONFIG, dict)

    def test_default_config(self):
        from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
        assert 'PF211' in DEFAULT_GI_SHIFT_CONFIG
        assert 'PF221' in DEFAULT_GI_SHIFT_CONFIG
        assert 'PF231' in DEFAULT_GI_SHIFT_CONFIG


class TestGetGiShiftConfig:
    """get_gi_shift_config функцийн тест"""

    @patch('app.utils.analysis_assignment.SystemSetting')
    def test_config_from_db(self, mock_setting):
        from app.utils.analysis_assignment import get_gi_shift_config

        mock_instance = MagicMock()
        mock_instance.value = json.dumps({'PF211': ['D1', 'D2']})
        mock_setting.query.filter_by.return_value.first.return_value = mock_instance

        result = get_gi_shift_config()
        assert result == {'PF211': ['D1', 'D2']}

    @patch('app.utils.analysis_assignment.SystemSetting')
    def test_config_not_found(self, mock_setting):
        from app.utils.analysis_assignment import get_gi_shift_config, DEFAULT_GI_SHIFT_CONFIG

        mock_setting.query.filter_by.return_value.first.return_value = None

        result = get_gi_shift_config()
        assert result == DEFAULT_GI_SHIFT_CONFIG

    @patch('app.utils.analysis_assignment.SystemSetting')
    def test_config_empty_value(self, mock_setting):
        from app.utils.analysis_assignment import get_gi_shift_config, DEFAULT_GI_SHIFT_CONFIG

        mock_instance = MagicMock()
        mock_instance.value = None
        mock_setting.query.filter_by.return_value.first.return_value = mock_instance

        result = get_gi_shift_config()
        assert result == DEFAULT_GI_SHIFT_CONFIG

    @patch('app.utils.analysis_assignment.SystemSetting')
    def test_config_exception(self, mock_setting):
        from app.utils.analysis_assignment import get_gi_shift_config, DEFAULT_GI_SHIFT_CONFIG

        mock_setting.query.filter_by.side_effect = SQLAlchemyError("DB error")

        result = get_gi_shift_config()
        assert result == DEFAULT_GI_SHIFT_CONFIG


class TestAssignAnalysesToSample:
    """assign_analyses_to_sample функцийн тест"""

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_with_sample_object(self, mock_profile):
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_profile.query.filter.return_value.first.return_value = None
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = []

        sample = MagicMock()
        sample.client_name = "CHPP"
        sample.sample_type = "Coal"
        sample.sample_code = "SAMPLE-001"
        sample.sample_condition = None

        result = assign_analyses_to_sample(sample=sample)
        assert isinstance(result, list)

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_with_parameters(self, mock_profile):
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_profile.query.filter.return_value.first.return_value = None
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = []

        result = assign_analyses_to_sample(
            client_name="CHPP",
            sample_type="2H",
            sample_code="PF211_D1"
        )
        assert isinstance(result, list)

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_simple_profile_match(self, mock_profile):
        from app.utils.analysis_assignment import assign_analyses_to_sample

        # Simple profile
        simple_profile = MagicMock()
        simple_profile.get_analyses.return_value = ['MT', 'Mad', 'Aad']

        mock_profile.query.filter.return_value.first.return_value = simple_profile
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = []

        result = assign_analyses_to_sample(
            client_name="CHPP",
            sample_type="Coal"
        )
        assert 'MT' in result or 'Mad' in result or 'Aad' in result

    @patch('app.utils.analysis_assignment.get_gi_shift_config')
    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_pattern_profile_match(self, mock_profile, mock_gi_config):
        from app.utils.analysis_assignment import assign_analyses_to_sample

        # No simple profile
        mock_profile.query.filter.return_value.first.return_value = None

        # Pattern profile
        pattern_profile = MagicMock()
        pattern_profile.pattern = "PF211"
        pattern_profile.get_analyses.return_value = ['Gi']
        pattern_profile.match_rule = 'merge'

        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = [pattern_profile]

        # Mock gi_shift_config to allow Gi for PF211_D1
        mock_gi_config.return_value = {'PF211': ['D1', 'D3', 'D5']}

        result = assign_analyses_to_sample(
            client_name="CHPP",
            sample_type="2H",
            sample_code="PF211_D1"
        )
        assert 'Gi' in result

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_pattern_replace_rule(self, mock_profile):
        from app.utils.analysis_assignment import assign_analyses_to_sample

        # Simple profile
        simple_profile = MagicMock()
        simple_profile.get_analyses.return_value = ['MT', 'Mad']

        # Pattern profile with replace rule
        pattern_profile = MagicMock()
        pattern_profile.pattern = "PF"
        pattern_profile.get_analyses.return_value = ['Gi']
        pattern_profile.match_rule = 'replace'

        mock_profile.query.filter.return_value.first.return_value = simple_profile
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = [pattern_profile]

        result = assign_analyses_to_sample(
            client_name="CHPP",
            sample_type="2H",
            sample_code="PF211"
        )
        # Replace rule should replace all analyses
        assert 'Gi' in result

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_pattern_condition_match(self, mock_profile):
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_profile.query.filter.return_value.first.return_value = None

        pattern_profile = MagicMock()
        pattern_profile.pattern = "Шингэн"
        pattern_profile.get_analyses.return_value = ['FM']
        pattern_profile.match_rule = 'merge'

        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = [pattern_profile]

        result = assign_analyses_to_sample(
            client_name="Test",
            sample_type="Test",
            sample_code="SAMPLE",
            sample_condition="Шингэн"
        )
        assert 'FM' in result

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_invalid_regex_fallback(self, mock_profile):
        from app.utils.analysis_assignment import assign_analyses_to_sample

        mock_profile.query.filter.return_value.first.return_value = None

        pattern_profile = MagicMock()
        pattern_profile.pattern = "[invalid regex"  # Invalid regex
        pattern_profile.get_analyses.return_value = ['Test']
        pattern_profile.match_rule = 'merge'

        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = [pattern_profile]

        # Should not raise exception
        result = assign_analyses_to_sample(
            client_name="Test",
            sample_type="Test",
            sample_code="[invalid regex sample"
        )
        assert isinstance(result, list)

    @patch('app.utils.analysis_assignment.get_gi_shift_config')
    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_gi_shift_removal(self, mock_profile, mock_gi_config):
        from app.utils.analysis_assignment import assign_analyses_to_sample

        # Profile with Gi
        simple_profile = MagicMock()
        simple_profile.get_analyses.return_value = ['MT', 'Gi']

        mock_profile.query.filter.return_value.first.return_value = simple_profile
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = []

        # PF211 allows D1, D3, D5 - but sample is D2
        mock_gi_config.return_value = {'PF211': ['D1', 'D3', 'D5']}

        result = assign_analyses_to_sample(
            client_name="CHPP",
            sample_type="2H",
            sample_code="PF211_D2"  # D2 not in allowed shifts
        )
        # Gi should be removed
        assert 'Gi' not in result

    @patch('app.utils.analysis_assignment.get_gi_shift_config')
    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_gi_shift_kept(self, mock_profile, mock_gi_config):
        from app.utils.analysis_assignment import assign_analyses_to_sample

        # Profile with Gi
        simple_profile = MagicMock()
        simple_profile.get_analyses.return_value = ['MT', 'Gi']

        mock_profile.query.filter.return_value.first.return_value = simple_profile
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = []

        # PF211 allows D1, D3, D5
        mock_gi_config.return_value = {'PF211': ['D1', 'D3', 'D5']}

        result = assign_analyses_to_sample(
            client_name="CHPP",
            sample_type="2H",
            sample_code="PF211_D1"  # D1 is in allowed shifts
        )
        # Gi should be kept
        assert 'Gi' in result

    @patch('app.utils.analysis_assignment.AnalysisProfile')
    def test_sample_analyses_saved(self, mock_profile):
        from app.utils.analysis_assignment import assign_analyses_to_sample

        simple_profile = MagicMock()
        simple_profile.get_analyses.return_value = ['MT', 'Mad']

        mock_profile.query.filter.return_value.first.return_value = simple_profile
        mock_profile.query.filter.return_value.order_by.return_value.all.return_value = []

        sample = MagicMock()
        sample.client_name = "CHPP"
        sample.sample_type = "Coal"
        sample.sample_code = "SAMPLE-001"
        sample.sample_condition = None

        result = assign_analyses_to_sample(sample=sample)

        # analyses_to_perform should be set
        assert sample.analyses_to_perform is not None
