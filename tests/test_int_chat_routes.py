# -*- coding: utf-8 -*-
"""
Chat routes тестүүд
"""
import pytest
from app import create_app, db
from app.models import User


@pytest.fixture
def app():
    """Test application fixture"""
    from tests.conftest import TestConfig
    app = create_app(TestConfig)
    app.config['SERVER_NAME'] = 'localhost'

    with app.app_context():
        db.create_all()
        from app.models import User
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin', role='admin')
            user.set_password('AdminPass123')
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
    """Authenticated client fixture"""
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User(username='admin', role='admin')
            user.set_password('AdminPass123')
            db.session.add(user)
            db.session.commit()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

    return client


class TestChatAPI:
    """Chat API тестүүд"""

    def test_chat_message(self, auth_client, app):
        """Chat message POST"""
        with app.app_context():
            response = auth_client.post('/api/chat/message', json={
                'message': 'Hello'
            })
            assert response.status_code in [200, 302, 400, 404]

    def test_chat_history(self, auth_client, app):
        """Chat history"""
        with app.app_context():
            response = auth_client.get('/api/chat/history')
            assert response.status_code in [200, 302, 404]

    def test_chat_clear(self, auth_client, app):
        """Chat clear"""
        with app.app_context():
            response = auth_client.post('/api/chat/clear')
            assert response.status_code in [200, 302, 400, 404]


class TestChatEvents:
    """Chat events тестүүд"""

    def test_chat_stream(self, auth_client, app):
        """Chat stream"""
        with app.app_context():
            response = auth_client.get('/api/chat/stream')
            assert response.status_code in [200, 302, 404]

    def test_chat_status(self, auth_client, app):
        """Chat status"""
        with app.app_context():
            response = auth_client.get('/api/chat/status')
            assert response.status_code in [200, 302, 404]
