# tests/test_analysis_assignment_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/analysis_assignment.py
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError


class TestGetGiShiftConfig:
    """Tests for get_gi_shift_config function."""

    def test_returns_dict(self, app, db):
        """Test returns a dictionary."""
        with app.app_context():
            from app.utils.analysis_assignment import get_gi_shift_config
            result = get_gi_shift_config()
            assert isinstance(result, dict)

    def test_returns_default_when_no_setting(self, app, db):
        """Test returns default when no DB setting."""
        with app.app_context():
            from app.utils.analysis_assignment import get_gi_shift_config, DEFAULT_GI_SHIFT_CONFIG
            from app.models import SystemSetting

            # Ensure no setting exists
            SystemSetting.query.filter_by(category='gi_shift', key='config').delete()
            db.session.commit()

            result = get_gi_shift_config()
            assert result == DEFAULT_GI_SHIFT_CONFIG

    def test_loads_from_db(self, app, db):
        """Test loads config from database."""
        with app.app_context():
            from app.utils.analysis_assignment import get_gi_shift_config
            from app.models import SystemSetting

            # Create test setting
            test_config = {'TEST_PF': ['D1', 'D2']}
            setting = SystemSetting(
                category='gi_shift',
                key='config',
                value=json.dumps(test_config)
            )
            db.session.add(setting)
            db.session.commit()

            result = get_gi_shift_config()
            assert 'TEST_PF' in result

            # Cleanup
            db.session.delete(setting)
            db.session.commit()

    def test_handles_db_exception(self, app, db):
        """Test handles DB exception gracefully."""
        with app.app_context():
            from app.utils.analysis_assignment import get_gi_shift_config, DEFAULT_GI_SHIFT_CONFIG

            with patch('app.utils.analysis_assignment.SystemSetting.query') as mock_query:
                mock_query.filter_by.side_effect = SQLAlchemyError("DB Error")
                result = get_gi_shift_config()
                assert result == DEFAULT_GI_SHIFT_CONFIG


class TestAssignAnalysesToSample:
    """Tests for assign_analyses_to_sample function."""

    def test_with_sample_object(self, app, db):
        """Test with Sample object."""
        with app.app_context():
            from app.utils.analysis_assignment import assign_analyses_to_sample
            from app.models import Sample

            sample = Sample.query.first()
            if sample:
                result = assign_analyses_to_sample(sample=sample)
                assert isinstance(result, list)

    def test_with_parameters(self, app, db):
        """Test with separate parameters."""
        with app.app_context():
            from app.utils.analysis_assignment import assign_analyses_to_sample
            result = assign_analyses_to_sample(
                client_name='Test Client',
                sample_type='Coal',
                sample_code='TEST-001'
            )
            assert isinstance(result, list)

    def test_returns_sorted_list(self, app, db):
        """Test returns sorted list."""
        with app.app_context():
            from app.utils.analysis_assignment import assign_analyses_to_sample
            result = assign_analyses_to_sample(
                client_name='Test',
                sample_type='Test',
                sample_code='Test'
            )
            assert result == sorted(result)

    def test_gi_removed_for_wrong_shift(self, app, db):
        """Test Gi is removed for wrong shift."""
        with app.app_context():
            from app.utils.analysis_assignment import assign_analyses_to_sample
            from app.models import AnalysisProfile

            # Create a profile that includes Gi (use set_analyses method)
            profile = AnalysisProfile(
                client_name='CHPP',
                sample_type='2H'
            )
            profile.set_analyses(['MT', 'Aad', 'Vad', 'Gi'])
            db.session.add(profile)
            db.session.commit()

            # PF211 with D2 should NOT have Gi (only D1,D3,D5,N1,N3,N5)
            result = assign_analyses_to_sample(
                client_name='CHPP',
                sample_type='2H',
                sample_code='PF211_D2'  # Even shift
            )

            # Cleanup
            db.session.delete(profile)
            db.session.commit()

            # Gi should be removed
            assert 'Gi' not in result

    def test_gi_kept_for_correct_shift(self, app, db):
        """Test Gi is kept for correct shift."""
        with app.app_context():
            from app.utils.analysis_assignment import assign_analyses_to_sample
            from app.models import AnalysisProfile

            # Create a profile that includes Gi (use set_analyses method)
            profile = AnalysisProfile(
                client_name='CHPP',
                sample_type='2H'
            )
            profile.set_analyses(['MT', 'Aad', 'Vad', 'Gi'])
            db.session.add(profile)
            db.session.commit()

            # PF211 with D1 should have Gi (D1,D3,D5,N1,N3,N5)
            result = assign_analyses_to_sample(
                client_name='CHPP',
                sample_type='2H',
                sample_code='PF211_D1'  # Odd shift
            )

            # Cleanup
            db.session.delete(profile)
            db.session.commit()

            # Gi should be kept
            assert 'Gi' in result

    def test_pattern_profile_match(self, app, db):
        """Test pattern profile matching."""
        with app.app_context():
            from app.utils.analysis_assignment import assign_analyses_to_sample
            from app.models import AnalysisProfile

            # Create a pattern profile (use set_analyses method)
            profile = AnalysisProfile(
                client_name='CHPP',
                sample_type='2H',
                pattern='PF211',
                priority=1
            )
            profile.set_analyses(['CV', 'TS'])
            db.session.add(profile)
            db.session.commit()

            result = assign_analyses_to_sample(
                client_name='CHPP',
                sample_type='2H',
                sample_code='PF211_D1'
            )

            # Cleanup
            db.session.delete(profile)
            db.session.commit()

            assert 'CV' in result
            assert 'TS' in result

    def test_sample_updates_analyses_to_perform(self, app, db):
        """Test Sample object gets updated."""
        with app.app_context():
            from app.utils.analysis_assignment import assign_analyses_to_sample
            from app.models import Sample

            sample = Sample.query.first()
            if sample:
                result = assign_analyses_to_sample(sample=sample)
                assert sample.analyses_to_perform is not None


class TestDefaultGiShiftConfig:
    """Tests for DEFAULT_GI_SHIFT_CONFIG constant."""

    def test_has_pf211(self, app):
        """Test has PF211 config."""
        with app.app_context():
            from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
            assert 'PF211' in DEFAULT_GI_SHIFT_CONFIG

    def test_has_pf221(self, app):
        """Test has PF221 config."""
        with app.app_context():
            from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
            assert 'PF221' in DEFAULT_GI_SHIFT_CONFIG

    def test_has_pf231(self, app):
        """Test has PF231 config."""
        with app.app_context():
            from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
            assert 'PF231' in DEFAULT_GI_SHIFT_CONFIG

    def test_pf211_odd_shifts(self, app):
        """Test PF211 has odd shifts."""
        with app.app_context():
            from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
            shifts = DEFAULT_GI_SHIFT_CONFIG['PF211']
            assert 'D1' in shifts
            assert 'D3' in shifts
            assert 'D5' in shifts

    def test_pf221_even_shifts(self, app):
        """Test PF221 has even shifts."""
        with app.app_context():
            from app.utils.analysis_assignment import DEFAULT_GI_SHIFT_CONFIG
            shifts = DEFAULT_GI_SHIFT_CONFIG['PF221']
            assert 'D2' in shifts
            assert 'D4' in shifts
            assert 'D6' in shifts
