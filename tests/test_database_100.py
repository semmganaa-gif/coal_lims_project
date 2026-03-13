# -*- coding: utf-8 -*-
"""
database.py модулийн 100% coverage тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


class TestDatabaseImport:
    """Модуль импорт тест"""

    def test_import_module(self):
        from app.utils import database
        assert database is not None

    def test_import_safe_commit(self):
        from app.utils.database import safe_commit
        assert safe_commit is not None
        assert callable(safe_commit)

    def test_import_safe_delete(self):
        from app.utils.database import safe_delete
        assert safe_delete is not None
        assert callable(safe_delete)

    def test_import_safe_add(self):
        from app.utils.database import safe_add
        assert safe_add is not None
        assert callable(safe_add)


class TestSafeCommit:
    """safe_commit функцийн тест"""

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_commit_success_with_message(self, mock_db, mock_flash):
        from app.utils.database import safe_commit

        result = safe_commit(success_msg="Амжилттай!")

        assert result is True
        mock_db.session.commit.assert_called_once()
        mock_flash.assert_called_with("Амжилттай!", "success")

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_commit_success_no_message(self, mock_db, mock_flash):
        from app.utils.database import safe_commit

        result = safe_commit()

        assert result is True
        mock_db.session.commit.assert_called_once()
        mock_flash.assert_not_called()

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_commit_integrity_error(self, mock_db, mock_flash):
        from app.utils.database import safe_commit

        mock_db.session.commit.side_effect = IntegrityError("statement", "params", "orig")

        result = safe_commit(error_msg="Давхардсан код")

        assert result is False
        mock_db.session.rollback.assert_called_once()
        mock_flash.assert_called_with("Давхардсан код", "danger")

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_commit_general_exception(self, mock_db, mock_flash):
        from app.utils.database import safe_commit

        mock_db.session.commit.side_effect = SQLAlchemyError("Unknown error")

        result = safe_commit(error_msg="Алдаа гарлаа")

        assert result is False
        mock_db.session.rollback.assert_called_once()
        mock_flash.assert_called()
        call_args = mock_flash.call_args[0]
        assert "Алдаа гарлаа" in call_args[0]

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_commit_default_error_message(self, mock_db, mock_flash):
        from app.utils.database import safe_commit

        mock_db.session.commit.side_effect = IntegrityError("stmt", "params", "orig")

        result = safe_commit()

        assert result is False
        mock_flash.assert_called_with("Error saving data", "danger")


class TestSafeDelete:
    """safe_delete функцийн тест"""

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_delete_success_with_message(self, mock_db, mock_flash):
        from app.utils.database import safe_delete

        obj = MagicMock()
        result = safe_delete(obj, success_msg="Устгагдлаа")

        assert result is True
        mock_db.session.delete.assert_called_once_with(obj)
        mock_db.session.commit.assert_called_once()
        mock_flash.assert_called_with("Устгагдлаа", "success")

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_delete_success_no_message(self, mock_db, mock_flash):
        from app.utils.database import safe_delete

        obj = MagicMock()
        result = safe_delete(obj)

        assert result is True
        mock_db.session.delete.assert_called_once_with(obj)
        mock_flash.assert_not_called()

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_delete_exception(self, mock_db, mock_flash):
        from app.utils.database import safe_delete

        obj = MagicMock()
        mock_db.session.delete.side_effect = SQLAlchemyError("FK constraint")

        result = safe_delete(obj, error_msg="Устгах боломжгүй")

        assert result is False
        mock_db.session.rollback.assert_called_once()
        mock_flash.assert_called()
        call_args = mock_flash.call_args[0]
        assert "Устгах боломжгүй" in call_args[0]

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_delete_default_error_message(self, mock_db, mock_flash):
        from app.utils.database import safe_delete

        obj = MagicMock()
        mock_db.session.commit.side_effect = SQLAlchemyError("Error")

        result = safe_delete(obj)

        assert result is False
        call_args = mock_flash.call_args[0]
        assert "Устгахад алдаа гарлаа" in call_args[0]


class TestSafeAdd:
    """safe_add функцийн тест"""

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_add_single_object_success(self, mock_db, mock_flash):
        from app.utils.database import safe_add

        obj = MagicMock()
        result = safe_add(obj, success_msg="Нэмэгдлээ")

        assert result is True
        mock_db.session.add.assert_called_once_with(obj)
        mock_db.session.commit.assert_called_once()
        mock_flash.assert_called_with("Нэмэгдлээ", "success")

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_add_list_of_objects(self, mock_db, mock_flash):
        from app.utils.database import safe_add

        obj1 = MagicMock()
        obj2 = MagicMock()
        obj_list = [obj1, obj2]

        result = safe_add(obj_list, success_msg="Бүгд нэмэгдлээ")

        assert result is True
        mock_db.session.add_all.assert_called_once_with(obj_list)
        mock_db.session.commit.assert_called_once()

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_add_success_no_message(self, mock_db, mock_flash):
        from app.utils.database import safe_add

        obj = MagicMock()
        result = safe_add(obj)

        assert result is True
        mock_flash.assert_not_called()

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_add_integrity_error(self, mock_db, mock_flash):
        from app.utils.database import safe_add

        obj = MagicMock()
        mock_db.session.commit.side_effect = IntegrityError("stmt", "params", "orig")

        result = safe_add(obj, error_msg="Давхардсан утга")

        assert result is False
        mock_db.session.rollback.assert_called_once()
        mock_flash.assert_called_with("Давхардсан утга", "danger")

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_add_general_exception(self, mock_db, mock_flash):
        from app.utils.database import safe_add

        obj = MagicMock()
        mock_db.session.commit.side_effect = SQLAlchemyError("Connection lost")

        result = safe_add(obj, error_msg="Нэмэх үед алдаа")

        assert result is False
        mock_db.session.rollback.assert_called_once()
        call_args = mock_flash.call_args[0]
        assert "Нэмэх үед алдаа" in call_args[0]

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_add_default_error_message(self, mock_db, mock_flash):
        from app.utils.database import safe_add

        obj = MagicMock()
        mock_db.session.commit.side_effect = IntegrityError("stmt", "params", "orig")

        result = safe_add(obj)

        assert result is False
        mock_flash.assert_called_with("Нэмэхэд алдаа гарлаа", "danger")

    @patch('app.utils.database._flash_msg')
    @patch('app.utils.database.db')
    def test_add_empty_list(self, mock_db, mock_flash):
        from app.utils.database import safe_add

        result = safe_add([], success_msg="OK")

        assert result is True
        mock_db.session.add_all.assert_called_once_with([])
