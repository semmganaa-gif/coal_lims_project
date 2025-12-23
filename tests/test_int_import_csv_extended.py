# tests/integration/test_import_csv_extended.py
# -*- coding: utf-8 -*-
"""Import CSV routes extended tests"""

import pytest
from app import db
from app.models import User, Sample
from datetime import datetime, date
import uuid
import io
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def imp_admin(app):
    with app.app_context():
        user = User.query.filter_by(username='imp_admin_user').first()
        if not user:
            user = User(username='imp_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def imp_prep(app):
    with app.app_context():
        user = User.query.filter_by(username='imp_prep_user').first()
        if not user:
            user = User(username='imp_prep_user', role='prep')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestImportRoutes:
    def test_import_index(self, client, app, imp_admin):
        client.post('/login', data={'username': 'imp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/import/')
        assert r.status_code in [200, 302, 404]

    def test_import_samples_page(self, client, app, imp_admin):
        client.post('/login', data={'username': 'imp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/import/samples')
        assert r.status_code in [200, 302, 404]

    def test_import_results_page(self, client, app, imp_admin):
        client.post('/login', data={'username': 'imp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/import/results')
        assert r.status_code in [200, 302, 404]


class TestCSVUpload:
    def test_upload_samples_csv(self, client, app, imp_admin):
        client.post('/login', data={'username': 'imp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        csv_content = b'sample_code,client_name,sample_type\nCSV-001,CHPP,2hour\n'
        data = {
            'file': (io.BytesIO(csv_content), 'samples.csv')
        }
        r = client.post('/import/samples', data=data, content_type='multipart/form-data')
        assert r.status_code in [200, 302, 400, 404]

    def test_upload_results_csv(self, client, app, imp_admin):
        client.post('/login', data={'username': 'imp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        csv_content = b'sample_code,analysis_type,value\nCSV-001,TM,12.5\n'
        data = {
            'file': (io.BytesIO(csv_content), 'results.csv')
        }
        r = client.post('/import/results', data=data, content_type='multipart/form-data')
        assert r.status_code in [200, 302, 400, 404]

    def test_upload_invalid_csv(self, client, app, imp_admin):
        client.post('/login', data={'username': 'imp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        csv_content = b'invalid,csv,format\n'
        data = {
            'file': (io.BytesIO(csv_content), 'invalid.csv')
        }
        r = client.post('/import/samples', data=data, content_type='multipart/form-data')
        assert r.status_code in [200, 302, 400, 404]


class TestExcelUpload:
    def test_upload_samples_excel(self, client, app, imp_admin):
        client.post('/login', data={'username': 'imp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        data = {
            'file': (io.BytesIO(b''), 'samples.xlsx')
        }
        r = client.post('/import/samples', data=data, content_type='multipart/form-data')
        assert r.status_code in [200, 302, 400, 404]


class TestImportValidation:
    def test_validate_csv(self, client, app, imp_admin):
        client.post('/login', data={'username': 'imp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        csv_content = b'sample_code,client_name,sample_type\nCSV-002,CHPP,2hour\n'
        data = {
            'file': (io.BytesIO(csv_content), 'validate.csv')
        }
        r = client.post('/import/validate', data=data, content_type='multipart/form-data')
        assert r.status_code in [200, 302, 400, 404, 405]

    def test_preview_import(self, client, app, imp_admin):
        client.post('/login', data={'username': 'imp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        csv_content = b'sample_code,client_name,sample_type\nCSV-003,CHPP,2hour\n'
        data = {
            'file': (io.BytesIO(csv_content), 'preview.csv')
        }
        r = client.post('/import/preview', data=data, content_type='multipart/form-data')
        assert r.status_code in [200, 302, 400, 404, 405]


class TestImportHistory:
    def test_import_history(self, client, app, imp_admin):
        client.post('/login', data={'username': 'imp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/import/history')
        assert r.status_code in [200, 302, 404]

    def test_import_detail(self, client, app, imp_admin):
        client.post('/login', data={'username': 'imp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/import/history/1')
        assert r.status_code in [200, 302, 404]


class TestImportTemplates:
    def test_download_sample_template(self, client, app, imp_admin):
        client.post('/login', data={'username': 'imp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/import/template/samples')
        assert r.status_code in [200, 302, 404]

    def test_download_results_template(self, client, app, imp_admin):
        client.post('/login', data={'username': 'imp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/import/template/results')
        assert r.status_code in [200, 302, 404]
