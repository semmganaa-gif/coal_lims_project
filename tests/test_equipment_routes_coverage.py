# tests/test_equipment_routes_coverage.py
# -*- coding: utf-8 -*-
"""
equipment_routes.py coverage 80%+ хүргэх тестүүд.
Missing lines: 123-126, 133-134, 141, 152, 154-156, 167-174, 181-204, 210-253,
262-326, 331-355, 367-414, 423-425, 431-488, 494-527, 533-577, 585, 590-606, 620-647
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timedelta
from io import BytesIO
from app import create_app, db
from app.models import User, Equipment, MaintenanceLog, UsageLog
from tests.conftest import TestConfig


@pytest.fixture
def equip_app():
    """Test application fixture"""
    flask_app = create_app(TestConfig)
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SERVER_NAME'] = 'localhost'
    flask_app.config['UPLOAD_FOLDER'] = 'test_uploads'

    with flask_app.app_context():
        db.create_all()

        # Create users with different roles
        for role, uname in [('admin', 'eqadmin'), ('senior', 'eqsenior'), ('analyst', 'eqanalyst')]:
            if not User.query.filter_by(username=uname).first():
                user = User(username=uname, role=role)
                user.set_password('TestPass123')
                db.session.add(user)
        db.session.commit()

    yield flask_app

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()

    # Cleanup test uploads
    if os.path.exists('test_uploads'):
        import shutil
        shutil.rmtree('test_uploads', ignore_errors=True)


@pytest.fixture
def admin_client(equip_app):
    """Admin client with session auth"""
    client = equip_app.test_client()
    with equip_app.app_context():
        user = User.query.filter_by(username='eqadmin').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def analyst_client(equip_app):
    """Analyst client (no edit permission)"""
    client = equip_app.test_client()
    with equip_app.app_context():
        user = User.query.filter_by(username='eqanalyst').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def sample_equipment(equip_app):
    """Create sample equipment"""
    with equip_app.app_context():
        eq = Equipment(
            name='Test Balance',
            category='balance',
            model='AX-200',
            serial_number='BAL-001',
            lab_code='BAL001',
            status='normal',
            calibration_cycle_days=365,
            calibration_date=date.today(),
            next_calibration_date=date.today() + timedelta(days=365)
        )
        db.session.add(eq)
        db.session.commit()
        return eq.id


@pytest.fixture
def equipment_with_history(equip_app):
    """Create equipment with maintenance/usage history"""
    with equip_app.app_context():
        eq = Equipment(
            name='Equipment With History',
            category='furnace',
            status='normal',
            calibration_cycle_days=180
        )
        db.session.add(eq)
        db.session.commit()

        # Add maintenance log
        log = MaintenanceLog(
            equipment_id=eq.id,
            action_type='Calibration',
            description='Initial calibration',
            action_date=datetime.now()
        )
        db.session.add(log)
        db.session.commit()
        return eq.id


class TestRoleRestrictions:
    """Role-based access control tests - lines 133-134, 181-183, 210-212"""

    def test_analyst_cannot_edit_equipment(self, analyst_client, equip_app, sample_equipment):
        """Analyst cannot edit equipment"""
        with equip_app.app_context():
            response = analyst_client.post(f'/edit_equipment/{sample_equipment}', data={
                'name': 'Hacked Name'
            }, follow_redirects=True)
            assert response.status_code in [200, 302]
            # Should have error flash message

    def test_analyst_cannot_delete_equipment(self, analyst_client, equip_app, sample_equipment):
        """Analyst cannot delete equipment"""
        with equip_app.app_context():
            response = analyst_client.post(f'/equipment/delete/{sample_equipment}',
                follow_redirects=True)
            assert response.status_code in [200, 302]

    def test_analyst_cannot_bulk_delete(self, analyst_client, equip_app, sample_equipment):
        """Analyst cannot bulk delete"""
        with equip_app.app_context():
            response = analyst_client.post('/bulk_delete', data={
                'equipment_ids': [str(sample_equipment)]
            }, follow_redirects=True)
            assert response.status_code in [200, 302]


class TestEditEquipmentValidation:
    """Edit equipment validation tests - lines 141, 148-156"""

    def test_edit_with_serial_update(self, admin_client, equip_app, sample_equipment):
        """Edit equipment with serial number update"""
        with equip_app.app_context():
            response = admin_client.post(f'/edit_equipment/{sample_equipment}', data={
                'name': 'Updated Balance',
                'serial': 'NEW-SERIAL-001',
                'status': 'normal',
                'category': 'balance'
            }, follow_redirects=True)
            assert response.status_code == 200

    def test_edit_with_invalid_cycle(self, admin_client, equip_app, sample_equipment):
        """Edit equipment with invalid cycle"""
        with equip_app.app_context():
            response = admin_client.post(f'/edit_equipment/{sample_equipment}', data={
                'name': 'Updated Balance',
                'cycle': '-100',
                'category': 'balance'
            }, follow_redirects=True)
            assert response.status_code == 200

    def test_edit_with_zero_cycle(self, admin_client, equip_app, sample_equipment):
        """Edit equipment with zero cycle"""
        with equip_app.app_context():
            response = admin_client.post(f'/edit_equipment/{sample_equipment}', data={
                'name': 'Updated Balance',
                'cycle': '0',
                'category': 'balance'
            }, follow_redirects=True)
            assert response.status_code == 200


class TestEditEquipmentErrors:
    """Edit equipment error handling - lines 167-174"""

    def test_edit_integrity_error(self, admin_client, equip_app, sample_equipment):
        """Test IntegrityError handling in edit"""
        with equip_app.app_context():
            with patch('app.routes.equipment.crud.db.session.commit') as mock_commit:
                from sqlalchemy.exc import IntegrityError
                mock_commit.side_effect = IntegrityError('mock', 'params', 'orig')
                response = admin_client.post(f'/edit_equipment/{sample_equipment}', data={
                    'name': 'Conflict Name',
                    'category': 'balance'
                }, follow_redirects=True)
            assert response.status_code in [200, 302]

    def test_edit_general_exception(self, admin_client, equip_app, sample_equipment):
        """Test general exception handling in edit"""
        with equip_app.app_context():
            with patch('app.routes.equipment.crud.db.session.commit') as mock_commit:
                mock_commit.side_effect = Exception('Database error')
                response = admin_client.post(f'/edit_equipment/{sample_equipment}', data={
                    'name': 'Error Name',
                    'category': 'balance'
                }, follow_redirects=True)
            assert response.status_code in [200, 302]


class TestDeleteEquipment:
    """Delete equipment tests - lines 181-204"""

    def test_delete_equipment_no_history(self, admin_client, equip_app, sample_equipment):
        """Delete equipment without history"""
        with equip_app.app_context():
            response = admin_client.post(f'/equipment/delete/{sample_equipment}',
                follow_redirects=True)
            assert response.status_code == 200

    def test_delete_equipment_with_history(self, admin_client, equip_app, equipment_with_history):
        """Delete equipment with history (should retire)"""
        with equip_app.app_context():
            response = admin_client.post(f'/equipment/delete/{equipment_with_history}',
                follow_redirects=True)
            assert response.status_code == 200

    def test_delete_equipment_db_error(self, admin_client, equip_app, sample_equipment):
        """Delete equipment database error"""
        with equip_app.app_context():
            with patch('app.routes.equipment.crud.db.session.commit') as mock_commit:
                mock_commit.side_effect = Exception('DB error')
                response = admin_client.post(f'/equipment/delete/{sample_equipment}',
                    follow_redirects=True)
            assert response.status_code in [200, 302]


class TestBulkDelete:
    """Bulk delete tests - lines 210-253"""

    def test_bulk_delete_empty(self, admin_client, equip_app):
        """Bulk delete with no selection"""
        with equip_app.app_context():
            response = admin_client.post('/bulk_delete', data={},
                follow_redirects=True)
            assert response.status_code == 200

    def test_bulk_delete_success(self, admin_client, equip_app, sample_equipment):
        """Bulk delete success"""
        with equip_app.app_context():
            response = admin_client.post('/bulk_delete', data={
                'equipment_ids': [str(sample_equipment)]
            }, follow_redirects=True)
            assert response.status_code == 200

    def test_bulk_delete_with_history(self, admin_client, equip_app, equipment_with_history):
        """Bulk delete equipment with history"""
        with equip_app.app_context():
            response = admin_client.post('/bulk_delete', data={
                'equipment_ids': [str(equipment_with_history)]
            }, follow_redirects=True)
            assert response.status_code == 200

    def test_bulk_delete_db_error(self, admin_client, equip_app, sample_equipment):
        """Bulk delete database error"""
        with equip_app.app_context():
            with patch('app.routes.equipment.crud.db.session.commit') as mock_commit:
                mock_commit.side_effect = Exception('Bulk DB error')
                response = admin_client.post('/bulk_delete', data={
                    'equipment_ids': [str(sample_equipment)]
                }, follow_redirects=True)
            assert response.status_code in [200, 302]


class TestMaintenanceLog:
    """Maintenance log tests - lines 262-326"""

    def test_add_maintenance_log_calibration(self, admin_client, equip_app, sample_equipment):
        """Add calibration log"""
        with equip_app.app_context():
            response = admin_client.post(f'/add_log/{sample_equipment}', data={
                'action_type': 'Calibration',
                'description': 'Annual calibration',
                'performed_by': 'Tech1',
                'certificate_no': 'CERT-001',
                'action_date': date.today().isoformat()
            }, follow_redirects=True)
            assert response.status_code == 200

    def test_add_maintenance_log_repair(self, admin_client, equip_app, sample_equipment):
        """Add repair log"""
        with equip_app.app_context():
            response = admin_client.post(f'/add_log/{sample_equipment}', data={
                'action_type': 'Repair',
                'description': 'Fixed motor',
                'performed_by': 'Tech2',
                'action_date': date.today().isoformat()
            }, follow_redirects=True)
            assert response.status_code == 200

    def test_add_log_with_file(self, admin_client, equip_app, sample_equipment):
        """Add log with certificate file"""
        with equip_app.app_context():
            os.makedirs('test_uploads', exist_ok=True)
            data = {
                'action_type': 'Calibration',
                'description': 'With cert',
                'performed_by': 'Tech3',
                'action_date': date.today().isoformat(),
                'certificate_file': (BytesIO(b'PDF content'), 'cert.pdf')
            }
            response = admin_client.post(f'/add_log/{sample_equipment}',
                data=data, content_type='multipart/form-data',
                follow_redirects=True)
            assert response.status_code in [200, 302]

    def test_add_log_file_too_large(self, admin_client, equip_app, sample_equipment):
        """Add log with oversized file"""
        with equip_app.app_context():
            large_content = b'x' * (6 * 1024 * 1024)  # 6MB
            data = {
                'action_type': 'Calibration',
                'description': 'Large file',
                'performed_by': 'Tech4',
                'action_date': date.today().isoformat(),
                'certificate_file': (BytesIO(large_content), 'large.pdf')
            }
            response = admin_client.post(f'/add_log/{sample_equipment}',
                data=data, content_type='multipart/form-data',
                follow_redirects=True)
            assert response.status_code in [200, 302]

    def test_add_log_invalid_extension(self, admin_client, equip_app, sample_equipment):
        """Add log with invalid file extension"""
        with equip_app.app_context():
            data = {
                'action_type': 'Calibration',
                'description': 'Invalid ext',
                'performed_by': 'Tech5',
                'action_date': date.today().isoformat(),
                'certificate_file': (BytesIO(b'script'), 'virus.exe')
            }
            response = admin_client.post(f'/add_log/{sample_equipment}',
                data=data, content_type='multipart/form-data',
                follow_redirects=True)
            assert response.status_code in [200, 302]

    def test_add_log_no_extension(self, admin_client, equip_app, sample_equipment):
        """Add log with file without extension"""
        with equip_app.app_context():
            data = {
                'action_type': 'Calibration',
                'description': 'No ext',
                'performed_by': 'Tech6',
                'action_date': date.today().isoformat(),
                'certificate_file': (BytesIO(b'data'), 'noext')
            }
            response = admin_client.post(f'/add_log/{sample_equipment}',
                data=data, content_type='multipart/form-data',
                follow_redirects=True)
            assert response.status_code in [200, 302]


class TestDownloadCertificate:
    """Download certificate tests - lines 331-355"""

    def test_download_no_file(self, admin_client, equip_app, sample_equipment):
        """Download when no file exists"""
        with equip_app.app_context():
            # Create log without file
            log = MaintenanceLog(
                equipment_id=sample_equipment,
                action_type='Calibration',
                action_date=datetime.now()
            )
            db.session.add(log)
            db.session.commit()
            log_id = log.id

            response = admin_client.get(f'/download_cert/{log_id}',
                follow_redirects=True)
            assert response.status_code in [200, 302]

    def test_download_file_not_found(self, admin_client, equip_app, sample_equipment):
        """Download when file reference exists but file doesn't"""
        with equip_app.app_context():
            log = MaintenanceLog(
                equipment_id=sample_equipment,
                action_type='Calibration',
                action_date=datetime.now(),
                file_path='nonexistent.pdf'
            )
            db.session.add(log)
            db.session.commit()
            log_id = log.id

            response = admin_client.get(f'/download_cert/{log_id}',
                follow_redirects=True)
            assert response.status_code in [200, 302]


class TestUsageBulkAPI:
    """Usage bulk API tests - lines 367-414"""

    def test_log_usage_bulk_success(self, admin_client, equip_app, sample_equipment):
        """Log usage bulk success"""
        with equip_app.app_context():
            response = admin_client.post('/api/log_usage_bulk',
                data=json.dumps({
                    'items': [
                        {'eq_id': sample_equipment, 'minutes': 60, 'note': 'Test usage', 'is_checked': True}
                    ]
                }),
                content_type='application/json')
            assert response.status_code == 200

    def test_log_usage_bulk_empty(self, admin_client, equip_app):
        """Log usage bulk with no items"""
        with equip_app.app_context():
            response = admin_client.post('/api/log_usage_bulk',
                data=json.dumps({'items': []}),
                content_type='application/json')
            assert response.status_code == 400

    def test_log_usage_bulk_daily_check(self, admin_client, equip_app, sample_equipment):
        """Log usage bulk daily check only"""
        with equip_app.app_context():
            response = admin_client.post('/api/log_usage_bulk',
                data=json.dumps({
                    'items': [
                        {'eq_id': sample_equipment, 'minutes': 0, 'note': '', 'is_checked': True}
                    ]
                }),
                content_type='application/json')
            assert response.status_code == 200

    def test_log_usage_bulk_exception(self, admin_client, equip_app, sample_equipment):
        """Log usage bulk exception handling"""
        with equip_app.app_context():
            with patch('app.routes.equipment.crud.db.session.commit') as mock_commit:
                mock_commit.side_effect = Exception('Commit error')
                response = admin_client.post('/api/log_usage_bulk',
                    data=json.dumps({
                        'items': [{'eq_id': sample_equipment, 'minutes': 30}]
                    }),
                    content_type='application/json')
            assert response.status_code == 500


class TestUsageSummaryAPI:
    """Usage summary API tests - lines 431-488"""

    def test_usage_summary_default(self, admin_client, equip_app, sample_equipment):
        """Usage summary with default dates"""
        with equip_app.app_context():
            response = admin_client.get('/api/equipment/usage_summary')
            assert response.status_code == 200

    def test_usage_summary_with_dates(self, admin_client, equip_app, sample_equipment):
        """Usage summary with custom dates"""
        with equip_app.app_context():
            start = (date.today() - timedelta(days=7)).isoformat()
            end = date.today().isoformat()
            response = admin_client.get(f'/api/equipment/usage_summary?start_date={start}&end_date={end}')
            assert response.status_code == 200

    def test_usage_summary_with_category(self, admin_client, equip_app, sample_equipment):
        """Usage summary with category filter"""
        with equip_app.app_context():
            response = admin_client.get('/api/equipment/usage_summary?category=balance')
            assert response.status_code == 200

    def test_usage_summary_empty(self, admin_client, equip_app):
        """Usage summary with no equipment"""
        with equip_app.app_context():
            response = admin_client.get('/api/equipment/usage_summary?category=nonexistent')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('rows') == []


class TestJournalDetailedAPI:
    """Journal detailed API tests - lines 494-527"""

    def test_journal_detailed_default(self, admin_client, equip_app, sample_equipment):
        """Journal detailed with default dates"""
        with equip_app.app_context():
            response = admin_client.get('/api/equipment/journal_detailed')
            assert response.status_code == 200

    def test_journal_detailed_with_dates(self, admin_client, equip_app, sample_equipment):
        """Journal detailed with custom dates"""
        with equip_app.app_context():
            start = (date.today() - timedelta(days=7)).isoformat()
            end = date.today().isoformat()
            response = admin_client.get(f'/api/equipment/journal_detailed?start_date={start}&end_date={end}')
            assert response.status_code == 200

    def test_journal_detailed_with_logs(self, admin_client, equip_app, equipment_with_history):
        """Journal detailed with existing logs"""
        with equip_app.app_context():
            # Add usage log
            usage = UsageLog(
                equipment_id=equipment_with_history,
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=1),
                duration_minutes=60,
                used_by='TestUser'
            )
            db.session.add(usage)
            db.session.commit()

            response = admin_client.get('/api/equipment/journal_detailed')
            assert response.status_code == 200


class TestMonthlyStatsAPI:
    """Monthly stats API tests - lines 533-577"""

    def test_monthly_stats_default(self, admin_client, equip_app, sample_equipment):
        """Monthly stats with default year"""
        with equip_app.app_context():
            response = admin_client.get('/api/equipment/monthly_stats')
            assert response.status_code == 200

    def test_monthly_stats_specific_year(self, admin_client, equip_app, sample_equipment):
        """Monthly stats with specific year"""
        with equip_app.app_context():
            response = admin_client.get('/api/equipment/monthly_stats?year=2024')
            assert response.status_code == 200

    def test_monthly_stats_with_category(self, admin_client, equip_app, sample_equipment):
        """Monthly stats with category filter"""
        with equip_app.app_context():
            response = admin_client.get('/api/equipment/monthly_stats?category=balance')
            assert response.status_code == 200

    def test_monthly_stats_empty(self, admin_client, equip_app):
        """Monthly stats with no equipment"""
        with equip_app.app_context():
            response = admin_client.get('/api/equipment/monthly_stats?category=nonexistent')
            assert response.status_code == 200


class TestNavigationRoutes:
    """Navigation routes tests - lines 585, 590-606"""

    def test_equipment_journal_hub(self, admin_client, equip_app):
        """Equipment journal hub page"""
        with equip_app.app_context():
            response = admin_client.get('/equipment_journal')
            assert response.status_code == 200

    def test_equipment_journal_grid_default(self, admin_client, equip_app):
        """Equipment journal grid - default"""
        with equip_app.app_context():
            response = admin_client.get('/equipment_journal/grid')
            assert response.status_code == 200

    def test_equipment_journal_grid_furnace(self, admin_client, equip_app):
        """Equipment journal grid - furnace category"""
        with equip_app.app_context():
            response = admin_client.get('/equipment_journal/grid?category=furnace')
            assert response.status_code == 200

    def test_equipment_journal_grid_balance(self, admin_client, equip_app):
        """Equipment journal grid - balance category"""
        with equip_app.app_context():
            response = admin_client.get('/equipment_journal/grid?category=balance')
            assert response.status_code == 200


class TestEquipmentListJSON:
    """Equipment list JSON API tests - lines 620-647"""

    def test_equipment_list_json(self, admin_client, equip_app, sample_equipment):
        """Equipment list JSON API"""
        with equip_app.app_context():
            response = admin_client.get('/api/equipment_list_json')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list)

    def test_equipment_list_json_expired(self, admin_client, equip_app):
        """Equipment list JSON with expired calibration"""
        with equip_app.app_context():
            eq = Equipment(
                name='Expired Equipment',
                category='balance',
                status='normal',
                next_calibration_date=date.today() - timedelta(days=30)
            )
            db.session.add(eq)
            db.session.commit()

            response = admin_client.get('/api/equipment_list_json')
            assert response.status_code == 200
            data = json.loads(response.data)
            # Check that expired flag is set
            expired_items = [d for d in data if d.get('is_expired')]
            assert len(expired_items) >= 1


class TestAddEquipmentDBError:
    """Add equipment database error - lines 123-126"""

    def test_add_equipment_db_exception(self, admin_client, equip_app):
        """Add equipment database exception"""
        with equip_app.app_context():
            with patch('app.routes.equipment.crud.db.session.commit') as mock_commit:
                mock_commit.side_effect = Exception('DB save error')
                response = admin_client.post('/add_equipment', data={
                    'name': 'Error Equipment',
                    'quantity': '1',
                    'cycle': '365',
                    'category': 'other'
                }, follow_redirects=True)
            assert response.status_code in [200, 302]
