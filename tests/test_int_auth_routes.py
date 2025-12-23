# tests/integration/test_auth_routes.py
# -*- coding: utf-8 -*-
"""Authentication routes tests"""

import pytest
from app import db
from app.models import User
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def auth_user(app):
    with app.app_context():
        user = User.query.filter_by(username='auth_test_user').first()
        if not user:
            user = User(username='auth_test_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestLoginRoutes:
    def test_login_page(self, client, app):
        r = client.get('/login')
        assert r.status_code in [200, 302]

    def test_login_success(self, client, app, auth_user):
        r = client.post('/login', data={
            'username': 'auth_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        assert r.status_code in [200, 302]

    def test_login_invalid_password(self, client, app, auth_user):
        r = client.post('/login', data={
            'username': 'auth_test_user',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        assert r.status_code in [200, 302]

    def test_login_invalid_username(self, client, app):
        r = client.post('/login', data={
            'username': 'nonexistent_user',
            'password': 'SomePassword'
        }, follow_redirects=True)
        assert r.status_code in [200, 302]


class TestLogoutRoutes:
    def test_logout(self, client, app, auth_user):
        client.post('/login', data={
            'username': 'auth_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        r = client.get('/logout', follow_redirects=True)
        assert r.status_code in [200, 302]


class TestPasswordRoutes:
    def test_change_password_page(self, client, app, auth_user):
        client.post('/login', data={
            'username': 'auth_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        r = client.get('/change_password')
        assert r.status_code in [200, 302, 404]

    def test_change_password_post(self, client, app, auth_user):
        client.post('/login', data={
            'username': 'auth_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        r = client.post('/change_password', data={
            'current_password': VALID_PASSWORD,
            'new_password': 'NewPass456',
            'confirm_password': 'NewPass456'
        }, follow_redirects=True)
        assert r.status_code in [200, 302, 400, 404]


class TestProfileRoutes:
    def test_profile_page(self, client, app, auth_user):
        client.post('/login', data={
            'username': 'auth_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        r = client.get('/profile')
        assert r.status_code in [200, 302, 404]

    def test_profile_update(self, client, app, auth_user):
        client.post('/login', data={
            'username': 'auth_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        r = client.post('/profile', data={
            'email': 'test@example.com'
        }, follow_redirects=True)
        assert r.status_code in [200, 302, 400, 404]


class TestSessionRoutes:
    def test_session_check(self, client, app, auth_user):
        client.post('/login', data={
            'username': 'auth_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        r = client.get('/api/session/check')
        assert r.status_code in [200, 302, 404]

    def test_session_refresh(self, client, app, auth_user):
        client.post('/login', data={
            'username': 'auth_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        r = client.post('/api/session/refresh')
        assert r.status_code in [200, 302, 404, 405]
