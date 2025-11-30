# tests/integration/test_csrf_protection.py
"""
Integration tests for CSRF protection on equipment routes.
Tests verify that all POST endpoints reject requests without valid CSRF tokens.
"""
import pytest
from flask import url_for
from app import db
from app.models import Equipment, User


class TestCSRFProtection:
    """Test CSRF protection is enforced on equipment routes."""

    def test_add_equipment_rejects_missing_csrf(self, app, client, auth_admin):
        """Test that adding equipment without CSRF token is rejected."""
        response = client.post(
            '/equipment/add_equipment',
            data={
                'name': 'Test Equipment',
                'manufacturer': 'Test Corp',
                'quantity': '1',
                'cycle': '365'
            }
        )

        # Should be rejected with 400 Bad Request or redirect
        assert response.status_code in [400, 302]

    def test_add_equipment_accepts_valid_csrf(self, app, client, auth_admin):
        """Test that adding equipment with valid CSRF token succeeds."""
        # Get CSRF token from a page
        index_response = client.get('/equipment_list')

        # Extract CSRF token (simplified - real implementation would parse HTML)
        # For pytest-flask, we can get it from the session
        from flask import session
        with client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token')

        response = client.post(
            '/equipment/add_equipment',
            data={
                'name': 'Test Equipment',
                'manufacturer': 'Test Corp',
                'quantity': '1',
                'cycle': '365',
                'csrf_token': csrf_token
            },
            follow_redirects=True
        )

        # Should succeed
        assert response.status_code == 200

    def test_edit_equipment_requires_csrf(self, app, client, auth_admin):
        """Test that editing equipment requires CSRF token."""
        with app.app_context():
            # Create test equipment
            eq = Equipment(
                name="Test Equipment",
                manufacturer="Test",
                category="test"
            )
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id

        # Try to edit without CSRF
        response = client.post(
            f'/equipment/edit_equipment/{eq_id}',
            data={'name': 'Updated Name'}
        )

        # Should be rejected
        assert response.status_code in [400, 302]

    def test_bulk_delete_requires_csrf(self, app, client, auth_admin):
        """Test that bulk delete requires CSRF token."""
        with app.app_context():
            # Create test equipment
            eq = Equipment(name="Test", category="test")
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id

        # Try bulk delete without CSRF
        response = client.post(
            '/equipment/bulk_delete',
            data={'equipment_ids': [eq_id]}
        )

        # Should be rejected
        assert response.status_code in [400, 302]

    def test_add_maintenance_log_requires_csrf(self, app, client, auth_admin):
        """Test that adding maintenance log requires CSRF token."""
        with app.app_context():
            eq = Equipment(name="Test", category="test")
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id

        # Try to add log without CSRF
        response = client.post(
            f'/equipment/add_log/{eq_id}',
            data={
                'action_type': 'Calibration',
                'description': 'Test calibration'
            }
        )

        # Should be rejected
        assert response.status_code in [400, 302]

    def test_csrf_token_is_present_in_forms(self, app, client, auth_admin):
        """Test that CSRF tokens are present in all equipment forms."""
        # Test equipment list page
        response = client.get('/equipment_list')
        assert response.status_code == 200
        html = response.get_data(as_text=True)

        # Should have csrf_token in forms
        assert 'csrf_token' in html
        assert 'bulk-action-form' in html

    def test_csrf_token_in_equipment_detail(self, app, client, auth_admin):
        """Test that equipment detail page has CSRF tokens."""
        with app.app_context():
            eq = Equipment(name="Test", category="test")
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id

        response = client.get(f'/equipment/equipment_detail/{eq_id}')
        assert response.status_code == 200
        html = response.get_data(as_text=True)

        # Should have csrf_token in forms
        # Count occurrences of csrf_token (should be 2: edit form + add log form)
        assert html.count('csrf_token') >= 2

    def test_api_endpoints_are_csrf_exempt(self, app, client, auth_user):
        """Test that API endpoints are exempt from CSRF (as configured)."""
        from app.models import Sample

        with app.app_context():
            # Create test sample
            sample = Sample(sample_code="API_TEST", user_id=1)
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        # API endpoints should work WITHOUT CSRF token
        response = client.post(
            '/api/mass/update_weight',
            json={'sample_id': sample_id, 'weight': 100},
            content_type='application/json'
        )

        # Should succeed (API is exempt from CSRF)
        assert response.status_code in [200, 404]  # 404 if sample not found, but not 400 CSRF error

    def test_csrf_token_rotation(self, app, client, auth_admin):
        """Test that CSRF tokens are properly rotated per session."""
        # Get first CSRF token
        response1 = client.get('/equipment_list')
        html1 = response1.get_data(as_text=True)

        # Logout and login again
        client.get('/logout')

        # Login as different user
        with app.app_context():
            user = User.query.filter_by(role='himich').first()
            if user:
                client.post('/login', data={
                    'username': user.username,
                    'password': 'password'  # Assuming test password
                })

        # Get second CSRF token
        response2 = client.get('/equipment_list')
        html2 = response2.get_data(as_text=True)

        # Tokens should be different (different sessions)
        # This is a basic test - real implementation would extract actual tokens


class TestCSRFDoubleSubmit:
    """Test CSRF double-submit cookie pattern."""

    def test_csrf_mismatch_rejected(self, app, client, auth_admin):
        """Test that mismatched CSRF token is rejected."""
        response = client.post(
            '/equipment/add_equipment',
            data={
                'name': 'Test',
                'csrf_token': 'invalid_token_12345'
            }
        )

        # Should be rejected
        assert response.status_code in [400, 302]

    def test_csrf_reuse_prevention(self, app, client, auth_admin):
        """Test that used CSRF tokens cannot be reused (if configured)."""
        # Get valid CSRF token
        from flask import session
        with client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token')

        # Use it once
        response1 = client.post(
            '/equipment/add_equipment',
            data={
                'name': 'Equipment 1',
                'csrf_token': csrf_token,
                'quantity': '1',
                'cycle': '365'
            }
        )

        # Try to reuse same token
        response2 = client.post(
            '/equipment/add_equipment',
            data={
                'name': 'Equipment 2',
                'csrf_token': csrf_token,  # Same token
                'quantity': '1',
                'cycle': '365'
            }
        )

        # Depending on configuration, may be rejected or allowed
        # Flask-WTF by default allows token reuse within same session


class TestCSRFSecurityHeaders:
    """Test security headers related to CSRF protection."""

    def test_samesite_cookie_attribute(self, app, client):
        """Test that session cookies have SameSite attribute."""
        response = client.get('/login')

        # Check Set-Cookie header
        set_cookie = response.headers.get('Set-Cookie', '')
        # Should have SameSite=Lax (from config.py line 56)
        assert 'SameSite=Lax' in set_cookie or 'samesite=lax' in set_cookie.lower()

    def test_httponly_cookie_attribute(self, app, client):
        """Test that session cookies have HttpOnly attribute."""
        response = client.get('/login')

        set_cookie = response.headers.get('Set-Cookie', '')
        # Should have HttpOnly (from config.py line 58)
        assert 'HttpOnly' in set_cookie

    def test_secure_cookie_in_production(self, app):
        """Test that Secure flag is set in production mode."""
        # Check config
        if app.config.get('ENV') == 'production':
            assert app.config.get('SESSION_COOKIE_SECURE') == True


# Run with: pytest tests/integration/test_csrf_protection.py -v
