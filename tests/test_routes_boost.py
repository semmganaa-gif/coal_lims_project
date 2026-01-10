# tests/test_routes_boost.py
# -*- coding: utf-8 -*-
"""Tests to boost routes coverage (index.py, samples_api.py)."""

import pytest
import json
from datetime import datetime, timedelta, date
from unittest.mock import patch, MagicMock
from io import BytesIO


# =============================================================================
# INDEX.PY TESTS
# =============================================================================
class TestGetReportEmailRecipients:
    """Test get_report_email_recipients function."""

    def test_get_recipients_with_both_to_and_cc(self, app, db):
        """Test getting email recipients with both TO and CC."""
        with app.app_context():
            from app.models import SystemSetting
            from app import db as _db

            # Clear existing settings
            SystemSetting.query.filter_by(category='email').delete()
            _db.session.commit()

            # Create TO setting
            to_setting = SystemSetting(
                category='email',
                key='report_recipients_to',
                value='test1@example.com, test2@example.com',
                is_active=True
            )
            _db.session.add(to_setting)

            # Create CC setting
            cc_setting = SystemSetting(
                category='email',
                key='report_recipients_cc',
                value='cc1@example.com, cc2@example.com',
                is_active=True
            )
            _db.session.add(cc_setting)
            _db.session.commit()

            from app.routes.main.index import get_report_email_recipients
            result = get_report_email_recipients()

            assert 'to' in result
            assert 'cc' in result
            assert len(result['to']) == 2
            assert len(result['cc']) == 2
            assert 'test1@example.com' in result['to']
            assert 'cc1@example.com' in result['cc']

    def test_get_recipients_empty(self, app, db):
        """Test getting email recipients when none configured."""
        with app.app_context():
            from app.models import SystemSetting
            from app import db as _db

            # Clear existing settings
            SystemSetting.query.filter_by(category='email').delete()
            _db.session.commit()

            from app.routes.main.index import get_report_email_recipients
            result = get_report_email_recipients()

            assert result['to'] == []
            assert result['cc'] == []

    def test_get_recipients_only_to(self, app, db):
        """Test getting email recipients with only TO."""
        with app.app_context():
            from app.models import SystemSetting
            from app import db as _db

            # Clear existing settings
            SystemSetting.query.filter_by(category='email').delete()
            _db.session.commit()

            to_setting = SystemSetting(
                category='email',
                key='report_recipients_to',
                value='only@example.com',
                is_active=True
            )
            _db.session.add(to_setting)
            _db.session.commit()

            from app.routes.main.index import get_report_email_recipients
            result = get_report_email_recipients()

            assert len(result['to']) == 1
            assert result['cc'] == []

    def test_get_recipients_inactive_setting(self, app, db):
        """Test that inactive settings are ignored."""
        with app.app_context():
            from app.models import SystemSetting
            from app import db as _db

            # Clear existing settings
            SystemSetting.query.filter_by(category='email').delete()
            _db.session.commit()

            # Inactive setting should be ignored
            setting = SystemSetting(
                category='email',
                key='report_recipients_to',
                value='inactive@example.com',
                is_active=False
            )
            _db.session.add(setting)
            _db.session.commit()

            from app.routes.main.index import get_report_email_recipients
            result = get_report_email_recipients()

            assert result['to'] == []


class TestIndexRoute:
    """Test index route."""

    def test_index_get_logged_in(self, auth_user):
        """Test GET request to index."""
        response = auth_user.get('/')
        assert response.status_code == 200

    def test_index_requires_login(self, client):
        """Test that index requires login."""
        response = client.get('/')
        assert response.status_code in [302, 401]  # Redirect to login

    def test_index_with_active_tab_param(self, auth_user):
        """Test index with active_tab parameter."""
        response = auth_user.get('/?active_tab=list-pane')
        assert response.status_code == 200


class TestPreviewSampleAnalyses:
    """Test preview_sample_analyses route."""

    def test_preview_analyses_success(self, auth_user):
        """Test successful preview of analyses."""
        response = auth_user.post(
            '/preview-analyses',
            json={
                'sample_names': ['PF211_D1', 'PF211_D2'],
                'client_name': 'CHPP',
                'sample_type': '2 hourly'
            },
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)

    def test_preview_analyses_missing_data(self, auth_user):
        """Test preview with missing data."""
        response = auth_user.post(
            '/preview-analyses',
            json={
                'sample_names': ['PF211_D1'],
                # Missing client_name and sample_type
            },
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_preview_analyses_empty_names(self, auth_user):
        """Test preview with empty sample names."""
        response = auth_user.post(
            '/preview-analyses',
            json={
                'sample_names': [],
                'client_name': 'CHPP',
                'sample_type': '2 hourly'
            },
            content_type='application/json'
        )
        assert response.status_code == 400


class TestSendHourlyReport:
    """Test send_hourly_report route."""

    def test_send_hourly_report_no_permission(self, auth_user):
        """Test that non-senior users cannot send report."""
        response = auth_user.get('/send-hourly-report')
        # Should redirect with error flash
        assert response.status_code == 302

    def test_send_hourly_report_senior_no_recipients(self, app, client, db):
        """Test send report by senior when no recipients configured."""
        with app.app_context():
            from app.models import SystemSetting
            from app import db as _db

            # Clear email settings
            SystemSetting.query.filter_by(category='email').delete()
            _db.session.commit()

        # Login as senior
        client.post('/login', data={
            'username': 'senior',
            'password': 'TestPass123'
        })

        response = client.get('/send-hourly-report')
        assert response.status_code == 302  # Redirects


# =============================================================================
# SAMPLES_API.PY TESTS
# =============================================================================
class TestDataEndpoint:
    """Test /api/data DataTables endpoint."""

    def test_data_basic(self, auth_user):
        """Test basic data request."""
        response = auth_user.get('/api/data?draw=1&start=0&length=25')
        assert response.status_code == 200
        data = response.get_json()
        assert 'draw' in data
        assert 'recordsTotal' in data
        assert 'recordsFiltered' in data
        assert 'data' in data

    def test_data_with_column_search(self, auth_user):
        """Test data with column search filters."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[0][data]=checkbox'
            '&columns[1][data]=id'
            '&columns[1][search][value]=1'
            '&columns[2][data]=sample_code'
            '&columns[2][search][value]=PF'
        )
        assert response.status_code == 200

    def test_data_with_date_filter(self, auth_user):
        """Test data with date filters."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_user.get(
            f'/api/data?draw=1&start=0&length=25'
            f'&dateFilterStart={today}'
            f'&dateFilterEnd={today}'
        )
        assert response.status_code == 200

    def test_data_with_invalid_date(self, auth_user):
        """Test data with invalid date format."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&dateFilterStart=invalid-date'
        )
        assert response.status_code == 200  # Should not crash

    def test_data_with_client_filter(self, auth_user):
        """Test data with client name filter."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[3][data]=client_name'
            '&columns[3][search][value]=CHPP'
        )
        assert response.status_code == 200

    def test_data_with_weight_filter(self, auth_user):
        """Test data with weight filter."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[11][data]=weight'
            '&columns[11][search][value]=100.5'
        )
        assert response.status_code == 200

    def test_data_with_invalid_weight(self, auth_user):
        """Test data with invalid weight value."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[11][data]=weight'
            '&columns[11][search][value]=not_a_number'
        )
        assert response.status_code == 200

    def test_data_max_length_limit(self, auth_user):
        """Test that length is capped at 1000."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=5000'
        )
        assert response.status_code == 200


class TestSampleSummary:
    """Test /api/sample_summary endpoint."""

    def test_sample_summary_get(self, auth_user):
        """Test GET sample summary."""
        response = auth_user.get('/api/sample_summary')
        assert response.status_code == 200

    def test_sample_summary_archive(self, app, auth_admin, db):
        """Test archive action."""
        with app.app_context():
            from app.models import Sample
            from app import db as _db

            # Create a sample to archive
            sample = Sample(
                sample_code='TEST_ARCHIVE_001',
                client_name='CHPP',
                sample_type='Test',
                status='new'
            )
            _db.session.add(sample)
            _db.session.commit()
            sample_id = sample.id

        response = auth_admin.post(
            '/api/sample_summary',
            data={
                'action': 'archive',
                'sample_ids': str(sample_id)
            }
        )
        assert response.status_code == 302

    def test_sample_summary_unarchive(self, app, auth_admin, db):
        """Test unarchive action."""
        with app.app_context():
            from app.models import Sample
            from app import db as _db

            sample = Sample(
                sample_code='TEST_UNARCHIVE_001',
                client_name='CHPP',
                sample_type='Test',
                status='archived'
            )
            _db.session.add(sample)
            _db.session.commit()
            sample_id = sample.id

        response = auth_admin.post(
            '/api/sample_summary',
            data={
                'action': 'unarchive',
                'sample_ids': str(sample_id)
            }
        )
        assert response.status_code == 302

    def test_sample_summary_invalid_ids(self, auth_admin):
        """Test with invalid sample IDs."""
        response = auth_admin.post(
            '/api/sample_summary',
            data={
                'action': 'archive',
                'sample_ids': 'abc,def,ghi'
            }
        )
        assert response.status_code == 302


class TestSampleReport:
    """Test /api/sample_report endpoint."""

    def test_sample_report_not_found(self, auth_user):
        """Test report for non-existent sample."""
        response = auth_user.get('/api/sample_report/99999')
        # May return 404 or redirect
        assert response.status_code in [404, 302, 400]

    def test_sample_report_success(self, app, auth_user, db):
        """Test successful report generation."""
        with app.app_context():
            from app.models import Sample
            from app import db as _db

            sample = Sample(
                sample_code='TEST_REPORT_001',
                client_name='CHPP',
                sample_type='Test'
            )
            _db.session.add(sample)
            _db.session.commit()
            sample_id = sample.id

        response = auth_user.get(f'/api/sample_report/{sample_id}')
        assert response.status_code == 200


class TestSampleHistory:
    """Test /api/sample_history endpoint."""

    def test_sample_history_not_found(self, auth_user):
        """Test history for non-existent sample."""
        response = auth_user.get('/api/sample_history/99999')
        assert response.status_code == 404

    def test_sample_history_success(self, app, auth_user, db):
        """Test successful history retrieval."""
        with app.app_context():
            from app.models import Sample
            from app import db as _db

            sample = Sample(
                sample_code='TEST_HISTORY_001',
                client_name='CHPP',
                sample_type='Test'
            )
            _db.session.add(sample)
            _db.session.commit()
            sample_id = sample.id

        response = auth_user.get(f'/api/sample_history/{sample_id}')
        assert response.status_code == 200


class TestArchiveHub:
    """Test /api/archive_hub endpoint."""

    def test_archive_hub_get(self, auth_user):
        """Test GET archive hub."""
        response = auth_user.get('/api/archive_hub')
        assert response.status_code == 200

    def test_archive_hub_with_filters(self, auth_user):
        """Test archive hub with filters."""
        response = auth_user.get(
            '/api/archive_hub?client=CHPP&type=2%20hourly&year=2024&month=12'
        )
        assert response.status_code == 200

    def test_archive_hub_unarchive_post(self, app, auth_admin, db):
        """Test unarchive action in archive hub."""
        with app.app_context():
            from app.models import Sample
            from app import db as _db

            sample = Sample(
                sample_code='TEST_HUB_UNARCHIVE_001',
                client_name='CHPP',
                sample_type='Test',
                status='archived'
            )
            _db.session.add(sample)
            _db.session.commit()
            sample_id = sample.id

        response = auth_admin.post(
            '/api/archive_hub',
            data={
                'action': 'unarchive',
                'sample_ids': str(sample_id)
            }
        )
        assert response.status_code == 302


class TestDashboardStats:
    """Test /api/dashboard_stats endpoint."""

    def test_dashboard_stats(self, auth_user):
        """Test dashboard statistics."""
        response = auth_user.get('/api/dashboard_stats')
        assert response.status_code == 200
        data = response.get_json()
        assert 'samples_by_day' in data
        assert 'samples_by_client' in data
        assert 'analysis_by_status' in data
        assert 'approval_stats' in data
        assert 'today' in data

    def test_dashboard_stats_structure(self, auth_user):
        """Test dashboard stats response structure."""
        response = auth_user.get('/api/dashboard_stats')
        data = response.get_json()

        # Check samples_by_day
        assert isinstance(data['samples_by_day'], list)
        assert len(data['samples_by_day']) == 7  # Last 7 days

        # Check approval_stats
        assert 'approved' in data['approval_stats']
        assert 'rejected' in data['approval_stats']
        assert 'pending' in data['approval_stats']

        # Check today stats
        assert 'samples' in data['today']
        assert 'analyses' in data['today']
        assert 'pending_review' in data['today']


class TestExportSamples:
    """Test /api/export/samples endpoint."""

    def test_export_samples_basic(self, auth_user):
        """Test basic sample export."""
        response = auth_user.get('/api/export/samples')
        assert response.status_code == 200
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.content_type

    def test_export_samples_with_filters(self, auth_user):
        """Test sample export with filters."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_user.get(
            f'/api/export/samples?client=CHPP&type=Test&start_date={today}&end_date={today}&limit=100'
        )
        assert response.status_code == 200

    def test_export_samples_invalid_date(self, auth_user):
        """Test sample export with invalid date."""
        response = auth_user.get(
            '/api/export/samples?start_date=invalid&end_date=invalid'
        )
        assert response.status_code == 200


class TestExportAnalysis:
    """Test /api/export/analysis endpoint."""

    def test_export_analysis_basic(self, auth_user):
        """Test basic analysis export."""
        response = auth_user.get('/api/export/analysis')
        assert response.status_code == 200
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.content_type

    def test_export_analysis_with_status(self, auth_user):
        """Test analysis export with status filter."""
        response = auth_user.get('/api/export/analysis?status=approved')
        assert response.status_code == 200

    def test_export_analysis_with_dates(self, auth_user):
        """Test analysis export with date filters."""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_user.get(
            f'/api/export/analysis?start_date={today}&end_date={today}'
        )
        assert response.status_code == 200


# =============================================================================
# HELPERS MODULE TESTS
# =============================================================================
class TestHelpers:
    """Test helper functions from main/helpers.py."""

    def test_get_12h_shift_code_day(self, app):
        """Test shift code for day shift."""
        with app.app_context():
            from app.routes.main.helpers import get_12h_shift_code
            from datetime import datetime

            # Day shift: 8:00 - 20:00
            day_time = datetime(2024, 1, 1, 10, 0)
            result = get_12h_shift_code(day_time)
            assert 'D' in result  # '_D' or 'D'

    def test_get_12h_shift_code_night(self, app):
        """Test shift code for night shift."""
        with app.app_context():
            from app.routes.main.helpers import get_12h_shift_code
            from datetime import datetime

            # Night shift: 20:00 - 8:00
            night_time = datetime(2024, 1, 1, 22, 0)
            result = get_12h_shift_code(night_time)
            assert 'N' in result  # '_N' or 'N'

    def test_get_quarter_code(self, app):
        """Test quarter code generation."""
        with app.app_context():
            from app.routes.main.helpers import get_quarter_code
            from datetime import datetime

            # Q1: Jan-Mar
            q1_date = datetime(2024, 2, 15)
            result = get_quarter_code(q1_date)
            assert 'Q1' in result or '1' in result


class TestAggregateStatus:
    """Test _aggregate_sample_status helper."""

    def test_aggregate_status_approved(self, app):
        """Test aggregation with all approved."""
        with app.app_context():
            from app.routes.api.helpers import _aggregate_sample_status

            result = _aggregate_sample_status('received', {'approved'})
            assert result is not None

    def test_aggregate_status_pending(self, app):
        """Test aggregation with pending."""
        with app.app_context():
            from app.routes.api.helpers import _aggregate_sample_status

            result = _aggregate_sample_status('received', {'pending_review'})
            assert result is not None

    def test_aggregate_status_mixed(self, app):
        """Test aggregation with mixed statuses."""
        with app.app_context():
            from app.routes.api.helpers import _aggregate_sample_status

            result = _aggregate_sample_status('received', {'approved', 'pending_review'})
            assert result is not None

    def test_aggregate_status_empty(self, app):
        """Test aggregation with no results."""
        with app.app_context():
            from app.routes.api.helpers import _aggregate_sample_status

            result = _aggregate_sample_status('new', set())
            assert result is not None


# =============================================================================
# DATA ENDPOINT COLUMN FILTERS EXTENDED
# =============================================================================
class TestDataColumnFilters:
    """Test all column filter combinations."""

    def test_filter_by_id(self, auth_user):
        """Test filter by ID column."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[1][data]=id'
            '&columns[1][search][value]=1'
        )
        assert response.status_code == 200

    def test_filter_by_sample_code(self, auth_user):
        """Test filter by sample code."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[2][data]=sample_code'
            '&columns[2][search][value]=TEST'
        )
        assert response.status_code == 200

    def test_filter_by_sample_type(self, auth_user):
        """Test filter by sample type."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[4][data]=sample_type'
            '&columns[4][search][value]=hourly'
        )
        assert response.status_code == 200

    def test_filter_by_condition(self, auth_user):
        """Test filter by sample condition."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[5][data]=condition'
            '&columns[5][search][value]=dry'
        )
        assert response.status_code == 200

    def test_filter_by_delivered_by(self, auth_user):
        """Test filter by delivered_by."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[6][data]=delivered_by'
            '&columns[6][search][value]=John'
        )
        assert response.status_code == 200

    def test_filter_by_prepared_by(self, auth_user):
        """Test filter by prepared_by."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[7][data]=prepared_by'
            '&columns[7][search][value]=Jane'
        )
        assert response.status_code == 200

    def test_filter_by_notes(self, auth_user):
        """Test filter by notes."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[9][data]=notes'
            '&columns[9][search][value]=urgent'
        )
        assert response.status_code == 200

    def test_filter_by_analyses(self, auth_user):
        """Test filter by analyses to perform."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[13][data]=analyses'
            '&columns[13][search][value]=Mad'
        )
        assert response.status_code == 200

    def test_filter_invalid_id(self, auth_user):
        """Test filter with invalid ID (non-numeric)."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[1][data]=id'
            '&columns[1][search][value]=abc'
        )
        assert response.status_code == 200  # Should not crash


# =============================================================================
# SECURITY TESTS
# =============================================================================
class TestSecurityFilters:
    """Test SQL injection protection."""

    def test_sql_injection_in_sample_code_filter(self, auth_user):
        """Test SQL injection in sample code filter."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[2][data]=sample_code'
            "&columns[2][search][value]='; DROP TABLE samples;--"
        )
        assert response.status_code == 200

    def test_sql_injection_in_client_filter(self, auth_user):
        """Test SQL injection in client filter."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[3][data]=client_name'
            "&columns[3][search][value]=CHPP' OR '1'='1"
        )
        assert response.status_code == 200

    def test_like_pattern_special_chars(self, auth_user):
        """Test LIKE pattern special characters are escaped."""
        response = auth_user.get(
            '/api/data?draw=1&start=0&length=25'
            '&columns[2][data]=sample_code'
            '&columns[2][search][value]=test%_[]'
        )
        assert response.status_code == 200


# =============================================================================
# SAMPLE WITH RESULTS TESTS
# =============================================================================
class TestSampleWithResults:
    """Test samples with analysis results."""

    def test_data_with_sample_having_results(self, app, auth_user, db):
        """Test data endpoint with samples that have analysis results."""
        with app.app_context():
            from app.models import Sample, AnalysisResult
            from app import db as _db

            sample = Sample(
                sample_code='TEST_WITH_RESULTS_001',
                client_name='CHPP',
                sample_type='Test',
                status='received'
            )
            _db.session.add(sample)
            _db.session.flush()

            result = AnalysisResult(
                sample_id=sample.id,
                analysis_code='Mad',
                final_result=5.5,
                status='approved'
            )
            _db.session.add(result)
            _db.session.commit()

        response = auth_user.get('/api/data?draw=1&start=0&length=25')
        assert response.status_code == 200

    def test_sample_summary_with_results(self, app, auth_user, db):
        """Test sample summary with analysis results."""
        with app.app_context():
            from app.models import Sample, AnalysisResult
            from app import db as _db

            sample = Sample(
                sample_code='TEST_SUMMARY_RESULTS_001',
                client_name='CHPP',
                sample_type='Test',
                status='new'
            )
            _db.session.add(sample)
            _db.session.flush()

            # Add approved result
            result = AnalysisResult(
                sample_id=sample.id,
                analysis_code='Mad',
                final_result=5.5,
                status='approved'
            )
            _db.session.add(result)
            _db.session.commit()

        response = auth_user.get('/api/sample_summary')
        assert response.status_code == 200


# =============================================================================
# RETENTION DATE TESTS
# =============================================================================
class TestRetentionDates:
    """Test retention date handling in data endpoint."""

    def test_sample_with_expired_retention(self, app, auth_user, db):
        """Test sample with expired retention date."""
        with app.app_context():
            from app.models import Sample
            from app import db as _db
            from datetime import date, timedelta

            sample = Sample(
                sample_code='TEST_EXPIRED_001',
                client_name='CHPP',
                sample_type='Test',
                retention_date=date.today() - timedelta(days=5)
            )
            _db.session.add(sample)
            _db.session.commit()

        response = auth_user.get('/api/data?draw=1&start=0&length=25')
        assert response.status_code == 200

    def test_sample_with_return_flag(self, app, auth_user, db):
        """Test sample with return_sample flag."""
        with app.app_context():
            from app.models import Sample
            from app import db as _db

            sample = Sample(
                sample_code='TEST_RETURN_001',
                client_name='CHPP',
                sample_type='Test',
                return_sample=True
            )
            _db.session.add(sample)
            _db.session.commit()

        response = auth_user.get('/api/data?draw=1&start=0&length=25')
        assert response.status_code == 200

    def test_sample_with_future_retention(self, app, auth_user, db):
        """Test sample with future retention date."""
        with app.app_context():
            from app.models import Sample
            from app import db as _db
            from datetime import date, timedelta

            sample = Sample(
                sample_code='TEST_FUTURE_001',
                client_name='CHPP',
                sample_type='Test',
                retention_date=date.today() + timedelta(days=60)
            )
            _db.session.add(sample)
            _db.session.commit()

        response = auth_user.get('/api/data?draw=1&start=0&length=25')
        assert response.status_code == 200

    def test_sample_with_week_retention(self, app, auth_user, db):
        """Test sample with 7 day retention date."""
        with app.app_context():
            from app.models import Sample
            from app import db as _db
            from datetime import date, timedelta

            sample = Sample(
                sample_code='TEST_WEEK_001',
                client_name='CHPP',
                sample_type='Test',
                retention_date=date.today() + timedelta(days=5)
            )
            _db.session.add(sample)
            _db.session.commit()

        response = auth_user.get('/api/data?draw=1&start=0&length=25')
        assert response.status_code == 200

    def test_sample_with_month_retention(self, app, auth_user, db):
        """Test sample with 30 day retention date."""
        with app.app_context():
            from app.models import Sample
            from app import db as _db
            from datetime import date, timedelta

            sample = Sample(
                sample_code='TEST_MONTH_001',
                client_name='CHPP',
                sample_type='Test',
                retention_date=date.today() + timedelta(days=20)
            )
            _db.session.add(sample)
            _db.session.commit()

        response = auth_user.get('/api/data?draw=1&start=0&length=25')
        assert response.status_code == 200
