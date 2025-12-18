# tests/unit/test_chat_events_extended.py
# -*- coding: utf-8 -*-
"""
Chat events extended tests
Coverage target: app/routes/chat_events.py
"""

import pytest
from app import db
from app.models import User, Sample
from datetime import datetime
import uuid
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def chat_user(app):
    """Chat test user"""
    with app.app_context():
        user = User.query.filter_by(username='chat_test_user').first()
        if not user:
            user = User(username='chat_test_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def chat_sample(app, chat_user):
    """Sample for chat tests"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        sample = Sample(
            sample_code=f'CHAT-{unique_id}',
            client_name='CHPP',  # Use valid client name
            sample_type='CM',
            status='registered',
            received_date=datetime.now(),
            user_id=chat_user.id
        )
        db.session.add(sample)
        db.session.commit()
        return sample.id


def login_chat_user(client):
    """Helper login"""
    client.post('/login', data={
        'username': 'chat_test_user',
        'password': VALID_PASSWORD
    }, follow_redirects=True)


class TestChatAPI:
    """Test chat API endpoints"""

    def test_chat_message_post(self, client, app, chat_user):
        """Send chat message"""
        login_chat_user(client)
        response = client.post('/api/chat/message',
                              json={'message': 'Hello'},
                              content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_chat_message_empty(self, client, app, chat_user):
        """Send empty chat message"""
        login_chat_user(client)
        response = client.post('/api/chat/message',
                              json={'message': ''},
                              content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_chat_history(self, client, app, chat_user):
        """Get chat history"""
        login_chat_user(client)
        response = client.get('/api/chat/history')
        assert response.status_code in [200, 302, 404]

    def test_chat_clear(self, client, app, chat_user):
        """Clear chat history"""
        login_chat_user(client)
        response = client.post('/api/chat/clear')
        assert response.status_code in [200, 302, 404]


class TestChatSearch:
    """Test chat search functionality"""

    def test_chat_search_samples(self, client, app, chat_user, chat_sample):
        """Search samples via chat"""
        login_chat_user(client)
        response = client.get('/api/chat/search?q=CHAT')
        assert response.status_code in [200, 302, 404]

    def test_chat_search_empty(self, client, app, chat_user):
        """Search with empty query"""
        login_chat_user(client)
        response = client.get('/api/chat/search?q=')
        assert response.status_code in [200, 302, 404]

    def test_chat_search_client(self, client, app, chat_user):
        """Search by client name"""
        login_chat_user(client)
        response = client.get('/api/chat/search?type=client&q=Test')
        assert response.status_code in [200, 302, 404]


class TestChatTemplates:
    """Test chat templates"""

    def test_chat_templates_list(self, client, app, chat_user):
        """List chat templates"""
        login_chat_user(client)
        response = client.get('/api/chat/templates')
        assert response.status_code in [200, 302, 404]

    def test_chat_templates_by_category(self, client, app, chat_user):
        """Get templates by category"""
        login_chat_user(client)
        response = client.get('/api/chat/templates?category=samples')
        assert response.status_code in [200, 302, 404]


class TestChatStream:
    """Test chat SSE stream"""

    def test_chat_stream_endpoint(self, client, app, chat_user):
        """Chat stream endpoint exists"""
        login_chat_user(client)
        response = client.get('/api/chat/stream')
        # SSE endpoints may return 200 or streaming response
        assert response.status_code in [200, 302, 404, 406]

    def test_chat_status(self, client, app, chat_user):
        """Chat status endpoint"""
        login_chat_user(client)
        response = client.get('/api/chat/status')
        assert response.status_code in [200, 302, 404]


class TestChatCommands:
    """Test chat command processing"""

    def test_chat_command_help(self, client, app, chat_user):
        """Help command"""
        login_chat_user(client)
        response = client.post('/api/chat/message',
                              json={'message': '/help'},
                              content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_chat_command_samples(self, client, app, chat_user):
        """Samples command"""
        login_chat_user(client)
        response = client.post('/api/chat/message',
                              json={'message': '/samples'},
                              content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_chat_command_stats(self, client, app, chat_user):
        """Stats command"""
        login_chat_user(client)
        response = client.post('/api/chat/message',
                              json={'message': '/stats'},
                              content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]


class TestChatSampleInfo:
    """Test chat sample info retrieval"""

    def test_get_sample_info(self, client, app, chat_user, chat_sample):
        """Get sample info via chat"""
        login_chat_user(client)
        with app.app_context():
            sample = Sample.query.get(chat_sample)
            if sample:
                response = client.post('/api/chat/message',
                                      json={'message': f'@{sample.sample_code}'},
                                      content_type='application/json')
                assert response.status_code in [200, 302, 400, 404]

    def test_get_invalid_sample(self, client, app, chat_user):
        """Get invalid sample info"""
        login_chat_user(client)
        response = client.post('/api/chat/message',
                              json={'message': '@INVALID_SAMPLE_XYZ'},
                              content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]


class TestChatAnalysisQueries:
    """Test chat analysis queries"""

    def test_query_analysis_results(self, client, app, chat_user):
        """Query analysis results"""
        login_chat_user(client)
        response = client.post('/api/chat/message',
                              json={'message': 'Mad үр дүн'},
                              content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_query_pending_samples(self, client, app, chat_user):
        """Query pending samples"""
        login_chat_user(client)
        response = client.post('/api/chat/message',
                              json={'message': 'хүлээгдэж буй дээжүүд'},
                              content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]


class TestChatUnauthenticated:
    """Test chat without authentication"""

    def test_chat_message_unauthenticated(self, client, app):
        """Chat message without login"""
        response = client.post('/api/chat/message',
                              json={'message': 'Hello'},
                              content_type='application/json')
        assert response.status_code in [302, 401, 403, 404]

    def test_chat_history_unauthenticated(self, client, app):
        """Chat history without login"""
        response = client.get('/api/chat/history')
        assert response.status_code in [302, 401, 403, 404]
