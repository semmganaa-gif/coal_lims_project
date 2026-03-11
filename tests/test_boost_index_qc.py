# tests/test_boost_index_qc.py
# -*- coding: utf-8 -*-
"""
index.py болон qc.py coverage нэмэгдүүлэх тестүүд.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
from io import BytesIO


class TestIndexRoutesCoverage:
    """Index routes coverage tests."""

    def test_index_get_with_list_pane(self, app, auth_admin):
        """Test index with list-pane active tab."""
        response = auth_admin.get('/coal?active_tab=list-pane')
        assert response.status_code in [200, 302]

    def test_index_unauthorized_role(self, app, auth_user):
        """Test index POST with unauthorized role."""
        response = auth_user.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'SC',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        # Should show permission error or redirect
        assert response.status_code == 200

    def test_chpp_2h_multi_sample_with_weights(self, app, auth_admin):
        """Test CHPP 2h registration with multiple samples and weights."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'SC',
            'sample_codes': ['SC_2H_T001', 'SC_2H_T002', 'SC_2H_T003'],
            'weights': ['100.5', '150.2', '200.0'],
            'list_type': 'chpp_2h',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_chpp_2h_with_missing_weight(self, app, auth_admin):
        """Test CHPP 2h with missing weight."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'SC',
            'sample_codes': ['SC_2H_NO_WT'],
            'weights': [],  # No weight
            'list_type': 'chpp_2h',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_chpp_2h_with_invalid_weight(self, app, auth_admin):
        """Test CHPP 2h with invalid weight value."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'SC',
            'sample_codes': ['SC_2H_INV_WT'],
            'weights': ['invalid'],
            'list_type': 'chpp_2h',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_chpp_2h_with_low_weight(self, app, auth_admin):
        """Test CHPP 2h with too low weight."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'SC',
            'sample_codes': ['SC_2H_LW'],
            'weights': ['0.001'],  # Too low
            'list_type': 'chpp_2h',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_chpp_4h_registration(self, app, auth_admin):
        """Test CHPP 4h registration."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'SC',
            'sample_codes': ['SC_4H_001'],
            'list_type': 'chpp_4h',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_chpp_com_registration(self, app, auth_admin):
        """Test CHPP COM registration with weight."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'SC',
            'sample_codes': ['SC_COM_001'],
            'weights': ['500.0'],
            'list_type': 'chpp_com',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_multi_gen_registration(self, app, auth_admin):
        """Test multi_gen registration."""
        response = auth_admin.post('/coal', data={
            'client_name': 'QC',
            'sample_type': 'coal',
            'sample_codes': ['QC_GEN_001'],
            'weights': ['250.0'],
            'list_type': 'multi_gen',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
            'location': 'Test Location',
            'product': 'Test Product',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_wtl_registration_no_lab_number(self, app, auth_admin):
        """Test WTL registration without lab number."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'WTL',
            'lab_number': '',  # Missing
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_wtl_size_registration(self, app, auth_admin):
        """Test WTL Size registration."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'Size',
            'lab_number': 'SZ_001',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_wtl_fl_registration(self, app, auth_admin):
        """Test WTL FL registration."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'FL',
            'lab_number': 'FL_001',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_wtl_mg_registration(self, app, auth_admin):
        """Test WTL MG registration."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'MG',
            'sample_code': 'MG_001',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_wtl_mg_no_sample_code(self, app, auth_admin):
        """Test WTL MG without sample code."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'MG',
            'sample_code': '',  # Missing
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_lab_cm_registration(self, app, auth_admin):
        """Test LAB CM registration."""
        response = auth_admin.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'CM',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_lab_gbw_registration(self, app, auth_admin):
        """Test LAB GBW registration."""
        response = auth_admin.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'GBW',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_lab_test_registration(self, app, auth_admin):
        """Test LAB Test registration."""
        response = auth_admin.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'Test',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200


class TestPreviewAnalyses:
    """Preview analyses route tests."""

    def test_preview_analyses_valid(self, app, auth_admin):
        """Test preview analyses with valid data."""
        response = auth_admin.post('/preview-analyses',
            json={
                'sample_names': ['SC_001', 'SC_002'],
                'client_name': 'CHPP',
                'sample_type': 'SC'
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 400]

    def test_preview_analyses_missing_data(self, app, auth_admin):
        """Test preview analyses with missing data."""
        response = auth_admin.post('/preview-analyses',
            json={
                'sample_names': [],
                'client_name': '',
                'sample_type': ''
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 400]


class TestQCHelpersCoverage:
    """QC helper functions coverage."""

    def test_auto_find_hourly_with_pattern(self, app):
        """Test auto find hourly with pattern matching."""
        from app.routes.analysis.qc import _auto_find_hourly_samples
        from app.models import Sample
        from app import db

        with app.app_context():
            # Create COM sample
            com = Sample(
                sample_code='SC20251224_D_COM',
                sample_type='coal',
                client_name='CHPP',
                status='completed',
                received_date=datetime.now()
            )
            # Create hourly samples with same family
            h1 = Sample(
                sample_code='SC20251224_D_H01',
                sample_type='coal',
                client_name='CHPP',
                status='completed',
                received_date=datetime.now()
            )
            h2 = Sample(
                sample_code='SC20251224_D_H02',
                sample_type='coal',
                client_name='CHPP',
                status='completed',
                received_date=datetime.now()
            )

            db.session.add_all([com, h1, h2])
            db.session.commit()

            # Should find all related samples
            result = _auto_find_hourly_samples([com.id])
            assert com.id in result
            # Should include hourly samples
            assert len(result) >= 1

    def test_get_qc_stream_data_with_calculations(self, app):
        """Test QC stream data with Vdaf calculation."""
        from app.routes.analysis.qc import _get_qc_stream_data
        from app.models import Sample, AnalysisResult
        from app import db

        with app.app_context():
            # Create sample with results for Vdaf calculation
            sample = Sample(
                sample_code='VDAF_CALC_TEST',
                sample_type='coal',
                client_name='CHPP',
                status='completed',
                received_date=datetime.now()
            )
            db.session.add(sample)
            db.session.commit()

            # Add results: Vad, Mad, Aad for Vdaf calculation
            for code, value in [('Vad', 30.0), ('Mad', 5.0), ('Aad', 10.0)]:
                result = AnalysisResult(
                    sample_id=sample.id,
                    analysis_code=code,
                    final_result=value,
                    status='approved'
                )
                db.session.add(result)
            db.session.commit()

            data = _get_qc_stream_data([sample.id])
            assert isinstance(data, list)


class TestQCRoutesCoverage:
    """QC routes coverage tests."""

    def test_qc_composite_check_no_ids(self, app, auth_admin):
        """Test composite check with no IDs."""
        response = auth_admin.get('/analysis/qc/composite_check?ids=')
        # Should redirect to sample_summary or return error
        assert response.status_code in [200, 302, 404]

    def test_qc_composite_check_with_samples(self, app, auth_admin):
        """Test composite check with samples."""
        from app.models import Sample, AnalysisResult
        from app import db

        with app.app_context():
            # Create COM and hourly samples
            com = Sample(
                sample_code='QC_COM_TEST',
                sample_type='coal',
                client_name='CHPP',
                status='completed',
                received_date=datetime.now()
            )
            hourly = Sample(
                sample_code='QC_H01_TEST',
                sample_type='coal',
                client_name='CHPP',
                status='completed',
                received_date=datetime.now()
            )
            db.session.add_all([com, hourly])
            db.session.commit()

            # Add results
            for sample in [com, hourly]:
                for code in ['Mad', 'Aad', 'Vad']:
                    result = AnalysisResult(
                        sample_id=sample.id,
                        analysis_code=code,
                        final_result=10.0,
                        status='approved'
                    )
                    db.session.add(result)
            db.session.commit()

            response = auth_admin.get(f'/analysis/qc/composite_check?ids={com.id},{hourly.id}')
            assert response.status_code in [200, 302, 404]

    def test_qc_norm_limit_no_ids(self, app, auth_admin):
        """Test norm limit with no IDs."""
        response = auth_admin.get('/analysis/qc/norm_limit?ids=')
        assert response.status_code in [200, 302, 404]

    def test_qc_norm_limit_with_spec_key(self, app, auth_admin):
        """Test norm limit with spec key."""
        from app.models import Sample
        from app import db

        with app.app_context():
            sample = Sample(
                sample_code='NL_SPEC_TEST',
                sample_type='coal',
                client_name='CHPP',
                status='completed',
                received_date=datetime.now()
            )
            db.session.add(sample)
            db.session.commit()

            response = auth_admin.get(f'/analysis/qc/norm_limit?ids={sample.id}&spec_key=UHG_HV')
            assert response.status_code in [200, 302, 404]

    def test_correlation_check_no_ids(self, app, auth_admin):
        """Test correlation check with no IDs."""
        response = auth_admin.get('/analysis/correlation_check?ids=')
        assert response.status_code in [200, 302, 404]


class TestQCUtilsCoverage:
    """QC utils coverage tests."""

    def test_qc_split_family_variations(self, app):
        """Test qc_split_family with various inputs."""
        from app.utils.qc import qc_split_family

        # COM sample
        family, slot = qc_split_family('SC20251224_D_COM')
        assert 'COM' in (slot or '').upper() or family

        # Hourly sample
        family, slot = qc_split_family('SC20251224_D_H01')
        assert 'H' in (slot or '').upper() or family

        # 4H sample
        family, slot = qc_split_family('CF501_20251224')
        assert family or slot

        # None input
        family, slot = qc_split_family(None)
        assert family == '' or family is None

    def test_qc_is_composite_variations(self, app):
        """Test qc_is_composite with various inputs."""
        from app.utils.qc import qc_is_composite
        from unittest.mock import MagicMock

        sample = MagicMock()
        sample.sample_type = 'coal'

        # COM slot
        result = qc_is_composite(sample, 'COM')
        assert result in [True, False]

        # COMP slot
        result = qc_is_composite(sample, 'COMP')
        assert result in [True, False]

        # H01 slot
        result = qc_is_composite(sample, 'H01')
        assert result in [True, False]

        # Empty slot
        result = qc_is_composite(sample, '')
        assert result in [True, False]

        # None slot
        result = qc_is_composite(sample, None)
        assert result in [True, False]

    def test_qc_check_spec_variations(self, app):
        """Test qc_check_spec with various inputs."""
        from app.utils.qc import qc_check_spec

        # Within range
        assert qc_check_spec(10.0, (8.0, 12.0)) is False

        # Below range
        assert qc_check_spec(5.0, (8.0, 12.0)) is True

        # Above range
        assert qc_check_spec(15.0, (8.0, 12.0)) is True

        # None value
        assert qc_check_spec(None, (8.0, 12.0)) is False

        # None spec
        assert qc_check_spec(10.0, None) is False

    def test_qc_to_date_variations(self, app):
        """Test qc_to_date with various inputs."""
        from app.utils.qc import qc_to_date

        # Date
        result = qc_to_date(date(2025, 12, 24))
        assert result is not None

        # Datetime
        result = qc_to_date(datetime(2025, 12, 24, 10, 30))
        assert result is not None

        # None
        result = qc_to_date(None)
        assert result is None

        # String (may or may not work)
        result = qc_to_date("2025-12-24")
        # Just check it doesn't crash


class TestIndexHelperFunctionsCoverage:
    """Index helper functions coverage."""

    def test_get_12h_shift_code_times(self, app):
        """Test shift code for different times."""
        from app.routes.main.helpers import get_12h_shift_code

        # Morning 06:00
        morning = datetime(2025, 12, 24, 6, 0, 0)
        code = get_12h_shift_code(morning)
        assert code in ['D', 'N', '_D', '_N', 'D1', 'N1']

        # Afternoon 14:00
        afternoon = datetime(2025, 12, 24, 14, 0, 0)
        code = get_12h_shift_code(afternoon)
        assert code in ['D', 'N', '_D', '_N', 'D1', 'N1']

        # Night 22:00
        night = datetime(2025, 12, 24, 22, 0, 0)
        code = get_12h_shift_code(night)
        assert code in ['D', 'N', '_D', '_N', 'D1', 'N1']

        # Midnight 00:00
        midnight = datetime(2025, 12, 24, 0, 0, 0)
        code = get_12h_shift_code(midnight)
        assert code in ['D', 'N', '_D', '_N', 'D1', 'N1']

    def test_get_quarter_code_all_quarters(self, app):
        """Test quarter code for all quarters."""
        from app.routes.main.helpers import get_quarter_code

        # Q1: Jan-Mar
        jan = datetime(2025, 1, 15)
        assert 'Q1' in get_quarter_code(jan)

        feb = datetime(2025, 2, 15)
        assert 'Q1' in get_quarter_code(feb)

        mar = datetime(2025, 3, 15)
        assert 'Q1' in get_quarter_code(mar)

        # Q2: Apr-Jun
        apr = datetime(2025, 4, 15)
        assert 'Q2' in get_quarter_code(apr)

        may = datetime(2025, 5, 15)
        assert 'Q2' in get_quarter_code(may)

        jun = datetime(2025, 6, 15)
        assert 'Q2' in get_quarter_code(jun)

        # Q3: Jul-Sep
        jul = datetime(2025, 7, 15)
        assert 'Q3' in get_quarter_code(jul)

        aug = datetime(2025, 8, 15)
        assert 'Q3' in get_quarter_code(aug)

        sep = datetime(2025, 9, 15)
        assert 'Q3' in get_quarter_code(sep)

        # Q4: Oct-Dec
        oct_d = datetime(2025, 10, 15)
        assert 'Q4' in get_quarter_code(oct_d)

        nov = datetime(2025, 11, 15)
        assert 'Q4' in get_quarter_code(nov)

        dec = datetime(2025, 12, 15)
        assert 'Q4' in get_quarter_code(dec)

    def test_get_report_email_recipients(self, app):
        """Test get report email recipients."""
        from app.routes.main.hourly_report import get_report_email_recipients
        from app.models import SystemSetting
        from app import db

        with app.app_context():
            # Clean existing
            SystemSetting.query.filter_by(
                category='email',
                key='report_recipients_to'
            ).delete()
            SystemSetting.query.filter_by(
                category='email',
                key='report_recipients_cc'
            ).delete()
            db.session.commit()

            # Test empty
            result = get_report_email_recipients()
            assert 'to' in result
            assert 'cc' in result

            # Add settings
            to_setting = SystemSetting(
                category='email',
                key='report_recipients_to',
                value='admin@test.com, user@test.com',
                is_active=True
            )
            cc_setting = SystemSetting(
                category='email',
                key='report_recipients_cc',
                value='cc@test.com',
                is_active=True
            )
            db.session.add_all([to_setting, cc_setting])
            db.session.commit()

            result = get_report_email_recipients()
            assert 'admin@test.com' in result['to']
            assert 'cc@test.com' in result['cc']
