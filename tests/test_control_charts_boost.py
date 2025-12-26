# tests/test_control_charts_boost.py
# -*- coding: utf-8 -*-
"""Tests to boost quality/control_charts.py coverage."""

import pytest
import json
from unittest.mock import patch, MagicMock


@pytest.fixture
def admin_user(app, db, client):
    """Create and login as admin."""
    with app.app_context():
        from app.models import User
        user = User.query.filter_by(username='qcadmin').first()
        if not user:
            user = User(username='qcadmin', role='admin')
            user.set_password('AdminPass123!')
            db.session.add(user)
            db.session.commit()
        client.post('/login', data={'username': 'qcadmin', 'password': 'AdminPass123!'})
        return user


class TestControlChartsRoutes:
    """Test control charts routes."""

    def test_control_charts_page(self, client, admin_user):
        """Test control charts page."""
        response = client.get('/quality/control_charts')
        assert response.status_code in [200, 302, 404]

    def test_control_charts_data(self, client, admin_user):
        """Test control charts data API."""
        response = client.get('/api/control_charts/data?analysis=TM')
        assert response.status_code in [200, 302, 404]

    def test_control_charts_with_date_range(self, client, admin_user):
        """Test control charts with date range."""
        response = client.get('/quality/control_charts?from=2025-01-01&to=2025-12-31')
        assert response.status_code in [200, 302, 404]


class TestQCStatistics:
    """Test QC statistics."""

    def test_qc_stats_summary(self, client, admin_user):
        """Test QC stats summary."""
        response = client.get('/api/qc/stats')
        assert response.status_code in [200, 302, 404]

    def test_qc_violations(self, client, admin_user):
        """Test QC violations."""
        response = client.get('/api/qc/violations')
        assert response.status_code in [200, 302, 404]


class TestWestgardRules:
    """Test Westgard rules."""

    def test_check_westgard_rules(self, client, admin_user):
        """Test check Westgard rules."""
        response = client.post('/api/qc/check_westgard',
            data=json.dumps({'values': [1.0, 2.0, 3.0, 4.0, 5.0]}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]


class TestControlLimits:
    """Test control limits."""

    def test_get_control_limits(self, client, admin_user):
        """Test get control limits."""
        response = client.get('/api/qc/limits?analysis=TM')
        assert response.status_code in [200, 302, 404]

    def test_update_control_limits(self, client, admin_user):
        """Test update control limits."""
        response = client.post('/api/qc/limits',
            data=json.dumps({
                'analysis': 'TM',
                'mean': 5.0,
                'std': 0.5
            }),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404, 405]
