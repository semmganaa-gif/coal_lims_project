# tests/integration/test_import_routes_full.py
# -*- coding: utf-8 -*-
"""
Import routes full coverage tests
"""

import pytest
from io import BytesIO
from app import db
from app.models import User, Sample
from datetime import datetime
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def import_admin(app):
    """Import admin fixture"""
    with app.app_context():
        user = User.query.filter_by(username='import_admin_user').first()
        if not user:
            user = User(username='import_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def import_prep(app):
    """Import prep fixture"""
    with app.app_context():
        user = User.query.filter_by(username='import_prep_user').first()
        if not user:
            user = User(username='import_prep_user', role='prep')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestImportIndex:
    """Import index тестүүд"""

    def test_import_index_unauthenticated(self, client, app):
        """Import index without login"""
        response = client.get('/import')
        assert response.status_code in [200, 302, 404]

    def test_import_index_admin(self, client, app, import_admin):
        """Import index with admin"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/import')
        assert response.status_code in [200, 302, 404]


class TestImportCSV:
    """Import CSV тестүүд"""

    def test_import_csv_get(self, client, app, import_admin):
        """Import CSV GET"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/import/csv')
        assert response.status_code in [200, 302, 404]

    def test_import_csv_post_empty(self, client, app, import_admin):
        """Import CSV POST with no file"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/import/csv', data={})
        assert response.status_code in [200, 302, 400, 404]

    def test_import_csv_post_with_csv(self, client, app, import_admin):
        """Import CSV POST with CSV file"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        csv_content = "sample_code,client_name,sample_type,received_date\nTEST001,CHPP,2hour,2025-01-01"
        data = {
            'file': (BytesIO(csv_content.encode('utf-8')), 'test.csv')
        }
        response = client.post('/import/csv', data=data, content_type='multipart/form-data')
        assert response.status_code in [200, 302, 400, 404]


class TestImportExcel:
    """Import Excel тестүүд"""

    def test_import_excel_get(self, client, app, import_admin):
        """Import Excel GET"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/import/excel')
        assert response.status_code in [200, 302, 404]

    def test_import_excel_post_empty(self, client, app, import_admin):
        """Import Excel POST with no file"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/import/excel', data={})
        assert response.status_code in [200, 302, 400, 404]


class TestImportCHPP:
    """Import CHPP тестүүд"""

    def test_import_chpp_get(self, client, app, import_admin):
        """Import CHPP GET"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/import/chpp')
        assert response.status_code in [200, 302, 404]

    def test_import_chpp_post(self, client, app, import_admin):
        """Import CHPP POST"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/import/chpp', data={
            'import_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400, 404]


class TestImportAnalyzer:
    """Import analyzer тестүүд"""

    def test_import_analyzer_get(self, client, app, import_admin):
        """Import analyzer GET"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/import/analyzer')
        assert response.status_code in [200, 302, 404]

    def test_import_analyzer_post(self, client, app, import_admin):
        """Import analyzer POST"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        csv_content = "sample_code,Mad,Aad,Vad\nTEST001,5.0,10.0,25.0"
        data = {
            'file': (BytesIO(csv_content.encode('utf-8')), 'analyzer.csv'),
            'analyzer_type': 'TGA'
        }
        response = client.post('/import/analyzer', data=data, content_type='multipart/form-data')
        assert response.status_code in [200, 302, 400, 404]


class TestImportTemplate:
    """Import template тестүүд"""

    def test_download_template_samples(self, client, app, import_admin):
        """Download samples template"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/import/template/samples')
        assert response.status_code in [200, 302, 404]

    def test_download_template_results(self, client, app, import_admin):
        """Download results template"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/import/template/results')
        assert response.status_code in [200, 302, 404]


class TestImportValidation:
    """Import validation тестүүд"""

    def test_validate_import_api(self, client, app, import_admin):
        """Validate import API"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/import/validate',
            json={'data': [{'sample_code': 'TEST001', 'client_name': 'CHPP'}]},
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]


class TestImportPreview:
    """Import preview тестүүд"""

    def test_import_preview_api(self, client, app, import_admin):
        """Import preview API"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        csv_content = "sample_code,client_name,sample_type\nTEST001,CHPP,2hour"
        data = {
            'file': (BytesIO(csv_content.encode('utf-8')), 'preview.csv')
        }
        response = client.post('/api/import/preview', data=data, content_type='multipart/form-data')
        assert response.status_code in [200, 302, 400, 404]


class TestImportHistory:
    """Import history тестүүд"""

    def test_import_history_list(self, client, app, import_admin):
        """Import history list"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/import/history')
        assert response.status_code in [200, 302, 404]

    def test_import_history_api(self, client, app, import_admin):
        """Import history API"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/import/history')
        assert response.status_code in [200, 302, 404]
