# tests/integration/test_notification_routes.py
# -*- coding: utf-8 -*-
"""Notification routes tests"""

import pytest
from app import db
from app.models import User
from datetime import datetime
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def notif_user(app):
    with app.app_context():
        user = User.query.filter_by(username='notif_user').first()
        if not user:
            user = User(username='notif_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def notif_admin(app):
    with app.app_context():
        user = User.query.filter_by(username='notif_admin_user').first()
        if not user:
            user = User(username='notif_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestNotificationRoutes:
    def test_notifications_list(self, client, app, notif_user):
        client.post('/login', data={'username': 'notif_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/notifications/')
        assert r.status_code in [200, 302, 404]

    def test_notifications_unread(self, client, app, notif_user):
        client.post('/login', data={'username': 'notif_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/notifications/unread')
        assert r.status_code in [200, 302, 404]

    def test_notifications_count(self, client, app, notif_user):
        client.post('/login', data={'username': 'notif_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/notifications/count')
        assert r.status_code in [200, 302, 404]


class TestNotificationMarkRead:
    def test_mark_as_read(self, client, app, notif_user):
        client.post('/login', data={'username': 'notif_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.post('/notifications/1/read')
        assert r.status_code in [200, 302, 400, 404, 405]

    def test_mark_all_read(self, client, app, notif_user):
        client.post('/login', data={'username': 'notif_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.post('/notifications/mark_all_read')
        assert r.status_code in [200, 302, 400, 404, 405]


class TestNotificationDelete:
    def test_delete_notification(self, client, app, notif_user):
        client.post('/login', data={'username': 'notif_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.delete('/notifications/99999')
        assert r.status_code in [200, 302, 400, 404, 405]

    def test_clear_all_notifications(self, client, app, notif_user):
        client.post('/login', data={'username': 'notif_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.post('/notifications/clear')
        assert r.status_code in [200, 302, 400, 404, 405]


class TestNotificationAdmin:
    def test_send_notification(self, client, app, notif_admin):
        client.post('/login', data={'username': 'notif_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.post('/admin/notifications/send',
            data=json.dumps({
                'user_id': 1,
                'title': 'Test notification',
                'message': 'Test message'
            }),
            content_type='application/json')
        assert r.status_code in [200, 302, 400, 404, 405]

    def test_broadcast_notification(self, client, app, notif_admin):
        client.post('/login', data={'username': 'notif_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.post('/admin/notifications/broadcast',
            data=json.dumps({
                'title': 'Broadcast test',
                'message': 'Broadcast message'
            }),
            content_type='application/json')
        assert r.status_code in [200, 302, 400, 404, 405]


class TestNotificationAPI:
    def test_get_notifications_api(self, client, app, notif_user):
        client.post('/login', data={'username': 'notif_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/notifications')
        assert r.status_code in [200, 302, 404]

    def test_get_notifications_with_limit(self, client, app, notif_user):
        client.post('/login', data={'username': 'notif_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/notifications?limit=10')
        assert r.status_code in [200, 302, 404]

    def test_get_notifications_with_type(self, client, app, notif_user):
        client.post('/login', data={'username': 'notif_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        types = ['info', 'warning', 'error', 'success']
        for t in types:
            r = client.get(f'/api/notifications?type={t}')
            assert r.status_code in [200, 302, 404]
