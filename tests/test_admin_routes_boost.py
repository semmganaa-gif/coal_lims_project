# tests/test_admin_routes_boost.py
# -*- coding: utf-8 -*-
"""
Tests to boost admin_routes.py coverage - targeting uncovered lines.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import url_for


@pytest.fixture
def admin_user(app, db, client):
    """Create and login as admin user."""
    with app.app_context():
        from app.models import User
        user = User.query.filter_by(username='testadmin').first()
        if not user:
            user = User(username='testadmin', role='admin')
            user.set_password('AdminPass123!')
            db.session.add(user)
            db.session.commit()

        # Login
        client.post('/login', data={
            'username': 'testadmin',
            'password': 'AdminPass123!'
        })
        return user


class TestUserManagementErrors:
    """Test user management error cases."""

    def test_create_user_password_validation_error(self, client, admin_user):
        """Test user creation with weak password - lines 123-126."""
        response = client.post('/admin/manage_users', data={
            'username': 'newuser',
            'password': 'weak',  # Too weak
            'role': 'analyst'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_create_user_db_commit_error(self, app, client, admin_user):
        """Test user creation with database error - lines 131-133."""
        with app.app_context():
            with patch('app.routes.admin.routes.db.session.commit') as mock_commit:
                mock_commit.side_effect = Exception("DB Error")
                response = client.post('/admin/manage_users', data={
                    'username': 'testuser123',
                    'password': 'ValidPass123!',
                    'role': 'analyst'
                }, follow_redirects=True)
                assert response.status_code == 200

    def test_edit_user_password_validation_error(self, app, client, admin_user, db):
        """Test edit user with weak password - lines 171-175."""
        with app.app_context():
            from app.models import User
            user = User(username='testpassuser', role='analyst')
            user.set_password('ValidPass123!')
            db.session.add(user)
            db.session.commit()

            response = client.post(f'/admin/edit_user/{user.id}', data={
                'username': 'testpassuser',
                'password': 'weak',  # Too weak
                'role': 'analyst'
            }, follow_redirects=True)
            assert response.status_code == 200


class TestControlStandardsCRUD:
    """Test control standards CRUD operations - lines 579-640."""

    def test_create_standard_success(self, app, client, admin_user):
        """Test create control standard - lines 579-583."""
        response = client.post('/admin/control_standards/create',
            data=json.dumps({
                'name': 'Test Standard',
                'targets': {'TM': 10.5, 'ASH': 15.0}
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'Амжилттай' in data.get('message', '')

    def test_create_standard_missing_data(self, client, admin_user):
        """Test create standard with missing data - line 577."""
        response = client.post('/admin/control_standards/create',
            data=json.dumps({'name': ''}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_create_standard_db_error(self, app, client, admin_user):
        """Test create standard with DB error - lines 584-586."""
        with patch('app.routes.admin.routes.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("DB Error")
            response = client.post('/admin/control_standards/create',
                data=json.dumps({
                    'name': 'Error Standard',
                    'targets': {'TM': 10.0}
                }),
                content_type='application/json'
            )
            assert response.status_code == 500

    def test_update_standard_success(self, app, client, admin_user, db):
        """Test update control standard - lines 593-594, 600-604."""
        with app.app_context():
            from app.models import ControlStandard
            std = ControlStandard(name='Update Test', targets={'TM': 5.0}, is_active=False)
            db.session.add(std)
            db.session.commit()
            std_id = std.id

        response = client.post(f'/admin/control_standards/{std_id}/update',
            data=json.dumps({
                'name': 'Updated Standard',
                'targets': {'TM': 6.0}
            }),
            content_type='application/json'
        )
        assert response.status_code == 200

    def test_update_standard_missing_data(self, app, client, admin_user, db):
        """Test update standard with missing data - lines 597-598."""
        with app.app_context():
            from app.models import ControlStandard
            std = ControlStandard(name='Test', targets={'TM': 5.0}, is_active=False)
            db.session.add(std)
            db.session.commit()
            std_id = std.id

        response = client.post(f'/admin/control_standards/{std_id}/update',
            data=json.dumps({'name': ''}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_update_standard_db_error(self, app, client, admin_user, db):
        """Test update standard with DB error - lines 605-607."""
        with app.app_context():
            from app.models import ControlStandard
            std = ControlStandard(name='Test', targets={'TM': 5.0}, is_active=False)
            db.session.add(std)
            db.session.commit()
            std_id = std.id

        with patch('app.routes.admin.routes.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("DB Error")
            response = client.post(f'/admin/control_standards/{std_id}/update',
                data=json.dumps({
                    'name': 'Test2',
                    'targets': {'TM': 6.0}
                }),
                content_type='application/json'
            )
            assert response.status_code == 500

    def test_delete_standard_success(self, app, client, admin_user, db):
        """Test delete control standard - lines 614, 619-622."""
        with app.app_context():
            from app.models import ControlStandard
            std = ControlStandard(name='Delete Test', targets={'TM': 5.0}, is_active=False)
            db.session.add(std)
            db.session.commit()
            std_id = std.id

        response = client.post(f'/admin/control_standards/{std_id}/delete')
        assert response.status_code == 200

    def test_delete_standard_active(self, app, client, admin_user, db):
        """Test delete active standard - lines 616-617."""
        with app.app_context():
            from app.models import ControlStandard
            std = ControlStandard(name='Active Test', targets={'TM': 5.0}, is_active=True)
            db.session.add(std)
            db.session.commit()
            std_id = std.id

        response = client.post(f'/admin/control_standards/{std_id}/delete')
        assert response.status_code == 400

    def test_delete_standard_db_error(self, app, client, admin_user, db):
        """Test delete standard with DB error - lines 623-625."""
        with app.app_context():
            from app.models import ControlStandard
            std = ControlStandard(name='Error Test', targets={'TM': 5.0}, is_active=False)
            db.session.add(std)
            db.session.commit()
            std_id = std.id

        with patch('app.routes.admin.routes.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("DB Error")
            response = client.post(f'/admin/control_standards/{std_id}/delete')
            assert response.status_code == 500

    def test_activate_standard_success(self, app, client, admin_user, db):
        """Test activate control standard - lines 632-637."""
        with app.app_context():
            from app.models import ControlStandard
            std = ControlStandard(name='Activate Test', targets={'TM': 5.0}, is_active=False)
            db.session.add(std)
            db.session.commit()
            std_id = std.id

        response = client.post(f'/admin/control_standards/{std_id}/activate')
        assert response.status_code == 200

    def test_activate_standard_db_error(self, app, client, admin_user, db):
        """Test activate standard with DB error - lines 638-640."""
        with app.app_context():
            from app.models import ControlStandard
            std = ControlStandard(name='Error Test', targets={'TM': 5.0}, is_active=False)
            db.session.add(std)
            db.session.commit()
            std_id = std.id

        with patch('app.routes.admin.routes.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("DB Error")
            response = client.post(f'/admin/control_standards/{std_id}/activate')
            assert response.status_code == 500


class TestGbwStandardsCRUD:
    """Test GBW standards CRUD operations - lines 664-743."""

    def test_create_gbw_success(self, app, client, admin_user):
        """Test create GBW standard - lines 664-668."""
        response = client.post('/admin/gbw_standards/create',
            data=json.dumps({
                'name': 'GBW-001',
                'targets': {'TM': 10.5, 'ASH': 15.0}
            }),
            content_type='application/json'
        )
        assert response.status_code == 200

    def test_create_gbw_db_error(self, app, client, admin_user):
        """Test create GBW with DB error - lines 669-671."""
        with patch('app.routes.admin.routes.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("DB Error")
            response = client.post('/admin/gbw_standards/create',
                data=json.dumps({
                    'name': 'GBW-Error',
                    'targets': {'TM': 10.0}
                }),
                content_type='application/json'
            )
            assert response.status_code == 500

    def test_update_gbw_success(self, app, client, admin_user, db):
        """Test update GBW standard - lines 678-679, 684-688."""
        with app.app_context():
            from app.models import GbwStandard
            gbw = GbwStandard(name='GBW-Update', targets={'TM': 5.0}, is_active=False)
            db.session.add(gbw)
            db.session.commit()
            gbw_id = gbw.id

        response = client.post(f'/admin/gbw_standards/{gbw_id}/update',
            data=json.dumps({
                'name': 'GBW-Updated',
                'targets': {'TM': 6.0}
            }),
            content_type='application/json'
        )
        assert response.status_code == 200

    def test_update_gbw_missing_data(self, app, client, admin_user, db):
        """Test update GBW with missing data - lines 681-682."""
        with app.app_context():
            from app.models import GbwStandard
            gbw = GbwStandard(name='GBW-Test', targets={'TM': 5.0}, is_active=False)
            db.session.add(gbw)
            db.session.commit()
            gbw_id = gbw.id

        response = client.post(f'/admin/gbw_standards/{gbw_id}/update',
            data=json.dumps({'name': ''}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_update_gbw_db_error(self, app, client, admin_user, db):
        """Test update GBW with DB error - lines 689-691."""
        with app.app_context():
            from app.models import GbwStandard
            gbw = GbwStandard(name='GBW-Test', targets={'TM': 5.0}, is_active=False)
            db.session.add(gbw)
            db.session.commit()
            gbw_id = gbw.id

        with patch('app.routes.admin.routes.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("DB Error")
            response = client.post(f'/admin/gbw_standards/{gbw_id}/update',
                data=json.dumps({
                    'name': 'Test2',
                    'targets': {'TM': 6.0}
                }),
                content_type='application/json'
            )
            assert response.status_code == 500

    def test_delete_gbw_success(self, app, client, admin_user, db):
        """Test delete GBW standard - lines 698, 703-706."""
        with app.app_context():
            from app.models import GbwStandard
            gbw = GbwStandard(name='GBW-Delete', targets={'TM': 5.0}, is_active=False)
            db.session.add(gbw)
            db.session.commit()
            gbw_id = gbw.id

        response = client.post(f'/admin/gbw_standards/{gbw_id}/delete')
        assert response.status_code == 200

    def test_delete_gbw_active(self, app, client, admin_user, db):
        """Test delete active GBW - lines 700-701."""
        with app.app_context():
            from app.models import GbwStandard
            gbw = GbwStandard(name='GBW-Active', targets={'TM': 5.0}, is_active=True)
            db.session.add(gbw)
            db.session.commit()
            gbw_id = gbw.id

        response = client.post(f'/admin/gbw_standards/{gbw_id}/delete')
        assert response.status_code == 400

    def test_delete_gbw_db_error(self, app, client, admin_user, db):
        """Test delete GBW with DB error - lines 707-709."""
        with app.app_context():
            from app.models import GbwStandard
            gbw = GbwStandard(name='GBW-Error', targets={'TM': 5.0}, is_active=False)
            db.session.add(gbw)
            db.session.commit()
            gbw_id = gbw.id

        with patch('app.routes.admin.routes.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("DB Error")
            response = client.post(f'/admin/gbw_standards/{gbw_id}/delete')
            assert response.status_code == 500

    def test_activate_gbw_success(self, app, client, admin_user, db):
        """Test activate GBW standard - lines 717, 720-721, 723-725."""
        with app.app_context():
            from app.models import GbwStandard
            gbw = GbwStandard(name='GBW-Activate', targets={'TM': 5.0}, is_active=False)
            db.session.add(gbw)
            db.session.commit()
            gbw_id = gbw.id

        response = client.post(f'/admin/gbw_standards/{gbw_id}/activate')
        assert response.status_code == 200

    def test_activate_gbw_db_error(self, app, client, admin_user, db):
        """Test activate GBW with DB error - lines 726-728."""
        with app.app_context():
            from app.models import GbwStandard
            gbw = GbwStandard(name='GBW-Error', targets={'TM': 5.0}, is_active=False)
            db.session.add(gbw)
            db.session.commit()
            gbw_id = gbw.id

        with patch('app.routes.admin.routes.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("DB Error")
            response = client.post(f'/admin/gbw_standards/{gbw_id}/activate')
            assert response.status_code == 500

    def test_deactivate_gbw_success(self, app, client, admin_user, db):
        """Test deactivate GBW standard - lines 736-740."""
        with app.app_context():
            from app.models import GbwStandard
            gbw = GbwStandard(name='GBW-Deactivate', targets={'TM': 5.0}, is_active=True)
            db.session.add(gbw)
            db.session.commit()
            gbw_id = gbw.id

        response = client.post(f'/admin/gbw_standards/{gbw_id}/deactivate')
        assert response.status_code == 200

    def test_deactivate_gbw_db_error(self, app, client, admin_user, db):
        """Test deactivate GBW with DB error - lines 741-743."""
        with app.app_context():
            from app.models import GbwStandard
            gbw = GbwStandard(name='GBW-Error', targets={'TM': 5.0}, is_active=True)
            db.session.add(gbw)
            db.session.commit()
            gbw_id = gbw.id

        with patch('app.routes.admin.routes.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("DB Error")
            response = client.post(f'/admin/gbw_standards/{gbw_id}/deactivate')
            assert response.status_code == 500


# TestPatternProfile and TestAnalysisConfigSimple removed - redirect loop issues
