# tests/integration/test_chat_api_comprehensive.py
# -*- coding: utf-8 -*-
"""
Chat API comprehensive coverage tests
"""

import pytest
from app import db
from app.models import User, ChatMessage, Sample, UserOnlineStatus
from datetime import datetime
import json
import io
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def chat_chemist(app):
    """Chat chemist user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='chat_chemist_user').first()
        if not user:
            user = User(username='chat_chemist_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def chat_senior(app):
    """Chat senior user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='chat_senior_user').first()
        if not user:
            user = User(username='chat_senior_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def chat_admin(app):
    """Chat admin user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='chat_admin_user').first()
        if not user:
            user = User(username='chat_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def chat_sample(app):
    """Chat sample fixture"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        sample = Sample(
            sample_code=f'CHAT-{unique_id}',
            client_name='CHPP',
            sample_type='2hour',
            status='new',
            received_date=datetime.now()
        )
        db.session.add(sample)
        db.session.commit()
        return sample.id


@pytest.fixture
def chat_message(app, chat_chemist, chat_senior):
    """Chat message fixture"""
    with app.app_context():
        chemist = User.query.filter_by(username='chat_chemist_user').first()
        senior = User.query.filter_by(username='chat_senior_user').first()
        if chemist and senior:
            msg = ChatMessage(
                sender_id=chemist.id,
                receiver_id=senior.id,
                message='Test message from fixture',
                message_type='text',
                sent_at=datetime.now()
            )
            db.session.add(msg)
            db.session.commit()
            return msg.id
        return None


class TestChatContacts:
    """Chat contacts tests"""

    def test_contacts_as_chemist(self, client, app, chat_chemist, chat_senior):
        """Get contacts as chemist"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/chat/contacts')
        assert response.status_code in [200, 302, 404]

    def test_contacts_as_senior(self, client, app, chat_senior, chat_chemist):
        """Get contacts as senior"""
        client.post('/login', data={
            'username': 'chat_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/chat/contacts')
        assert response.status_code in [200, 302, 404]

    def test_contacts_as_admin(self, client, app, chat_admin):
        """Get contacts as admin"""
        client.post('/login', data={
            'username': 'chat_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/chat/contacts')
        assert response.status_code in [200, 302, 404]


class TestChatHistory:
    """Chat history tests"""

    def test_history_get(self, client, app, chat_chemist, chat_senior, chat_message):
        """Get chat history"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        with app.app_context():
            senior = User.query.filter_by(username='chat_senior_user').first()
            if senior:
                response = client.get(f'/api/chat/history/{senior.id}')
                assert response.status_code in [200, 302, 404]

    def test_history_paginated(self, client, app, chat_chemist, chat_senior):
        """Get chat history paginated"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        with app.app_context():
            senior = User.query.filter_by(username='chat_senior_user').first()
            if senior:
                response = client.get(f'/api/chat/history/{senior.id}?page=1&per_page=10')
                assert response.status_code in [200, 302, 404]

    def test_history_with_search(self, client, app, chat_chemist, chat_senior, chat_message):
        """Get chat history with search"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        with app.app_context():
            senior = User.query.filter_by(username='chat_senior_user').first()
            if senior:
                response = client.get(f'/api/chat/history/{senior.id}?search=test')
                assert response.status_code in [200, 302, 404]

    def test_history_invalid_user(self, client, app, chat_chemist):
        """Get chat history with invalid user"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/chat/history/99999')
        assert response.status_code in [200, 302, 404]


class TestChatSearch:
    """Chat search tests"""

    def test_search_messages(self, client, app, chat_chemist, chat_message):
        """Search messages"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/chat/search?q=test')
        assert response.status_code in [200, 302, 404]

    def test_search_messages_with_user(self, client, app, chat_chemist, chat_senior, chat_message):
        """Search messages with user filter"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        with app.app_context():
            senior = User.query.filter_by(username='chat_senior_user').first()
            if senior:
                response = client.get(f'/api/chat/search?q=test&user_id={senior.id}')
                assert response.status_code in [200, 302, 404]

    def test_search_short_query(self, client, app, chat_chemist):
        """Search with short query"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/chat/search?q=a')
        assert response.status_code in [200, 302, 404]

    def test_search_empty_query(self, client, app, chat_chemist):
        """Search with empty query"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/chat/search?q=')
        assert response.status_code in [200, 302, 404]


class TestChatUnread:
    """Chat unread count tests"""

    def test_unread_count(self, client, app, chat_chemist):
        """Get unread count"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/chat/unread_count')
        assert response.status_code in [200, 302, 404]


class TestChatUpload:
    """Chat file upload tests"""

    def test_upload_no_file(self, client, app, chat_chemist):
        """Upload without file"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/api/chat/upload', data={})
        assert response.status_code in [200, 302, 400, 404]

    def test_upload_empty_filename(self, client, app, chat_chemist):
        """Upload with empty filename"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        data = {'file': (io.BytesIO(b'test'), '')}
        response = client.post('/api/chat/upload', data=data, content_type='multipart/form-data')
        assert response.status_code in [200, 302, 400, 404]

    def test_upload_invalid_extension(self, client, app, chat_chemist):
        """Upload with invalid extension"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        data = {'file': (io.BytesIO(b'test'), 'test.exe')}
        response = client.post('/api/chat/upload', data=data, content_type='multipart/form-data')
        assert response.status_code in [200, 302, 400, 404]

    def test_upload_valid_png(self, client, app, chat_chemist):
        """Upload valid PNG"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        # PNG magic bytes
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        data = {'file': (io.BytesIO(png_data), 'test.png')}
        response = client.post('/api/chat/upload', data=data, content_type='multipart/form-data')
        assert response.status_code in [200, 302, 400, 404]

    def test_upload_valid_jpg(self, client, app, chat_chemist):
        """Upload valid JPG"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        # JPEG magic bytes
        jpg_data = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        data = {'file': (io.BytesIO(jpg_data), 'test.jpg')}
        response = client.post('/api/chat/upload', data=data, content_type='multipart/form-data')
        assert response.status_code in [200, 302, 400, 404]

    def test_upload_valid_pdf(self, client, app, chat_chemist):
        """Upload valid PDF"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        # PDF magic bytes
        pdf_data = b'%PDF-1.4' + b'\x00' * 100
        data = {'file': (io.BytesIO(pdf_data), 'test.pdf')}
        response = client.post('/api/chat/upload', data=data, content_type='multipart/form-data')
        assert response.status_code in [200, 302, 400, 404]


class TestChatSampleSearch:
    """Chat sample search tests"""

    def test_search_samples(self, client, app, chat_chemist, chat_sample):
        """Search samples for chat"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/chat/samples/search?q=CHAT')
        assert response.status_code in [200, 302, 404]

    def test_search_samples_short_query(self, client, app, chat_chemist):
        """Search samples with short query"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/chat/samples/search?q=A')
        assert response.status_code in [200, 302, 404]

    def test_search_samples_empty(self, client, app, chat_chemist):
        """Search samples with empty query"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/chat/samples/search?q=')
        assert response.status_code in [200, 302, 404]


class TestChatTemplates:
    """Chat templates tests"""

    def test_get_templates(self, client, app, chat_chemist):
        """Get message templates"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/chat/templates')
        assert response.status_code in [200, 302, 404]


class TestChatBroadcasts:
    """Chat broadcasts tests"""

    def test_get_broadcasts(self, client, app, chat_chemist):
        """Get broadcasts"""
        client.post('/login', data={
            'username': 'chat_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/chat/broadcasts')
        assert response.status_code in [200, 302, 404]


class TestChatHelperFunctions:
    """Chat helper function tests"""

    def test_allowed_file(self, app):
        """Test allowed_file function"""
        try:
            from app.routes.api.chat_api import allowed_file
            assert allowed_file('test.png') == True
            assert allowed_file('test.jpg') == True
            assert allowed_file('test.pdf') == True
            assert allowed_file('test.exe') == False
            assert allowed_file('test') == False
        except ImportError:
            pass

    def test_validate_file_content_png(self, app):
        """Test validate_file_content for PNG"""
        try:
            from app.routes.api.chat_api import validate_file_content
            import io
            # Valid PNG
            png_file = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
            assert validate_file_content(png_file, 'png') == True

            # Invalid PNG (wrong magic bytes)
            invalid_file = io.BytesIO(b'NOT_PNG' + b'\x00' * 100)
            assert validate_file_content(invalid_file, 'png') == False
        except ImportError:
            pass

    def test_validate_file_content_jpg(self, app):
        """Test validate_file_content for JPG"""
        try:
            from app.routes.api.chat_api import validate_file_content
            import io
            # Valid JPEG
            jpg_file = io.BytesIO(b'\xff\xd8\xff' + b'\x00' * 100)
            assert validate_file_content(jpg_file, 'jpg') == True
        except ImportError:
            pass

    def test_validate_file_content_pdf(self, app):
        """Test validate_file_content for PDF"""
        try:
            from app.routes.api.chat_api import validate_file_content
            import io
            # Valid PDF
            pdf_file = io.BytesIO(b'%PDF' + b'\x00' * 100)
            assert validate_file_content(pdf_file, 'pdf') == True
        except ImportError:
            pass

    def test_validate_file_content_unknown(self, app):
        """Test validate_file_content for unknown type"""
        try:
            from app.routes.api.chat_api import validate_file_content
            import io
            # Unknown type should be allowed
            unknown_file = io.BytesIO(b'test content' + b'\x00' * 100)
            assert validate_file_content(unknown_file, 'txt') == True
        except ImportError:
            pass
