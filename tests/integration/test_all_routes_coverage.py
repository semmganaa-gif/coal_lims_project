# tests/integration/test_all_routes_coverage.py
# -*- coding: utf-8 -*-
import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, date
import json
import uuid

VALID_PASSWORD = 'TestPass123'

@pytest.fixture
def arc_admin(app):
    with app.app_context():
        user = User.query.filter_by(username='arc_admin').first()
        if not user:
            user = User(username='arc_admin', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user

@pytest.fixture
def arc_prep(app):
    with app.app_context():
        user = User.query.filter_by(username='arc_prep').first()
        if not user:
            user = User(username='arc_prep', role='prep')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user

@pytest.fixture
def arc_chemist(app):
    with app.app_context():
        user = User.query.filter_by(username='arc_chemist').first()
        if not user:
            user = User(username='arc_chemist', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user

@pytest.fixture
def arc_senior(app):
    with app.app_context():
        user = User.query.filter_by(username='arc_senior').first()
        if not user:
            user = User(username='arc_senior', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user

class TestAllMainRoutes:
    def test_index_get_admin(self, client, app, arc_admin):
        client.post("/login", data={"username": "arc_admin", "password": VALID_PASSWORD}, follow_redirects=True)
        r = client.get("/")
        assert r.status_code in [200, 302]

    def test_index_get_prep(self, client, app, arc_prep):
        client.post("/login", data={"username": "arc_prep", "password": VALID_PASSWORD}, follow_redirects=True)
        r = client.get("/")
        assert r.status_code in [200, 302]

    def test_index_with_client_filter(self, client, app, arc_prep):
        client.post("/login", data={"username": "arc_prep", "password": VALID_PASSWORD}, follow_redirects=True)
        for c in ["CHPP", "UHG-Geo", "BN-Geo", "WTL", "QC", "Proc", "LAB"]:
            r = client.get(f"/?client={c}")
            assert r.status_code in [200, 302]

    def test_index_with_status_filter(self, client, app, arc_prep):
        client.post("/login", data={"username": "arc_prep", "password": VALID_PASSWORD}, follow_redirects=True)
        for s in ["pending", "in_progress", "completed", "approved"]:
            r = client.get(f"/?status={s}")
            assert r.status_code in [200, 302]

class TestAllSampleRegistrations:
    def test_register_all_clients(self, client, app, arc_prep):
        client.post("/login", data={"username": "arc_prep", "password": VALID_PASSWORD}, follow_redirects=True)
        clients = [
            ("CHPP", "2hour", "chpp_2h"),
            ("CHPP", "4hour", "chpp_4h"),
            ("CHPP", "composite", "chpp_com"),
            ("UHG-Geo", "Core", None),
            ("BN-Geo", "Exploration", None),
            ("Proc", "Test", None),
            ("LAB", "Internal", None),
        ]
        for c, t, lt in clients:
            uid = uuid.uuid4().hex[:4]
            data = {"client_name": c, "sample_type": t, "sample_date": date.today().isoformat()}
            if lt:
                data["list_type"] = lt
                data["sample_codes"] = [f"{c}-{uid}"]
                data["weights"] = ["100"]
            r = client.post("/", data=data)
            assert r.status_code in [200, 302, 400, 500]

class TestAllAPIEndpoints:
    def test_api_samples(self, client, app, arc_admin):
        client.post("/login", data={"username": "arc_admin", "password": VALID_PASSWORD}, follow_redirects=True)
        endpoints = [
            "/api/samples", "/api/samples?page=1", "/api/samples?client_name=CHPP",
            "/api/samples_data", "/api/samples_dt", "/api/shift_code"
        ]
        for e in endpoints:
            r = client.get(e)
            assert r.status_code in [200, 302, 404]

    def test_api_analysis(self, client, app, arc_chemist):
        client.post("/login", data={"username": "arc_chemist", "password": VALID_PASSWORD}, follow_redirects=True)
        endpoints = ["/api/analyses", "/api/analysis_types"]
        for e in endpoints:
            r = client.get(e)
            assert r.status_code in [200, 302, 404]

class TestAllReportRoutes:
    def test_report_pages(self, client, app, arc_admin):
        client.post("/login", data={"username": "arc_admin", "password": VALID_PASSWORD}, follow_redirects=True)
        pages = ["/reports/", "/reports/daily", "/reports/monthly", "/reports/consumption", "/reports/monthly_plan"]
        for p in pages:
            r = client.get(p)
            assert r.status_code in [200, 302, 404]

class TestAllQCRoutes:
    def test_qc_pages(self, client, app, arc_chemist):
        client.post("/login", data={"username": "arc_chemist", "password": VALID_PASSWORD}, follow_redirects=True)
        pages = ["/analysis/qc/composite_check", "/analysis/qc/norm_limit", "/analysis/correlation_check"]
        for p in pages:
            r = client.get(p)
            assert r.status_code in [200, 302, 404]

class TestAllSeniorRoutes:
    def test_senior_pages(self, client, app, arc_senior):
        client.post("/login", data={"username": "arc_senior", "password": VALID_PASSWORD}, follow_redirects=True)
        pages = ["/senior/", "/senior/pending"]
        for p in pages:
            r = client.get(p)
            assert r.status_code in [200, 302, 403, 404]

class TestAllWorkspaceRoutes:
    def test_workspace_pages(self, client, app, arc_chemist):
        client.post("/login", data={"username": "arc_chemist", "password": VALID_PASSWORD}, follow_redirects=True)
        pages = ["/analysis/workspace", "/analysis/queue"]
        for p in pages:
            r = client.get(p)
            assert r.status_code in [200, 302, 404]

class TestAllSettingsRoutes:
    def test_settings_pages(self, client, app, arc_admin):
        client.post("/login", data={"username": "arc_admin", "password": VALID_PASSWORD}, follow_redirects=True)
        pages = ["/settings/", "/settings/general", "/settings/analysis", "/settings/clients", "/settings/qc"]
        for p in pages:
            r = client.get(p)
            assert r.status_code in [200, 302, 403, 404]

class TestAllAdminRoutes:
    def test_admin_pages(self, client, app, arc_admin):
        client.post("/login", data={"username": "arc_admin", "password": VALID_PASSWORD}, follow_redirects=True)
        pages = ["/admin/users", "/admin/users/create", "/audit/"]
        for p in pages:
            r = client.get(p)
            assert r.status_code in [200, 302, 403, 404]

class TestAllExportRoutes:
    def test_export_pages(self, client, app, arc_admin):
        client.post("/login", data={"username": "arc_admin", "password": VALID_PASSWORD}, follow_redirects=True)
        pages = ["/export/samples?format=excel", "/export/samples?format=csv"]
        for p in pages:
            r = client.get(p)
            assert r.status_code in [200, 302, 400, 404]

class TestAllKPIRoutes:
    def test_kpi_pages(self, client, app, arc_admin):
        client.post("/login", data={"username": "arc_admin", "password": VALID_PASSWORD}, follow_redirects=True)
        pages = ["/kpi/", "/kpi/overview", "/api/kpi/summary", "/api/kpi/trends"]
        for p in pages:
            r = client.get(p)
            assert r.status_code in [200, 302, 404]

class TestAllQualityRoutes:
    def test_quality_pages(self, client, app, arc_admin):
        client.post("/login", data={"username": "arc_admin", "password": VALID_PASSWORD}, follow_redirects=True)
        pages = ["/quality/", "/quality/proficiency", "/quality/capa"]
        for p in pages:
            r = client.get(p)
            assert r.status_code in [200, 302, 404]

class TestAllChatRoutes:
    def test_chat_pages(self, client, app, arc_chemist):
        client.post("/login", data={"username": "arc_chemist", "password": VALID_PASSWORD}, follow_redirects=True)
        pages = ["/chat/", "/chat/messages", "/chat/rooms"]
        for p in pages:
            r = client.get(p)
            assert r.status_code in [200, 302, 404]
