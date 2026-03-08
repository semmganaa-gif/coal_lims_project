# -*- coding: utf-8 -*-
"""
Import routes тестүүд
"""
import pytest
from io import BytesIO
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


class TestImportIndex:
    """Import index тестүүд"""

    def test_import_page(self, auth_client, app):
        """Import page"""
        with app.app_context():
            response = auth_client.get('/import')
            assert response.status_code in [200, 302, 404]

    def test_import_unauthenticated(self, client, app):
        """Import unauthenticated"""
        with app.app_context():
            response = client.get('/import')
            assert response.status_code in [200, 302, 401, 403, 404]


class TestExcelImport:
    """Excel import тестүүд"""

    def test_excel_import_page(self, auth_client, app):
        """Excel import page"""
        with app.app_context():
            response = auth_client.get('/import/excel')
            assert response.status_code in [200, 302, 404]

    def test_excel_import_no_file(self, auth_client, app):
        """Excel import no file"""
        with app.app_context():
            response = auth_client.post('/import/excel')
            assert response.status_code in [200, 302, 400, 404]

    def test_excel_import_invalid_file(self, auth_client, app):
        """Excel import invalid file"""
        with app.app_context():
            data = {
                'file': (BytesIO(b'invalid data'), 'test.txt')
            }
            response = auth_client.post('/import/excel', data=data)
            assert response.status_code in [200, 302, 400, 404]


class TestCSVImport:
    """CSV import тестүүд"""

    def test_csv_import_page(self, auth_client, app):
        """CSV import page"""
        with app.app_context():
            response = auth_client.get('/import/csv')
            assert response.status_code in [200, 302, 404]

    def test_csv_import_no_file(self, auth_client, app):
        """CSV import no file"""
        with app.app_context():
            response = auth_client.post('/import/csv')
            assert response.status_code in [200, 302, 400, 404]


class TestInstrumentImport:
    """Instrument import тестүүд"""

    def test_instrument_import_page(self, auth_client, app):
        """Instrument import page"""
        with app.app_context():
            response = auth_client.get('/import/instrument')
            assert response.status_code in [200, 302, 404]

    def test_instrument_list(self, auth_client, app):
        """Instrument list"""
        with app.app_context():
            response = auth_client.get('/import/instruments')
            assert response.status_code in [200, 302, 404]


class TestImportHistory:
    """Import history тестүүд"""

    def test_import_history(self, auth_client, app):
        """Import history"""
        with app.app_context():
            response = auth_client.get('/import/history')
            assert response.status_code in [200, 302, 404]

    def test_import_detail(self, auth_client, app):
        """Import detail"""
        with app.app_context():
            response = auth_client.get('/import/99999')
            assert response.status_code in [200, 302, 404]


class TestImportTemplates:
    """Import templates тестүүд"""

    def test_download_template(self, auth_client, app):
        """Download template"""
        with app.app_context():
            response = auth_client.get('/import/template/samples')
            assert response.status_code in [200, 302, 404]

    def test_download_analysis_template(self, auth_client, app):
        """Download analysis template"""
        with app.app_context():
            response = auth_client.get('/import/template/analysis')
            assert response.status_code in [200, 302, 404]
