# -*- coding: utf-8 -*-
"""
Import CSV routes интеграцийн тестүүд
"""
import pytest
import io
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
            user.set_password('Admin123')
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
            user.set_password('Admin123')
            db.session.add(user)
            db.session.commit()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

    return client


class TestHistoricalCsvImport:
    """Historical CSV import тестүүд"""

    def test_import_page_accessible(self, auth_client, app):
        """Import хуудас харагдана"""
        with app.app_context():
            response = auth_client.get('/admin/import/historical_csv')
            assert response.status_code in [200, 302]

    def test_import_empty_file(self, auth_client, app):
        """Хоосон файл import"""
        with app.app_context():
            csv_data = io.BytesIO(b'')
            response = auth_client.post('/admin/import/historical_csv', data={
                'file': (csv_data, 'empty.csv')
            }, content_type='multipart/form-data')
            assert response.status_code in [200, 302, 400]

    def test_import_with_headers_only(self, auth_client, app):
        """Headers only CSV"""
        with app.app_context():
            csv_content = b'sample_code,client_name,sample_type,analysis_code,value\n'
            csv_data = io.BytesIO(csv_content)
            response = auth_client.post('/admin/import/historical_csv', data={
                'file': (csv_data, 'headers.csv')
            }, content_type='multipart/form-data')
            assert response.status_code in [200, 302, 400]

    def test_import_invalid_format(self, auth_client, app):
        """Invalid format import"""
        with app.app_context():
            invalid_data = io.BytesIO(b'not,valid,csv,data\nwithout,proper,headers,here')
            response = auth_client.post('/admin/import/historical_csv', data={
                'file': (invalid_data, 'invalid.csv')
            }, content_type='multipart/form-data')
            assert response.status_code in [200, 302, 400]
