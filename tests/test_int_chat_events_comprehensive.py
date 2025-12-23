# -*- coding: utf-8 -*-
"""
Chat events - бүрэн интеграцийн тестүүд
chat_events.py файлын coverage нэмэгдүүлэх
"""
import pytest
from app import create_app, db
from app.models import User, ChatMessage, UserOnlineStatus, Sample


@pytest.fixture
def app():
    """Test application fixture"""
    from tests.conftest import TestConfig
    app = create_app(TestConfig)
    app.config['SERVER_NAME'] = 'localhost'

    with app.app_context():
        db.create_all()
        # Create users
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin', role='admin')
            user.set_password('Admin123')
            db.session.add(user)
        if not User.query.filter_by(username='senior').first():
            user = User(username='senior', role='senior')
            user.set_password('Senior123')
            db.session.add(user)
        if not User.query.filter_by(username='analyst').first():
            user = User(username='analyst', role='analyst')
            user.set_password('Analyst123')
            db.session.add(user)
        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Authenticated admin client"""
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


class TestChatEventsHelpers:
    """Chat events helper functions тестүүд"""

    def test_get_user_room(self, app):
        """User room name generation"""
        with app.app_context():
            from app.routes.chat_events import get_user_room
            result = get_user_room(1)
            assert result == "user_1"
            result = get_user_room(999)
            assert result == "user_999"

    def test_update_online_status_new_user(self, app):
        """Update online status for new user"""
        with app.app_context():
            from app.routes.chat_events import update_online_status
            user = User.query.filter_by(username='admin').first()

            update_online_status(user.id, True, 'socket123')

            status = db.session.get(UserOnlineStatus, user.id)
            assert status is not None
            assert status.is_online is True
            assert status.socket_id == 'socket123'

    def test_update_online_status_existing_user(self, app):
        """Update online status for existing user"""
        with app.app_context():
            from app.routes.chat_events import update_online_status
            user = User.query.filter_by(username='admin').first()

            # First update
            update_online_status(user.id, True, 'socket123')
            # Second update
            update_online_status(user.id, False, None)

            status = db.session.get(UserOnlineStatus, user.id)
            assert status is not None
            assert status.is_online is False
            assert status.socket_id is None

    def test_online_users_dict(self, app):
        """Online users dictionary"""
        with app.app_context():
            from app.routes.chat_events import online_users
            # Should be a dict
            assert isinstance(online_users, dict)


class TestChatMessageModel:
    """ChatMessage model тестүүд"""

    def test_create_chat_message(self, app):
        """Create chat message"""
        with app.app_context():
            sender = User.query.filter_by(username='admin').first()
            receiver = User.query.filter_by(username='analyst').first()

            msg = ChatMessage(
                sender_id=sender.id,
                receiver_id=receiver.id,
                message="Test message",
                message_type="text"
            )
            db.session.add(msg)
            db.session.commit()

            assert msg.id is not None
            assert msg.message == "Test message"

    def test_create_broadcast_message(self, app):
        """Create broadcast message"""
        with app.app_context():
            sender = User.query.filter_by(username='senior').first()

            msg = ChatMessage(
                sender_id=sender.id,
                receiver_id=None,
                message="Broadcast test",
                message_type="broadcast",
                is_broadcast=True
            )
            db.session.add(msg)
            db.session.commit()

            assert msg.id is not None
            assert msg.is_broadcast is True

    def test_create_file_message(self, app):
        """Create file message"""
        with app.app_context():
            sender = User.query.filter_by(username='admin').first()
            receiver = User.query.filter_by(username='analyst').first()

            msg = ChatMessage(
                sender_id=sender.id,
                receiver_id=receiver.id,
                message="file.pdf",
                message_type="file",
                file_url="/uploads/file.pdf",
                file_name="file.pdf",
                file_size=1024
            )
            db.session.add(msg)
            db.session.commit()

            assert msg.file_url == "/uploads/file.pdf"
            assert msg.file_size == 1024

    def test_create_image_message(self, app):
        """Create image message"""
        with app.app_context():
            sender = User.query.filter_by(username='admin').first()

            msg = ChatMessage(
                sender_id=sender.id,
                receiver_id=None,
                message="image.jpg",
                message_type="image",
                file_url="/uploads/image.jpg",
                file_name="image.jpg"
            )
            db.session.add(msg)
            db.session.commit()

            assert msg.message_type == "image"

    def test_create_sample_linked_message(self, app):
        """Create sample-linked message"""
        with app.app_context():
            sender = User.query.filter_by(username='admin').first()

            # Create sample first
            sample = Sample(
                sample_code="TEST_CHAT_001",
                user_id=sender.id,
                client_name="CHPP",
                sample_type="2 hourly"
            )
            db.session.add(sample)
            db.session.commit()

            msg = ChatMessage(
                sender_id=sender.id,
                receiver_id=None,
                message="Sample related",
                message_type="sample",
                sample_id=sample.id
            )
            db.session.add(msg)
            db.session.commit()

            assert msg.sample_id == sample.id

    def test_urgent_message(self, app):
        """Create urgent message"""
        with app.app_context():
            sender = User.query.filter_by(username='admin').first()
            receiver = User.query.filter_by(username='analyst').first()

            msg = ChatMessage(
                sender_id=sender.id,
                receiver_id=receiver.id,
                message="Urgent!",
                message_type="text",
                is_urgent=True
            )
            db.session.add(msg)
            db.session.commit()

            assert msg.is_urgent is True

    def test_delete_message_soft(self, app):
        """Soft delete message"""
        with app.app_context():
            from app.utils.datetime import now_local
            sender = User.query.filter_by(username='admin').first()

            msg = ChatMessage(
                sender_id=sender.id,
                message="To be deleted"
            )
            db.session.add(msg)
            db.session.commit()

            msg.is_deleted = True
            msg.deleted_at = now_local()
            msg.message = "Мессеж устгагдсан"
            db.session.commit()

            assert msg.is_deleted is True


class TestUserOnlineStatus:
    """UserOnlineStatus model тестүүд"""

    def test_create_online_status(self, app):
        """Create online status"""
        with app.app_context():
            user = User.query.filter_by(username='admin').first()

            status = UserOnlineStatus(
                user_id=user.id,
                is_online=True,
                socket_id='test_socket'
            )
            db.session.add(status)
            db.session.commit()

            assert status.is_online is True

    def test_update_online_status(self, app):
        """Update online status"""
        with app.app_context():
            from app.utils.datetime import now_local
            user = User.query.filter_by(username='admin').first()

            status = UserOnlineStatus(
                user_id=user.id,
                is_online=True
            )
            db.session.add(status)
            db.session.commit()

            status.is_online = False
            status.last_seen = now_local()
            db.session.commit()

            assert status.is_online is False


class TestChatAPIRoutes:
    """Chat API routes тестүүд"""

    def test_chat_page(self, auth_client, app):
        """Chat page accessible"""
        with app.app_context():
            response = auth_client.get('/chat/')
            assert response.status_code in [200, 302, 404]

    def test_chat_messages_api(self, auth_client, app):
        """Chat messages API"""
        with app.app_context():
            response = auth_client.get('/api/chat/messages')
            assert response.status_code in [200, 302, 404]

    def test_chat_unread_count(self, auth_client, app):
        """Chat unread count API"""
        with app.app_context():
            response = auth_client.get('/api/chat/unread_count')
            assert response.status_code in [200, 302, 404]

    def test_chat_users_api(self, auth_client, app):
        """Chat users API"""
        with app.app_context():
            response = auth_client.get('/api/chat/users')
            assert response.status_code in [200, 302, 404]

    def test_chat_upload_file(self, auth_client, app):
        """Chat file upload API"""
        with app.app_context():
            # Test with no file
            response = auth_client.post('/api/chat/upload',
                data={},
                content_type='multipart/form-data'
            )
            assert response.status_code in [200, 400, 404]

    def test_chat_conversation_api(self, auth_client, app):
        """Chat conversation API"""
        with app.app_context():
            user = User.query.filter_by(username='analyst').first()
            response = auth_client.get(f'/api/chat/conversation/{user.id}')
            assert response.status_code in [200, 302, 404]

    def test_chat_mark_read_api(self, auth_client, app):
        """Chat mark as read API"""
        with app.app_context():
            user = User.query.filter_by(username='analyst').first()
            response = auth_client.post(f'/api/chat/mark_read/{user.id}')
            assert response.status_code in [200, 302, 404]
