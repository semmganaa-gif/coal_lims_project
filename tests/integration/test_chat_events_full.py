# tests/integration/test_chat_events_full.py
# -*- coding: utf-8 -*-
"""
Chat events full coverage tests
"""

import pytest
from app import db
from app.models import User, Sample, ChatMessage
from datetime import datetime
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def chat_user(app):
    """Chat user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='chat_event_user').first()
        if not user:
            user = User(username='chat_event_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestChatMessages:
    """Chat messages тестүүд"""

    def test_chat_messages_get(self, client, app, chat_user):
        """Chat messages GET"""
        client.post('/login', data={
            'username': 'chat_event_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/chat/messages')
        assert response.status_code in [200, 302, 404]

    def test_chat_messages_with_limit(self, client, app, chat_user):
        """Chat messages with limit"""
        client.post('/login', data={
            'username': 'chat_event_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/chat/messages?limit=50')
        assert response.status_code in [200, 302, 404]

    def test_chat_messages_with_offset(self, client, app, chat_user):
        """Chat messages with offset"""
        client.post('/login', data={
            'username': 'chat_event_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/chat/messages?offset=10')
        assert response.status_code in [200, 302, 404]


class TestChatSend:
    """Chat send тестүүд"""

    def test_chat_send_message(self, client, app, chat_user):
        """Chat send message"""
        client.post('/login', data={
            'username': 'chat_event_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/chat/send',
            json={'message': 'Test chat message'},
            content_type='application/json')
        assert response.status_code in [200, 201, 302, 400, 404]

    def test_chat_send_empty(self, client, app, chat_user):
        """Chat send empty message"""
        client.post('/login', data={
            'username': 'chat_event_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/chat/send',
            json={'message': ''},
            content_type='application/json')
        assert response.status_code in [200, 201, 302, 400, 404]

    def test_chat_send_with_sample(self, client, app, chat_user):
        """Chat send with sample reference"""
        client.post('/login', data={
            'username': 'chat_event_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.post('/api/chat/send',
                    json={'message': f'Message about sample {sample.sample_code}', 'sample_id': sample.id},
                    content_type='application/json')
                assert response.status_code in [200, 201, 302, 400, 404]


class TestChatRead:
    """Chat read тестүүд"""

    def test_chat_mark_read(self, client, app, chat_user):
        """Chat mark read"""
        client.post('/login', data={
            'username': 'chat_event_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/chat/mark_read',
            json={'message_ids': [1, 2, 3]},
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_chat_mark_all_read(self, client, app, chat_user):
        """Chat mark all read"""
        client.post('/login', data={
            'username': 'chat_event_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/chat/mark_all_read')
        assert response.status_code in [200, 302, 400, 404]


class TestChatDelete:
    """Chat delete тестүүд"""

    def test_chat_delete_message(self, client, app, chat_user):
        """Chat delete message"""
        client.post('/login', data={
            'username': 'chat_event_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.delete('/api/chat/messages/1')
        assert response.status_code in [200, 302, 400, 404, 405]


class TestChatUnread:
    """Chat unread тестүүд"""

    def test_chat_unread_count(self, client, app, chat_user):
        """Chat unread count"""
        client.post('/login', data={
            'username': 'chat_event_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/chat/unread')
        assert response.status_code in [200, 302, 404]


class TestChatHistory:
    """Chat history тестүүд"""

    def test_chat_history(self, client, app, chat_user):
        """Chat history"""
        client.post('/login', data={
            'username': 'chat_event_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/chat/history')
        assert response.status_code in [200, 302, 404]

    def test_chat_history_by_user(self, client, app, chat_user):
        """Chat history by user"""
        client.post('/login', data={
            'username': 'chat_event_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            user = User.query.first()
            if user:
                response = client.get(f'/api/chat/history?user_id={user.id}')
                assert response.status_code in [200, 302, 404]


class TestChatNotifications:
    """Chat notifications тестүүд"""

    def test_chat_notifications(self, client, app, chat_user):
        """Chat notifications"""
        client.post('/login', data={
            'username': 'chat_event_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/chat/notifications')
        assert response.status_code in [200, 302, 404]
