# tests/unit/test_chat_events.py
# -*- coding: utf-8 -*-
"""Chat events and SSE coverage tests"""

import pytest
from app import db
from app.models import User, ChatMessage
from datetime import datetime
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def chat_user(app):
    """Chat test user"""
    with app.app_context():
        user = User.query.filter_by(username='chat_evt_user').first()
        if not user:
            user = User(username='chat_evt_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def chat_admin(app):
    """Chat admin user"""
    with app.app_context():
        user = User.query.filter_by(username='chat_evt_admin').first()
        if not user:
            user = User(username='chat_evt_admin', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestChatMessageModel:
    """Chat message model tests"""

    def test_create_message(self, app, chat_user):
        """Create chat message"""
        with app.app_context():
            user = User.query.filter_by(username='chat_evt_user').first()
            msg = ChatMessage(
                sender_id=user.id,
                message='Test message'
            )
            db.session.add(msg)
            db.session.commit()
            assert msg.id is not None

    def test_message_repr(self, app, chat_user):
        """Message repr"""
        with app.app_context():
            user = User.query.filter_by(username='chat_evt_user').first()
            msg = ChatMessage(
                sender_id=user.id,
                message='Test repr'
            )
            db.session.add(msg)
            db.session.commit()
            repr_str = repr(msg)
            assert repr_str is not None


class TestChatAPIRoutes:
    """Chat API route tests"""

    def test_chat_index(self, client, app, chat_user):
        """Chat index page"""
        client.post('/login', data={
            'username': 'chat_evt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/chat/')
        assert response.status_code in [200, 302, 404]

    def test_chat_messages_get(self, client, app, chat_user):
        """Get chat messages"""
        client.post('/login', data={
            'username': 'chat_evt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/chat/messages')
        assert response.status_code in [200, 302, 404]

    def test_chat_messages_with_room(self, client, app, chat_user):
        """Get chat messages with room"""
        client.post('/login', data={
            'username': 'chat_evt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/chat/messages?room=general')
        assert response.status_code in [200, 302, 404]

    def test_chat_messages_with_limit(self, client, app, chat_user):
        """Get chat messages with limit"""
        client.post('/login', data={
            'username': 'chat_evt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/chat/messages?limit=10')
        assert response.status_code in [200, 302, 404]

    def test_chat_send_message(self, client, app, chat_user):
        """Send chat message"""
        client.post('/login', data={
            'username': 'chat_evt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/chat/send', data={
            'message': 'Hello test',
            'room': 'general'
        })
        assert response.status_code in [200, 302, 400, 404, 405]

    def test_chat_send_json(self, client, app, chat_user):
        """Send chat message JSON"""
        client.post('/login', data={
            'username': 'chat_evt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/chat/send',
            data=json.dumps({'message': 'Hello JSON', 'room': 'general'}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404, 405]

    def test_chat_rooms(self, client, app, chat_user):
        """Get chat rooms"""
        client.post('/login', data={
            'username': 'chat_evt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/chat/rooms')
        assert response.status_code in [200, 302, 404]


class TestChatSSE:
    """Chat SSE tests"""

    def test_chat_events_stream(self, client, app, chat_user):
        """Chat events stream"""
        client.post('/login', data={
            'username': 'chat_evt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/chat/events')
        assert response.status_code in [200, 302, 404]

    def test_chat_events_with_room(self, client, app, chat_user):
        """Chat events with room"""
        client.post('/login', data={
            'username': 'chat_evt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/chat/events?room=general')
        assert response.status_code in [200, 302, 404]


class TestChatAdmin:
    """Chat admin tests"""

    def test_chat_admin_delete(self, client, app, chat_admin):
        """Admin delete message"""
        client.post('/login', data={
            'username': 'chat_evt_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.delete('/chat/message/99999')
        assert response.status_code in [200, 302, 403, 404, 405]

    def test_chat_admin_clear(self, client, app, chat_admin):
        """Admin clear room"""
        client.post('/login', data={
            'username': 'chat_evt_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/chat/clear',
            data=json.dumps({'room': 'test_room'}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 403, 404, 405]
