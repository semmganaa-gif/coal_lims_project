import pytest
from app import create_app, db as _db
from app.models import User, Sample, Equipment, AnalysisResult, AnalysisType
from config import Config


class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'

    # SQLite-д pool тохиргоо хэрэггүй - хоослох
    SQLALCHEMY_ENGINE_OPTIONS = {}

    # Rate limiting идэвхгүй болгох (тест орчинд)
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_DEFAULT = "10000 per minute"  # Маш өндөр хязгаар

    # Mail идэвхгүй болгох
    MAIL_SUPPRESS_SEND = True


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    flask_app = create_app(TestConfig)

    with flask_app.app_context():
        _db.create_all()

        # Create test users
        users = [
            User(username='admin', role='admin'),
            User(username='chemist', role='chemist'),
            User(username='senior', role='senior'),
        ]
        for user in users:
            user.set_password('TestPass123')  # Meets password requirements: 8+ chars, uppercase, lowercase, number
            _db.session.add(user)

        _db.session.commit()

    yield flask_app

    # Cleanup: properly close all database connections
    with flask_app.app_context():
        _db.session.remove()
        _db.drop_all()
        _db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    """Database fixture."""
    with app.app_context():
        yield _db


@pytest.fixture
def auth_user(client):
    """Login as regular user."""
    client.post('/login', data={'username': 'chemist', 'password': 'TestPass123'})
    yield client
    client.get('/logout')


@pytest.fixture
def auth_admin(client):
    """Login as admin user."""
    client.post('/login', data={'username': 'admin', 'password': 'TestPass123'})
    yield client
    client.get('/logout')


class AuthActions:
    """Authentication helper for tests."""
    def __init__(self, client):
        self._client = client

    def login(self, username='chemist', password='TestPass123'):
        return self._client.post('/login', data={
            'username': username,
            'password': password
        })

    def logout(self):
        return self._client.get('/logout')


@pytest.fixture
def auth(client):
    """Authentication fixture with login/logout methods."""
    return AuthActions(client)


@pytest.fixture
def test_user(app):
    """Get test user fixture."""
    with app.app_context():
        user = User.query.filter_by(username='chemist').first()
        yield user


@pytest.fixture
def test_sample(app, test_user):
    """Create a test sample fixture."""
    import uuid
    with app.app_context():
        user = User.query.filter_by(username='chemist').first()
        unique_code = f"TEST-{uuid.uuid4().hex[:8]}"
        sample = Sample(
            sample_code=unique_code,
            user_id=user.id,
            client_name="QC",
            sample_type="Нүүрс"
        )
        _db.session.add(sample)
        _db.session.commit()

        # Re-query to get attached object
        # Note: sample_code is uppercased by model validation
        sample = Sample.query.filter_by(sample_code=unique_code.upper()).first()
        yield sample

        # Cleanup
        try:
            _db.session.delete(sample)
            _db.session.commit()
        except Exception:
            _db.session.rollback()


# =============================================================================
# Integration Test Fixtures
# =============================================================================

class AuthClient:
    """Extended auth client for integration tests."""

    def __init__(self, client):
        self._client = client

    def login(self, username='chemist', password='TestPass123'):
        """Login as regular user."""
        return self._client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def login_as_admin(self, username='admin', password='TestPass123'):
        """Login as admin user."""
        return self._client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def logout(self):
        """Logout current user."""
        return self._client.get('/logout', follow_redirects=True)


@pytest.fixture
def auth_client(client):
    """Authentication client for integration tests."""
    return AuthClient(client)


@pytest.fixture
def init_database(app):
    """Initialize database with test data."""
    import uuid
    with app.app_context():
        # Create some test samples
        user = User.query.filter_by(username='chemist').first()
        if user:
            samples = []
            for i in range(3):
                unique_code = f"INIT-{uuid.uuid4().hex[:6]}"
                sample = Sample(
                    sample_code=unique_code,
                    user_id=user.id,
                    client_name="QC",
                    sample_type="Нүүрс"
                )
                samples.append(sample)
                _db.session.add(sample)

            _db.session.commit()

            yield samples

            # Cleanup
            for sample in samples:
                try:
                    _db.session.delete(sample)
                except Exception:
                    pass
            _db.session.commit()
        else:
            yield []


class SampleFactory:
    """Factory for creating test samples."""

    def __init__(self, app, db):
        self.app = app
        self.db = db
        self.created_samples = []

    def create(self, **kwargs):
        """Create a sample with given attributes."""
        import uuid
        with self.app.app_context():
            user = User.query.filter_by(username='chemist').first()
            defaults = {
                'sample_code': f"FAC-{uuid.uuid4().hex[:6]}",
                'user_id': user.id if user else 1,
                'client_name': 'QC',
                'sample_type': 'Нүүрс'
            }
            defaults.update(kwargs)
            sample = Sample(**defaults)
            self.db.session.add(sample)
            self.db.session.commit()
            self.created_samples.append(sample.id)
            return sample

    def cleanup(self):
        """Remove all created samples."""
        with self.app.app_context():
            for sample_id in self.created_samples:
                sample = Sample.query.get(sample_id)
                if sample:
                    try:
                        self.db.session.delete(sample)
                    except Exception:
                        pass
            self.db.session.commit()


@pytest.fixture
def sample_factory(app, db):
    """Sample factory fixture."""
    factory = SampleFactory(app, db)
    yield factory
    factory.cleanup()
