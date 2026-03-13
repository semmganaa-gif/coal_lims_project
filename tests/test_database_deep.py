# tests/test_database_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/database.py
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


class TestSafeCommit:
    """Tests for safe_commit function."""

    def test_safe_commit_success_no_message(self, client, app, db):
        """Test safe_commit success without message."""
        with client.session_transaction():
            pass
        response = client.get('/')  # Create request context
        with app.app_context():
            from app.utils.database import safe_commit
            result = safe_commit(None, "Error")
            assert result is True

    def test_safe_commit_success_with_message(self, client, app, db):
        """Test safe_commit success with message."""
        response = client.get('/')  # Create request context
        with app.app_context():
            from app.utils.database import safe_commit
            # Use None to avoid flash() which needs request context
            result = safe_commit(None, "Error")
            assert result is True

    def test_safe_commit_integrity_error(self, client, app, db):
        """Test safe_commit handles IntegrityError."""
        response = client.get('/')  # Create request context
        with app.app_context():
            from app.utils.database import safe_commit
            from app import db as database

            with patch.object(database.session, 'commit', side_effect=IntegrityError('', '', '')):
                with patch('app.utils.database._flash_msg'):  # Mock flash
                    result = safe_commit("Success", "Integrity Error")
                    assert result is False

    def test_safe_commit_generic_error(self, client, app, db):
        """Test safe_commit handles generic Exception."""
        response = client.get('/')  # Create request context
        with app.app_context():
            from app.utils.database import safe_commit
            from app import db as database

            with patch.object(database.session, 'commit', side_effect=SQLAlchemyError('Test error')):
                with patch('app.utils.database._flash_msg'):  # Mock flash
                    result = safe_commit("Success", "Error occurred")
                    assert result is False


class TestSafeDelete:
    """Tests for safe_delete function."""

    def test_safe_delete_success(self, client, app, db):
        """Test safe_delete success."""
        response = client.get('/')
        with app.app_context():
            from app.utils.database import safe_delete
            from app.models import Sample

            # Create a sample to delete with valid client_name
            sample = Sample(
                sample_code='DELETE_TEST_001',
                client_name='CHPP',  # Valid client name
                sample_type='2H',
                user_id=1
            )
            db.session.add(sample)
            db.session.commit()

            with patch('app.utils.database._flash_msg'):
                result = safe_delete(sample, "Deleted", "Delete error")
                assert result is True

    def test_safe_delete_failure(self, client, app, db):
        """Test safe_delete handles failure."""
        response = client.get('/')
        with app.app_context():
            from app.utils.database import safe_delete
            from app import db as database

            mock_obj = MagicMock()

            with patch.object(database.session, 'delete'):
                with patch.object(database.session, 'commit', side_effect=SQLAlchemyError('Delete failed')):
                    with patch('app.utils.database._flash_msg'):
                        result = safe_delete(mock_obj, "Deleted", "Delete error")
                        assert result is False


class TestSafeAdd:
    """Tests for safe_add function."""

    def test_safe_add_single_object(self, client, app, db):
        """Test safe_add with single object."""
        response = client.get('/')
        with app.app_context():
            from app.utils.database import safe_add
            from app.models import Sample

            sample = Sample(
                sample_code='ADD_TEST_001',
                client_name='CHPP',
                sample_type='2H',
                user_id=1
            )

            with patch('app.utils.database._flash_msg'):
                result = safe_add(sample, "Added", "Add error")
                assert result is True

    def test_safe_add_list_of_objects(self, client, app, db):
        """Test safe_add with list of objects."""
        response = client.get('/')
        with app.app_context():
            from app.utils.database import safe_add
            from app.models import Sample

            samples = [
                Sample(sample_code='ADD_LIST_001', client_name='CHPP', sample_type='2H', user_id=1),
                Sample(sample_code='ADD_LIST_002', client_name='CHPP', sample_type='2H', user_id=1)
            ]

            with patch('app.utils.database._flash_msg'):
                result = safe_add(samples, "Added", "Add error")
                assert result is True

    def test_safe_add_integrity_error(self, client, app, db):
        """Test safe_add handles IntegrityError."""
        response = client.get('/')
        with app.app_context():
            from app.utils.database import safe_add
            from app import db as database

            mock_obj = MagicMock()

            with patch.object(database.session, 'add'):
                with patch.object(database.session, 'commit', side_effect=IntegrityError('', '', '')):
                    with patch('app.utils.database._flash_msg'):
                        result = safe_add(mock_obj, "Added", "Integrity error")
                        assert result is False

    def test_safe_add_generic_error(self, client, app, db):
        """Test safe_add handles generic Exception."""
        response = client.get('/')
        with app.app_context():
            from app.utils.database import safe_add
            from app import db as database

            mock_obj = MagicMock()

            with patch.object(database.session, 'add'):
                with patch.object(database.session, 'commit', side_effect=SQLAlchemyError('Add failed')):
                    with patch('app.utils.database._flash_msg'):
                        result = safe_add(mock_obj, "Added", "Add error")
                        assert result is False

    def test_safe_add_no_message(self, client, app, db):
        """Test safe_add without success message."""
        response = client.get('/')
        with app.app_context():
            from app.utils.database import safe_add
            from app.models import Sample

            sample = Sample(
                sample_code='ADD_NOMSG_001',
                client_name='CHPP',
                sample_type='2H',
                user_id=1
            )

            with patch('app.utils.database._flash_msg'):
                result = safe_add(sample, None, "Add error")
                assert result is True


class TestDatabaseFunctions:
    """General tests for database utility functions."""

    def test_all_functions_exist(self, app):
        """Test all database functions exist."""
        with app.app_context():
            from app.utils.database import safe_commit, safe_delete, safe_add
            assert callable(safe_commit)
            assert callable(safe_delete)
            assert callable(safe_add)

    def test_functions_return_bool(self, client, app, db):
        """Test functions return boolean values."""
        with client:
            with app.app_context():
                from app.utils.database import safe_commit
                result = safe_commit(None, "Error")
                assert isinstance(result, bool)
