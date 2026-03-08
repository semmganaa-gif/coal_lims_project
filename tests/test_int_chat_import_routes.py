# -*- coding: utf-8 -*-
"""
Chat болон Import routes интеграцийн тестүүд
"""
import pytest
from app import create_app, db
from app.models import User, ChatMessage


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
    """Test client fixture"""
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


class TestChatApiRoutes:
    """Chat API route тестүүд"""

    def test_chat_messages_api(self, auth_client, app):
        """Chat messages API"""
        with app.app_context():
            response = auth_client.get('/api/chat/messages')
            assert response.status_code in [200, 302, 404]

    def test_chat_samples_search(self, auth_client, app):
        """Chat samples search API"""
        with app.app_context():
            response = auth_client.get('/api/chat/samples/search')
            assert response.status_code in [200, 302, 404]


class TestImportRoutes:
    """Import route тестүүд"""

    def test_import_csv_accessible(self, auth_client, app):
        """Import CSV form"""
        with app.app_context():
            response = auth_client.get('/admin/import/historical_csv')
            assert response.status_code in [200, 302]


class TestImportHelperFunctions:
    """Import helper функцүүдийн тестүүд"""

    def test_alias_to_base_mapping(self):
        """Alias to base code mapping"""
        from app.utils.analysis_aliases import normalize_analysis_code

        assert normalize_analysis_code('ts') == 'TS'
        assert normalize_analysis_code('cv') == 'CV'
        assert normalize_analysis_code('mad') == 'Mad'

    def test_normalize_unknown_code(self):
        """Unknown code returns original"""
        from app.utils.analysis_aliases import normalize_analysis_code

        assert normalize_analysis_code('UNKNOWN123') == 'UNKNOWN123'

    def test_get_aliases_for_base(self):
        """Get all aliases for a base code"""
        from app.utils.analysis_aliases import get_all_aliases_for_base

        ts_aliases = get_all_aliases_for_base('TS')
        assert 'ts' in ts_aliases
        assert 's' in ts_aliases
