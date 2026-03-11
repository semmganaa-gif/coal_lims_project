# -*- coding: utf-8 -*-
"""
Tests for app/utils/database.py
Database utility functions tests
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


class TestSafeCommit:
    """safe_commit function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.database import safe_commit
        assert callable(safe_commit)

    def test_successful_commit(self, app):
        """Successful commit returns True"""
        from app.utils.database import safe_commit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'commit'):
                result = safe_commit()
                assert result is True

    def test_success_message_flashed(self, app):
        """Success message is flashed"""
        from app.utils.database import safe_commit
        from app import db
        from flask import get_flashed_messages

        with app.test_request_context():
            with patch.object(db.session, 'commit'):
                safe_commit(success_msg="Амжилттай!")

            messages = get_flashed_messages(with_categories=True)
            assert any("Амжилттай" in msg for cat, msg in messages)

    def test_no_flash_without_success_msg(self, app):
        """No flash when success_msg is None"""
        from app.utils.database import safe_commit
        from app import db
        from flask import get_flashed_messages

        with app.test_request_context():
            with patch.object(db.session, 'commit'):
                safe_commit(success_msg=None)

            messages = get_flashed_messages()
            assert len(messages) == 0

    def test_integrity_error_returns_false(self, app):
        """IntegrityError returns False"""
        from app.utils.database import safe_commit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'commit', side_effect=IntegrityError("", "", "")):
                with patch.object(db.session, 'rollback'):
                    result = safe_commit()
                    assert result is False

    def test_integrity_error_rollback(self, app):
        """IntegrityError triggers rollback"""
        from app.utils.database import safe_commit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'commit', side_effect=IntegrityError("", "", "")):
                with patch.object(db.session, 'rollback') as mock_rollback:
                    safe_commit()
                    mock_rollback.assert_called_once()

    def test_integrity_error_flashes_message(self, app):
        """IntegrityError flashes error message"""
        from app.utils.database import safe_commit
        from app import db
        from flask import get_flashed_messages

        with app.test_request_context():
            with patch.object(db.session, 'commit', side_effect=IntegrityError("", "", "")):
                with patch.object(db.session, 'rollback'):
                    safe_commit(error_msg="Давхардсан код")

            messages = get_flashed_messages(with_categories=True)
            assert any("Давхардсан" in msg for cat, msg in messages)

    def test_general_exception_returns_false(self, app):
        """General exception returns False"""
        from app.utils.database import safe_commit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'commit', side_effect=SQLAlchemyError("DB Error")):
                with patch.object(db.session, 'rollback'):
                    result = safe_commit()
                    assert result is False

    def test_general_exception_flashes_error_msg(self, app):
        """General exception flashes the error_msg (not raw exception details)"""
        from app.utils.database import safe_commit
        from app import db
        from flask import get_flashed_messages

        with app.test_request_context():
            with patch.object(db.session, 'commit', side_effect=SQLAlchemyError("Specific Error")):
                with patch.object(db.session, 'rollback'):
                    safe_commit(error_msg="Custom error message")

            messages = get_flashed_messages()
            assert any("Custom error message" in msg for msg in messages)


class TestSafeDelete:
    """safe_delete function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.database import safe_delete
        assert callable(safe_delete)

    def test_successful_delete(self, app):
        """Successful delete returns True"""
        from app.utils.database import safe_delete
        from app import db

        mock_obj = MagicMock()

        with app.test_request_context():
            with patch.object(db.session, 'delete'):
                with patch.object(db.session, 'commit'):
                    result = safe_delete(mock_obj)
                    assert result is True

    def test_delete_called_with_object(self, app):
        """Delete is called with the object"""
        from app.utils.database import safe_delete
        from app import db

        mock_obj = MagicMock()

        with app.test_request_context():
            with patch.object(db.session, 'delete') as mock_delete:
                with patch.object(db.session, 'commit'):
                    safe_delete(mock_obj)
                    mock_delete.assert_called_once_with(mock_obj)

    def test_success_message_flashed(self, app):
        """Success message is flashed"""
        from app.utils.database import safe_delete
        from app import db
        from flask import get_flashed_messages

        mock_obj = MagicMock()

        with app.test_request_context():
            with patch.object(db.session, 'delete'):
                with patch.object(db.session, 'commit'):
                    safe_delete(mock_obj, success_msg="Устгагдлаа!")

            messages = get_flashed_messages(with_categories=True)
            assert any("Устгагдлаа" in msg for cat, msg in messages)

    def test_exception_returns_false(self, app):
        """Exception returns False"""
        from app.utils.database import safe_delete
        from app import db

        mock_obj = MagicMock()

        with app.test_request_context():
            with patch.object(db.session, 'delete', side_effect=SQLAlchemyError("Delete Error")):
                with patch.object(db.session, 'rollback'):
                    result = safe_delete(mock_obj)
                    assert result is False

    def test_exception_triggers_rollback(self, app):
        """Exception triggers rollback"""
        from app.utils.database import safe_delete
        from app import db

        mock_obj = MagicMock()

        with app.test_request_context():
            with patch.object(db.session, 'delete', side_effect=SQLAlchemyError("Error")):
                with patch.object(db.session, 'rollback') as mock_rollback:
                    safe_delete(mock_obj)
                    mock_rollback.assert_called_once()

    def test_error_message_flashed(self, app):
        """Error message is flashed on exception"""
        from app.utils.database import safe_delete
        from app import db
        from flask import get_flashed_messages

        mock_obj = MagicMock()

        with app.test_request_context():
            with patch.object(db.session, 'delete', side_effect=SQLAlchemyError("Error")):
                with patch.object(db.session, 'rollback'):
                    safe_delete(mock_obj, error_msg="Устгаж чадсангүй")

            messages = get_flashed_messages()
            assert any("Устгаж" in msg for msg in messages)


class TestSafeAdd:
    """safe_add function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.database import safe_add
        assert callable(safe_add)

    def test_successful_add_single(self, app):
        """Successful add single object returns True"""
        from app.utils.database import safe_add
        from app import db

        mock_obj = MagicMock()

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit'):
                    result = safe_add(mock_obj)
                    assert result is True

    def test_add_called_with_object(self, app):
        """Add is called with the object"""
        from app.utils.database import safe_add
        from app import db

        mock_obj = MagicMock()

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch.object(db.session, 'commit'):
                    safe_add(mock_obj)
                    mock_add.assert_called_once_with(mock_obj)

    def test_add_all_called_with_list(self, app):
        """Add_all is called when passing list"""
        from app.utils.database import safe_add
        from app import db

        mock_objs = [MagicMock(), MagicMock()]

        with app.test_request_context():
            with patch.object(db.session, 'add_all') as mock_add_all:
                with patch.object(db.session, 'commit'):
                    safe_add(mock_objs)
                    mock_add_all.assert_called_once_with(mock_objs)

    def test_success_message_flashed(self, app):
        """Success message is flashed"""
        from app.utils.database import safe_add
        from app import db
        from flask import get_flashed_messages

        mock_obj = MagicMock()

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit'):
                    safe_add(mock_obj, success_msg="Нэмэгдлээ!")

            messages = get_flashed_messages(with_categories=True)
            assert any("Нэмэгдлээ" in msg for cat, msg in messages)

    def test_integrity_error_returns_false(self, app):
        """IntegrityError returns False"""
        from app.utils.database import safe_add
        from app import db

        mock_obj = MagicMock()

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit', side_effect=IntegrityError("", "", "")):
                    with patch.object(db.session, 'rollback'):
                        result = safe_add(mock_obj)
                        assert result is False

    def test_integrity_error_flashes_message(self, app):
        """IntegrityError flashes error message"""
        from app.utils.database import safe_add
        from app import db
        from flask import get_flashed_messages

        mock_obj = MagicMock()

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit', side_effect=IntegrityError("", "", "")):
                    with patch.object(db.session, 'rollback'):
                        safe_add(mock_obj, error_msg="Давхардсан")

            messages = get_flashed_messages()
            assert any("Давхардсан" in msg for msg in messages)

    def test_general_exception_returns_false(self, app):
        """General exception returns False"""
        from app.utils.database import safe_add
        from app import db

        mock_obj = MagicMock()

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit', side_effect=SQLAlchemyError("Error")):
                    with patch.object(db.session, 'rollback'):
                        result = safe_add(mock_obj)
                        assert result is False

    def test_exception_flashes_error_msg(self, app):
        """Exception flashes the error_msg (not raw exception details)"""
        from app.utils.database import safe_add
        from app import db
        from flask import get_flashed_messages

        mock_obj = MagicMock()

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit', side_effect=SQLAlchemyError("Specific DB Error")):
                    with patch.object(db.session, 'rollback'):
                        safe_add(mock_obj, error_msg="Нэмэхэд алдаа")

            messages = get_flashed_messages()
            assert any("Нэмэхэд алдаа" in msg for msg in messages)
