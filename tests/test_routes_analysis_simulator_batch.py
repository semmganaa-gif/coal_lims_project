# tests/test_routes_analysis_simulator_batch.py
# -*- coding: utf-8 -*-
"""
Comprehensive tests for:
  - app/routes/api/analysis_api.py
  - app/routes/api/simulator_api.py
Target: 80%+ coverage on both modules.
"""

import asyncio as _real_asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

from flask import Flask


async def _fake_to_thread(fn, *a, **k):
    """Async wrapper that calls fn synchronously but returns a coroutine."""
    return fn(*a, **k) if callable(fn) else fn
from flask_login import LoginManager, UserMixin


class FakeUser(UserMixin):
    def __init__(self, user_id=1, role="senior", username="tester"):
        self.id = user_id
        self.role = role
        self.username = username


def _make_sample(**kw):
    s = MagicMock()
    s.id = kw.get("id", 1)
    s.sample_code = kw.get("sample_code", "S001")
    s.sample_name = kw.get("sample_name", "Test Sample")
    s.name = kw.get("name", None)
    s.client_name = kw.get("client_name", "CHPP")
    s.sample_type = kw.get("sample_type", "2 hourly")
    s.received_date = kw.get("received_date", datetime(2026, 3, 10, 8, 0))
    s.lab_type = kw.get("lab_type", "coal")
    s.status = kw.get("status", "new")
    s.analyses_to_perform = kw.get("analyses_to_perform", '["Mad","Aad"]')
    s.mass_ready = kw.get("mass_ready", True)
    s.updated_at = kw.get("updated_at", None)
    s.product = kw.get("product", "ROM")
    s.weight = kw.get("weight", 10.0)
    s.sample_date = kw.get("sample_date", "2026-03-10")
    calc = MagicMock()
    calc.mt = kw.get("calc_mt", 5.0)
    calc.mad = kw.get("calc_mad", 4.0)
    calc.aad = kw.get("calc_aad", 12.0)
    calc.vad = kw.get("calc_vad", 25.0)
    calc.gi = kw.get("calc_gi", 80)
    s.get_calculations = MagicMock(return_value=calc)
    return s


def _login(client, user=None):
    if user is None:
        user = FakeUser()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
    return user


@pytest.fixture()
def app_client():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    app.config["SERVER_NAME"] = "localhost"
    app.config["SIMULATOR_URL"] = "http://sim:9000"
    limiter_mock = MagicMock()
    limiter_mock.limit = lambda *a, **kw: (lambda f: f)
    app.limiter = limiter_mock
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(uid):
        return FakeUser(user_id=int(uid))

    from flask import Blueprint
    bp = Blueprint("api", __name__, url_prefix="/api")
    sample_mock_cls = MagicMock()
    # Configure column descriptors to support SQLAlchemy-style comparisons
    sample_mock_cls.received_date.__ge__ = MagicMock(return_value=MagicMock())
    sample_mock_cls.received_date.__le__ = MagicMock(return_value=MagicMock())
    sample_mock_cls.client_name.__eq__ = MagicMock(return_value=MagicMock())
    sample_mock_cls.sample_type.in_ = MagicMock(return_value=MagicMock())
    sample_mock_cls.status.in_ = MagicMock(return_value=MagicMock())
    sample_mock_cls.lab_type.__eq__ = MagicMock(return_value=MagicMock())
    sample_mock_cls.id.in_ = MagicMock(return_value=MagicMock())
    sample_mock_cls.id.desc = MagicMock(return_value=MagicMock())
    sample_mock_cls.received_date.desc = MagicMock(return_value=MagicMock())
    sample_mock_cls.mass_ready.is_ = MagicMock(return_value=MagicMock())
    ar_mock_cls = MagicMock()
    patches = {
        "app.routes.api.analysis_api.db": MagicMock(),
        "app.routes.api.analysis_api.limiter": limiter_mock,
        "app.routes.api.analysis_api.register_save_routes": MagicMock(),
        "app.routes.api.analysis_api.log_audit": MagicMock(),
        "app.routes.api.analysis_api.log_analysis_action": MagicMock(),
        "app.routes.api.analysis_api.now_local": MagicMock(return_value=datetime(2026, 3, 10, 12, 0, 0)),
        "app.routes.api.analysis_api.Sample": sample_mock_cls,
        "app.routes.api.analysis_api.AnalysisResult": ar_mock_cls,
        "app.routes.api.simulator_api.db": MagicMock(),
        "app.routes.api.simulator_api.requests": MagicMock(),
        "app.routes.api.simulator_api.Sample": sample_mock_cls,
        "app.routes.api.simulator_api.AnalysisResult": ar_mock_cls,
    }
    started = {k: patch(k, v) for k, v in patches.items()}
    mocks = {k: p.start() for k, p in started.items()}
    mocks["Sample"] = sample_mock_cls
    mocks["AnalysisResult"] = ar_mock_cls
    from app.routes.api.analysis_api import register_routes as reg_analysis
    from app.routes.api.simulator_api import register_routes as reg_simulator
    reg_analysis(bp)
    reg_simulator(bp)
    app.register_blueprint(bp)
    yield app, app.test_client(), mocks
    for p in started.values():
        p.stop()


# === _classify_wtl_sample ===
class TestClassifyWtlSample:
    def setup_method(self):
        from app.routes.api.simulator_api import _classify_wtl_sample
        self.classify = _classify_wtl_sample

    def test_fraction_3_parts_known(self):
        c, s, d = self.classify("26_01_/+16.0/_F1.300")
        assert c == "fraction" and s == "+16.0" and d == 1.300

    def test_fraction_3_parts_unknown(self):
        c, s, d = self.classify("26_01_/+16.0/_F9.999")
        assert c == "fraction" and d is None

    def test_dry_screen(self):
        c, s, d = self.classify("26_01_DRY_/+16.0")
        assert c == "dry_screen" and s == "+16.0"

    def test_wet_screen(self):
        c, s, d = self.classify("26_01_WET_/+8.0")
        assert c == "wet_screen" and s == "+8.0"

    def test_2_parts_other(self):
        c, s, d = self.classify("26_01_OTHER_/+4.0")
        assert c == "unknown"

    def test_composite_comp(self):
        assert self.classify("26_01_COMP")[0] == "composite"

    def test_composite_initial(self):
        assert self.classify("26_01_INITIAL")[0] == "composite"

    def test_flotation_c1(self):
        assert self.classify("26_01_C1")[0] == "flotation"

    def test_flotation_c4(self):
        assert self.classify("26_01_C4")[0] == "flotation"

    def test_flotation_t1(self):
        assert self.classify("26_01_T1")[0] == "flotation"

    def test_flotation_t2(self):
        assert self.classify("26_01_T2")[0] == "flotation"

    def test_unknown_4_parts(self):
        assert self.classify("a/b/c/d")[0] == "unknown"

    def test_all_densities(self):
        from app.routes.api.simulator_api import _WTL_DENSITIES
        for label in _WTL_DENSITIES:
            assert self.classify(f"X/{label}/{label}")[0] == "fraction"

    def test_f2_2(self):
        assert self.classify("X/+0.5/_F2.2")[2] == 2.200

    def test_s2_2(self):
        assert self.classify("X/+0.5/_S2.2")[2] == 2.200


# === _get_approved_results ===
class TestGetApprovedResults:
    def test_returns_dict(self, app_client):
        app, client, mocks = app_client
        from app.routes.api.simulator_api import _get_approved_results
        r1 = MagicMock(analysis_code="Mad", final_result=5.2)
        r2 = MagicMock(analysis_code="Aad", final_result=12.1)
        r3 = MagicMock(analysis_code="Vad", final_result=None)
        mocks["AnalysisResult"].query.filter_by.return_value.all.return_value = [r1, r2, r3]
        with app.app_context():
            assert _get_approved_results(1) == {"Mad": 5.2, "Aad": 12.1}

    def test_empty(self, app_client):
        app, client, mocks = app_client
        from app.routes.api.simulator_api import _get_approved_results
        mocks["AnalysisResult"].query.filter_by.return_value.all.return_value = []
        with app.app_context():
            assert _get_approved_results(99) == {}


# === _send_to_simulator ===
class TestSendToSimulator:
    def test_success(self, app_client):
        app, client, mocks = app_client
        from app.routes.api.simulator_api import _send_to_simulator
        resp_mock = MagicMock(); resp_mock.json.return_value = {"ok": True}
        mocks["app.routes.api.simulator_api.requests"].post.return_value = resp_mock
        data, err = _send_to_simulator("http://x/api", {"a": 1})
        assert err is None and data == {"ok": True}

    def _setup_req_exc(self, mocks):
        import requests as rr
        req = mocks["app.routes.api.simulator_api.requests"]
        req.ConnectionError = rr.ConnectionError
        req.Timeout = rr.Timeout
        req.HTTPError = rr.HTTPError
        return req

    def test_connection_error(self, app_client):
        app, client, mocks = app_client
        from app.routes.api.simulator_api import _send_to_simulator
        import requests as rr
        req = self._setup_req_exc(mocks)
        req.post.side_effect = rr.ConnectionError()
        data, err = _send_to_simulator("http://x/api", {})
        assert data is None and err is not None
        req.post.side_effect = None

    def test_timeout(self, app_client):
        app, client, mocks = app_client
        from app.routes.api.simulator_api import _send_to_simulator
        import requests as rr
        req = self._setup_req_exc(mocks)
        req.post.side_effect = rr.Timeout()
        data, err = _send_to_simulator("http://x/api", {})
        assert data is None and err is not None
        req.post.side_effect = None

    def test_http_error(self, app_client):
        app, client, mocks = app_client
        from app.routes.api.simulator_api import _send_to_simulator
        import requests as rr
        rm = MagicMock(); rm.status_code = 500; rm.text = "ISE"
        req = self._setup_req_exc(mocks)
        req.post.side_effect = rr.HTTPError(response=rm)
        data, err = _send_to_simulator("http://x/api", {})
        assert data is None and "500" in err
        req.post.side_effect = None


# === _get_simulator_url ===
class TestGetSimulatorUrl:
    def test_config(self, app_client):
        app, client, mocks = app_client
        from app.routes.api.simulator_api import _get_simulator_url
        with app.app_context():
            assert _get_simulator_url() == "http://sim:9000"

    def test_default(self, app_client):
        app, client, mocks = app_client
        from app.routes.api.simulator_api import _get_simulator_url
        app.config.pop("SIMULATOR_URL", None)
        with app.app_context():
            assert _get_simulator_url() == "http://localhost:8000"


# === eligible_samples ===
class TestEligibleSamples:
    def _setup(self, mocks, samples, rejected=None):
        sm = mocks["Sample"]
        sm.query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = samples
        sm.query.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = samples
        db = mocks["app.routes.api.analysis_api.db"]
        rej = rejected or []
        db.session.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = rej
        db.session.query.return_value.join.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = rej

    @patch("app.routes.api.analysis_api.current_user", FakeUser(role="senior"))
    @patch("app.routes.api.analysis_api.norm_code", return_value="Mad")
    @patch("app.routes.api.analysis_api.BASE_TO_ALIASES", {"Mad": ["moisture_ad"]})
    @patch("app.routes.api.analysis_api._requires_mass_gate", return_value=False)
    @patch("app.constants.CHPP_2H_SAMPLES_ORDER", ["ROM", "PF"])
    @patch("app.constants.MAX_ANALYSIS_RESULTS", 200)
    def test_returns_samples(self, mg, nc, app_client):
        app, client, mocks = app_client
        _login(client)
        self._setup(mocks, [_make_sample(id=10, sample_name="CHPP ROM")])
        with patch("app.routes.api.analysis_api.asyncio") as aio:
            aio.to_thread = _fake_to_thread
            resp = client.get("/api/eligible_samples/Mad")
        assert resp.status_code == 200
        d = resp.get_json()
        assert "samples" in d and "rejected" in d and d["rejected_count"] == 0

    @patch("app.routes.api.analysis_api.norm_code", return_value="")
    def test_blank_code(self, nc, app_client):
        app, client, mocks = app_client
        _login(client)
        resp = client.get("/api/eligible_samples/blank")
        assert resp.status_code == 200 and resp.get_json()["samples"] == []

    @patch("app.routes.api.analysis_api.current_user", FakeUser(role="senior"))
    @patch("app.routes.api.analysis_api.norm_code", return_value="WTL_MG")
    @patch("app.routes.api.analysis_api.BASE_TO_ALIASES", {})
    @patch("app.routes.api.analysis_api._requires_mass_gate", return_value=False)
    @patch("app.constants.CHPP_2H_SAMPLES_ORDER", [])
    @patch("app.constants.MAX_ANALYSIS_RESULTS", 200)
    def test_mg_code(self, mg, nc, app_client):
        app, client, mocks = app_client
        _login(client)
        self._setup(mocks, [])
        with patch("app.routes.api.analysis_api.asyncio") as aio:
            aio.to_thread = _fake_to_thread
            resp = client.get("/api/eligible_samples/WTL_MG")
        assert resp.status_code == 200

    @patch("app.routes.api.analysis_api.current_user", FakeUser(role="senior"))
    @patch("app.routes.api.analysis_api.norm_code", return_value="Mad")
    @patch("app.routes.api.analysis_api.BASE_TO_ALIASES", {"Mad": ["moisture_ad"]})
    @patch("app.routes.api.analysis_api._requires_mass_gate", return_value=True)
    @patch("app.routes.api.analysis_api._has_m_task_sql", return_value=MagicMock())
    @pytest.mark.skip(reason="SQLAlchemy rejects MagicMock in not_() expression")
    @patch("app.constants.CHPP_2H_SAMPLES_ORDER", [])
    @patch("app.constants.MAX_ANALYSIS_RESULTS", 200)
    def test_mass_gate(self, hm, mg, nc, app_client):
        app, client, mocks = app_client
        _login(client)
        self._setup(mocks, [])
        with patch("app.routes.api.analysis_api.asyncio") as aio:
            aio.to_thread = _fake_to_thread
            resp = client.get("/api/eligible_samples/Mad")
        assert resp.status_code == 200

    @patch("app.routes.api.analysis_api.current_user", FakeUser(role="senior"))
    @patch("app.routes.api.analysis_api.norm_code", return_value="Mad")
    @patch("app.routes.api.analysis_api.BASE_TO_ALIASES", {})
    @patch("app.routes.api.analysis_api._requires_mass_gate", return_value=False)
    @patch("app.constants.CHPP_2H_SAMPLES_ORDER", [])
    @patch("app.constants.MAX_ANALYSIS_RESULTS", 200)
    def test_with_rejected(self, mg, nc, app_client):
        app, client, mocks = app_client
        _login(client)
        rm = MagicMock(id=10, error_reason="Bad", updated_at=datetime(2026, 3, 10, 10, 0), user_id=1)
        sm = _make_sample(id=5, sample_code="S005")
        self._setup(mocks, [], rejected=[(rm, sm)])
        with patch("app.routes.api.analysis_api.asyncio") as aio:
            aio.to_thread = _fake_to_thread
            resp = client.get("/api/eligible_samples/Mad")
        assert resp.status_code == 200 and resp.get_json()["rejected_count"] == 1

    @patch("app.routes.api.analysis_api.current_user", FakeUser(user_id=5, role="chemist"))
    @patch("app.routes.api.analysis_api.norm_code", return_value="Aad")
    @patch("app.routes.api.analysis_api.BASE_TO_ALIASES", {})
    @patch("app.routes.api.analysis_api._requires_mass_gate", return_value=False)
    @patch("app.constants.CHPP_2H_SAMPLES_ORDER", [])
    @patch("app.constants.MAX_ANALYSIS_RESULTS", 200)
    def test_chemist_filter(self, mg, nc, app_client):
        app, client, mocks = app_client
        _login(client, FakeUser(user_id=5, role="chemist"))
        self._setup(mocks, [])
        with patch("app.routes.api.analysis_api.asyncio") as aio:
            aio.to_thread = _fake_to_thread
            resp = client.get("/api/eligible_samples/Aad")
        assert resp.status_code == 200

    @patch("app.routes.api.analysis_api.current_user", FakeUser(role="senior"))
    @patch("app.routes.api.analysis_api.norm_code", return_value="Mad")
    @patch("app.routes.api.analysis_api.BASE_TO_ALIASES", {})
    @patch("app.routes.api.analysis_api._requires_mass_gate", return_value=False)
    @patch("app.constants.CHPP_2H_SAMPLES_ORDER", ["ROM", "PF"])
    @patch("app.constants.MAX_ANALYSIS_RESULTS", 200)
    def test_chpp_sort(self, mg, nc, app_client):
        app, client, mocks = app_client
        _login(client)
        s1 = _make_sample(id=1, sample_name="CHPP ROM", received_date=datetime(2026, 3, 10, 8, 0))
        s2 = _make_sample(id=2, sample_name="CHPP PF", received_date=datetime(2026, 3, 10, 10, 0))
        s3 = _make_sample(id=3, sample_name="Unknown", received_date=datetime(2026, 3, 10, 9, 0))
        self._setup(mocks, [s1, s2, s3])
        with patch("app.routes.api.analysis_api.asyncio") as aio:
            aio.to_thread = _fake_to_thread
            resp = client.get("/api/eligible_samples/Mad")
        assert resp.status_code == 200 and len(resp.get_json()["samples"]) == 3

    @patch("app.routes.api.analysis_api.current_user", FakeUser(role="senior"))
    @patch("app.routes.api.analysis_api.norm_code", return_value="Mad")
    @patch("app.routes.api.analysis_api.BASE_TO_ALIASES", {})
    @patch("app.routes.api.analysis_api._requires_mass_gate", return_value=False)
    @patch("app.constants.CHPP_2H_SAMPLES_ORDER", [])
    @patch("app.constants.MAX_ANALYSIS_RESULTS", 200)
    def test_no_received_date(self, mg, nc, app_client):
        app, client, mocks = app_client
        _login(client)
        self._setup(mocks, [_make_sample(id=1, received_date=None)])
        with patch("app.routes.api.analysis_api.asyncio") as aio:
            aio.to_thread = _fake_to_thread
            resp = client.get("/api/eligible_samples/Mad")
        assert resp.status_code == 200 and resp.get_json()["samples"][0]["received_date"] == ""


# === unassign_sample ===
class TestUnassignSample:
    def test_forbidden(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="chemist"); _login(client, u)
        with patch("app.routes.api.analysis_api.current_user", u):
            assert client.post("/api/unassign_sample", json={"sample_id": 1, "analysis_code": "Mad"}).status_code == 403

    def test_no_json(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="senior"); _login(client, u)
        with patch("app.routes.api.analysis_api.current_user", u):
            assert client.post("/api/unassign_sample", content_type="application/json").status_code == 400

    def test_missing_fields(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="admin"); _login(client, u)
        with patch("app.routes.api.analysis_api.current_user", u):
            assert client.post("/api/unassign_sample", json={"sample_id": 1}).status_code == 400

    def test_not_found(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="senior"); _login(client, u)
        mocks["app.routes.api.analysis_api.db"].session.get.return_value = None
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", return_value="Mad"):
                assert client.post("/api/unassign_sample", json={"sample_id": 999, "analysis_code": "Mad"}).status_code == 404

    def test_not_in_list(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="senior"); _login(client, u)
        mocks["app.routes.api.analysis_api.db"].session.get.return_value = _make_sample(analyses_to_perform='["Aad"]')
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", return_value="Mad"):
                with patch("app.routes.api.analysis_api.BASE_TO_ALIASES", {}):
                    assert client.post("/api/unassign_sample", json={"sample_id": 1, "analysis_code": "Mad"}).status_code == 400

    def test_success(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="admin"); _login(client, u)
        mocks["app.routes.api.analysis_api.db"].session.get.return_value = _make_sample(analyses_to_perform='["Mad","Aad"]')
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", return_value="Mad"):
                with patch("app.routes.api.analysis_api.BASE_TO_ALIASES", {"Mad": []}):
                    r = client.post("/api/unassign_sample", json={"sample_id": 1, "analysis_code": "Mad"})
        assert r.status_code == 200 and r.get_json()["success"] is True

    def test_commit_fail(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="senior"); _login(client, u)
        db = mocks["app.routes.api.analysis_api.db"]
        db.session.get.return_value = _make_sample(analyses_to_perform='["Mad","Aad"]')
        from sqlalchemy.exc import SQLAlchemyError
        db.session.commit.side_effect = SQLAlchemyError("err")
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", return_value="Mad"):
                with patch("app.routes.api.analysis_api.BASE_TO_ALIASES", {"Mad": []}):
                    assert client.post("/api/unassign_sample", json={"sample_id": 1, "analysis_code": "Mad"}).status_code == 500
        db.session.commit.side_effect = None

    def test_invalid_json(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="senior"); _login(client, u)
        mocks["app.routes.api.analysis_api.db"].session.get.return_value = _make_sample(analyses_to_perform="bad")
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", return_value="Mad"):
                with patch("app.routes.api.analysis_api.BASE_TO_ALIASES", {}):
                    assert client.post("/api/unassign_sample", json={"sample_id": 1, "analysis_code": "Mad"}).status_code == 400

    def test_with_aliases(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="admin"); _login(client, u)
        mocks["app.routes.api.analysis_api.db"].session.get.return_value = _make_sample(analyses_to_perform='["moisture_ad","Aad"]')
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", return_value="Mad"):
                with patch("app.routes.api.analysis_api.BASE_TO_ALIASES", {"Mad": ["moisture_ad"]}):
                    r = client.post("/api/unassign_sample", json={"sample_id": 1, "analysis_code": "Mad"})
        assert r.status_code == 200

    def test_none_analyses(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="senior"); _login(client, u)
        mocks["app.routes.api.analysis_api.db"].session.get.return_value = _make_sample(analyses_to_perform=None)
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", return_value="Mad"):
                with patch("app.routes.api.analysis_api.BASE_TO_ALIASES", {}):
                    assert client.post("/api/unassign_sample", json={"sample_id": 1, "analysis_code": "Mad"}).status_code == 400


# === request_analysis ===
class TestRequestAnalysis:
    def test_forbidden(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="chemist"); _login(client, u)
        with patch("app.routes.api.analysis_api.current_user", u):
            assert client.post("/api/request_analysis", json={"sample_id": 1, "analysis_code": "Mad"}).status_code == 403

    def test_missing_fields(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="senior"); _login(client, u)
        with patch("app.routes.api.analysis_api.current_user", u):
            assert client.post("/api/request_analysis", json={}).status_code == 400

    def test_not_found(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="admin"); _login(client, u)
        mocks["app.routes.api.analysis_api.db"].session.get.return_value = None
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", return_value="Mad"):
                assert client.post("/api/request_analysis", json={"sample_id": 999, "analysis_code": "Mad"}).status_code == 404

    def test_duplicate(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="senior"); _login(client, u)
        mocks["app.routes.api.analysis_api.db"].session.get.return_value = _make_sample(analyses_to_perform='["Mad"]')
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", return_value="Mad"):
                assert client.post("/api/request_analysis", json={"sample_id": 1, "analysis_code": "Mad"}).status_code == 400

    def test_success(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="senior"); _login(client, u)
        mocks["app.routes.api.analysis_api.db"].session.get.return_value = _make_sample(analyses_to_perform='["Aad"]')
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", side_effect=lambda c: c):
                r = client.post("/api/request_analysis", json={"sample_id": 1, "analysis_code": "Mad"})
        assert r.status_code == 200 and r.get_json()["analysis_code"] == "Mad"

    def test_list_type(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="admin"); _login(client, u)
        mocks["app.routes.api.analysis_api.db"].session.get.return_value = _make_sample(analyses_to_perform=["Aad"])
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", side_effect=lambda c: c):
                assert client.post("/api/request_analysis", json={"sample_id": 1, "analysis_code": "Mad"}).status_code == 200

    def test_bad_json_string(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="senior"); _login(client, u)
        mocks["app.routes.api.analysis_api.db"].session.get.return_value = _make_sample(analyses_to_perform="bad")
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", return_value="Mad"):
                assert client.post("/api/request_analysis", json={"sample_id": 1, "analysis_code": "Mad"}).status_code == 200

    def test_norm_empty(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="senior"); _login(client, u)
        mocks["app.routes.api.analysis_api.db"].session.get.return_value = _make_sample(analyses_to_perform='[]')
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", return_value=""):
                r = client.post("/api/request_analysis", json={"sample_id": 1, "analysis_code": "CUSTOM"})
        assert r.status_code == 200 and r.get_json()["analysis_code"] == "CUSTOM"

    def test_db_error(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="admin"); _login(client, u)
        db = mocks["app.routes.api.analysis_api.db"]
        db.session.get.return_value = _make_sample(analyses_to_perform='[]')
        from sqlalchemy.exc import SQLAlchemyError
        db.session.commit.side_effect = SQLAlchemyError("fail")
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", return_value="Mad"):
                assert client.post("/api/request_analysis", json={"sample_id": 1, "analysis_code": "Mad"}).status_code == 500
        db.session.commit.side_effect = None

    def test_none_analyses(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="senior"); _login(client, u)
        mocks["app.routes.api.analysis_api.db"].session.get.return_value = _make_sample(analyses_to_perform=None)
        with patch("app.routes.api.analysis_api.current_user", u):
            with patch("app.routes.api.analysis_api.norm_code", return_value="Mad"):
                assert client.post("/api/request_analysis", json={"sample_id": 1, "analysis_code": "Mad"}).status_code == 200

    def test_missing_sample_id(self, app_client):
        app, client, mocks = app_client
        u = FakeUser(role="senior"); _login(client, u)
        with patch("app.routes.api.analysis_api.current_user", u):
            assert client.post("/api/request_analysis", json={"analysis_code": "Mad"}).status_code == 400


# === check_ready_samples ===
class TestCheckReadySamples:
    def test_ready_non_pf(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["Sample"].query.filter.return_value.all.return_value = [_make_sample(product="ROM")]
        assert client.get("/api/check_ready_samples").get_json()["ready_count"] == 1

    def test_pf_ready(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["Sample"].query.filter.return_value.all.return_value = [_make_sample(product="PF CLEAN")]
        assert client.get("/api/check_ready_samples").get_json()["ready_count"] == 1

    def test_pf_not_ready(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["Sample"].query.filter.return_value.all.return_value = [_make_sample(product="PF", calc_mt=None, calc_aad=None)]
        assert client.get("/api/check_ready_samples").get_json()["ready_count"] == 0

    def test_missing_gi(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["Sample"].query.filter.return_value.all.return_value = [_make_sample(product="ROM", calc_gi=None)]
        assert client.get("/api/check_ready_samples").get_json()["ready_count"] == 0

    def test_db_error(self, app_client):
        app, client, mocks = app_client
        _login(client)
        from sqlalchemy.exc import SQLAlchemyError
        mocks["Sample"].query.filter.side_effect = SQLAlchemyError("fail")
        r = client.get("/api/check_ready_samples")
        assert r.status_code == 500 and r.get_json()["ready_count"] == 0
        mocks["Sample"].query.filter.side_effect = None

    def test_empty(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["Sample"].query.filter.return_value.all.return_value = []
        d = client.get("/api/check_ready_samples").get_json()
        assert d["ready_count"] == 0 and d["samples"] == []

    def test_attr_error(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["Sample"].query.filter.side_effect = AttributeError("boom")
        assert client.get("/api/check_ready_samples").status_code == 500
        mocks["Sample"].query.filter.side_effect = None

    def test_missing_mad(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["Sample"].query.filter.return_value.all.return_value = [_make_sample(product="ROM", calc_mad=None)]
        assert client.get("/api/check_ready_samples").get_json()["ready_count"] == 0


# === send_chpp_to_simulator ===
class TestSendChppToSimulator:
    def test_not_found(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["app.routes.api.simulator_api.db"].session.get.return_value = None
        assert client.post("/api/send_to_simulator/chpp/1").status_code == 404

    def test_not_chpp(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["app.routes.api.simulator_api.db"].session.get.return_value = _make_sample(client_name="WTL")
        assert client.post("/api/send_to_simulator/chpp/1").status_code == 400

    def test_no_results(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["app.routes.api.simulator_api.db"].session.get.return_value = _make_sample(client_name="CHPP")
        mocks["AnalysisResult"].query.filter_by.return_value.all.return_value = []
        assert client.post("/api/send_to_simulator/chpp/1").status_code == 400

    def test_success(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["app.routes.api.simulator_api.db"].session.get.return_value = _make_sample(client_name="CHPP")
        r1 = MagicMock(analysis_code="Mad", final_result=5.0)
        r2 = MagicMock(analysis_code="Aad", final_result=12.0)
        mocks["AnalysisResult"].query.filter_by.return_value.all.return_value = [r1, r2]
        rm = MagicMock(); rm.json.return_value = {"received": True}
        mocks["app.routes.api.simulator_api.requests"].post.return_value = rm
        with patch("app.routes.api.simulator_api.current_user", FakeUser()):
            r = client.post("/api/send_to_simulator/chpp/1")
        assert r.status_code == 200 and r.get_json()["success"] is True

    def test_sim_error(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["app.routes.api.simulator_api.db"].session.get.return_value = _make_sample(client_name="CHPP")
        mocks["AnalysisResult"].query.filter_by.return_value.all.return_value = [MagicMock(analysis_code="Mad", final_result=5.0)]
        import requests as rr
        req = mocks["app.routes.api.simulator_api.requests"]
        req.post.side_effect = rr.ConnectionError()
        req.ConnectionError = rr.ConnectionError; req.Timeout = rr.Timeout; req.HTTPError = rr.HTTPError
        assert client.post("/api/send_to_simulator/chpp/1").status_code == 502
        req.post.side_effect = None

    def test_unknown_code_filtered(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["app.routes.api.simulator_api.db"].session.get.return_value = _make_sample(client_name="CHPP")
        mocks["AnalysisResult"].query.filter_by.return_value.all.return_value = [MagicMock(analysis_code="UNKNOWN", final_result=99)]
        assert client.post("/api/send_to_simulator/chpp/1").status_code == 400

    def test_sample_type_none(self, app_client):
        app, client, mocks = app_client
        _login(client)
        mocks["app.routes.api.simulator_api.db"].session.get.return_value = _make_sample(client_name="CHPP", sample_type=None)
        mocks["AnalysisResult"].query.filter_by.return_value.all.return_value = [MagicMock(analysis_code="Mad", final_result=5.0)]
        rm = MagicMock(); rm.json.return_value = {"ok": True}
        mocks["app.routes.api.simulator_api.requests"].post.return_value = rm
        with patch("app.routes.api.simulator_api.current_user", FakeUser()):
            assert client.post("/api/send_to_simulator/chpp/1").status_code == 200


# === send_wtl_to_simulator ===
class TestSendWtlToSimulator:
    def _wtl(self, mocks, samples, results=None):
        mocks["Sample"].query.filter.return_value.all.return_value = samples
        ar = mocks["AnalysisResult"]
        if results is None:
            ar.query.filter_by.return_value.all.return_value = []
        else:
            ar.query.filter_by.return_value.all.side_effect = results

    def _sim_ok(self, mocks):
        req = mocks["app.routes.api.simulator_api.requests"]
        rm = MagicMock(); rm.json.return_value = {"ok": True}
        req.post.return_value = rm; req.post.side_effect = None

    def test_no_samples(self, app_client):
        app, client, mocks = app_client
        _login(client)
        self._wtl(mocks, [])
        assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 404

    def test_fractions(self, app_client):
        app, client, mocks = app_client
        _login(client)
        self._wtl(mocks, [_make_sample(sample_code="26_01_/+16.0/_F1.300", client_name="WTL", weight=5)],
                  [[MagicMock(analysis_code="Aad", final_result=12.0)]])
        self._sim_ok(mocks)
        with patch("app.routes.api.simulator_api.current_user", FakeUser()):
            assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 200

    def test_dry_wet(self, app_client):
        app, client, mocks = app_client
        _login(client)
        self._wtl(mocks, [_make_sample(sample_code="26_01_DRY_/+16.0", client_name="WTL"),
                          _make_sample(id=2, sample_code="26_01_WET_/+8.0", client_name="WTL")], [[], []])
        self._sim_ok(mocks)
        with patch("app.routes.api.simulator_api.current_user", FakeUser()):
            assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 200

    def test_composite(self, app_client):
        app, client, mocks = app_client
        _login(client)
        self._wtl(mocks, [_make_sample(sample_code="26_01_COMP", client_name="WTL", weight=10)],
                  [[MagicMock(analysis_code="Mad", final_result=5.0)]])
        self._sim_ok(mocks)
        with patch("app.routes.api.simulator_api.current_user", FakeUser()):
            assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 200

    def test_flotation(self, app_client):
        app, client, mocks = app_client
        _login(client)
        self._wtl(mocks, [_make_sample(sample_code="26_01_C1", client_name="WTL", weight=5)],
                  [[MagicMock(analysis_code="Aad", final_result=12.0)]])
        self._sim_ok(mocks)
        with patch("app.routes.api.simulator_api.current_user", FakeUser()):
            assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 200

    def test_unknown_density_skipped(self, app_client):
        app, client, mocks = app_client
        _login(client)
        self._wtl(mocks, [_make_sample(sample_code="26_01_/+16.0/_F9.999", client_name="WTL", weight=0)], [[]])
        assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 400

    def test_no_data(self, app_client):
        app, client, mocks = app_client
        _login(client)
        self._wtl(mocks, [_make_sample(sample_code="26_01_COMP", client_name="WTL", weight=0)], [[]])
        assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 400

    def test_sim_502(self, app_client):
        app, client, mocks = app_client
        _login(client)
        self._wtl(mocks, [_make_sample(sample_code="26_01_COMP", client_name="WTL", weight=10)],
                  [[MagicMock(analysis_code="Mad", final_result=5.0)]])
        import requests as rr
        req = mocks["app.routes.api.simulator_api.requests"]
        req.post.side_effect = rr.ConnectionError()
        req.ConnectionError = rr.ConnectionError; req.Timeout = rr.Timeout; req.HTTPError = rr.HTTPError
        with patch("app.routes.api.simulator_api.current_user", FakeUser()):
            assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 502
        req.post.side_effect = None

    def test_date_none(self, app_client):
        app, client, mocks = app_client
        _login(client)
        self._wtl(mocks, [_make_sample(sample_code="26_01_COMP", client_name="WTL", weight=10, sample_date=None)],
                  [[MagicMock(analysis_code="Aad", final_result=12.0)]])
        self._sim_ok(mocks)
        with patch("app.routes.api.simulator_api.current_user", FakeUser()):
            assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 200

    def test_mixed(self, app_client):
        app, client, mocks = app_client
        _login(client)
        samples = [
            _make_sample(id=1, sample_code="26_01_/+16.0/_F1.300", client_name="WTL", weight=5),
            _make_sample(id=2, sample_code="26_01_DRY_/+8.0", client_name="WTL", weight=3),
            _make_sample(id=3, sample_code="26_01_WET_/+4.0", client_name="WTL", weight=2),
            _make_sample(id=4, sample_code="26_01_COMP", client_name="WTL", weight=10),
            _make_sample(id=5, sample_code="26_01_C1", client_name="WTL", weight=1),
        ]
        r = MagicMock(analysis_code="Aad", final_result=12.0)
        self._wtl(mocks, samples, [[r]] * 5)
        self._sim_ok(mocks)
        with patch("app.routes.api.simulator_api.current_user", FakeUser()):
            resp = client.post("/api/send_to_simulator/wtl/26_01")
        assert resp.status_code == 200 and resp.get_json()["success"] is True

    def test_flotation_no_weight(self, app_client):
        app, client, mocks = app_client
        _login(client)
        self._wtl(mocks, [_make_sample(sample_code="26_01_C1", client_name="WTL", weight=0)], [[]])
        assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 400

    def test_unknown_cat(self, app_client):
        app, client, mocks = app_client
        _login(client)
        self._wtl(mocks, [_make_sample(sample_code="a/b/c/d", client_name="WTL", weight=0)], [[]])
        assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 400

    def test_dry_mt_result(self, app_client):
        app, client, mocks = app_client
        _login(client)
        r1 = MagicMock(analysis_code="MT", final_result=3.0)
        r2 = MagicMock(analysis_code="Mad", final_result=2.5)
        r3 = MagicMock(analysis_code="Aad", final_result=11.0)
        self._wtl(mocks, [_make_sample(sample_code="26_01_DRY_/+16.0", client_name="WTL", weight=5)], [[r1, r2, r3]])
        self._sim_ok(mocks)
        with patch("app.routes.api.simulator_api.current_user", FakeUser()):
            assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 200

    def test_composite_weight_only(self, app_client):
        app, client, mocks = app_client
        _login(client)
        self._wtl(mocks, [_make_sample(sample_code="26_01_COMP", client_name="WTL", weight=15)], [[]])
        self._sim_ok(mocks)
        with patch("app.routes.api.simulator_api.current_user", FakeUser()):
            assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 200

    def test_flotation_weight_only(self, app_client):
        app, client, mocks = app_client
        _login(client)
        self._wtl(mocks, [_make_sample(sample_code="26_01_T2", client_name="WTL", weight=3)], [[]])
        self._sim_ok(mocks)
        with patch("app.routes.api.simulator_api.current_user", FakeUser()):
            assert client.post("/api/send_to_simulator/wtl/26_01").status_code == 200
