# -*- coding: utf-8 -*-
"""
Admin Routes модулийн coverage тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock


class TestAdminBlueprintExists:
    """admin_bp Blueprint тест"""

    def test_blueprint_exists(self):
        from app.routes.admin.routes import admin_bp
        assert admin_bp is not None
        assert admin_bp.name == 'admin'
        assert admin_bp.url_prefix == '/admin'


class TestAdminRequiredDecorator:
    """admin_required декоратор тест"""

    def test_import_decorator(self):
        from app.routes.admin.routes import admin_required
        assert admin_required is not None
        assert callable(admin_required)

    def test_decorator_returns_function(self):
        from app.routes.admin.routes import admin_required

        @admin_required
        def test_func():
            return "success"

        assert callable(test_func)


class TestSeniorOrAdminRequiredDecorator:
    """senior_or_admin_required декоратор тест"""

    def test_import_decorator(self):
        from app.routes.admin.routes import senior_or_admin_required
        assert senior_or_admin_required is not None
        assert callable(senior_or_admin_required)

    def test_decorator_returns_function(self):
        from app.routes.admin.routes import senior_or_admin_required

        @senior_or_admin_required
        def test_func():
            return "success"

        assert callable(test_func)


class TestSeedAnalysisTypes:
    """_seed_analysis_types функц тест"""

    def test_import_function(self):
        from app.services.admin_service import seed_analysis_types
        assert seed_analysis_types is not None
        assert callable(seed_analysis_types)


# ============================================================
# Route Tests - Actual Routes
# ============================================================

class TestManageUsersRoute:
    """manage_users route тест"""

    def test_requires_login(self, client):
        response = client.get('/admin/manage_users')
        # Redirect to login or forbidden
        assert response.status_code in [302, 401, 403]

    def test_regular_user_forbidden(self, logged_in_user):
        response = logged_in_user.get('/admin/manage_users')
        assert response.status_code == 403

    def test_admin_can_access(self, logged_in_admin):
        response = logged_in_admin.get('/admin/manage_users')
        assert response.status_code == 200


class TestEditUserRoute:
    """edit_user route тест"""

    def test_requires_login(self, client):
        response = client.get('/admin/edit_user/1')
        assert response.status_code in [302, 401, 403]

    def test_regular_user_forbidden(self, logged_in_user):
        response = logged_in_user.get('/admin/edit_user/1')
        assert response.status_code == 403


class TestDeleteUserRoute:
    """delete_user route тест"""

    def test_requires_login(self, client):
        response = client.post('/admin/delete_user/1')
        assert response.status_code in [302, 401, 403]

    def test_requires_post(self, logged_in_admin):
        response = logged_in_admin.get('/admin/delete_user/1')
        assert response.status_code == 405

    def test_regular_user_forbidden(self, logged_in_user):
        response = logged_in_user.post('/admin/delete_user/1')
        assert response.status_code == 403


class TestAnalysisConfigRoute:
    """analysis_config route тест"""

    def test_requires_login(self, client):
        response = client.get('/admin/analysis_config')
        assert response.status_code in [302, 401, 403]

    def test_admin_can_access(self, logged_in_admin):
        response = logged_in_admin.get('/admin/analysis_config')
        # May redirect or show page
        assert response.status_code in [200, 302]


class TestAnalysisConfigSimpleRoute:
    """analysis_config_simple route тест"""

    def test_requires_login(self, client):
        response = client.get('/admin/analysis_config_simple')
        assert response.status_code in [302, 401, 403]


class TestControlStandardsRoute:
    """control_standards route тест"""

    def test_requires_login(self, client):
        response = client.get('/admin/control_standards')
        assert response.status_code in [302, 401, 403]

    def test_admin_can_access(self, logged_in_admin):
        response = logged_in_admin.get('/admin/control_standards')
        assert response.status_code == 200


class TestControlStandardsCreateRoute:
    """control_standards/create route тест"""

    def test_requires_login(self, client):
        response = client.post('/admin/control_standards/create',
                              json={'name': 'CM-2026-Q1'})
        assert response.status_code in [302, 401, 403]

    def test_regular_user_forbidden(self, logged_in_user):
        response = logged_in_user.post('/admin/control_standards/create',
                                      json={'name': 'CM-2026-Q1'})
        assert response.status_code == 403


class TestGbwStandardsRoute:
    """gbw_standards route тест"""

    def test_requires_login(self, client):
        response = client.get('/admin/gbw_standards')
        assert response.status_code in [302, 401, 403]

    def test_admin_can_access(self, logged_in_admin):
        response = logged_in_admin.get('/admin/gbw_standards')
        assert response.status_code == 200


class TestGbwStandardsCreateRoute:
    """gbw_standards/create route тест"""

    def test_requires_login(self, client):
        response = client.post('/admin/gbw_standards/create',
                              json={'name': 'GBW11135a'})
        assert response.status_code in [302, 401, 403]

    def test_regular_user_forbidden(self, logged_in_user):
        response = logged_in_user.post('/admin/gbw_standards/create',
                                      json={'name': 'GBW11135a'})
        assert response.status_code == 403


class TestDeletePatternProfileRoute:
    """delete_pattern_profile route тест"""

    def test_requires_login(self, client):
        response = client.post('/admin/delete_pattern_profile/1')
        assert response.status_code in [302, 401, 403]


# ============================================================
# Fixtures - conftest.py дээрээс app, client, auth_user, auth_admin авна
# ============================================================

@pytest.fixture
def logged_in_user(auth_user):
    """auth_user-г ашиглана (chemist role)"""
    return auth_user


@pytest.fixture
def logged_in_admin(auth_admin):
    """auth_admin-г ашиглана"""
    return auth_admin
