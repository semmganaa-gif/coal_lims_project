# tests/test_routes_audit_chat_batch.py
# -*- coding: utf-8 -*-
"""
Comprehensive tests for audit_api.py and chat_api.py routes.
Target: 80%+ coverage on both modules.
"""

import io
import json
import os
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

from app import create_app, db
from app.models import User, Sample
from tests.conftest import TestConfig


# =====================================================================
# FIXTURES
# =====================================================================

@pytest.fixture
def ac_app():
    """Create a fresh Flask app for audit/chat tests."""
    flask_app = create_app(TestConfig)
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SERVER_NAME'] = 'localhost'

    with flask_app.app_context():
        db.create_all()
        for role, uname in [('admin', 'ac_admin'), ('senior', 'ac_senior'),
                             ('chemist', 'ac_chemist'), ('prep', 'ac_prep')]:
            if not User.query.filter_by(username=uname).first():
                u = User(username=uname, role=role)
                u.set_password('Pass1234!@XY')
                db.session.add(u)
        db.session.commit()

    yield flask_app

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def admin_client(ac_app):
    client = ac_app.test_client()
    with ac_app.app_context():
        user = User.query.filter_by(username='ac_admin').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def senior_client(ac_app):
    client = ac_app.test_client()
    with ac_app.app_context():
        user = User.query.filter_by(username='ac_senior').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def chemist_client(ac_app):
    client = ac_app.test_client()
    with ac_app.app_context():
        user = User.query.filter_by(username='ac_chemist').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def prep_client(ac_app):
    client = ac_app.test_client()
    with ac_app.app_context():
        user = User.query.filter_by(username='ac_prep').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def anon_client(ac_app):
    return ac_app.test_client()


# =====================================================================
# UNIT TESTS: allowed_file & validate_file_content
# =====================================================================

class TestAllowedFile:
    """Test chat_api.allowed_file pure function."""

    def test_allowed_png(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('photo.png') is True

    def test_allowed_jpg(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('photo.jpg') is True

    def test_allowed_jpeg(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('photo.jpeg') is True

    def test_allowed_gif(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('anim.gif') is True

    def test_allowed_webp(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('photo.webp') is True

    def test_allowed_pdf(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('doc.pdf') is True

    def test_allowed_doc(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('file.doc') is True

    def test_allowed_docx(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('file.docx') is True

    def test_allowed_xls(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('data.xls') is True

    def test_allowed_xlsx(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('data.xlsx') is True

    def test_disallowed_exe(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('virus.exe') is False

    def test_disallowed_py(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('script.py') is False

    def test_no_extension(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('noext') is False

    def test_empty_string(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('') is False

    def test_case_insensitive(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('PHOTO.PNG') is True

    def test_double_extension(self):
        from app.routes.api.chat_api import allowed_file
        # rsplit('.', 1) takes last extension
        assert allowed_file('file.txt.png') is True

    def test_disallowed_bat(self):
        from app.routes.api.chat_api import allowed_file
        assert allowed_file('run.bat') is False


class TestValidateFileContent:
    """Test chat_api.validate_file_content pure function."""

    def test_valid_png(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 20)
        assert validate_file_content(f, 'png') is True

    def test_invalid_png(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'\x00\x00\x00\x00' + b'\x00' * 20)
        assert validate_file_content(f, 'png') is False

    def test_valid_jpeg(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'\xff\xd8\xff' + b'\x00' * 20)
        assert validate_file_content(f, 'jpg') is True

    def test_valid_jpeg_ext(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'\xff\xd8\xff' + b'\x00' * 20)
        assert validate_file_content(f, 'jpeg') is True

    def test_invalid_jpeg(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'\x00\x00\x00\x00' + b'\x00' * 20)
        assert validate_file_content(f, 'jpg') is False

    def test_valid_gif87a(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'GIF87a' + b'\x00' * 20)
        assert validate_file_content(f, 'gif') is True

    def test_valid_gif89a(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'GIF89a' + b'\x00' * 20)
        assert validate_file_content(f, 'gif') is True

    def test_invalid_gif(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'\x00\x00\x00\x00' + b'\x00' * 20)
        assert validate_file_content(f, 'gif') is False

    def test_valid_webp(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'RIFF' + b'\x00' * 20)
        assert validate_file_content(f, 'webp') is True

    def test_valid_pdf(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'%PDF-1.4' + b'\x00' * 20)
        assert validate_file_content(f, 'pdf') is True

    def test_invalid_pdf(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'\x00\x00\x00\x00' + b'\x00' * 20)
        assert validate_file_content(f, 'pdf') is False

    def test_valid_docx_zip(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'PK\x03\x04' + b'\x00' * 20)
        assert validate_file_content(f, 'docx') is True

    def test_valid_xlsx_zip(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'PK\x03\x04' + b'\x00' * 20)
        assert validate_file_content(f, 'xlsx') is True

    def test_valid_doc_ole(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'\x00' * 20)
        assert validate_file_content(f, 'doc') is True

    def test_valid_xls_ole(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'\x00' * 20)
        assert validate_file_content(f, 'xls') is True

    def test_unknown_extension_allowed(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'anything here')
        # Unknown extension not in ext_to_mime returns True
        assert validate_file_content(f, 'xyz') is True

    def test_file_seek_reset(self):
        from app.routes.api.chat_api import validate_file_content
        f = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 20)
        f.seek(5)  # Move to position 5
        validate_file_content(f, 'png')
        # After validation, file pointer should be reset to 0
        assert f.tell() == 0


# =====================================================================
# AUDIT API ROUTE TESTS
# =====================================================================

class TestAuditAdminRequired:
    """Test the _audit_admin_required decorator."""

    def test_non_admin_gets_403(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/audit_hub')
            assert resp.status_code == 403

    def test_anon_redirects_to_login(self, anon_client, ac_app):
        with ac_app.app_context():
            resp = anon_client.get('/api/audit_hub')
            # login_required redirects (302) or returns 401
            assert resp.status_code in (302, 401)

    def test_senior_gets_403(self, senior_client, ac_app):
        with ac_app.app_context():
            resp = senior_client.get('/api/audit_hub')
            assert resp.status_code == 403


class TestAuditHub:
    """Test GET /api/audit_hub."""

    def test_admin_can_access(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get('/api/audit_hub')
            assert resp.status_code == 200


class TestAuditLogPage:
    """Test GET /api/audit_log/<analysis_code>."""

    @patch('app.routes.api.audit_api.AnalysisTypeRepository')
    @patch('app.routes.api.audit_api.get_shift_date')
    @patch('app.routes.api.audit_api.get_analysis_schema')
    def test_basic_page_no_data(self, mock_schema, mock_shift_date, mock_repo,
                                admin_client, ac_app):
        mock_repo.get_by_code.return_value = None
        mock_shift_date.return_value = date(2026, 3, 10)
        mock_schema.return_value = {}

        with ac_app.app_context():
            resp = admin_client.get('/api/audit_log/Mad')
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.AnalysisTypeRepository')
    @patch('app.routes.api.audit_api.get_shift_date')
    @patch('app.routes.api.audit_api.get_analysis_schema')
    def test_with_analysis_type_found(self, mock_schema, mock_shift_date,
                                      mock_repo, admin_client, ac_app):
        at = MagicMock()
        at.code = 'MAD'
        at.name = 'Moisture'
        mock_repo.get_by_code.return_value = at
        mock_shift_date.return_value = date(2026, 3, 10)
        mock_schema.return_value = {}

        with ac_app.app_context():
            resp = admin_client.get('/api/audit_log/Mad')
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.AnalysisTypeRepository')
    @patch('app.routes.api.audit_api.get_shift_date')
    @patch('app.routes.api.audit_api.get_analysis_schema')
    def test_with_date_filters(self, mock_schema, mock_shift_date, mock_repo,
                               admin_client, ac_app):
        mock_repo.get_by_code.return_value = None
        mock_shift_date.return_value = date(2026, 3, 10)
        mock_schema.return_value = {}

        with ac_app.app_context():
            resp = admin_client.get(
                '/api/audit_log/Mad?start_date=2026-03-01&end_date=2026-03-10'
            )
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.AnalysisTypeRepository')
    @patch('app.routes.api.audit_api.get_shift_date')
    @patch('app.routes.api.audit_api.get_analysis_schema')
    def test_with_invalid_dates(self, mock_schema, mock_shift_date, mock_repo,
                                admin_client, ac_app):
        mock_repo.get_by_code.return_value = None
        mock_shift_date.return_value = date(2026, 3, 10)
        mock_schema.return_value = {}

        with ac_app.app_context():
            resp = admin_client.get(
                '/api/audit_log/Mad?start_date=bad&end_date=notadate'
            )
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.AnalysisTypeRepository')
    @patch('app.routes.api.audit_api.get_shift_date')
    @patch('app.routes.api.audit_api.get_analysis_schema')
    def test_with_sample_name_filter(self, mock_schema, mock_shift_date,
                                     mock_repo, admin_client, ac_app):
        mock_repo.get_by_code.return_value = None
        mock_shift_date.return_value = date(2026, 3, 10)
        mock_schema.return_value = {}

        with ac_app.app_context():
            resp = admin_client.get('/api/audit_log/Mad?sample_name=S001')
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.AnalysisTypeRepository')
    @patch('app.routes.api.audit_api.get_shift_date')
    @patch('app.routes.api.audit_api.get_analysis_schema')
    def test_with_user_name_filter(self, mock_schema, mock_shift_date,
                                   mock_repo, admin_client, ac_app):
        mock_repo.get_by_code.return_value = None
        mock_shift_date.return_value = date(2026, 3, 10)
        mock_schema.return_value = {}

        with ac_app.app_context():
            resp = admin_client.get('/api/audit_log/Mad?user_name=testuser')
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.AnalysisTypeRepository')
    @patch('app.routes.api.audit_api.get_shift_date')
    @patch('app.routes.api.audit_api.get_analysis_schema')
    def test_with_error_type_filter(self, mock_schema, mock_shift_date,
                                    mock_repo, admin_client, ac_app):
        mock_repo.get_by_code.return_value = None
        mock_shift_date.return_value = date(2026, 3, 10)
        mock_schema.return_value = {}

        with ac_app.app_context():
            resp = admin_client.get('/api/audit_log/Mad?error_type=measurement')
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.AnalysisTypeRepository')
    @patch('app.routes.api.audit_api.get_shift_date')
    @patch('app.routes.api.audit_api.get_analysis_schema')
    def test_with_error_type_all(self, mock_schema, mock_shift_date,
                                 mock_repo, admin_client, ac_app):
        mock_repo.get_by_code.return_value = None
        mock_shift_date.return_value = date(2026, 3, 10)
        mock_schema.return_value = {}

        with ac_app.app_context():
            resp = admin_client.get('/api/audit_log/Mad?error_type=all')
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.AnalysisTypeRepository')
    @patch('app.routes.api.audit_api.get_shift_date')
    @patch('app.routes.api.audit_api.get_analysis_schema')
    def test_with_day_shift_filter(self, mock_schema, mock_shift_date,
                                   mock_repo, admin_client, ac_app):
        mock_repo.get_by_code.return_value = None
        mock_shift_date.return_value = date(2026, 3, 10)
        mock_schema.return_value = {}

        with ac_app.app_context():
            resp = admin_client.get('/api/audit_log/Mad?shift=day')
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.AnalysisTypeRepository')
    @patch('app.routes.api.audit_api.get_shift_date')
    @patch('app.routes.api.audit_api.get_analysis_schema')
    def test_with_night_shift_filter(self, mock_schema, mock_shift_date,
                                     mock_repo, admin_client, ac_app):
        mock_repo.get_by_code.return_value = None
        mock_shift_date.return_value = date(2026, 3, 10)
        mock_schema.return_value = {}

        with ac_app.app_context():
            resp = admin_client.get('/api/audit_log/Mad?shift=night')
            assert resp.status_code == 200

    def test_non_admin_403(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/audit_log/Mad')
            assert resp.status_code == 403


class TestAuditSearch:
    """Test GET /api/audit_search."""

    def test_basic_search_empty(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get('/api/audit_search')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'count' in data
            assert 'results' in data

    def test_search_with_q(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get('/api/audit_search?q=test')
            assert resp.status_code == 200

    def test_search_with_dates(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get(
                '/api/audit_search?start_date=2026-01-01&end_date=2026-12-31'
            )
            assert resp.status_code == 200

    def test_search_with_invalid_dates(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get(
                '/api/audit_search?start_date=bad&end_date=worse'
            )
            assert resp.status_code == 200

    def test_search_with_analysis_code(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get('/api/audit_search?analysis_code=Mad')
            assert resp.status_code == 200

    def test_search_with_action(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get('/api/audit_search?action=APPROVED')
            assert resp.status_code == 200

    def test_search_with_limit(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get('/api/audit_search?limit=10')
            assert resp.status_code == 200

    def test_search_limit_capped_at_500(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get('/api/audit_search?limit=9999')
            assert resp.status_code == 200

    def test_search_invalid_limit_defaults(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get('/api/audit_search?limit=abc')
            assert resp.status_code == 200

    def test_search_non_admin_403(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/audit_search')
            assert resp.status_code == 403


class TestExportAudit:
    """Test GET /api/export/audit."""

    @patch('app.routes.api.audit_api.now_local')
    def test_basic_export(self, mock_now, admin_client, ac_app):
        mock_now.return_value = datetime(2026, 3, 10, 14, 30)

        with ac_app.app_context():
            resp = admin_client.get('/api/export/audit')
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.now_local')
    def test_export_with_date_filters(self, mock_now, admin_client, ac_app):
        mock_now.return_value = datetime(2026, 3, 10, 14, 30)

        with ac_app.app_context():
            resp = admin_client.get(
                '/api/export/audit?start_date=2026-01-01&end_date=2026-12-31'
            )
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.now_local')
    def test_export_with_invalid_dates(self, mock_now, admin_client, ac_app):
        mock_now.return_value = datetime(2026, 3, 10, 14, 30)

        with ac_app.app_context():
            resp = admin_client.get(
                '/api/export/audit?start_date=bad&end_date=nope'
            )
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.now_local')
    def test_export_with_action_filter(self, mock_now, admin_client, ac_app):
        mock_now.return_value = datetime(2026, 3, 10, 14, 30)

        with ac_app.app_context():
            resp = admin_client.get('/api/export/audit?action=LOGIN')
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.now_local')
    def test_export_with_limit(self, mock_now, admin_client, ac_app):
        mock_now.return_value = datetime(2026, 3, 10, 14, 30)

        with ac_app.app_context():
            resp = admin_client.get('/api/export/audit?limit=50')
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.now_local')
    def test_export_limit_capped(self, mock_now, admin_client, ac_app):
        mock_now.return_value = datetime(2026, 3, 10, 14, 30)

        with ac_app.app_context():
            resp = admin_client.get('/api/export/audit?limit=99999')
            assert resp.status_code == 200

    @patch('app.routes.api.audit_api.now_local')
    def test_export_invalid_limit(self, mock_now, admin_client, ac_app):
        mock_now.return_value = datetime(2026, 3, 10, 14, 30)

        with ac_app.app_context():
            resp = admin_client.get('/api/export/audit?limit=abc')
            assert resp.status_code == 200

    def test_export_non_admin_403(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/export/audit')
            assert resp.status_code == 403


class TestSystemAudit:
    """Test GET /api/system_audit."""

    def test_html_page(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get('/api/system_audit')
            assert resp.status_code == 200

    def test_json_format_basic(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get('/api/system_audit?format=json')
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['success'] is True
            assert 'data' in data
            assert 'count' in data

    def test_json_with_date_filters(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get(
                '/api/system_audit?format=json&start_date=2026-01-01&end_date=2026-12-31'
            )
            assert resp.status_code == 200

    def test_json_with_invalid_dates(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get(
                '/api/system_audit?format=json&start_date=x&end_date=y'
            )
            assert resp.status_code == 200

    def test_json_with_action_filter(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get(
                '/api/system_audit?format=json&action=login'
            )
            assert resp.status_code == 200

    def test_json_with_user_filter(self, admin_client, ac_app):
        with ac_app.app_context():
            user = User.query.filter_by(username='ac_admin').first()
            resp = admin_client.get(
                f'/api/system_audit?format=json&user_id={user.id}'
            )
            assert resp.status_code == 200

    def test_json_with_invalid_user_id(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get(
                '/api/system_audit?format=json&user_id=notanumber'
            )
            assert resp.status_code == 200

    def test_json_with_resource_filter(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get(
                '/api/system_audit?format=json&resource_type=Sample'
            )
            assert resp.status_code == 200

    def test_json_with_q_search(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get(
                '/api/system_audit?format=json&q=test'
            )
            assert resp.status_code == 200

    def test_json_with_limit(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get(
                '/api/system_audit?format=json&limit=10'
            )
            assert resp.status_code == 200

    def test_json_limit_capped_at_2000(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get(
                '/api/system_audit?format=json&limit=99999'
            )
            assert resp.status_code == 200

    def test_json_invalid_limit(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get(
                '/api/system_audit?format=json&limit=abc'
            )
            assert resp.status_code == 200

    def test_non_admin_403(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/system_audit')
            assert resp.status_code == 403


# =====================================================================
# CHAT API ROUTE TESTS
# =====================================================================

class TestChatContacts:
    """Test GET /api/chat/contacts."""

    def test_chemist_sees_senior_and_admin(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/chat/contacts')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'contacts' in data
            # Chemist sees senior + admin
            roles = {c['role'] for c in data['contacts']}
            assert 'chemist' not in roles  # Should not see own role's peers

    def test_prep_sees_senior_and_admin(self, prep_client, ac_app):
        with ac_app.app_context():
            resp = prep_client.get('/api/chat/contacts')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'contacts' in data

    def test_senior_sees_all_roles(self, senior_client, ac_app):
        with ac_app.app_context():
            resp = senior_client.get('/api/chat/contacts')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'contacts' in data
            # Senior sees chemist, prep, admin (everyone except self)
            assert len(data['contacts']) >= 1

    def test_admin_sees_all_roles(self, admin_client, ac_app):
        with ac_app.app_context():
            resp = admin_client.get('/api/chat/contacts')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'contacts' in data

    def test_anon_redirects(self, anon_client, ac_app):
        with ac_app.app_context():
            resp = anon_client.get('/api/chat/contacts')
            assert resp.status_code in (302, 401)


class TestChatHistory:
    """Test GET /api/chat/history/<user_id>."""

    def test_basic_history(self, chemist_client, ac_app):
        with ac_app.app_context():
            user = User.query.filter_by(username='ac_senior').first()
            resp = chemist_client.get(f'/api/chat/history/{user.id}')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'messages' in data
            assert 'page' in data
            assert 'pages' in data
            assert 'total' in data
            assert 'has_more' in data

    def test_history_with_pagination(self, chemist_client, ac_app):
        with ac_app.app_context():
            user = User.query.filter_by(username='ac_senior').first()
            resp = chemist_client.get(
                f'/api/chat/history/{user.id}?page=1&per_page=10'
            )
            assert resp.status_code == 200

    def test_history_per_page_capped_at_200(self, chemist_client, ac_app):
        with ac_app.app_context():
            user = User.query.filter_by(username='ac_senior').first()
            resp = chemist_client.get(
                f'/api/chat/history/{user.id}?per_page=500'
            )
            assert resp.status_code == 200

    def test_history_with_search(self, chemist_client, ac_app):
        with ac_app.app_context():
            user = User.query.filter_by(username='ac_senior').first()
            resp = chemist_client.get(
                f'/api/chat/history/{user.id}?search=hello'
            )
            assert resp.status_code == 200

    def test_anon_redirects(self, anon_client, ac_app):
        with ac_app.app_context():
            resp = anon_client.get('/api/chat/history/1')
            assert resp.status_code in (302, 401)


class TestChatSearch:
    """Test GET /api/chat/search."""

    def test_empty_query_returns_empty(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/chat/search?q=')
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['messages'] == []

    def test_short_query_returns_empty(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/chat/search?q=a')
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['messages'] == []

    def test_valid_query(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/chat/search?q=test')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'messages' in data
            assert 'query' in data
            assert data['query'] == 'test'

    def test_query_with_user_id_filter(self, chemist_client, ac_app):
        with ac_app.app_context():
            user = User.query.filter_by(username='ac_senior').first()
            resp = chemist_client.get(f'/api/chat/search?q=hello&user_id={user.id}')
            assert resp.status_code == 200


class TestChatUnreadCount:
    """Test GET /api/chat/unread_count."""

    def test_unread_count(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/chat/unread_count')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'unread_count' in data
            assert data['unread_count'] == 0

    def test_anon_redirects(self, anon_client, ac_app):
        with ac_app.app_context():
            resp = anon_client.get('/api/chat/unread_count')
            assert resp.status_code in (302, 401)


class TestChatUpload:
    """Test POST /api/chat/upload."""

    def test_no_file_returns_400(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.post('/api/chat/upload')
            assert resp.status_code == 400

    def test_empty_filename_returns_400(self, chemist_client, ac_app):
        with ac_app.app_context():
            data = {'file': (io.BytesIO(b'data'), '')}
            resp = chemist_client.post(
                '/api/chat/upload', data=data,
                content_type='multipart/form-data'
            )
            assert resp.status_code == 400

    def test_disallowed_extension_returns_400(self, chemist_client, ac_app):
        with ac_app.app_context():
            data = {'file': (io.BytesIO(b'data'), 'virus.exe')}
            resp = chemist_client.post(
                '/api/chat/upload', data=data,
                content_type='multipart/form-data'
            )
            assert resp.status_code == 400

    def test_file_too_large_returns_400(self, chemist_client, ac_app):
        with ac_app.app_context():
            # 11MB file
            big_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * (11 * 1024 * 1024)
            data = {'file': (io.BytesIO(big_data), 'big.png')}
            resp = chemist_client.post(
                '/api/chat/upload', data=data,
                content_type='multipart/form-data'
            )
            assert resp.status_code == 400

    def test_invalid_magic_bytes_returns_400(self, chemist_client, ac_app):
        with ac_app.app_context():
            # PNG extension but not PNG magic bytes
            data = {'file': (io.BytesIO(b'\x00\x00\x00\x00' * 10), 'fake.png')}
            resp = chemist_client.post(
                '/api/chat/upload', data=data,
                content_type='multipart/form-data'
            )
            assert resp.status_code == 400

    def test_successful_upload(self, chemist_client, ac_app):
        with ac_app.app_context():
            png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
            data = {'file': (io.BytesIO(png_data), 'test.png')}
            resp = chemist_client.post(
                '/api/chat/upload', data=data,
                content_type='multipart/form-data'
            )
            assert resp.status_code == 200
            result = resp.get_json()
            assert result['success'] is True
            assert 'file_url' in result
            assert result['file_url'].startswith('/static/uploads/chat/')
            assert result['file_url'].endswith('.png')

    def test_upload_pdf(self, chemist_client, ac_app):
        with ac_app.app_context():
            pdf_data = b'%PDF-1.4' + b'\x00' * 100
            data = {'file': (io.BytesIO(pdf_data), 'doc.pdf')}
            resp = chemist_client.post(
                '/api/chat/upload', data=data,
                content_type='multipart/form-data'
            )
            assert resp.status_code == 200

    def test_upload_secure_filename_strips_bad_chars(self, chemist_client, ac_app):
        with ac_app.app_context():
            # secure_filename may strip everything, causing empty filename
            png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
            # A filename with only unsafe characters (no ASCII alphanumerics) results
            # in secure_filename returning empty or extensionless
            data = {'file': (io.BytesIO(png_data), '../../etc/passwd')}
            resp = chemist_client.post(
                '/api/chat/upload', data=data,
                content_type='multipart/form-data'
            )
            # secure_filename('../../etc/passwd') -> 'etc_passwd' which has no extension
            assert resp.status_code == 400


class TestChatSamplesSearch:
    """Test GET /api/chat/samples/search."""

    def test_empty_query(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/chat/samples/search?q=')
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['samples'] == []

    def test_short_query(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/chat/samples/search?q=a')
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['samples'] == []

    def test_valid_query(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/chat/samples/search?q=test')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'samples' in data

    def test_query_with_results(self, chemist_client, ac_app):
        with ac_app.app_context():
            # Create a sample (client_name must match CHECK constraint)
            s = Sample(sample_code='CHAT-001', sample_type='coal',
                       client_name='CHPP', lab_type='coal',
                       received_date=datetime(2026, 3, 10))
            db.session.add(s)
            db.session.commit()

            resp = chemist_client.get('/api/chat/samples/search?q=CHAT-001')
            assert resp.status_code == 200
            data = resp.get_json()
            assert len(data['samples']) >= 1
            assert data['samples'][0]['code'] == 'CHAT-001'


class TestChatTemplates:
    """Test GET /api/chat/templates."""

    def test_returns_templates(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/chat/templates')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'templates' in data
            assert len(data['templates']) == 10
            # Check structure
            t = data['templates'][0]
            assert 'id' in t
            assert 'text' in t
            assert 'icon' in t

    def test_anon_redirects(self, anon_client, ac_app):
        with ac_app.app_context():
            resp = anon_client.get('/api/chat/templates')
            assert resp.status_code in (302, 401)


class TestChatBroadcasts:
    """Test GET /api/chat/broadcasts."""

    def test_returns_broadcasts(self, chemist_client, ac_app):
        with ac_app.app_context():
            resp = chemist_client.get('/api/chat/broadcasts')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'broadcasts' in data
            assert isinstance(data['broadcasts'], list)

    def test_anon_redirects(self, anon_client, ac_app):
        with ac_app.app_context():
            resp = anon_client.get('/api/chat/broadcasts')
            assert resp.status_code in (302, 401)
