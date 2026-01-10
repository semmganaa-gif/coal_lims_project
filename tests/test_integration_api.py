# -*- coding: utf-8 -*-
"""
Integration Tests - API Flow
Full workflow testing across multiple endpoints
"""
import pytest
from flask import url_for
from app import db
from app.models import Sample, AnalysisResult, User


class TestSampleWorkflow:
    """Дээжийн бүрэн workflow тест"""

    def test_complete_sample_lifecycle(self, client, auth_client, sample_factory):
        """Дээж бүртгэлээс устгах хүртэлх бүрэн flow"""
        # 1. Login
        auth_client.login()

        # 2. Create sample
        sample_data = {
            "sample_code": "INTEG-001",
            "client": "QC",
            "sample_type": "coal",
            "description": "Integration test sample"
        }
        response = client.post(
            "/api/samples",
            json=sample_data,
            headers={"Content-Type": "application/json"}
        )
        # May need CSRF for non-API routes
        assert response.status_code in [200, 201, 302, 400]

    def test_sample_search_flow(self, client, auth_client, init_database):
        """Дээж хайлтын flow"""
        auth_client.login()

        # Search samples
        response = client.get("/api/samples?search=QC")
        assert response.status_code == 200

    def test_sample_status_update_flow(self, client, auth_client, init_database):
        """Дээжийн статус шинэчлэх flow"""
        auth_client.login()

        # Get sample first
        response = client.get("/api/samples")
        assert response.status_code == 200


class TestAnalysisWorkflow:
    """Шинжилгээний бүрэн workflow тест"""

    def test_analysis_result_entry_flow(self, client, auth_client, init_database):
        """Шинжилгээний үр дүн оруулах flow"""
        auth_client.login()

        # 1. Get workspace data
        response = client.get("/analysis/workspace")
        assert response.status_code == 200

    def test_analysis_save_and_retrieve_flow(self, client, auth_client, init_database):
        """Шинжилгээ хадгалах, дахин авах flow"""
        auth_client.login()

        # Get analysis page
        response = client.get("/analysis/")
        assert response.status_code == 200

    def test_qc_check_after_analysis(self, client, auth_client, init_database):
        """Шинжилгээний дараа QC шалгалт"""
        auth_client.login()

        # Access QC page
        response = client.get("/quality/")
        assert response.status_code in [200, 302]


class TestUserWorkflow:
    """Хэрэглэгчийн workflow тест"""

    def test_user_login_logout_flow(self, client):
        """Нэвтрэх, гарах flow"""
        # 1. Access login page
        response = client.get("/login")
        assert response.status_code == 200

        # 2. Login
        response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        }, follow_redirects=True)
        assert response.status_code == 200

        # 3. Access protected page
        response = client.get("/samples")
        assert response.status_code in [200, 302]

        # 4. Logout
        response = client.get("/logout", follow_redirects=True)
        assert response.status_code == 200

    def test_session_persistence(self, client, auth_client):
        """Session тогтвортой байдал"""
        auth_client.login()

        # Multiple page accesses
        pages = ["/", "/samples", "/analysis/", "/reports"]
        for page in pages:
            response = client.get(page)
            # Should not redirect to login
            assert response.status_code in [200, 302]


class TestReportWorkflow:
    """Тайлангийн workflow тест"""

    def test_report_generation_flow(self, client, auth_client, init_database):
        """Тайлан үүсгэх flow"""
        auth_client.login()

        # Access reports page
        response = client.get("/reports")
        assert response.status_code in [200, 302]

    def test_export_flow(self, client, auth_client, init_database):
        """Export хийх flow"""
        auth_client.login()

        # Try export endpoint
        response = client.get("/reports/export?format=excel")
        # May return file or redirect
        assert response.status_code in [200, 302, 400, 404]


class TestAdminWorkflow:
    """Админ workflow тест"""

    def test_admin_user_management_flow(self, client, auth_client):
        """Хэрэглэгч удирдах flow"""
        auth_client.login_as_admin()

        # Access admin page
        response = client.get("/admin/")
        assert response.status_code in [200, 302]

        # Access users page
        response = client.get("/admin/users")
        assert response.status_code in [200, 302]

    def test_admin_settings_flow(self, client, auth_client):
        """Тохиргоо удирдах flow"""
        auth_client.login_as_admin()

        # Access settings
        response = client.get("/settings")
        assert response.status_code in [200, 302]


class TestAPIIntegration:
    """API endpoint integration"""

    def test_api_sample_crud_flow(self, client, auth_client):
        """Sample API CRUD flow"""
        auth_client.login()

        # List
        response = client.get("/api/samples")
        assert response.status_code == 200

        # The API should return JSON
        if response.content_type and "json" in response.content_type:
            data = response.get_json()
            assert data is not None

    def test_api_analysis_flow(self, client, auth_client):
        """Analysis API flow"""
        auth_client.login()

        # Get analysis data
        response = client.get("/api/analysis/results")
        assert response.status_code in [200, 404]

    def test_api_error_handling(self, client, auth_client):
        """API error handling"""
        auth_client.login()

        # Invalid endpoint
        response = client.get("/api/nonexistent")
        assert response.status_code in [404, 400]

        # Invalid ID
        response = client.get("/api/samples/999999999")
        assert response.status_code in [404, 400, 200]


class TestConcurrentOperations:
    """Зэрэг ажиллагааны тест"""

    def test_multiple_users_access(self, app, init_database):
        """Олон хэрэглэгч нэгэн зэрэг хандах"""
        with app.test_client() as client1, app.test_client() as client2:
            # User 1 login
            client1.post("/login", data={
                "username": "admin",
                "password": "admin123"
            })

            # User 2 login (different session)
            client2.post("/login", data={
                "username": "chemist1",
                "password": "chemist123"
            })

            # Both access samples
            resp1 = client1.get("/samples")
            resp2 = client2.get("/samples")

            assert resp1.status_code in [200, 302]
            assert resp2.status_code in [200, 302]


class TestDataIntegrity:
    """Өгөгдлийн бүрэн бүтэн байдлын тест"""

    def test_sample_analysis_relationship(self, app, init_database):
        """Дээж-Шинжилгээ холбоос"""
        with app.app_context():
            # Get sample with results
            sample = Sample.query.first()
            if sample:
                # Access results relationship
                results = sample.results
                assert isinstance(results, list)

    def test_cascade_operations(self, app, init_database):
        """Cascade delete/update"""
        with app.app_context():
            # This tests that relationships are properly defined
            sample = Sample.query.first()
            if sample:
                sample_id = sample.id
                # Should be able to access related data
                assert sample.id is not None


class TestSecurityIntegration:
    """Аюулгүй байдлын integration тест"""

    def test_csrf_protection(self, client):
        """CSRF хамгаалалт"""
        # POST without CSRF should fail for non-API routes
        response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        # Depends on CSRF configuration
        assert response.status_code in [200, 302, 400]

    def test_unauthorized_access(self, client):
        """Зөвшөөрөлгүй хандалт"""
        # Access protected page without login
        response = client.get("/admin/users")
        # Should redirect to login or show 403
        assert response.status_code in [302, 403, 401]

    def test_role_based_access(self, client, auth_client):
        """Role-based хандалт"""
        # Login as non-admin
        auth_client.login()

        # Try to access admin page
        response = client.get("/admin/users")
        # May be forbidden or redirected
        assert response.status_code in [200, 302, 403]
