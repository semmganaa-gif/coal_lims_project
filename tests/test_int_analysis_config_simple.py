# -*- coding: utf-8 -*-
"""
Test: Шинэ энгийн шинжилгээний тохиргоо (Card-based UI)
"""
import pytest


class TestAnalysisConfigSimple:
    """Шинэ тохиргооны хуудасны тестүүд"""

    def test_config_page_requires_login(self, client):
        """Login шаардлагатай"""
        response = client.get('/admin/analysis_config_simple')
        assert response.status_code in [302, 401, 403]

    def test_config_page_requires_senior_role(self, auth_user):
        """Chemist эрхтэй хэрэглэгч хандах боломжгүй"""
        response = auth_user.get('/admin/analysis_config_simple')
        assert response.status_code in [302, 403]

    def test_config_page_admin_access(self, auth_admin):
        """Admin эрхтэй хэрэглэгч хандах боломжтой"""
        response = auth_admin.get('/admin/analysis_config_simple')
        assert response.status_code == 200

    def test_config_page_has_card_ui(self, auth_admin):
        """Card-based UI байгаа эсэх"""
        response = auth_admin.get('/admin/analysis_config_simple')
        html = response.data.decode('utf-8')

        assert 'client-card' in html
        assert 'analysis-chip' in html

    def test_config_page_has_gi_modal(self, auth_admin):
        """Gi modal байгаа эсэх"""
        response = auth_admin.get('/admin/analysis_config_simple')
        html = response.data.decode('utf-8')

        assert 'giModal' in html
        assert 'PF211' in html
        assert 'PF221' in html

    def test_config_save_endpoint(self, auth_admin):
        """Хадгалах endpoint ажиллаж байгаа эсэх"""
        response = auth_admin.post('/admin/analysis_config_simple_save', data={})
        # Should redirect after save
        assert response.status_code in [200, 302]

    def test_config_page_has_analysis_types(self, auth_admin):
        """Шинжилгээний төрлүүд байгаа эсэх"""
        response = auth_admin.get('/admin/analysis_config_simple')
        html = response.data.decode('utf-8')

        # Check for common analysis codes
        assert 'MT' in html or 'Mad' in html or 'Aad' in html
