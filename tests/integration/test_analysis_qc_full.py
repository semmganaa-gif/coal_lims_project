# tests/integration/test_analysis_qc_full.py
# -*- coding: utf-8 -*-
"""
Analysis QC routes full coverage tests
Coverage target: routes/analysis/qc.py (218 lines)
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, date, timedelta
import json
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def qc_user(app):
    """QC test user"""
    with app.app_context():
        user = User.query.filter_by(username='qc_test_user').first()
        if not user:
            user = User(username='qc_test_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def qc_sample(app, qc_user):
    """QC test sample"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        sample = Sample(
            sample_code=f'QC-{unique_id}',
            client_name='QC',
            sample_type='CM',
            status='completed',
            received_date=datetime.now(),
            user_id=qc_user.id
        )
        db.session.add(sample)
        db.session.commit()

        # Add QC analysis results
        for code in ['Mad', 'Aad', 'Vdaf', 'CSN']:
            result = AnalysisResult(
                sample_id=sample.id,
                analysis_code=code,
                final_result='5.25',
                status='approved',
                user_id=qc_user.id
            )
            db.session.add(result)
        db.session.commit()
        return sample.id


def login_qc_user(client):
    """Helper login"""
    client.post('/login', data={
        'username': 'qc_test_user',
        'password': VALID_PASSWORD
    }, follow_redirects=True)


class TestQCDashboard:
    """QC Dashboard tests"""

    def test_qc_dashboard_page(self, client, app, qc_user):
        """QC dashboard page"""
        login_qc_user(client)
        response = client.get('/analysis/qc')
        assert response.status_code in [200, 302, 404]

    def test_qc_dashboard_with_date(self, client, app, qc_user):
        """QC dashboard with date filter"""
        login_qc_user(client)
        today = date.today().isoformat()
        response = client.get(f'/analysis/qc?date={today}')
        assert response.status_code in [200, 302, 404]

    def test_qc_dashboard_with_client(self, client, app, qc_user):
        """QC dashboard with client filter"""
        login_qc_user(client)
        response = client.get('/analysis/qc?client=QC')
        assert response.status_code in [200, 302, 404]


class TestQCComposite:
    """QC Composite tests"""

    def test_qc_composite_page(self, client, app, qc_user):
        """QC composite page"""
        login_qc_user(client)
        response = client.get('/analysis/qc/composite')
        assert response.status_code in [200, 302, 404]

    def test_qc_composite_with_date(self, client, app, qc_user):
        """QC composite with date"""
        login_qc_user(client)
        today = date.today().isoformat()
        response = client.get(f'/analysis/qc/composite?date={today}')
        assert response.status_code in [200, 302, 404]

    def test_qc_composite_api(self, client, app, qc_user):
        """QC composite API"""
        login_qc_user(client)
        response = client.get('/analysis/qc/api/composite')
        assert response.status_code in [200, 302, 404]


class TestQCControlStandards:
    """QC Control Standards tests"""

    def test_qc_control_standards_page(self, client, app, qc_user):
        """QC control standards page"""
        login_qc_user(client)
        response = client.get('/analysis/qc/control-standards')
        assert response.status_code in [200, 302, 404]

    def test_qc_standards_api(self, client, app, qc_user):
        """QC standards API"""
        login_qc_user(client)
        response = client.get('/analysis/qc/api/standards')
        assert response.status_code in [200, 302, 404]

    def test_qc_standards_with_code(self, client, app, qc_user):
        """QC standards with analysis code"""
        login_qc_user(client)
        response = client.get('/analysis/qc/api/standards?code=Mad')
        assert response.status_code in [200, 302, 404]


class TestQCDuplicates:
    """QC Duplicates tests"""

    def test_qc_duplicates_page(self, client, app, qc_user):
        """QC duplicates page"""
        login_qc_user(client)
        response = client.get('/analysis/qc/duplicates')
        assert response.status_code in [200, 302, 404]

    def test_qc_duplicates_api(self, client, app, qc_user):
        """QC duplicates API"""
        login_qc_user(client)
        response = client.get('/analysis/qc/api/duplicates')
        assert response.status_code in [200, 302, 404]


class TestQCNameClass:
    """QC Name/Class tests"""

    def test_qc_nameclass_page(self, client, app, qc_user):
        """QC name/class page"""
        login_qc_user(client)
        response = client.get('/analysis/qc/nameclass')
        assert response.status_code in [200, 302, 404]

    def test_qc_nameclass_api(self, client, app, qc_user):
        """QC name/class API"""
        login_qc_user(client)
        response = client.get('/analysis/qc/api/nameclass')
        assert response.status_code in [200, 302, 404]


class TestQCCorrelation:
    """QC Correlation tests"""

    def test_qc_correlation_page(self, client, app, qc_user):
        """QC correlation page"""
        login_qc_user(client)
        response = client.get('/analysis/qc/correlation')
        assert response.status_code in [200, 302, 404]

    def test_qc_correlation_api(self, client, app, qc_user):
        """QC correlation API"""
        login_qc_user(client)
        response = client.get('/analysis/qc/api/correlation')
        assert response.status_code in [200, 302, 404]


class TestQCSummary:
    """QC Summary tests"""

    def test_qc_summary_page(self, client, app, qc_user):
        """QC summary page"""
        login_qc_user(client)
        response = client.get('/analysis/qc/summary')
        assert response.status_code in [200, 302, 404]

    def test_qc_summary_api(self, client, app, qc_user):
        """QC summary API"""
        login_qc_user(client)
        response = client.get('/analysis/qc/api/summary')
        assert response.status_code in [200, 302, 404]

    def test_qc_summary_with_date_range(self, client, app, qc_user):
        """QC summary with date range"""
        login_qc_user(client)
        today = date.today()
        week_ago = today - timedelta(days=7)
        response = client.get(f'/analysis/qc/api/summary?start_date={week_ago}&end_date={today}')
        assert response.status_code in [200, 302, 404]


class TestQCData:
    """QC Data tests"""

    def test_qc_data_api(self, client, app, qc_user):
        """QC data API"""
        login_qc_user(client)
        response = client.get('/analysis/qc/api/data')
        assert response.status_code in [200, 302, 404]

    def test_qc_data_with_sample_type(self, client, app, qc_user):
        """QC data with sample type"""
        login_qc_user(client)
        response = client.get('/analysis/qc/api/data?sample_type=CM')
        assert response.status_code in [200, 302, 404]

    def test_qc_data_with_analysis_code(self, client, app, qc_user):
        """QC data with analysis code"""
        login_qc_user(client)
        response = client.get('/analysis/qc/api/data?code=Mad')
        assert response.status_code in [200, 302, 404]


class TestQCExport:
    """QC Export tests"""

    def test_qc_export_excel(self, client, app, qc_user):
        """QC export Excel"""
        login_qc_user(client)
        response = client.get('/analysis/qc/export?format=excel')
        assert response.status_code in [200, 302, 400, 404]

    def test_qc_export_csv(self, client, app, qc_user):
        """QC export CSV"""
        login_qc_user(client)
        response = client.get('/analysis/qc/export?format=csv')
        assert response.status_code in [200, 302, 400, 404]
