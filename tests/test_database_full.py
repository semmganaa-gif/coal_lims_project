# tests/test_database_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/database.py
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError


class TestSafeCommit:
    """Tests for safe_commit function."""

    def test_successful_commit(self, app, db):
        """Test successful commit returns True."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_commit
                from app.models import SystemSetting

                # Create a test object
                setting = SystemSetting(
                    category='test_safe_commit',
                    key='test_key',
                    value='test_value'
                )
                db.session.add(setting)

                result = safe_commit()
                assert result is True

                # Cleanup
                db.session.delete(setting)
                db.session.commit()

    def test_successful_commit_with_message(self, app, db):
        """Test successful commit with success message."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_commit
                from app.models import SystemSetting

                setting = SystemSetting(
                    category='test_safe_commit2',
                    key='test_key2',
                    value='test_value2'
                )
                db.session.add(setting)

                result = safe_commit(success_msg="Successfully saved!")
                assert result is True

                # Cleanup
                db.session.delete(setting)
                db.session.commit()

    def test_integrity_error_returns_false(self, app, db):
        """Test IntegrityError returns False."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_commit

                with patch('app.utils.database.db.session.commit', side_effect=IntegrityError("stmt", "params", "orig")):
                    result = safe_commit(error_msg="Duplicate entry")
                    assert result is False

    def test_general_exception_returns_false(self, app, db):
        """Test general exception returns False."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_commit

                with patch('app.utils.database.db.session.commit', side_effect=Exception("DB Error")):
                    result = safe_commit()
                    assert result is False

    def test_rollback_on_error(self, app, db):
        """Test rollback is called on error."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_commit

                with patch('app.utils.database.db.session.commit', side_effect=Exception("Error")):
                    with patch('app.utils.database.db.session.rollback') as mock_rollback:
                        safe_commit()
                        mock_rollback.assert_called_once()


class TestSafeDelete:
    """Tests for safe_delete function."""

    def test_successful_delete(self, app, db):
        """Test successful delete returns True."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_delete
                from app.models import SystemSetting

                # Create object to delete
                setting = SystemSetting(
                    category='test_delete',
                    key='delete_key',
                    value='delete_value'
                )
                db.session.add(setting)
                db.session.commit()

                result = safe_delete(setting)
                assert result is True

    def test_successful_delete_with_message(self, app, db):
        """Test successful delete with success message."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_delete
                from app.models import SystemSetting

                setting = SystemSetting(
                    category='test_delete2',
                    key='delete_key2',
                    value='delete_value2'
                )
                db.session.add(setting)
                db.session.commit()

                result = safe_delete(setting, success_msg="Successfully deleted!")
                assert result is True

    def test_delete_exception_returns_false(self, app, db):
        """Test exception on delete returns False."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_delete

                mock_obj = MagicMock()
                with patch('app.utils.database.db.session.delete'):
                    with patch('app.utils.database.db.session.commit', side_effect=Exception("Delete error")):
                        result = safe_delete(mock_obj)
                        assert result is False

    def test_rollback_on_delete_error(self, app, db):
        """Test rollback is called on delete error."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_delete

                mock_obj = MagicMock()
                with patch('app.utils.database.db.session.delete'):
                    with patch('app.utils.database.db.session.commit', side_effect=Exception("Error")):
                        with patch('app.utils.database.db.session.rollback') as mock_rollback:
                            safe_delete(mock_obj)
                            mock_rollback.assert_called_once()


class TestSafeAdd:
    """Tests for safe_add function."""

    def test_successful_add(self, app, db):
        """Test successful add returns True."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_add
                from app.models import SystemSetting

                setting = SystemSetting(
                    category='test_add',
                    key='add_key',
                    value='add_value'
                )

                result = safe_add(setting)
                assert result is True

                # Cleanup
                db.session.delete(setting)
                db.session.commit()

    def test_successful_add_with_message(self, app, db):
        """Test successful add with success message."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_add
                from app.models import SystemSetting

                setting = SystemSetting(
                    category='test_add2',
                    key='add_key2',
                    value='add_value2'
                )

                result = safe_add(setting, success_msg="Successfully added!")
                assert result is True

                # Cleanup
                db.session.delete(setting)
                db.session.commit()

    def test_add_list_of_objects(self, app, db):
        """Test adding a list of objects."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_add
                from app.models import SystemSetting

                settings = [
                    SystemSetting(category='test_list1', key='key1', value='val1'),
                    SystemSetting(category='test_list2', key='key2', value='val2')
                ]

                result = safe_add(settings)
                assert result is True

                # Cleanup
                for s in settings:
                    db.session.delete(s)
                db.session.commit()

    def test_integrity_error_returns_false(self, app, db):
        """Test IntegrityError on add returns False."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_add

                mock_obj = MagicMock()
                with patch('app.utils.database.db.session.add'):
                    with patch('app.utils.database.db.session.commit', side_effect=IntegrityError("stmt", "params", "orig")):
                        result = safe_add(mock_obj, error_msg="Duplicate entry")
                        assert result is False

    def test_general_exception_returns_false(self, app, db):
        """Test general exception on add returns False."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_add

                mock_obj = MagicMock()
                with patch('app.utils.database.db.session.add'):
                    with patch('app.utils.database.db.session.commit', side_effect=Exception("DB Error")):
                        result = safe_add(mock_obj)
                        assert result is False

    def test_rollback_on_add_error(self, app, db):
        """Test rollback is called on add error."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_add

                mock_obj = MagicMock()
                with patch('app.utils.database.db.session.add'):
                    with patch('app.utils.database.db.session.commit', side_effect=Exception("Error")):
                        with patch('app.utils.database.db.session.rollback') as mock_rollback:
                            safe_add(mock_obj)
                            mock_rollback.assert_called_once()

    def test_add_all_called_for_list(self, app, db):
        """Test add_all is called for list input."""
        with app.app_context():
            with app.test_request_context('/'):
                from app.utils.database import safe_add

                mock_objs = [MagicMock(), MagicMock()]
                with patch('app.utils.database.db.session.add_all') as mock_add_all:
                    with patch('app.utils.database.db.session.commit'):
                        safe_add(mock_objs)
                        mock_add_all.assert_called_once_with(mock_objs)
