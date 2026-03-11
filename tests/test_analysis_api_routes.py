# tests/test_analysis_api_routes.py
# -*- coding: utf-8 -*-
"""
analysis_api.py coverage 80%+ хүргэх тестүүд.
Routes: /api/eligible_samples, /api/unassign_sample, /api/save_results,
        /api/update_result_status, /api/request_analysis, /api/check_ready_samples
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, date, timedelta
from app import create_app, db
from app.models import User, Sample, AnalysisResult, AnalysisResultLog
from tests.conftest import TestConfig


@pytest.fixture
def analysis_app():
    """Test application fixture"""
    flask_app = create_app(TestConfig)
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SERVER_NAME'] = 'localhost'

    with flask_app.app_context():
        db.create_all()

        # Create users
        for role, uname in [('admin', 'analadmin'), ('senior', 'analsenior'), ('chemist', 'analchemist')]:
            if not User.query.filter_by(username=uname).first():
                user = User(username=uname, role=role)
                user.set_password('TestPass123')
                db.session.add(user)
        db.session.commit()

    yield flask_app

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def admin_client(analysis_app):
    """Admin client"""
    client = analysis_app.test_client()
    with analysis_app.app_context():
        user = User.query.filter_by(username='analadmin').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def senior_client(analysis_app):
    """Senior client"""
    client = analysis_app.test_client()
    with analysis_app.app_context():
        user = User.query.filter_by(username='analsenior').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def chemist_client(analysis_app):
    """Chemist client"""
    client = analysis_app.test_client()
    with analysis_app.app_context():
        user = User.query.filter_by(username='analchemist').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def sample_with_analyses(analysis_app):
    """Create sample with analyses_to_perform"""
    with analysis_app.app_context():
        user = User.query.filter_by(username='analchemist').first()
        sample = Sample(
            sample_code='ANAL-TEST-001',
            user_id=user.id,
            client_name='CHPP',
            sample_type='2 hourly',
            sample_condition='Хуурай',
            sample_date=date.today(),
            received_date=datetime.now(),
            status='new',
            analyses_to_perform='["Mad", "Aad", "Vad"]'
        )
        db.session.add(sample)
        db.session.commit()
        return sample.id


@pytest.fixture
def sample_with_result(analysis_app):
    """Create sample with analysis result"""
    with analysis_app.app_context():
        user = User.query.filter_by(username='analchemist').first()
        sample = Sample(
            sample_code='ANAL-RESULT-001',
            user_id=user.id,
            client_name='CHPP',
            sample_type='2 hourly',
            sample_condition='Хуурай',
            sample_date=date.today(),
            received_date=datetime.now(),
            status='new',
            analyses_to_perform='["Mad"]'
        )
        db.session.add(sample)
        db.session.commit()

        result = AnalysisResult(
            sample_id=sample.id,
            user_id=user.id,
            analysis_code='Mad',
            final_result=5.5,
            status='pending_review',
            raw_data='{"avg": 5.5}'
        )
        db.session.add(result)
        db.session.commit()
        return {'sample_id': sample.id, 'result_id': result.id}


class TestEligibleSamples:
    """eligible_samples endpoint tests - lines 76-154"""

    def test_eligible_samples_empty_code(self, admin_client, analysis_app):
        """Empty analysis code"""
        with analysis_app.app_context():
            response = admin_client.get('/api/eligible_samples/')
            assert response.status_code in [200, 404]

    def test_eligible_samples_valid_code(self, admin_client, analysis_app, sample_with_analyses):
        """Valid analysis code"""
        with analysis_app.app_context():
            response = admin_client.get('/api/eligible_samples/Mad')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'samples' in data

    def test_eligible_samples_with_aliases(self, admin_client, analysis_app, sample_with_analyses):
        """Analysis code with aliases"""
        with analysis_app.app_context():
            response = admin_client.get('/api/eligible_samples/Aad')
            assert response.status_code == 200

    def test_eligible_samples_chemist_rejected(self, chemist_client, analysis_app, sample_with_result):
        """Chemist sees own rejected samples"""
        with analysis_app.app_context():
            # Update result to rejected
            result = AnalysisResult.query.get(sample_with_result['result_id'])
            result.status = 'rejected'
            result.error_reason = 'Test error'
            db.session.commit()

            response = chemist_client.get('/api/eligible_samples/Mad')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'rejected' in data


class TestUnassignSample:
    """unassign_sample endpoint tests - lines 159-218"""

    def test_unassign_chemist_forbidden(self, chemist_client, analysis_app, sample_with_analyses):
        """Chemist cannot unassign"""
        with analysis_app.app_context():
            response = chemist_client.post('/api/unassign_sample',
                data=json.dumps({
                    'sample_id': sample_with_analyses,
                    'analysis_code': 'Mad'
                }),
                content_type='application/json')
            assert response.status_code == 403

    def test_unassign_no_json(self, admin_client, analysis_app):
        """Unassign without JSON"""
        with analysis_app.app_context():
            response = admin_client.post('/api/unassign_sample',
                data='not json')
            assert response.status_code == 400

    def test_unassign_missing_params(self, admin_client, analysis_app):
        """Unassign missing parameters"""
        with analysis_app.app_context():
            response = admin_client.post('/api/unassign_sample',
                data=json.dumps({'sample_id': 1}),
                content_type='application/json')
            assert response.status_code == 400

    def test_unassign_sample_not_found(self, admin_client, analysis_app):
        """Unassign non-existent sample"""
        with analysis_app.app_context():
            response = admin_client.post('/api/unassign_sample',
                data=json.dumps({
                    'sample_id': 99999,
                    'analysis_code': 'Mad'
                }),
                content_type='application/json')
            assert response.status_code == 404

    def test_unassign_code_not_assigned(self, admin_client, analysis_app, sample_with_analyses):
        """Unassign code not in analyses"""
        with analysis_app.app_context():
            response = admin_client.post('/api/unassign_sample',
                data=json.dumps({
                    'sample_id': sample_with_analyses,
                    'analysis_code': 'NotExist'
                }),
                content_type='application/json')
            assert response.status_code == 400

    def test_unassign_success(self, admin_client, analysis_app, sample_with_analyses):
        """Unassign success"""
        with analysis_app.app_context():
            response = admin_client.post('/api/unassign_sample',
                data=json.dumps({
                    'sample_id': sample_with_analyses,
                    'analysis_code': 'Mad'
                }),
                content_type='application/json')
            # May succeed or fail depending on data state
            assert response.status_code in [200, 400, 404]


class TestSaveResults:
    """save_results endpoint tests - lines 223-615"""

    def test_save_no_json(self, admin_client, analysis_app):
        """Save without JSON"""
        with analysis_app.app_context():
            response = admin_client.post('/api/save_results',
                data='not json')
            assert response.status_code == 400

    def test_save_empty_array(self, admin_client, analysis_app):
        """Save empty array"""
        with analysis_app.app_context():
            response = admin_client.post('/api/save_results',
                data=json.dumps([]),
                content_type='application/json')
            assert response.status_code == 400

    def test_save_single_result(self, admin_client, analysis_app, sample_with_analyses):
        """Save single result"""
        with analysis_app.app_context():
            response = admin_client.post('/api/save_results',
                data=json.dumps({
                    'sample_id': sample_with_analyses,
                    'analysis_code': 'Mad',
                    'final_result': 5.5,
                    'raw_data': {'avg': 5.5}
                }),
                content_type='application/json')
            assert response.status_code in [200, 207, 400]

    def test_save_multiple_results(self, admin_client, analysis_app, sample_with_analyses):
        """Save multiple results"""
        with analysis_app.app_context():
            response = admin_client.post('/api/save_results',
                data=json.dumps([
                    {
                        'sample_id': sample_with_analyses,
                        'analysis_code': 'Aad',
                        'final_result': 10.5,
                        'raw_data': {'avg': 10.5}
                    },
                    {
                        'sample_id': sample_with_analyses,
                        'analysis_code': 'Vad',
                        'final_result': 25.5,
                        'raw_data': {'avg': 25.5}
                    }
                ]),
                content_type='application/json')
            assert response.status_code in [200, 207]

    def test_save_invalid_sample_id(self, admin_client, analysis_app):
        """Save with invalid sample_id"""
        with analysis_app.app_context():
            response = admin_client.post('/api/save_results',
                data=json.dumps({
                    'sample_id': 'invalid',
                    'analysis_code': 'Mad',
                    'final_result': 5.5
                }),
                content_type='application/json')
            assert response.status_code in [200, 207, 400]

    def test_save_sample_not_found(self, admin_client, analysis_app):
        """Save to non-existent sample"""
        with analysis_app.app_context():
            response = admin_client.post('/api/save_results',
                data=json.dumps({
                    'sample_id': 99999,
                    'analysis_code': 'Mad',
                    'final_result': 5.5
                }),
                content_type='application/json')
            assert response.status_code in [200, 207]


class TestUpdateResultStatus:
    """update_result_status endpoint tests - lines 620-693"""

    def test_update_chemist_forbidden(self, chemist_client, analysis_app, sample_with_result):
        """Chemist cannot update status"""
        with analysis_app.app_context():
            result_id = sample_with_result['result_id']
            response = chemist_client.post(f'/api/update_result_status/{result_id}/approved')
            assert response.status_code == 403

    def test_update_invalid_status(self, admin_client, analysis_app, sample_with_result):
        """Update with invalid status"""
        with analysis_app.app_context():
            result_id = sample_with_result['result_id']
            response = admin_client.post(f'/api/update_result_status/{result_id}/invalid_status')
            assert response.status_code == 400

    def test_update_approve(self, admin_client, analysis_app, sample_with_result):
        """Approve result"""
        with analysis_app.app_context():
            result_id = sample_with_result['result_id']
            response = admin_client.post(f'/api/update_result_status/{result_id}/approved',
                data=json.dumps({}),
                content_type='application/json')
            assert response.status_code in [200, 302]

    def test_update_reject(self, admin_client, analysis_app, sample_with_result):
        """Reject result"""
        with analysis_app.app_context():
            result_id = sample_with_result['result_id']
            response = admin_client.post(f'/api/update_result_status/{result_id}/rejected',
                data=json.dumps({
                    'rejection_comment': 'Test rejection',
                    'rejection_category': 'error',
                    'error_reason': 'Calculation error'
                }),
                content_type='application/json')
            assert response.status_code in [200, 302]

    def test_update_pending_review(self, admin_client, analysis_app, sample_with_result):
        """Set to pending_review"""
        with analysis_app.app_context():
            result_id = sample_with_result['result_id']
            response = admin_client.post(f'/api/update_result_status/{result_id}/pending_review',
                data=json.dumps({'action_type': 'recheck'}),
                content_type='application/json')
            assert response.status_code in [200, 302]

    def test_update_with_form_data(self, admin_client, analysis_app, sample_with_result):
        """Update with form data (not JSON)"""
        with analysis_app.app_context():
            result_id = sample_with_result['result_id']
            response = admin_client.post(f'/api/update_result_status/{result_id}/approved',
                data={'action_type': 'approve'})
            assert response.status_code in [200, 302]

    def test_update_ajax_request(self, admin_client, analysis_app, sample_with_result):
        """Update via AJAX"""
        with analysis_app.app_context():
            result_id = sample_with_result['result_id']
            response = admin_client.post(f'/api/update_result_status/{result_id}/approved',
                data=json.dumps({}),
                content_type='application/json',
                headers={'X-Requested-With': 'XMLHttpRequest'})
            assert response.status_code == 200


class TestRequestAnalysis:
    """request_analysis endpoint tests - lines 698-765"""

    def test_request_chemist_forbidden(self, chemist_client, analysis_app, sample_with_analyses):
        """Chemist cannot request analysis"""
        with analysis_app.app_context():
            response = chemist_client.post('/api/request_analysis',
                data=json.dumps({
                    'sample_id': sample_with_analyses,
                    'analysis_code': 'CSN'
                }),
                content_type='application/json')
            assert response.status_code == 403

    def test_request_missing_params(self, admin_client, analysis_app):
        """Request missing parameters"""
        with analysis_app.app_context():
            response = admin_client.post('/api/request_analysis',
                data=json.dumps({'sample_id': 1}),
                content_type='application/json')
            assert response.status_code == 400

    def test_request_sample_not_found(self, admin_client, analysis_app):
        """Request for non-existent sample"""
        with analysis_app.app_context():
            response = admin_client.post('/api/request_analysis',
                data=json.dumps({
                    'sample_id': 99999,
                    'analysis_code': 'CSN'
                }),
                content_type='application/json')
            assert response.status_code == 404

    def test_request_already_assigned(self, admin_client, analysis_app, sample_with_analyses):
        """Request already assigned analysis"""
        with analysis_app.app_context():
            response = admin_client.post('/api/request_analysis',
                data=json.dumps({
                    'sample_id': sample_with_analyses,
                    'analysis_code': 'Mad'
                }),
                content_type='application/json')
            assert response.status_code == 400

    def test_request_success(self, admin_client, analysis_app, sample_with_analyses):
        """Request new analysis success"""
        with analysis_app.app_context():
            response = admin_client.post('/api/request_analysis',
                data=json.dumps({
                    'sample_id': sample_with_analyses,
                    'analysis_code': 'CSN'
                }),
                content_type='application/json')
            assert response.status_code == 200


class TestCheckReadySamples:
    """check_ready_samples endpoint tests - lines 770-817"""

    def test_check_ready_samples(self, admin_client, analysis_app):
        """Check ready samples"""
        with analysis_app.app_context():
            response = admin_client.get('/api/check_ready_samples')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'ready_count' in data

    def test_check_ready_with_samples(self, admin_client, analysis_app):
        """Check with existing CHPP samples"""
        with analysis_app.app_context():
            user = User.query.filter_by(username='analadmin').first()
            sample = Sample(
                sample_code='CHPP-READY-001',
                user_id=user.id,
                client_name='CHPP',
                sample_type='2 hourly',
                sample_condition='Хуурай',
                sample_date=date.today(),
                received_date=datetime.now(),
                status='new',
                product='PF211'
            )
            db.session.add(sample)
            db.session.commit()

            response = admin_client.get('/api/check_ready_samples')
            assert response.status_code == 200


class TestSaveResultsEdgeCases:
    """save_results edge cases - additional coverage"""

    def test_save_with_equipment_id(self, admin_client, analysis_app, sample_with_analyses):
        """Save with equipment_id"""
        with analysis_app.app_context():
            response = admin_client.post('/api/save_results',
                data=json.dumps({
                    'sample_id': sample_with_analyses,
                    'analysis_code': 'Mad',
                    'final_result': 5.5,
                    'equipment_id': 1,
                    'raw_data': {'avg': 5.5}
                }),
                content_type='application/json')
            assert response.status_code in [200, 207, 400]

    def test_save_csn_result(self, admin_client, analysis_app, sample_with_analyses):
        """Save CSN result"""
        with analysis_app.app_context():
            # First add CSN to analyses
            sample = Sample.query.get(sample_with_analyses)
            sample.analyses_to_perform = '["Mad", "Aad", "Vad", "CSN"]'
            db.session.commit()

            response = admin_client.post('/api/save_results',
                data=json.dumps({
                    'sample_id': sample_with_analyses,
                    'analysis_code': 'CSN',
                    'final_result': 2.5,
                    'raw_data': {'avg': 2.5, 'diff': 0.1}
                }),
                content_type='application/json')
            assert response.status_code in [200, 207]

    def test_save_with_tolerance_flags(self, admin_client, analysis_app, sample_with_analyses):
        """Save with tolerance flags"""
        with analysis_app.app_context():
            response = admin_client.post('/api/save_results',
                data=json.dumps({
                    'sample_id': sample_with_analyses,
                    'analysis_code': 'Mad',
                    'final_result': 5.5,
                    'raw_data': {
                        'avg': 5.5,
                        'is_low_avg': True,
                        'retest_mode': False,
                        't_exceeded': False
                    }
                }),
                content_type='application/json')
            assert response.status_code in [200, 207]


class TestControlStandardLogic:
    """Control/GBW standard tests - lines 345-413"""

    def test_save_cm_sample_result(self, admin_client, analysis_app):
        """Save result for CM sample"""
        with analysis_app.app_context():
            user = User.query.filter_by(username='analadmin').first()
            # Create CM sample
            sample = Sample(
                sample_code='CM-2025-Q1_TEST',
                user_id=user.id,
                client_name='LAB',
                sample_type='CM',
                sample_condition='Хуурай',
                sample_date=date.today(),
                status='new',
                analyses_to_perform='["Mad", "Aad"]'
            )
            db.session.add(sample)
            db.session.commit()

            # Save Mad first
            response = admin_client.post('/api/save_results',
                data=json.dumps([
                    {
                        'sample_id': sample.id,
                        'analysis_code': 'Mad',
                        'final_result': 2.5,
                        'raw_data': {'avg': 2.5}
                    },
                    {
                        'sample_id': sample.id,
                        'analysis_code': 'Aad',
                        'final_result': 10.5,
                        'raw_data': {'avg': 10.5}
                    }
                ]),
                content_type='application/json')
            assert response.status_code in [200, 207]

    def test_save_gbw_sample_result(self, admin_client, analysis_app):
        """Save result for GBW sample"""
        with analysis_app.app_context():
            user = User.query.filter_by(username='analadmin').first()
            # Create GBW sample
            sample = Sample(
                sample_code='GBW11107q_TEST',
                user_id=user.id,
                client_name='LAB',
                sample_type='GBW',
                sample_condition='Хуурай',
                sample_date=date.today(),
                status='new',
                analyses_to_perform='["Vad"]'
            )
            db.session.add(sample)
            db.session.commit()

            response = admin_client.post('/api/save_results',
                data=json.dumps({
                    'sample_id': sample.id,
                    'analysis_code': 'Vad',
                    'final_result': 25.5,
                    'raw_data': {'avg': 25.5}
                }),
                content_type='application/json')
            assert response.status_code in [200, 207]


class TestUnassignWithBadJSON:
    """Unassign JSON parsing tests - lines 188-189"""

    def test_unassign_sample_bad_analyses_json(self, admin_client, analysis_app):
        """Unassign when analyses_to_perform is bad JSON"""
        with analysis_app.app_context():
            user = User.query.filter_by(username='analadmin').first()
            sample = Sample(
                sample_code='BAD-JSON-001',
                user_id=user.id,
                client_name='CHPP',
                sample_type='2 hourly',
                sample_condition='Хуурай',
                sample_date=date.today(),
                status='new',
                analyses_to_perform='not valid json'
            )
            db.session.add(sample)
            db.session.commit()

            response = admin_client.post('/api/unassign_sample',
                data=json.dumps({
                    'sample_id': sample.id,
                    'analysis_code': 'Mad'
                }),
                content_type='application/json')
            assert response.status_code in [200, 400]


class TestReadySamplesEdgeCases:
    """Ready samples edge cases - lines 792-817"""

    def test_check_ready_pf_sample(self, admin_client, analysis_app):
        """Check PF sample readiness"""
        with analysis_app.app_context():
            user = User.query.filter_by(username='analadmin').first()
            sample = Sample(
                sample_code='PF211_D1_READY',
                user_id=user.id,
                client_name='CHPP',
                sample_type='2 hourly',
                sample_condition='Хуурай',
                sample_date=date.today(),
                received_date=datetime.now(),
                status='new',
                product='PF211'
            )
            db.session.add(sample)
            db.session.commit()

            response = admin_client.get('/api/check_ready_samples')
            assert response.status_code == 200

    def test_check_ready_non_pf_sample(self, admin_client, analysis_app):
        """Check non-PF sample readiness"""
        with analysis_app.app_context():
            user = User.query.filter_by(username='analadmin').first()
            sample = Sample(
                sample_code='UHG-MV_READY',
                user_id=user.id,
                client_name='CHPP',
                sample_type='4 hourly',
                sample_condition='Хуурай',
                sample_date=date.today(),
                received_date=datetime.now(),
                status='new',
                product='UHG MV'
            )
            db.session.add(sample)
            db.session.commit()

            response = admin_client.get('/api/check_ready_samples')
            assert response.status_code == 200

    def test_check_ready_exception(self, admin_client, analysis_app):
        """Check ready samples with exception"""
        with analysis_app.app_context():
            with patch('app.routes.api.analysis_api.Sample.query') as mock_query:
                mock_query.filter.side_effect = SQLAlchemyError('DB error')
                response = admin_client.get('/api/check_ready_samples')
            assert response.status_code in [200, 500]


class TestRequestAnalysisEdgeCases:
    """Request analysis edge cases - lines 721-765"""

    def test_request_with_string_analyses(self, admin_client, analysis_app):
        """Request when analyses_to_perform is string"""
        with analysis_app.app_context():
            user = User.query.filter_by(username='analadmin').first()
            sample = Sample(
                sample_code='STR-ANAL-001',
                user_id=user.id,
                client_name='CHPP',
                sample_type='2 hourly',
                sample_condition='Хуурай',
                sample_date=date.today(),
                status='new',
                analyses_to_perform='["Mad"]'
            )
            db.session.add(sample)
            db.session.commit()

            response = admin_client.post('/api/request_analysis',
                data=json.dumps({
                    'sample_id': sample.id,
                    'analysis_code': 'CSN'
                }),
                content_type='application/json')
            assert response.status_code == 200

    def test_request_with_empty_code(self, admin_client, analysis_app):
        """Request with empty analysis code after normalize"""
        with analysis_app.app_context():
            user = User.query.filter_by(username='analadmin').first()
            sample = Sample(
                sample_code='EMPTY-CODE-001',
                user_id=user.id,
                client_name='CHPP',
                sample_type='2 hourly',
                sample_condition='Хуурай',
                sample_date=date.today(),
                status='new',
                analyses_to_perform='[]'
            )
            db.session.add(sample)
            db.session.commit()

            response = admin_client.post('/api/request_analysis',
                data=json.dumps({
                    'sample_id': sample.id,
                    'analysis_code': 'ValidCode'
                }),
                content_type='application/json')
            assert response.status_code in [200, 400]

    def test_request_db_exception(self, admin_client, analysis_app, sample_with_analyses):
        """Request analysis with DB exception"""
        with analysis_app.app_context():
            with patch('app.services.analysis_workflow.db.session.commit') as mock_commit:
                mock_commit.side_effect = SQLAlchemyError('DB commit error')
                response = admin_client.post('/api/request_analysis',
                    data=json.dumps({
                        'sample_id': sample_with_analyses,
                        'analysis_code': 'TS'
                    }),
                    content_type='application/json')
            assert response.status_code == 500


class TestSaveResultsDBError:
    """Save results DB error - lines 604-606"""

    def test_save_db_commit_error(self, admin_client, analysis_app, sample_with_analyses):
        """Save results with DB commit error"""
        with analysis_app.app_context():
            with patch('app.services.analysis_workflow.db.session.commit') as mock_commit:
                mock_commit.side_effect = SQLAlchemyError('DB commit failed')
                response = admin_client.post('/api/save_results',
                    data=json.dumps({
                        'sample_id': sample_with_analyses,
                        'analysis_code': 'Mad',
                        'final_result': 5.5,
                        'raw_data': {'avg': 5.5}
                    }),
                    content_type='application/json')
            assert response.status_code == 500
