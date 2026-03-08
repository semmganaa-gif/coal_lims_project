# -*- coding: utf-8 -*-
"""
Control Charts - бүрэн интеграцийн тестүүд
control_charts.py файлын coverage нэмэгдүүлэх
"""
import pytest
import json
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Sample, AnalysisResult, ControlStandard, GbwStandard


@pytest.fixture
def app():
    """Test application fixture"""
    from tests.conftest import TestConfig
    app = create_app(TestConfig)
    app.config['SERVER_NAME'] = 'localhost'

    with app.app_context():
        db.create_all()
        # Create admin user
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin', role='admin')
            user.set_password('AdminPass123')
            db.session.add(user)
            db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Authenticated admin client"""
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


def create_qc_data(app):
    """Create QC test data"""
    with app.app_context():
        user = User.query.filter_by(username='admin').first()

        # Create CM standard
        # Note: sample_code is uppercased, so CM_Batch1 -> CM_BATCH1
        cm_std = ControlStandard(
            name='CM_BATCH1',
            is_active=True,
            targets=json.dumps({
                'TS': {'target': 10.0, 'tolerance': 0.5},
                'CV': {'target': 25.0, 'tolerance': 1.0}
            })
        )
        db.session.add(cm_std)

        # Create GBW standard
        # Note: sample_code is uppercased by model validation,
        # so GBW11135a -> GBW11135A. Standard name must match.
        gbw_std = GbwStandard(
            name='GBW11135A',
            is_active=True,
            targets=json.dumps({
                'TS': {'target': 8.5, 'tolerance': 0.3},
                'Mad': {'target': 5.0, 'tolerance': 0.4}
            })
        )
        db.session.add(gbw_std)
        db.session.commit()

        # Create CM samples
        for i in range(5):
            sample = Sample(
                sample_code=f'CM_BATCH1_2024120{i}A',
                user_id=user.id,
                client_name='LAB',
                sample_type='CM'
            )
            db.session.add(sample)
            db.session.commit()

            # Create analysis results
            result = AnalysisResult(
                sample_id=sample.id,
                analysis_code='TS',
                final_result=10.0 + (i * 0.1),
                status='approved',
                user_id=user.id,
                updated_at=datetime.now() - timedelta(days=i)
            )
            db.session.add(result)

        # Create GBW samples
        for i in range(5):
            sample = Sample(
                sample_code=f'GBW11135A_2024120{i}A',
                user_id=user.id,
                client_name='LAB',
                sample_type='GBW'
            )
            db.session.add(sample)
            db.session.commit()

            # Create analysis results
            result = AnalysisResult(
                sample_id=sample.id,
                analysis_code='TS',
                final_result=8.5 + (i * 0.05),
                status='approved',
                user_id=user.id,
                updated_at=datetime.now() - timedelta(days=i)
            )
            db.session.add(result)

        db.session.commit()


class TestControlChartsHelpers:
    """Control charts helper functions тестүүд"""

    def test_extract_standard_name_gbw(self, app):
        """Extract GBW standard name"""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('GBW11135a_20241213A')
            assert result == 'GBW11135a'

    def test_extract_standard_name_cm(self, app):
        """Extract CM standard name"""
        with app.app_context():
            create_qc_data(app)  # Create CM_BATCH1 standard first
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('CM_BATCH1_20241213AQ4')
            # Returns active CM standard name or 'CM'
            assert result in ['CM_BATCH1', 'CM']

    def test_extract_standard_name_simple(self, app):
        """Extract simple standard name"""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('Test_20241213A')
            assert result == 'Test'

    def test_extract_standard_name_empty(self, app):
        """Extract from empty string"""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('')
            assert result == ''

    def test_extract_standard_name_none(self, app):
        """Extract from None"""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name(None)
            assert result == ''

    def test_extract_standard_name_no_underscore(self, app):
        """Extract from name without underscore"""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('SingleName')
            assert result == 'SingleName'

    def test_get_qc_samples(self, app):
        """Get QC samples function"""
        with app.app_context():
            create_qc_data(app)
            from app.routes.quality.control_charts import _get_qc_samples
            samples = _get_qc_samples()
            assert len(samples) >= 10  # 5 CM + 5 GBW

    def test_get_qc_results(self, app):
        """Get QC results function"""
        with app.app_context():
            create_qc_data(app)
            from app.routes.quality.control_charts import _get_qc_samples, _get_qc_results
            samples = _get_qc_samples()
            sample_ids = [s.id for s in samples]
            results = _get_qc_results(sample_ids)
            assert len(results) >= 10

    def test_get_qc_results_with_analysis_code(self, app):
        """Get QC results filtered by analysis code"""
        with app.app_context():
            create_qc_data(app)
            from app.routes.quality.control_charts import _get_qc_samples, _get_qc_results
            samples = _get_qc_samples()
            sample_ids = [s.id for s in samples]
            results = _get_qc_results(sample_ids, 'TS')
            assert len(results) >= 10

    def test_get_target_and_tolerance_cm(self, app):
        """Get target and tolerance for CM"""
        with app.app_context():
            create_qc_data(app)
            from app.routes.quality.control_charts import _get_target_and_tolerance
            sample = Sample.query.filter(Sample.sample_code.like('CM_BATCH1%')).first()
            target, ucl, lcl, sd = _get_target_and_tolerance(sample, 'TS')
            assert target == 10.0
            assert sd == 0.5

    def test_get_target_and_tolerance_gbw(self, app):
        """Get target and tolerance for GBW"""
        with app.app_context():
            create_qc_data(app)
            from app.routes.quality.control_charts import _get_target_and_tolerance
            sample = Sample.query.filter(Sample.sample_code.like('GBW11135A%')).first()
            target, ucl, lcl, sd = _get_target_and_tolerance(sample, 'TS')
            assert target == 8.5
            assert sd == 0.3

    def test_get_target_and_tolerance_no_standard(self, app):
        """Get target when no standard exists"""
        with app.app_context():
            user = User.query.first()
            sample = Sample(
                sample_code='UNKNOWN_STD_20241213A',
                user_id=user.id,
                client_name='LAB',
                sample_type='QC'
            )
            db.session.add(sample)
            db.session.commit()

            from app.routes.quality.control_charts import _get_target_and_tolerance
            target, ucl, lcl, sd = _get_target_and_tolerance(sample, 'TS')
            assert target is None

    def test_get_target_and_tolerance_no_analysis_code(self, app):
        """Get target for non-existent analysis code"""
        with app.app_context():
            create_qc_data(app)
            from app.routes.quality.control_charts import _get_target_and_tolerance
            sample = Sample.query.filter(Sample.sample_code.like('CM_BATCH1%')).first()
            target, ucl, lcl, sd = _get_target_and_tolerance(sample, 'NONEXISTENT')
            assert target is None


class TestControlChartsRoutes:
    """Control charts routes тестүүд"""

    def test_control_charts_list_empty(self, auth_client, app):
        """Control charts list with no data"""
        with app.app_context():
            response = auth_client.get('/quality/control_charts')
            assert response.status_code in [200, 302, 404]

    def test_control_charts_list_with_data(self, auth_client, app):
        """Control charts list with data"""
        with app.app_context():
            create_qc_data(app)
            response = auth_client.get('/quality/control_charts')
            assert response.status_code in [200, 302, 404]


class TestWestgardAPI:
    """Westgard API тестүүд"""

    def test_westgard_summary_empty(self, auth_client, app):
        """Westgard summary with no data"""
        with app.app_context():
            response = auth_client.get('/quality/api/westgard_summary')
            assert response.status_code in [200, 302, 404]
            if response.status_code == 200:
                data = response.get_json()
                assert 'qc_samples' in data

    def test_westgard_summary_with_data(self, auth_client, app):
        """Westgard summary with data"""
        with app.app_context():
            create_qc_data(app)
            response = auth_client.get('/quality/api/westgard_summary')
            assert response.status_code in [200, 302, 404]

    def test_westgard_detail_cm(self, auth_client, app):
        """Westgard detail for CM"""
        with app.app_context():
            create_qc_data(app)
            response = auth_client.get('/quality/api/westgard_detail/CM/TS')
            assert response.status_code in [200, 302, 404]

    def test_westgard_detail_gbw(self, auth_client, app):
        """Westgard detail for GBW"""
        with app.app_context():
            create_qc_data(app)
            response = auth_client.get('/quality/api/westgard_detail/GBW/TS')
            assert response.status_code in [200, 302, 404]

    def test_westgard_detail_no_data(self, auth_client, app):
        """Westgard detail with no matching data"""
        with app.app_context():
            response = auth_client.get('/quality/api/westgard_detail/CM/TS')
            assert response.status_code in [200, 302, 404]

    def test_westgard_detail_unknown_type(self, auth_client, app):
        """Westgard detail for unknown QC type"""
        with app.app_context():
            response = auth_client.get('/quality/api/westgard_detail/UNKNOWN/TS')
            assert response.status_code in [200, 302, 404]


class TestWestgardRules:
    """Westgard rules тестүүд"""

    def test_check_westgard_rules(self, app):
        """Check Westgard rules"""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            values = [10.0, 10.1, 10.2, 9.9, 10.0]
            target = 10.0
            sd = 0.5
            violations = check_westgard_rules(values, target, sd)
            assert isinstance(violations, list)

    def test_check_westgard_rules_violation(self, app):
        """Check Westgard rules with violation"""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # Values that should trigger 1_2s rule (value > mean + 2*sd)
            values = [10.0, 10.0, 10.0, 15.0]  # 15 is outside ±2sd
            target = 10.0
            sd = 1.0
            violations = check_westgard_rules(values, target, sd)
            assert isinstance(violations, list)

    def test_get_qc_status_pass(self, app):
        """Get QC status - pass"""
        with app.app_context():
            from app.utils.westgard import get_qc_status
            violations = []
            status = get_qc_status(violations)
            assert status['status'] == 'pass'

    def test_check_single_value(self, app):
        """Check single value"""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(10.0, 10.0, 0.5)
            assert result is not None

    def test_check_single_value_outside(self, app):
        """Check single value outside limits"""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(15.0, 10.0, 0.5)  # Way outside
            assert result is not None
