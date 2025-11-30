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


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    flask_app = create_app(TestConfig)

    with flask_app.app_context():
        _db.create_all()

        # Create test users
        users = [
            User(username='admin', role='admin'),
            User(username='himich', role='himich'),
            User(username='ahlah', role='ahlah'),
        ]
        for user in users:
            user.set_password('TestPass123')  # Meets password requirements: 8+ chars, uppercase, lowercase, number
            _db.session.add(user)

        _db.session.commit()

    yield flask_app

    with flask_app.app_context():
        _db.session.remove()
        _db.drop_all()


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
    client.post('/login', data={'username': 'himich', 'password': 'TestPass123'})
    yield client
    client.get('/logout')


@pytest.fixture
def auth_admin(client):
    """Login as admin user."""
    client.post('/login', data={'username': 'admin', 'password': 'TestPass123'})
    yield client
    client.get('/logout')
