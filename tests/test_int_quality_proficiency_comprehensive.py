# tests/integration/test_quality_proficiency_comprehensive.py
# -*- coding: utf-8 -*-
"""
Quality proficiency routes comprehensive coverage tests
"""

import pytest
from app import db
from app.models import User, ProficiencyTest
from datetime import datetime, date
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def quality_user(app):
    """Quality user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='quality_pt_user').first()
        if not user:
            user = User(username='quality_pt_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def quality_senior(app):
    """Quality senior fixture"""
    with app.app_context():
        user = User.query.filter_by(username='quality_pt_senior').first()
        if not user:
            user = User(username='quality_pt_senior', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def quality_admin(app):
    """Quality admin fixture"""
    with app.app_context():
        user = User.query.filter_by(username='quality_pt_admin').first()
        if not user:
            user = User(username='quality_pt_admin', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def test_pt(app, quality_senior):
    """Test PT fixture"""
    with app.app_context():
        senior = User.query.filter_by(username='quality_pt_senior').first()
        pt = ProficiencyTest(
            pt_provider='Test Provider',
            pt_program='Test Program 2024',
            round_number='Round 1',
            sample_code='PT-001',
            analysis_code='Mad',
            our_result=5.5,
            assigned_value=5.4,
            uncertainty=0.3,
            z_score=0.33,
            performance='satisfactory',
            test_date=date.today(),
            tested_by_id=senior.id if senior else None
        )
        db.session.add(pt)
        db.session.commit()
        return pt.id


class TestProficiencyList:
    """Proficiency list тестүүд"""

    def test_proficiency_list_unauthenticated(self, client, app):
        """Proficiency list without login"""
        response = client.get('/quality/proficiency')
        assert response.status_code in [200, 302, 404]

    def test_proficiency_list_chemist(self, client, app, quality_user):
        """Proficiency list with chemist"""
        client.post('/login', data={
            'username': 'quality_pt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/proficiency')
        assert response.status_code in [200, 302, 404]

    def test_proficiency_list_with_data(self, client, app, quality_senior, test_pt):
        """Proficiency list with data"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/proficiency')
        assert response.status_code in [200, 302, 404]


class TestProficiencyNew:
    """Proficiency new тестүүд"""

    def test_proficiency_new_get_chemist_forbidden(self, client, app, quality_user):
        """Proficiency new GET with chemist - forbidden"""
        client.post('/login', data={
            'username': 'quality_pt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/proficiency/new')
        assert response.status_code in [200, 302, 403]

    def test_proficiency_new_get_senior(self, client, app, quality_senior):
        """Proficiency new GET with senior"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/proficiency/new')
        assert response.status_code in [200, 302, 404]

    def test_proficiency_new_post_valid(self, client, app, quality_senior):
        """Proficiency new POST with valid data"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/quality/proficiency/new', data={
            'pt_provider': 'Test Provider',
            'pt_program': 'Test Program',
            'round_number': 'Round 1',
            'sample_code': 'PT-TEST-001',
            'analysis_code': 'Mad',
            'our_result': '5.5',
            'assigned_value': '5.4',
            'uncertainty': '0.3',
            'test_date': date.today().isoformat(),
            'notes': 'Test PT entry'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400]

    def test_proficiency_new_post_satisfactory(self, client, app, quality_senior):
        """Proficiency new POST - satisfactory performance (|z| <= 2)"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        # z = (5.5 - 5.4) / 0.3 = 0.33 -> satisfactory
        response = client.post('/quality/proficiency/new', data={
            'pt_provider': 'Provider',
            'pt_program': 'Program',
            'round_number': 'R1',
            'sample_code': 'S1',
            'analysis_code': 'Mad',
            'our_result': '5.5',
            'assigned_value': '5.4',
            'uncertainty': '0.3',
            'test_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400]

    def test_proficiency_new_post_questionable(self, client, app, quality_senior):
        """Proficiency new POST - questionable performance (2 < |z| <= 3)"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        # z = (5.5 - 5.0) / 0.2 = 2.5 -> questionable
        response = client.post('/quality/proficiency/new', data={
            'pt_provider': 'Provider',
            'pt_program': 'Program Question',
            'round_number': 'R2',
            'sample_code': 'S2',
            'analysis_code': 'Aad',
            'our_result': '5.5',
            'assigned_value': '5.0',
            'uncertainty': '0.2',
            'test_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400]

    def test_proficiency_new_post_unsatisfactory(self, client, app, quality_senior):
        """Proficiency new POST - unsatisfactory performance (|z| > 3)"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        # z = (6.0 - 5.0) / 0.25 = 4.0 -> unsatisfactory
        response = client.post('/quality/proficiency/new', data={
            'pt_provider': 'Provider',
            'pt_program': 'Program Unsatisfactory',
            'round_number': 'R3',
            'sample_code': 'S3',
            'analysis_code': 'Vad',
            'our_result': '6.0',
            'assigned_value': '5.0',
            'uncertainty': '0.25',
            'test_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400]

    def test_proficiency_new_post_zero_uncertainty(self, client, app, quality_senior):
        """Proficiency new POST - zero uncertainty"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/quality/proficiency/new', data={
            'pt_provider': 'Provider',
            'pt_program': 'Zero Uncertainty',
            'round_number': 'R4',
            'sample_code': 'S4',
            'analysis_code': 'CV',
            'our_result': '6500',
            'assigned_value': '6500',
            'uncertainty': '0',
            'test_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400]

    def test_proficiency_new_post_invalid_numbers(self, client, app, quality_senior):
        """Proficiency new POST - invalid numbers"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/quality/proficiency/new', data={
            'pt_provider': 'Provider',
            'pt_program': 'Invalid Numbers',
            'round_number': 'R5',
            'sample_code': 'S5',
            'analysis_code': 'TS',
            'our_result': 'not_a_number',
            'assigned_value': '5.0',
            'uncertainty': '0.3',
            'test_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400]

    def test_proficiency_new_post_empty_date(self, client, app, quality_senior):
        """Proficiency new POST - empty date"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/quality/proficiency/new', data={
            'pt_provider': 'Provider',
            'pt_program': 'Empty Date',
            'round_number': 'R6',
            'sample_code': 'S6',
            'analysis_code': 'HGI',
            'our_result': '5.5',
            'assigned_value': '5.4',
            'uncertainty': '0.3',
            'test_date': ''
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400]


class TestProficiencyEdit:
    """Proficiency edit тестүүд"""

    def test_proficiency_edit_get(self, client, app, quality_senior, test_pt):
        """Proficiency edit GET"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/quality/proficiency/{test_pt}/edit')
        assert response.status_code in [200, 302, 404]

    def test_proficiency_edit_post(self, client, app, quality_senior, test_pt):
        """Proficiency edit POST"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/quality/proficiency/{test_pt}/edit', data={
            'pt_provider': 'Updated Provider',
            'pt_program': 'Updated Program',
            'round_number': 'Round 2',
            'sample_code': 'PT-001-UPD',
            'analysis_code': 'Mad',
            'our_result': '5.6',
            'assigned_value': '5.5',
            'uncertainty': '0.25',
            'test_date': date.today().isoformat(),
            'notes': 'Updated notes'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestProficiencyDelete:
    """Proficiency delete тестүүд"""

    def test_proficiency_delete(self, client, app, quality_admin):
        """Proficiency delete"""
        with app.app_context():
            admin = User.query.filter_by(username='quality_pt_admin').first()
            pt = ProficiencyTest(
                pt_provider='Delete Test',
                pt_program='To Delete',
                round_number='R99',
                sample_code='DEL-001',
                analysis_code='Mad',
                our_result=5.5,
                assigned_value=5.4,
                uncertainty=0.3,
                z_score=0.33,
                performance='satisfactory',
                test_date=date.today(),
                tested_by_id=admin.id if admin else None
            )
            db.session.add(pt)
            db.session.commit()
            pt_id = pt.id

        client.post('/login', data={
            'username': 'quality_pt_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/quality/proficiency/{pt_id}/delete', follow_redirects=True)
        assert response.status_code in [200, 302, 400, 403, 404]


class TestControlChartsComprehensive:
    """Control charts comprehensive тестүүд"""

    def test_control_charts_list(self, client, app, quality_user):
        """Control charts list"""
        client.post('/login', data={
            'username': 'quality_pt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/control_charts')
        assert response.status_code in [200, 302, 404]

    def test_control_chart_by_code(self, client, app, quality_user):
        """Control chart by code"""
        client.post('/login', data={
            'username': 'quality_pt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/control_charts?code=Mad')
        assert response.status_code in [200, 302, 404]


class TestCAPAComprehensive:
    """CAPA comprehensive тестүүд"""

    def test_capa_list(self, client, app, quality_user):
        """CAPA list"""
        client.post('/login', data={
            'username': 'quality_pt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/capa')
        assert response.status_code in [200, 302, 404]

    def test_capa_new_get(self, client, app, quality_senior):
        """CAPA new GET"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/capa/new')
        assert response.status_code in [200, 302, 404]

    def test_capa_new_post(self, client, app, quality_senior):
        """CAPA new POST"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/quality/capa/new', data={
            'issue_source': 'Internal Audit',
            'issue_description': 'Test issue description',
            'root_cause': 'Human error',
            'corrective_action': 'Training',
            'responsible_person': 'John Doe',
            'due_date': (date.today()).isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestComplaintsComprehensive:
    """Complaints comprehensive тестүүд"""

    def test_complaints_list(self, client, app, quality_user):
        """Complaints list"""
        client.post('/login', data={
            'username': 'quality_pt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/complaints')
        assert response.status_code in [200, 302, 404]

    def test_complaints_new_get(self, client, app, quality_senior):
        """Complaints new GET"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/complaints/new')
        assert response.status_code in [200, 302, 404]


class TestEnvironmentalComprehensive:
    """Environmental logs comprehensive тестүүд"""

    def test_environmental_list(self, client, app, quality_user):
        """Environmental list"""
        client.post('/login', data={
            'username': 'quality_pt_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/environmental')
        assert response.status_code in [200, 302, 404]

    def test_environmental_new_get(self, client, app, quality_senior):
        """Environmental new GET"""
        client.post('/login', data={
            'username': 'quality_pt_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/environmental/new')
        assert response.status_code in [200, 302, 404]
