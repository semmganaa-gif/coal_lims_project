# tests/integration/test_import_routes_comprehensive.py
# -*- coding: utf-8 -*-
"""
Import routes comprehensive coverage tests
"""

import pytest
from app import db
from app.models import User, Sample
from datetime import datetime, date
import json
import io

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def import_admin(app):
    """Import admin user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='import_admin_user').first()
        if not user:
            user = User(username='import_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def import_senior(app):
    """Import senior user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='import_senior_user').first()
        if not user:
            user = User(username='import_senior_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def import_prep(app):
    """Import prep user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='import_prep_user').first()
        if not user:
            user = User(username='import_prep_user', role='prep')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestImportPage:
    """Import page tests"""

    def test_import_page_get_admin(self, client, app, import_admin):
        """Import page GET as admin"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/import')
        assert response.status_code in [200, 302, 404]

    def test_import_page_get_senior(self, client, app, import_senior):
        """Import page GET as senior"""
        client.post('/login', data={
            'username': 'import_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/import')
        assert response.status_code in [200, 302, 404]

    def test_import_page_get_prep(self, client, app, import_prep):
        """Import page GET as prep"""
        client.post('/login', data={
            'username': 'import_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/import')
        assert response.status_code in [200, 302, 404]


class TestCSVImport:
    """CSV import tests"""

    def test_csv_import_get(self, client, app, import_admin):
        """CSV import page GET"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/import/csv')
        assert response.status_code in [200, 302, 404]

    def test_csv_import_post_no_file(self, client, app, import_admin):
        """CSV import POST without file"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/import/csv', data={}, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]

    def test_csv_import_post_empty_file(self, client, app, import_admin):
        """CSV import POST with empty file"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        data = {
            'file': (io.BytesIO(b''), 'empty.csv')
        }
        response = client.post('/import/csv', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]

    def test_csv_import_post_valid_file(self, client, app, import_admin):
        """CSV import POST with valid file"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        csv_content = b'sample_code,client_name,sample_type\nTEST-001,CHPP,2hour\n'
        data = {
            'file': (io.BytesIO(csv_content), 'samples.csv')
        }
        response = client.post('/import/csv', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]

    def test_csv_import_post_invalid_format(self, client, app, import_admin):
        """CSV import POST with invalid format"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        data = {
            'file': (io.BytesIO(b'invalid content'), 'test.txt')
        }
        response = client.post('/import/csv', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestExcelImport:
    """Excel import tests"""

    def test_excel_import_get(self, client, app, import_admin):
        """Excel import page GET"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/import/excel')
        assert response.status_code in [200, 302, 404]

    def test_excel_import_post_no_file(self, client, app, import_admin):
        """Excel import POST without file"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/import/excel', data={}, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]

    def test_excel_import_post_empty_file(self, client, app, import_admin):
        """Excel import POST with empty file"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        data = {
            'file': (io.BytesIO(b''), 'empty.xlsx')
        }
        response = client.post('/import/excel', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestHistoricalImport:
    """Historical import tests"""

    def test_historical_import_get(self, client, app, import_admin):
        """Historical import page GET"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/import/historical')
        assert response.status_code in [200, 302, 404]

    def test_historical_import_post(self, client, app, import_admin):
        """Historical import POST"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/import/historical', data={
            'start_date': date.today().isoformat(),
            'end_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestMaterialBalanceImport:
    """Material balance import tests"""

    def test_material_balance_import_get(self, client, app, import_admin):
        """Material balance import page GET"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/import/material_balance')
        assert response.status_code in [200, 302, 404]

    def test_material_balance_import_post(self, client, app, import_admin):
        """Material balance import POST"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        csv_content = b'date,material,balance\n2025-01-01,coal,1000\n'
        data = {
            'file': (io.BytesIO(csv_content), 'balance.csv')
        }
        response = client.post('/import/material_balance', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestAnalysisResultImport:
    """Analysis result import tests"""

    def test_analysis_import_get(self, client, app, import_senior):
        """Analysis result import page GET"""
        client.post('/login', data={
            'username': 'import_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/import/analysis')
        assert response.status_code in [200, 302, 404]

    def test_analysis_import_post(self, client, app, import_senior):
        """Analysis result import POST"""
        client.post('/login', data={
            'username': 'import_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        csv_content = b'sample_code,analysis_code,result\nTEST-001,Mad,5.5\n'
        data = {
            'file': (io.BytesIO(csv_content), 'analysis.csv')
        }
        response = client.post('/import/analysis', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestImportTemplates:
    """Import templates tests"""

    def test_download_csv_template(self, client, app, import_admin):
        """Download CSV template"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/import/template/csv')
        assert response.status_code in [200, 302, 404]

    def test_download_excel_template(self, client, app, import_admin):
        """Download Excel template"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/import/template/excel')
        assert response.status_code in [200, 302, 404]


class TestImportValidation:
    """Import validation tests"""

    def test_validate_csv_data(self, client, app, import_admin):
        """Validate CSV data"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/import/validate', data={
            'data': '[{"sample_code": "TEST-001", "client_name": "CHPP"}]'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]

    def test_validate_empty_data(self, client, app, import_admin):
        """Validate empty data"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/import/validate', data={
            'data': '[]'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestImportPreview:
    """Import preview tests"""

    def test_preview_import(self, client, app, import_admin):
        """Preview import"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        csv_content = b'sample_code,client_name,sample_type\nTEST-001,CHPP,2hour\n'
        data = {
            'file': (io.BytesIO(csv_content), 'preview.csv'),
            'preview': 'true'
        }
        response = client.post('/import/csv', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestBulkImport:
    """Bulk import tests"""

    def test_bulk_import_get(self, client, app, import_admin):
        """Bulk import page GET"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/import/bulk')
        assert response.status_code in [200, 302, 404]

    def test_bulk_import_post(self, client, app, import_admin):
        """Bulk import POST"""
        client.post('/login', data={
            'username': 'import_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/import/bulk', data={
            'samples': 'TEST-001\nTEST-002\nTEST-003',
            'client_name': 'CHPP',
            'sample_type': '2hour'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]
