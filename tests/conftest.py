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
        sample = Sample.query.filter_by(sample_code=unique_code).first()
        yield sample

        # Cleanup
        try:
            _db.session.delete(sample)
            _db.session.commit()
        except Exception:
            _db.session.rollback()
