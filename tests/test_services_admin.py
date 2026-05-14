# tests/test_services_admin.py
# -*- coding: utf-8 -*-
"""Comprehensive tests for app/services/admin_service.py targeting 80%+ coverage."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from sqlalchemy.exc import SQLAlchemyError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    """Minimal Flask app with db mock. Babel-ийг initialize хийнэ — service
    функцэд `_l()` LazyString-ийг str()-ээр хөрвүүлэхэд request context
    шаардахгүй болгох."""
    from flask import Flask
    from flask_babel import Babel
    _app = Flask(__name__)
    _app.config['TESTING'] = True
    _app.config['SECRET_KEY'] = 'test'
    _app.config['BABEL_DEFAULT_LOCALE'] = 'mn'
    Babel(_app)
    return _app


@pytest.fixture(autouse=True)
def app_context(app):
    with app.app_context():
        yield


@pytest.fixture()
def mock_db():
    """Patch both `admin_service.db` and `app.utils.transaction.db` with the
    same mock — @transactional decorator-ийн commit/rollback-ыг ижил mock
    дээр assert хийх боломжтой."""
    shared = MagicMock()
    shared.session = MagicMock()
    with patch('app.services.admin_service.db', shared), \
         patch('app.utils.transaction.db', shared):
        yield shared


@pytest.fixture()
def mock_log_audit():
    with patch('app.services.admin_service.log_audit') as m:
        yield m


# ===========================================================================
# seed_analysis_types
# ===========================================================================

class TestSeedAnalysisTypes:

    @patch('app.services.admin_service.MASTER_ANALYSIS_TYPES_LIST', [
        {'code': 'Mad', 'name': 'Moisture', 'order': 1, 'role': 'chemist'},
    ])
    @patch('app.services.admin_service.AnalysisTypeRepository')
    def test_creates_new_type(self, mock_repo, mock_db):
        """New analysis type is added when not in DB."""
        mock_repo.get_all.return_value = []

        from app.services.admin_service import seed_analysis_types
        result = seed_analysis_types()

        assert result is True
        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()

    @patch('app.services.admin_service.MASTER_ANALYSIS_TYPES_LIST', [
        {'code': 'Mad', 'name': 'Moisture', 'order': 1, 'role': 'chemist'},
    ])
    @patch('app.services.admin_service.AnalysisTypeRepository')
    def test_updates_existing_type(self, mock_repo, mock_db):
        """Existing type with changed fields gets updated."""
        existing = MagicMock()
        existing.code = 'Mad'
        existing.name = 'Old Name'
        existing.order_num = 99
        existing.required_role = 'prep'
        mock_repo.get_all.return_value = [existing]

        from app.services.admin_service import seed_analysis_types
        result = seed_analysis_types()

        assert result is True
        assert existing.name == 'Moisture'
        assert existing.order_num == 1
        assert existing.required_role == 'chemist'

    @patch('app.services.admin_service.MASTER_ANALYSIS_TYPES_LIST', [
        {'code': 'Mad', 'name': 'Moisture', 'order': 1, 'role': 'chemist'},
    ])
    @patch('app.services.admin_service.AnalysisTypeRepository')
    def test_no_changes_needed(self, mock_repo, mock_db):
        """Returns False when nothing changed."""
        existing = MagicMock()
        existing.code = 'Mad'
        existing.name = 'Moisture'
        existing.order_num = 1
        existing.required_role = 'chemist'
        mock_repo.get_all.return_value = [existing]

        from app.services.admin_service import seed_analysis_types
        result = seed_analysis_types()

        assert result is False
        mock_db.session.add.assert_not_called()

    @patch('app.services.admin_service.MASTER_ANALYSIS_TYPES_LIST', [
        {'code': 'New', 'name': 'New Type', 'order': 5, 'role': 'senior'},
    ])
    @patch('app.services.admin_service.AnalysisTypeRepository')
    def test_commit_error_rollback(self, mock_repo, mock_db):
        """SQLAlchemyError triggers rollback and returns False."""
        mock_repo.get_all.return_value = []
        mock_db.session.commit.side_effect = SQLAlchemyError('db error')

        from app.services.admin_service import seed_analysis_types
        result = seed_analysis_types()

        assert result is False
        mock_db.session.rollback.assert_called_once()


# ===========================================================================
# auto_populate_profiles
# ===========================================================================

class TestAutoPopulateProfiles:

    @patch('app.services.admin_service.CHPP_CONFIG_GROUPS', {
        'hourly': {
            'samples': [{'name': 'Sample1'}]
        }
    })
    @patch('app.services.admin_service.SAMPLE_TYPE_CHOICES_MAP', {
        'ClientA': ['type1'],
    })
    @patch('app.services.admin_service.AnalysisProfileRepository')
    @patch('app.services.admin_service.AnalysisProfile')
    def test_creates_simple_and_chpp_profiles(self, mock_profile_cls, mock_repo, mock_db):
        """Creates both simple and CHPP profiles when none exist."""
        mock_repo.find_simple.return_value = None
        mock_repo.find_pattern.return_value = None
        mock_profile_cls.side_effect = lambda **kw: MagicMock(**kw)

        from app.services.admin_service import auto_populate_profiles
        result = auto_populate_profiles()

        assert result is True
        assert mock_db.session.add.call_count == 2
        mock_db.session.commit.assert_called_once()

    @patch('app.services.admin_service.CHPP_CONFIG_GROUPS', {})
    @patch('app.services.admin_service.SAMPLE_TYPE_CHOICES_MAP', {
        'ClientA': ['type1'],
    })
    @patch('app.services.admin_service.AnalysisProfileRepository')
    def test_skips_existing_profiles(self, mock_repo, mock_db):
        """Returns False when all profiles exist already."""
        mock_repo.find_simple.return_value = MagicMock()
        mock_repo.find_pattern.return_value = MagicMock()

        from app.services.admin_service import auto_populate_profiles
        result = auto_populate_profiles()

        assert result is False

    @patch('app.services.admin_service.CHPP_CONFIG_GROUPS', {})
    @patch('app.services.admin_service.SAMPLE_TYPE_CHOICES_MAP', {
        'CHPP': ['type1'],
        'ClientB': ['type2'],
    })
    @patch('app.services.admin_service.AnalysisProfileRepository')
    @patch('app.services.admin_service.AnalysisProfile')
    def test_skips_chpp_in_simple_loop(self, mock_profile_cls, mock_repo, mock_db):
        """CHPP is skipped in the simple profiles loop."""
        mock_repo.find_simple.return_value = None
        mock_repo.find_pattern.return_value = None
        mock_profile_cls.side_effect = lambda **kw: MagicMock(**kw)

        from app.services.admin_service import auto_populate_profiles
        result = auto_populate_profiles()

        assert result is True
        # Only ClientB type2 should be added (1 call), not CHPP
        assert mock_db.session.add.call_count == 1

    @patch('app.services.admin_service.CHPP_CONFIG_GROUPS', {})
    @patch('app.services.admin_service.SAMPLE_TYPE_CHOICES_MAP', {
        'X': ['t1'],
    })
    @patch('app.services.admin_service.AnalysisProfileRepository')
    @patch('app.services.admin_service.AnalysisProfile')
    def test_commit_error_rollback(self, mock_profile_cls, mock_repo, mock_db):
        """SQLAlchemyError triggers rollback."""
        mock_repo.find_simple.return_value = None
        mock_repo.find_pattern.return_value = None
        mock_profile_cls.side_effect = lambda **kw: MagicMock(**kw)
        mock_db.session.commit.side_effect = SQLAlchemyError('fail')

        from app.services.admin_service import auto_populate_profiles
        result = auto_populate_profiles()

        assert result is False
        mock_db.session.rollback.assert_called_once()


# ===========================================================================
# load_gi_shift_config
# ===========================================================================

class TestLoadGiShiftConfig:

    @patch('app.services.admin_service.SystemSettingRepository')
    def test_loads_from_db(self, mock_repo):
        """Returns config from DB when valid JSON exists."""
        setting = MagicMock()
        setting.value = json.dumps({'PF211': ['D1', 'D3']})
        mock_repo.get_gi_shift_config.return_value = setting

        from app.services.admin_service import load_gi_shift_config
        result = load_gi_shift_config()

        assert result == {'PF211': ['D1', 'D3']}

    @patch('app.services.admin_service.SystemSettingRepository')
    def test_returns_default_when_no_setting(self, mock_repo):
        """Returns default config when DB returns None."""
        mock_repo.get_gi_shift_config.return_value = None

        from app.services.admin_service import load_gi_shift_config
        result = load_gi_shift_config()

        assert 'PF211' in result
        assert 'PF221' in result
        assert 'PF231' in result

    @patch('app.services.admin_service.SystemSettingRepository')
    def test_returns_default_on_invalid_json(self, mock_repo):
        """Returns default config when DB value is invalid JSON."""
        setting = MagicMock()
        setting.value = 'not-json{'
        mock_repo.get_gi_shift_config.return_value = setting

        from app.services.admin_service import load_gi_shift_config
        result = load_gi_shift_config()

        assert 'PF211' in result

    @patch('app.services.admin_service.SystemSettingRepository')
    def test_returns_default_on_empty_value(self, mock_repo):
        """Returns default config when value is empty string."""
        setting = MagicMock()
        setting.value = ''
        mock_repo.get_gi_shift_config.return_value = setting

        from app.services.admin_service import load_gi_shift_config
        result = load_gi_shift_config()

        assert 'PF211' in result


# ===========================================================================
# validate_and_create_user
# ===========================================================================

class TestValidateAndCreateUser:

    def _call(self, **overrides):
        from app.services.admin_service import validate_and_create_user
        defaults = dict(
            username='testuser',
            password='StrongPass1234',
            role='chemist',
            full_name='Test User',
            email='test@example.com',
            phone='12345678',
            position='Lab Tech',
            allowed_labs=['coal'],
        )
        defaults.update(overrides)
        return validate_and_create_user(**defaults)

    @patch('app.services.admin_service.sa')
    @patch('app.services.admin_service.log_audit')
    @patch('app.services.admin_service.UserSchema')
    @patch('app.services.admin_service.User')
    def test_success(self, mock_user_cls, mock_schema_cls, mock_audit, mock_sa, mock_db):
        """Successfully creates a user."""
        mock_schema_cls.return_value.validate.return_value = {}
        mock_db.session.scalar.return_value = None  # no duplicate
        user_inst = MagicMock()
        user_inst.id = 42
        user_inst.username = 'testuser'
        user_inst.role = 'chemist'
        user_inst.allowed_labs = ['coal']
        mock_user_cls.return_value = user_inst

        ok, msg, uid = self._call()

        assert ok is True
        assert uid == 42
        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()
        mock_audit.assert_called_once()

    @patch('app.services.admin_service.UserSchema')
    def test_schema_validation_error(self, mock_schema_cls, mock_db):
        """Returns error when schema validation fails."""
        mock_schema_cls.return_value.validate.return_value = {
            'username': ['too short']
        }

        ok, msg, uid = self._call()

        assert ok is False
        assert 'too short' in msg
        assert uid is None

    @patch('app.services.admin_service.UserSchema')
    def test_schema_validation_error_string_messages(self, mock_schema_cls, mock_db):
        """Handles non-list error messages from schema."""
        mock_schema_cls.return_value.validate.return_value = {
            'role': 'invalid role'
        }

        ok, msg, uid = self._call()

        assert ok is False
        assert 'invalid role' in msg

    @patch('app.services.admin_service.sa')
    @patch('app.services.admin_service.UserSchema')
    def test_duplicate_user(self, mock_schema_cls, mock_sa, mock_db):
        """Returns error when username already exists."""
        mock_schema_cls.return_value.validate.return_value = {}
        mock_db.session.scalar.return_value = MagicMock()  # existing user

        ok, msg, uid = self._call()

        assert ok is False
        assert uid is None

    @patch('app.services.admin_service.sa')
    @patch('app.services.admin_service.UserSchema')
    def test_admin_role_blocked(self, mock_schema_cls, mock_sa, mock_db):
        """Cannot create admin user."""
        mock_schema_cls.return_value.validate.return_value = {}
        mock_db.session.scalar.return_value = None

        ok, msg, uid = self._call(role='admin')

        assert ok is False
        assert uid is None

    @patch('app.services.admin_service.sa')
    @patch('app.services.admin_service.UserSchema')
    @patch('app.services.admin_service.User')
    def test_password_value_error(self, mock_user_cls, mock_schema_cls, mock_sa, mock_db):
        """Returns error when set_password raises ValueError."""
        mock_schema_cls.return_value.validate.return_value = {}
        mock_db.session.scalar.return_value = None
        user_inst = MagicMock()
        user_inst.set_password.side_effect = ValueError('bad password')
        mock_user_cls.return_value = user_inst

        ok, msg, uid = self._call()

        assert ok is False
        assert uid is None

    @patch('app.services.admin_service.sa')
    @patch('app.services.admin_service.UserSchema')
    @patch('app.services.admin_service.User')
    def test_commit_error(self, mock_user_cls, mock_schema_cls, mock_sa, mock_db):
        """SQLAlchemyError on commit triggers rollback."""
        mock_schema_cls.return_value.validate.return_value = {}
        mock_db.session.scalar.return_value = None
        mock_user_cls.return_value = MagicMock()
        mock_db.session.commit.side_effect = SQLAlchemyError('db fail')

        ok, msg, uid = self._call()

        assert ok is False
        assert uid is None
        mock_db.session.rollback.assert_called_once()

    @patch('app.services.admin_service.sa')
    @patch('app.services.admin_service.log_audit')
    @patch('app.services.admin_service.UserSchema')
    @patch('app.services.admin_service.User')
    def test_allowed_labs_default(self, mock_user_cls, mock_schema_cls, mock_audit, mock_sa, mock_db):
        """Defaults allowed_labs to ['coal'] when None."""
        mock_schema_cls.return_value.validate.return_value = {}
        mock_db.session.scalar.return_value = None
        user_inst = MagicMock()
        user_inst.id = 1
        user_inst.username = 'u'
        user_inst.role = 'chemist'
        user_inst.allowed_labs = ['coal']
        mock_user_cls.return_value = user_inst

        ok, msg, uid = self._call(allowed_labs=None)
        assert ok is True


# ===========================================================================
# update_user
# ===========================================================================

class TestUpdateUser:

    def _call(self, **overrides):
        from app.services.admin_service import update_user
        defaults = dict(
            user_id=1,
            username='updated_user',
            password=None,
            role='chemist',
            full_name='Updated',
            email='u@example.com',
            phone='999',
            position='Tech',
            allowed_labs=['coal'],
        )
        defaults.update(overrides)
        return update_user(**defaults)

    @patch('app.services.admin_service.log_audit')
    def test_user_not_found(self, mock_audit, mock_db):
        """Returns not_found when user doesn't exist."""
        mock_db.session.get.return_value = None

        ok, msg = self._call()

        assert ok is False
        assert msg == 'not_found'

    @patch('app.services.admin_service.log_audit')
    def test_success_no_password(self, mock_audit, mock_db):
        """Successfully updates user without password change."""
        user = MagicMock()
        user.username = 'updated_user'
        user.role = 'chemist'
        user.id = 1
        user.allowed_labs = ['coal']
        mock_db.session.get.return_value = user

        ok, msg = self._call()

        assert ok is True
        mock_audit.assert_called_once()

    @patch('app.services.admin_service.sa')
    @patch('app.services.admin_service.log_audit')
    def test_duplicate_username(self, mock_audit, mock_sa, mock_db):
        """Returns error when new username already taken."""
        user = MagicMock()
        user.username = 'original_name'
        user.role = 'chemist'
        mock_db.session.get.return_value = user
        mock_db.session.scalar.return_value = MagicMock()  # duplicate found

        ok, msg = self._call(username='taken_name')

        assert ok is False

    @patch('app.services.admin_service.log_audit')
    def test_admin_role_protection(self, mock_audit, mock_db):
        """Cannot change admin role to something else."""
        user = MagicMock()
        user.username = 'admin_user'
        user.role = 'admin'
        user.id = 1
        user.allowed_labs = ['coal']
        mock_db.session.get.return_value = user

        ok, msg = self._call(username='admin_user', role='chemist')

        assert ok is True
        # Role should NOT have been changed; admin warning appended
        assert user.role == 'admin'

    @patch('app.services.admin_service.log_audit')
    def test_admin_stays_admin(self, mock_audit, mock_db):
        """Admin updating with role=admin produces no warning."""
        user = MagicMock()
        user.username = 'admin_user'
        user.role = 'admin'
        user.id = 1
        user.allowed_labs = ['coal']
        mock_db.session.get.return_value = user

        ok, msg = self._call(username='admin_user', role='admin')

        assert ok is True

    @patch('app.services.admin_service.log_audit')
    def test_password_change_success(self, mock_audit, mock_db):
        """Password is updated when provided."""
        user = MagicMock()
        user.username = 'u'
        user.role = 'chemist'
        user.id = 1
        user.allowed_labs = ['coal']
        mock_db.session.get.return_value = user

        ok, msg = self._call(username='u', password='NewPass1234')

        assert ok is True
        user.set_password.assert_called_once_with('NewPass1234')

    @patch('app.services.admin_service.log_audit')
    def test_password_change_value_error(self, mock_audit, mock_db):
        """Returns error when set_password raises ValueError."""
        user = MagicMock()
        user.username = 'u'
        user.role = 'chemist'
        user.set_password.side_effect = ValueError('bad')
        mock_db.session.get.return_value = user

        ok, msg = self._call(username='u', password='weak')

        assert ok is False

    @patch('app.services.admin_service.log_audit')
    def test_commit_error(self, mock_audit, mock_db):
        """SQLAlchemyError on commit triggers rollback."""
        user = MagicMock()
        user.username = 'u'
        user.role = 'chemist'
        mock_db.session.get.return_value = user
        mock_db.session.commit.side_effect = SQLAlchemyError('fail')

        ok, msg = self._call(username='u')

        assert ok is False
        mock_db.session.rollback.assert_called_once()

    @patch('app.services.admin_service.log_audit')
    def test_non_admin_role_change(self, mock_audit, mock_db):
        """Non-admin user role can be changed."""
        user = MagicMock()
        user.username = 'u'
        user.role = 'prep'
        user.id = 1
        user.allowed_labs = ['coal']
        mock_db.session.get.return_value = user

        ok, msg = self._call(username='u', role='senior')

        assert ok is True
        assert user.role == 'senior'


# ===========================================================================
# delete_user
# ===========================================================================

class TestDeleteUser:

    @patch('app.services.admin_service.log_audit')
    def test_cannot_delete_self(self, mock_audit, mock_db):
        """Cannot delete your own account."""
        from app.services.admin_service import delete_user
        ok, msg = delete_user(user_id=5, current_user_id=5)

        assert ok is False

    @patch('app.services.admin_service.log_audit')
    def test_user_not_found(self, mock_audit, mock_db):
        """Returns not_found when user doesn't exist."""
        mock_db.session.get.return_value = None

        from app.services.admin_service import delete_user
        ok, msg = delete_user(user_id=99, current_user_id=1)

        assert ok is False
        assert msg == 'not_found'

    @patch('app.services.admin_service.log_audit')
    def test_cannot_delete_admin(self, mock_audit, mock_db):
        """Cannot delete admin user."""
        user = MagicMock()
        user.role = 'admin'
        mock_db.session.get.return_value = user

        from app.services.admin_service import delete_user
        ok, msg = delete_user(user_id=2, current_user_id=1)

        assert ok is False

    @patch('app.services.admin_service.log_audit')
    def test_success(self, mock_audit, mock_db):
        """Successfully deletes user."""
        user = MagicMock()
        user.role = 'chemist'
        user.username = 'del_me'
        mock_db.session.get.return_value = user

        from app.services.admin_service import delete_user
        ok, msg = delete_user(user_id=10, current_user_id=1)

        assert ok is True
        mock_db.session.delete.assert_called_once_with(user)
        mock_db.session.commit.assert_called_once()
        mock_audit.assert_called_once()

    @patch('app.services.admin_service.log_audit')
    def test_commit_error(self, mock_audit, mock_db):
        """SQLAlchemyError triggers rollback."""
        user = MagicMock()
        user.role = 'chemist'
        user.username = 'x'
        mock_db.session.get.return_value = user
        mock_db.session.commit.side_effect = SQLAlchemyError('fail')

        from app.services.admin_service import delete_user
        ok, msg = delete_user(user_id=10, current_user_id=1)

        assert ok is False
        mock_db.session.rollback.assert_called_once()


# ===========================================================================
# save_analysis_config
# ===========================================================================

class TestSaveAnalysisConfig:

    @patch('app.services.admin_service.SystemSettingRepository')
    @patch('app.services.admin_service.AnalysisProfileRepository')
    def test_success(self, mock_profile_repo, mock_repo, mock_db):
        """Saves simple and CHPP profiles and Gi config."""
        simple_p = MagicMock()
        simple_p.id = 1
        chpp_p = MagicMock()
        chpp_p.id = 2

        mock_profile_repo.get_simple_profiles.return_value = [simple_p]
        mock_profile_repo.get_chpp_profiles.return_value = [chpp_p]

        form_data = MagicMock()
        form_data.getlist.side_effect = lambda key: {
            'simple-1-analyses': ['Mad', 'Aad'],
            'chpp-2-analyses': ['Vdaf'],
            'gi_shifts_PF211': ['D1'],
            'gi_shifts_PF221': [],
            'gi_shifts_PF231': [],
        }.get(key, [])

        from app.services.admin_service import save_analysis_config
        ok, msg = save_analysis_config(form_data)

        assert ok is True
        mock_db.session.commit.assert_called_once()

    @patch('app.services.admin_service.SystemSettingRepository')
    @patch('app.services.admin_service.AnalysisProfileRepository')
    def test_commit_error(self, mock_profile_repo, mock_repo, mock_db):
        """SQLAlchemyError triggers rollback."""
        mock_profile_repo.get_simple_profiles.return_value = []
        mock_profile_repo.get_chpp_profiles.return_value = []
        mock_db.session.commit.side_effect = SQLAlchemyError('fail')

        form_data = MagicMock()
        form_data.getlist.return_value = []

        from app.services.admin_service import save_analysis_config
        ok, msg = save_analysis_config(form_data)

        assert ok is False
        mock_db.session.rollback.assert_called_once()

    @patch('app.services.admin_service.SystemSettingRepository')
    @patch('app.services.admin_service.AnalysisProfileRepository')
    def test_no_gi_config(self, mock_profile_repo, mock_repo, mock_db):
        """Works when no Gi shifts provided."""
        mock_profile_repo.get_simple_profiles.return_value = []
        mock_profile_repo.get_chpp_profiles.return_value = []
        form_data = MagicMock()
        form_data.getlist.return_value = []

        from app.services.admin_service import save_analysis_config
        ok, msg = save_analysis_config(form_data)

        assert ok is True
        mock_repo.set_value.assert_not_called()


# ===========================================================================
# Control Standard CRUD
# ===========================================================================

class TestCreateStandard:

    def test_empty_name(self, mock_db):
        from app.services.admin_service import create_standard
        ok, msg = create_standard('', {'Mad': 10})
        assert ok is False

    def test_empty_targets(self, mock_db):
        from app.services.admin_service import create_standard
        ok, msg = create_standard('STD-1', {})
        assert ok is False

    @patch('app.services.admin_service.ControlStandard')
    def test_success(self, mock_cls, mock_db):
        from app.services.admin_service import create_standard
        ok, msg = create_standard('STD-1', {'Mad': 10})
        assert ok is True
        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()

    @patch('app.services.admin_service.ControlStandard')
    def test_commit_error(self, mock_cls, mock_db):
        mock_db.session.commit.side_effect = SQLAlchemyError('fail')
        from app.services.admin_service import create_standard
        ok, msg = create_standard('STD-1', {'Mad': 10})
        assert ok is False
        mock_db.session.rollback.assert_called_once()


class TestUpdateStandard:

    @patch('app.services.admin_service.ControlStandardRepository')
    def test_not_found(self, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = None
        from app.services.admin_service import update_standard
        ok, msg = update_standard(1, 'name', {'a': 1})
        assert ok is False
        assert msg == 'not_found'

    @patch('app.services.admin_service.ControlStandardRepository')
    def test_empty_data(self, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = MagicMock()
        from app.services.admin_service import update_standard
        ok, msg = update_standard(1, '', {'a': 1})
        assert ok is False

    @patch('app.services.admin_service.ControlStandardRepository')
    def test_empty_targets(self, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = MagicMock()
        from app.services.admin_service import update_standard
        ok, msg = update_standard(1, 'name', {})
        assert ok is False

    @patch('app.services.admin_service.ControlStandardRepository')
    def test_success(self, mock_repo, mock_db):
        std = MagicMock()
        mock_repo.get_by_id.return_value = std
        from app.services.admin_service import update_standard
        ok, msg = update_standard(1, 'NewName', {'Mad': 5})
        assert ok is True
        assert std.name == 'NewName'
        assert std.targets == {'Mad': 5}

    @patch('app.services.admin_service.ControlStandardRepository')
    def test_commit_error(self, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = MagicMock()
        mock_db.session.commit.side_effect = SQLAlchemyError('fail')
        from app.services.admin_service import update_standard
        ok, msg = update_standard(1, 'N', {'a': 1})
        assert ok is False
        mock_db.session.rollback.assert_called_once()


class TestDeleteStandard:

    @patch('app.services.admin_service.ControlStandardRepository')
    def test_not_found(self, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = None
        from app.services.admin_service import delete_standard
        ok, msg = delete_standard(1)
        assert ok is False
        assert msg == 'not_found'

    @patch('app.services.admin_service.ControlStandardRepository')
    def test_active_cannot_delete(self, mock_repo, mock_db):
        std = MagicMock()
        std.is_active = True
        mock_repo.get_by_id.return_value = std
        from app.services.admin_service import delete_standard
        ok, msg = delete_standard(1)
        assert ok is False

    @patch('app.services.admin_service.ControlStandardRepository')
    def test_success(self, mock_repo, mock_db):
        std = MagicMock()
        std.is_active = False
        mock_repo.get_by_id.return_value = std
        from app.services.admin_service import delete_standard
        ok, msg = delete_standard(1)
        assert ok is True
        mock_db.session.delete.assert_called_once_with(std)

    @patch('app.services.admin_service.ControlStandardRepository')
    def test_commit_error(self, mock_repo, mock_db):
        std = MagicMock()
        std.is_active = False
        mock_repo.get_by_id.return_value = std
        mock_db.session.commit.side_effect = SQLAlchemyError('fail')
        from app.services.admin_service import delete_standard
        ok, msg = delete_standard(1)
        assert ok is False
        mock_db.session.rollback.assert_called_once()


class TestActivateStandard:

    @patch('app.services.admin_service.ControlStandardRepository')
    def test_not_found(self, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = None
        from app.services.admin_service import activate_standard
        ok, msg = activate_standard(1)
        assert ok is False
        assert msg == 'not_found'

    @patch('app.services.admin_service.ControlStandardRepository')
    def test_success(self, mock_repo, mock_db):
        std = MagicMock()
        mock_repo.get_by_id.return_value = std
        from app.services.admin_service import activate_standard
        ok, msg = activate_standard(1)
        assert ok is True
        mock_repo.deactivate_all.assert_called_once_with(commit=False)
        assert std.is_active is True

    @patch('app.services.admin_service.ControlStandardRepository')
    def test_commit_error(self, mock_repo, mock_db):
        std = MagicMock()
        mock_repo.get_by_id.return_value = std
        mock_db.session.commit.side_effect = SQLAlchemyError('fail')
        from app.services.admin_service import activate_standard
        ok, msg = activate_standard(1)
        assert ok is False
        mock_db.session.rollback.assert_called_once()


# ===========================================================================
# GBW Standard CRUD
# ===========================================================================

class TestCreateGbw:

    def test_empty_name(self, mock_db):
        from app.services.admin_service import create_gbw
        ok, msg = create_gbw('', {'a': 1})
        assert ok is False

    def test_empty_targets(self, mock_db):
        from app.services.admin_service import create_gbw
        ok, msg = create_gbw('GBW-1', {})
        assert ok is False

    @patch('app.services.admin_service.GbwStandard')
    def test_success(self, mock_cls, mock_db):
        from app.services.admin_service import create_gbw
        ok, msg = create_gbw('GBW-1', {'Mad': 10})
        assert ok is True
        mock_db.session.add.assert_called_once()

    @patch('app.services.admin_service.GbwStandard')
    def test_commit_error(self, mock_cls, mock_db):
        mock_db.session.commit.side_effect = SQLAlchemyError('fail')
        from app.services.admin_service import create_gbw
        ok, msg = create_gbw('GBW-1', {'a': 1})
        assert ok is False
        mock_db.session.rollback.assert_called_once()


class TestUpdateGbw:

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_not_found(self, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = None
        from app.services.admin_service import update_gbw
        ok, msg = update_gbw(1, 'name', {'a': 1})
        assert ok is False
        assert msg == 'not_found'

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_empty_data(self, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = MagicMock()
        from app.services.admin_service import update_gbw
        ok, msg = update_gbw(1, '', {'a': 1})
        assert ok is False

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_empty_targets(self, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = MagicMock()
        from app.services.admin_service import update_gbw
        ok, msg = update_gbw(1, 'name', {})
        assert ok is False

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_success(self, mock_repo, mock_db):
        gbw = MagicMock()
        mock_repo.get_by_id.return_value = gbw
        from app.services.admin_service import update_gbw
        ok, msg = update_gbw(1, 'GBW-New', {'St': 0.5})
        assert ok is True
        assert gbw.name == 'GBW-New'
        assert gbw.targets == {'St': 0.5}

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_commit_error(self, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = MagicMock()
        mock_db.session.commit.side_effect = SQLAlchemyError('fail')
        from app.services.admin_service import update_gbw
        ok, msg = update_gbw(1, 'N', {'a': 1})
        assert ok is False
        mock_db.session.rollback.assert_called_once()


class TestDeleteGbw:

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_not_found(self, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = None
        from app.services.admin_service import delete_gbw
        ok, msg = delete_gbw(1)
        assert ok is False
        assert msg == 'not_found'

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_active_cannot_delete(self, mock_repo, mock_db):
        gbw = MagicMock()
        gbw.is_active = True
        mock_repo.get_by_id.return_value = gbw
        from app.services.admin_service import delete_gbw
        ok, msg = delete_gbw(1)
        assert ok is False

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_success(self, mock_repo, mock_db):
        gbw = MagicMock()
        gbw.is_active = False
        mock_repo.get_by_id.return_value = gbw
        from app.services.admin_service import delete_gbw
        ok, msg = delete_gbw(1)
        assert ok is True
        mock_db.session.delete.assert_called_once_with(gbw)

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_commit_error(self, mock_repo, mock_db):
        gbw = MagicMock()
        gbw.is_active = False
        mock_repo.get_by_id.return_value = gbw
        mock_db.session.commit.side_effect = SQLAlchemyError('fail')
        from app.services.admin_service import delete_gbw
        ok, msg = delete_gbw(1)
        assert ok is False
        mock_db.session.rollback.assert_called_once()


class TestActivateGbw:

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_not_found(self, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = None
        from app.services.admin_service import activate_gbw
        ok, msg = activate_gbw(1)
        assert ok is False
        assert msg == 'not_found'

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_success(self, mock_repo, mock_db):
        gbw = MagicMock()
        mock_repo.get_by_id.return_value = gbw
        from app.services.admin_service import activate_gbw
        ok, msg = activate_gbw(1)
        assert ok is True
        mock_repo.deactivate_all.assert_called_once_with(commit=False)
        assert gbw.is_active is True

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_commit_error(self, mock_repo, mock_db):
        gbw = MagicMock()
        mock_repo.get_by_id.return_value = gbw
        mock_db.session.commit.side_effect = SQLAlchemyError('fail')
        from app.services.admin_service import activate_gbw
        ok, msg = activate_gbw(1)
        assert ok is False
        mock_db.session.rollback.assert_called_once()


class TestDeactivateGbw:

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_not_found(self, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = None
        from app.services.admin_service import deactivate_gbw
        ok, msg = deactivate_gbw(1)
        assert ok is False
        assert msg == 'not_found'

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_success(self, mock_repo, mock_db):
        gbw = MagicMock()
        mock_repo.get_by_id.return_value = gbw
        from app.services.admin_service import deactivate_gbw
        ok, msg = deactivate_gbw(1)
        assert ok is True
        assert gbw.is_active is False

    @patch('app.services.admin_service.GbwStandardRepository')
    def test_commit_error(self, mock_repo, mock_db):
        gbw = MagicMock()
        mock_repo.get_by_id.return_value = gbw
        mock_db.session.commit.side_effect = SQLAlchemyError('fail')
        from app.services.admin_service import deactivate_gbw
        ok, msg = deactivate_gbw(1)
        assert ok is False
        mock_db.session.rollback.assert_called_once()
