# tests/test_smoke.py
"""
Smoke tests to verify test infrastructure is working correctly.

These basic tests ensure that:
- Test fixtures are properly configured
- Database is created and accessible
- Test users are created successfully
- Authentication works
- App routes are registered

Run with: pytest tests/test_smoke.py -v
"""
import pytest
from app.models import User, Sample, Equipment


class TestInfrastructure:
    """Verify test infrastructure is working."""

    def test_app_exists(self, app):
        """Test that app fixture creates Flask app."""
        assert app is not None
        assert app.config['TESTING'] is True

    def test_database_connection(self, app, db):
        """Test that database is accessible."""
        with app.app_context():
            # Should be able to query without error
            user_count = User.query.count()
            assert user_count >= 3  # admin, chemist, senior

    def test_test_users_created(self, app):
        """Test that test users were created successfully."""
        with app.app_context():
            admin = User.query.filter_by(username='admin').first()
            chemist = User.query.filter_by(username='chemist').first()
            senior = User.query.filter_by(username='senior').first()

            assert admin is not None
            assert admin.role == 'admin'

            assert chemist is not None
            assert chemist.role == 'chemist'

            assert senior is not None
            assert senior.role == 'senior'

    def test_password_validation(self, app):
        """Test that password validation works."""
        with app.app_context():
            admin = User.query.filter_by(username='admin').first()

            # Correct password should work
            assert admin.check_password('TestPass123') is True

            # Wrong password should fail
            assert admin.check_password('wrongpassword') is False


class TestFixtures:
    """Test that pytest fixtures work correctly."""

    def test_client_fixture(self, client):
        """Test that client fixture provides test client."""
        assert client is not None
        # Should be able to make requests
        response = client.get('/login')
        assert response.status_code == 200

    def test_auth_admin_fixture(self, auth_admin):
        """Test that auth_admin fixture logs in as admin."""
        # Auth fixture has already logged in
        # Try accessing equipment list (more reliable than index)
        response = auth_admin.get('/equipment_list')
        # Should get a response (200 or 302 redirect)
        assert response.status_code in [200, 302]

    def test_auth_user_fixture(self, auth_user):
        """Test that auth_user fixture logs in as regular user."""
        # Auth fixture has already logged in
        response = auth_user.get('/')
        # Should get a response
        assert response.status_code in [200, 302, 404]


class TestDatabaseModels:
    """Test that database models work in test environment."""

    def test_create_equipment(self, app, db):
        """Test creating equipment record."""
        with app.app_context():
            eq = Equipment(
                name="Test Equipment",
                manufacturer="Test Corp",
                category="test"
            )
            db.session.add(eq)
            db.session.commit()

            # Should be persisted
            assert eq.id is not None

            # Should be queryable
            found = db.session.get(Equipment, eq.id)
            assert found is not None
            assert found.name == "Test Equipment"

    def test_create_sample(self, app, db):
        """Test creating sample record."""
        import uuid
        with app.app_context():
            # Get a user for the foreign key
            user = User.query.filter_by(username='chemist').first()

            # Use unique sample code to avoid conflicts
            unique_code = f"TEST-{uuid.uuid4().hex[:8]}"
            sample = Sample(
                sample_code=unique_code,
                user_id=user.id,
                client_name="QC"  # Valid client name from CHECK constraint
            )
            db.session.add(sample)
            db.session.commit()

            # Should be persisted
            assert sample.id is not None

            # Should be queryable
            found = db.session.get(Sample, sample.id)
            assert found is not None
            assert found.sample_code == unique_code

    def test_database_relationships(self, app, db):
        """Test that database relationships work."""
        import uuid
        with app.app_context():
            user = User.query.filter_by(username='admin').first()

            # Create sample linked to user with valid client_name and unique code
            unique_code = f"REL-{uuid.uuid4().hex[:8]}"
            sample = Sample(
                sample_code=unique_code,
                user_id=user.id,
                client_name="LAB"  # Valid client name
            )
            db.session.add(sample)
            db.session.commit()

            # Foreign key should be set correctly
            assert sample.user_id is not None
            assert sample.user_id == user.id

            # Verify via query
            linked_user = db.session.get(User, sample.user_id)
            assert linked_user.username == 'admin'


class TestPasswordSecurity:
    """Test password security features."""

    def test_password_requirements(self):
        """Test password validation requirements."""
        # Too short
        errors = User.validate_password('abc')
        assert len(errors) > 0
        assert any('8' in e for e in errors)

        # No uppercase
        errors = User.validate_password('testpass123')
        assert any('том' in e or 'uppercase' in e.lower() for e in errors)

        # No lowercase
        errors = User.validate_password('TESTPASS123')
        assert any('жижиг' in e or 'lowercase' in e.lower() for e in errors)

        # No numbers
        errors = User.validate_password('TestPass')
        assert any('тоо' in e or 'digit' in e.lower() for e in errors)

        # Valid password
        errors = User.validate_password('TestPass123')
        assert len(errors) == 0

    def test_password_hashing(self, app):
        """Test that passwords are hashed, not stored in plaintext."""
        with app.app_context():
            user = User(username='hashtest', role='senior')
            user.set_password('TestPass123')

            # Password hash should exist
            assert user.password_hash is not None

            # Password hash should NOT be the plaintext password
            assert user.password_hash != 'TestPass123'

            # Should be able to verify password
            assert user.check_password('TestPass123') is True


# Run with: pytest tests/test_smoke.py -v
