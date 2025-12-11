# tests/unit/test_database.py
# -*- coding: utf-8 -*-
"""
Database utility functions тест
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import IntegrityError


class TestSafeCommit:
    """safe_commit() функцийн тест"""

    def test_safe_commit_success(self, app):
        """Амжилттай commit"""
        from app.utils.database import safe_commit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'commit') as mock_commit:
                mock_commit.return_value = None
                result = safe_commit(success_msg="Амжилттай")
                assert result is True
                mock_commit.assert_called_once()

    def test_safe_commit_success_no_message(self, app):
        """Амжилттай commit (мессежгүй)"""
        from app.utils.database import safe_commit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'commit') as mock_commit:
                result = safe_commit()  # No success message
                assert result is True

    def test_safe_commit_integrity_error(self, app):
        """IntegrityError"""
        from app.utils.database import safe_commit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'commit', side_effect=IntegrityError(None, None, None)):
                with patch.object(db.session, 'rollback') as mock_rollback:
                    result = safe_commit(error_msg="Давхардсан")
                    assert result is False
                    mock_rollback.assert_called_once()

    def test_safe_commit_generic_error(self, app):
        """Generic алдаа"""
        from app.utils.database import safe_commit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'commit', side_effect=Exception("DB error")):
                with patch.object(db.session, 'rollback') as mock_rollback:
                    result = safe_commit()
                    assert result is False
                    mock_rollback.assert_called_once()


class TestSafeDelete:
    """safe_delete() функцийн тест"""

    def test_safe_delete_success(self, app):
        """Амжилттай устгах"""
        from app.utils.database import safe_delete
        from app import db

        mock_obj = Mock()

        with app.test_request_context():
            with patch.object(db.session, 'delete') as mock_delete:
                with patch.object(db.session, 'commit') as mock_commit:
                    result = safe_delete(mock_obj, success_msg="Устгагдлаа")
                    assert result is True
                    mock_delete.assert_called_once_with(mock_obj)
                    mock_commit.assert_called_once()

    def test_safe_delete_success_no_message(self, app):
        """Амжилттай устгах (мессежгүй)"""
        from app.utils.database import safe_delete
        from app import db

        mock_obj = Mock()

        with app.test_request_context():
            with patch.object(db.session, 'delete'):
                with patch.object(db.session, 'commit'):
                    result = safe_delete(mock_obj)  # No success message
                    assert result is True

    def test_safe_delete_error(self, app):
        """Устгахад алдаа"""
        from app.utils.database import safe_delete
        from app import db

        mock_obj = Mock()

        with app.test_request_context():
            with patch.object(db.session, 'delete', side_effect=Exception("Delete error")):
                with patch.object(db.session, 'rollback') as mock_rollback:
                    result = safe_delete(mock_obj)
                    assert result is False
                    mock_rollback.assert_called_once()


class TestSafeAdd:
    """safe_add() функцийн тест"""

    def test_safe_add_single_object(self, app):
        """Нэг объект нэмэх"""
        from app.utils.database import safe_add
        from app import db

        mock_obj = Mock()

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch.object(db.session, 'commit'):
                    result = safe_add(mock_obj, success_msg="Нэмэгдлээ")
                    assert result is True
                    mock_add.assert_called_once_with(mock_obj)

    def test_safe_add_list_objects(self, app):
        """Олон объект нэмэх (list)"""
        from app.utils.database import safe_add
        from app import db

        mock_objs = [Mock(), Mock(), Mock()]

        with app.test_request_context():
            with patch.object(db.session, 'add_all') as mock_add_all:
                with patch.object(db.session, 'commit'):
                    result = safe_add(mock_objs)
                    assert result is True
                    mock_add_all.assert_called_once_with(mock_objs)

    def test_safe_add_integrity_error(self, app):
        """IntegrityError нэмэхэд"""
        from app.utils.database import safe_add
        from app import db

        mock_obj = Mock()

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit', side_effect=IntegrityError(None, None, None)):
                    with patch.object(db.session, 'rollback') as mock_rollback:
                        result = safe_add(mock_obj, error_msg="Давхардсан")
                        assert result is False
                        mock_rollback.assert_called_once()

    def test_safe_add_generic_error(self, app):
        """Generic алдаа нэмэхэд"""
        from app.utils.database import safe_add
        from app import db

        mock_obj = Mock()

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit', side_effect=Exception("Add error")):
                    with patch.object(db.session, 'rollback') as mock_rollback:
                        result = safe_add(mock_obj)
                        assert result is False
                        mock_rollback.assert_called_once()
