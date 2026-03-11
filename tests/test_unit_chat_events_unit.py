# -*- coding: utf-8 -*-
"""
Chat Events - unit тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from app.routes.chat.events import (
    get_user_room,
    update_online_status,
    online_users,
)


class TestGetUserRoom:
    """get_user_room function tests"""

    def test_returns_room_name(self):
        """Returns correct room name"""
        assert get_user_room(1) == "user_1"
        assert get_user_room(100) == "user_100"
        assert get_user_room(999) == "user_999"

    def test_with_different_ids(self):
        """Works with different user IDs"""
        for i in range(10):
            assert get_user_room(i) == f"user_{i}"


class TestOnlineUsers:
    """online_users tracking tests"""

    def test_online_users_is_dict(self):
        """online_users is a dictionary"""
        assert isinstance(online_users, dict)


class TestUpdateOnlineStatus:
    """update_online_status function tests"""

    @patch('app.routes.chat.events.db')
    @patch('app.routes.chat.events.now_mn')
    def test_update_existing_status(self, mock_now, mock_db):
        """Update existing user online status"""
        mock_now.return_value = MagicMock()
        mock_status = MagicMock()
        mock_db.session.get.return_value = mock_status

        update_online_status(1, True, 'socket123')

        assert mock_status.is_online is True
        assert mock_status.socket_id == 'socket123'
        mock_db.session.commit.assert_called_once()

    @patch('app.routes.chat.events.db')
    @patch('app.routes.chat.events.now_mn')
    def test_create_new_status(self, mock_now, mock_db):
        """Create new status when not exists"""
        mock_now.return_value = MagicMock()
        mock_db.session.get.return_value = None

        update_online_status(2, True, 'socket456')

        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()

    @patch('app.routes.chat.events.db')
    @patch('app.routes.chat.events.now_mn')
    def test_set_offline(self, mock_now, mock_db):
        """Set user offline"""
        mock_now.return_value = MagicMock()
        mock_status = MagicMock()
        mock_db.session.get.return_value = mock_status

        update_online_status(1, False, None)

        assert mock_status.is_online is False
        assert mock_status.socket_id is None
        mock_db.session.commit.assert_called_once()

    @patch('app.routes.chat.events.logger')
    @patch('app.routes.chat.events.db')
    @patch('app.routes.chat.events.now_mn')
    def test_handles_exception(self, mock_now, mock_db, mock_logger):
        """Handles database exceptions"""
        mock_now.return_value = MagicMock()
        from sqlalchemy.exc import SQLAlchemyError
        mock_db.session.get.side_effect = SQLAlchemyError("DB Error")

        update_online_status(1, True, 'socket123')

        mock_logger.error.assert_called_once()
        mock_db.session.rollback.assert_called_once()


class TestSocketIOHandlers:
    """SocketIO handler tests with mocks"""

    @pytest.mark.skip(reason="Requires SocketIO test client context")
    def test_handle_connect_authenticated(self):
        """Test connect handler for authenticated user - requires SocketIO client"""
        pass

    @patch('app.routes.chat.events.current_user')
    def test_handle_connect_unauthenticated(self, mock_user):
        """Test connect handler for unauthenticated user"""
        from app.routes.chat.events import handle_connect

        mock_user.is_authenticated = False

        result = handle_connect()
        assert result is False

    @patch('app.routes.chat.events.emit')
    @patch('app.routes.chat.events.leave_room')
    @patch('app.routes.chat.events.current_user')
    @patch('app.routes.chat.events.update_online_status')
    def test_handle_disconnect(self, mock_update, mock_user, mock_leave, mock_emit):
        """Test disconnect handler"""
        from app.routes.chat.events import handle_disconnect, online_users

        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_user.username = "testuser"
        online_users[1] = "socket123"

        handle_disconnect()

        mock_leave.assert_called()
        mock_update.assert_called_once_with(1, False, None)
        assert 1 not in online_users

    @patch('app.routes.chat.events.current_user')
    def test_handle_disconnect_unauthenticated(self, mock_user):
        """Test disconnect handler for unauthenticated user"""
        from app.routes.chat.events import handle_disconnect

        mock_user.is_authenticated = False

        result = handle_disconnect()
        assert result is None

    @patch('app.routes.chat.events.emit')
    @patch('app.routes.chat.events.current_user')
    def test_handle_send_message_unauthenticated(self, mock_user, mock_emit):
        """Test send_message for unauthenticated user"""
        from app.routes.chat.events import handle_send_message

        mock_user.is_authenticated = False

        handle_send_message({})

        mock_emit.assert_called_once_with('error', {'message': 'Нэвтрэх шаардлагатай'})

    @patch('app.routes.chat.events.emit')
    @patch('app.routes.chat.events.current_user')
    def test_handle_send_message_empty(self, mock_user, mock_emit):
        """Test send_message with empty message"""
        from app.routes.chat.events import handle_send_message

        mock_user.is_authenticated = True

        handle_send_message({'message': ''})

        mock_emit.assert_called_with('error', {'message': 'Мессеж хоосон байна'})

    @patch('app.routes.chat.events.UserRepository')
    @patch('app.routes.chat.events.emit')
    @patch('app.routes.chat.events.current_user')
    def test_handle_send_message_invalid_receiver(self, mock_user, mock_emit, mock_user_repo):
        """Test send_message with invalid receiver"""
        from app.routes.chat.events import handle_send_message

        mock_user.is_authenticated = True
        mock_user_repo.get_by_id.return_value = None

        handle_send_message({'message': 'test', 'receiver_id': 999})

        mock_emit.assert_called_with('error', {'message': 'Хүлээн авагч олдсонгүй'})

    @patch('app.routes.chat.events.emit')
    @patch('app.routes.chat.events.current_user')
    def test_handle_send_file_unauthenticated(self, mock_user, mock_emit):
        """Test send_file for unauthenticated user"""
        from app.routes.chat.events import handle_send_file

        mock_user.is_authenticated = False

        handle_send_file({})

        mock_emit.assert_called_once_with('error', {'message': 'Нэвтрэх шаардлагатай'})

    @patch('app.routes.chat.events.emit')
    @patch('app.routes.chat.events.current_user')
    def test_handle_send_file_no_url(self, mock_user, mock_emit):
        """Test send_file without URL"""
        from app.routes.chat.events import handle_send_file

        mock_user.is_authenticated = True

        handle_send_file({'file_url': None})

        mock_emit.assert_called_with('error', {'message': 'Файл URL шаардлагатай'})

    @patch('app.routes.chat.events.current_user')
    def test_handle_delete_message_unauthenticated(self, mock_user):
        """Test delete_message for unauthenticated user"""
        from app.routes.chat.events import handle_delete_message

        mock_user.is_authenticated = False

        result = handle_delete_message({})
        assert result is None

    @patch('app.routes.chat.events.emit')
    @patch('app.routes.chat.events.db')
    @patch('app.routes.chat.events.current_user')
    def test_handle_delete_message_not_found(self, mock_user, mock_db, mock_emit):
        """Test delete_message when message not found"""
        from app.routes.chat.events import handle_delete_message

        mock_user.is_authenticated = True
        mock_db.session.get.return_value = None

        handle_delete_message({'message_id': 999})

        mock_emit.assert_called_with('error', {'message': 'Мессеж олдсонгүй'})

    @patch('app.routes.chat.events.emit')
    @patch('app.routes.chat.events.db')
    @patch('app.routes.chat.events.current_user')
    def test_handle_delete_message_not_owner(self, mock_user, mock_db, mock_emit):
        """Test delete_message when not the owner"""
        from app.routes.chat.events import handle_delete_message

        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_msg = MagicMock(sender_id=2)  # Different user
        mock_db.session.get.return_value = mock_msg

        handle_delete_message({'message_id': 1})

        mock_emit.assert_called_with('error', {'message': 'Зөвхөн өөрийн мессежийг устгах боломжтой'})

    @patch('app.routes.chat.events.current_user')
    def test_handle_broadcast_unauthenticated(self, mock_user):
        """Test broadcast for unauthenticated user"""
        from app.routes.chat.events import handle_broadcast

        mock_user.is_authenticated = False

        result = handle_broadcast({})
        assert result is None

    @patch('app.routes.chat.events.emit')
    @patch('app.routes.chat.events.current_user')
    def test_handle_broadcast_not_admin(self, mock_user, mock_emit):
        """Test broadcast for non-admin user"""
        from app.routes.chat.events import handle_broadcast

        mock_user.is_authenticated = True
        mock_user.role = 'analyst'

        handle_broadcast({'message': 'test'})

        mock_emit.assert_called_with('error', {'message': 'Зөвхөн ахлах болон админ зарлал илгээх эрхтэй'})

    @patch('app.routes.chat.events.current_user')
    def test_handle_broadcast_empty_message(self, mock_user):
        """Test broadcast with empty message"""
        from app.routes.chat.events import handle_broadcast

        mock_user.is_authenticated = True
        mock_user.role = 'admin'

        result = handle_broadcast({'message': ''})
        assert result is None

    @patch('app.routes.chat.events.current_user')
    def test_handle_mark_read_unauthenticated(self, mock_user):
        """Test mark_read for unauthenticated user"""
        from app.routes.chat.events import handle_mark_read

        mock_user.is_authenticated = False

        result = handle_mark_read({})
        assert result is None

    @patch('app.routes.chat.events.current_user')
    def test_handle_typing_unauthenticated(self, mock_user):
        """Test typing for unauthenticated user"""
        from app.routes.chat.events import handle_typing

        mock_user.is_authenticated = False

        result = handle_typing({})
        assert result is None

    @patch('app.routes.chat.events.emit')
    @patch('app.routes.chat.events.current_user')
    def test_handle_typing(self, mock_user, mock_emit):
        """Test typing handler"""
        from app.routes.chat.events import handle_typing

        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_user.username = "testuser"

        handle_typing({'receiver_id': 2})

        mock_emit.assert_called_once()

    @patch('app.routes.chat.events.current_user')
    def test_handle_stop_typing_unauthenticated(self, mock_user):
        """Test stop_typing for unauthenticated user"""
        from app.routes.chat.events import handle_stop_typing

        mock_user.is_authenticated = False

        result = handle_stop_typing({})
        assert result is None

    @patch('app.routes.chat.events.emit')
    @patch('app.routes.chat.events.current_user')
    def test_handle_stop_typing(self, mock_user, mock_emit):
        """Test stop_typing handler"""
        from app.routes.chat.events import handle_stop_typing

        mock_user.is_authenticated = True
        mock_user.id = 1

        handle_stop_typing({'receiver_id': 2})

        mock_emit.assert_called_once()

    @patch('app.routes.chat.events.current_user')
    def test_handle_get_online_users_unauthenticated(self, mock_user):
        """Test get_online_users for unauthenticated user"""
        from app.routes.chat.events import handle_get_online_users

        mock_user.is_authenticated = False

        result = handle_get_online_users()
        assert result is None

    @patch('app.routes.chat.events.emit')
    @patch('app.routes.chat.events.User')
    @patch('app.routes.chat.events.current_user')
    def test_handle_get_online_users(self, mock_user, mock_user_model, mock_emit):
        """Test get_online_users handler"""
        from app.routes.chat.events import handle_get_online_users, online_users

        mock_user.is_authenticated = True

        # Clear and set online users
        online_users.clear()
        online_users[1] = 'socket1'
        online_users[2] = 'socket2'

        mock_user1 = MagicMock(id=1, username='user1', role='analyst')
        mock_user2 = MagicMock(id=2, username='user2', role='senior')
        mock_user_model.query.filter.return_value.all.return_value = [mock_user1, mock_user2]

        handle_get_online_users()

        mock_emit.assert_called_once()
        call_args = mock_emit.call_args
        assert 'online_users_list' in str(call_args)
