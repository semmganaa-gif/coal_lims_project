# tests/test_remaining_low_coverage.py
# -*- coding: utf-8 -*-
"""
Coverage boost tests for:
  1. app/routes/api/simulator_api.py
  2. app/routes/equipment/registers.py
  3. app/routes/chemicals/waste.py
  4. app/routes/spare_parts/crud.py
  5. app/routes/chemicals/crud.py
"""

import uuid
import pytest
from unittest.mock import patch, MagicMock

from app import db as _db
from app.models import (
    User, Sample, AnalysisResult, Equipment,
)
from app.models.chemicals import Chemical, ChemicalWaste, ChemicalWasteRecord, ChemicalUsage, ChemicalLog
from app.models.spare_parts import SparePart, SparePartCategory


# =====================================================
# Helpers
# =====================================================

def _login(client, username="admin", password="TestPass123"):
    return client.post("/login", data={"username": username, "password": password})


def _unique(prefix="T"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# =====================================================
# Fixtures
# =====================================================

@pytest.fixture()
def admin_client(client, app):
    """Logged-in admin client."""
    _login(client, "admin")
    yield client
    client.get("/logout")


@pytest.fixture()
def chemist_client(client, app):
    """Logged-in chemist client."""
    _login(client, "chemist")
    yield client
    client.get("/logout")


@pytest.fixture()
def senior_client(client, app):
    """Logged-in senior client."""
    _login(client, "senior")
    yield client
    client.get("/logout")


@pytest.fixture()
def _equipment_item(app):
    """Create a register Equipment row for tests, cleanup after."""
    with app.app_context():
        item = Equipment(
            name="Test Register Equip",
            manufacturer="TestMfg",
            model="TM-100",
            serial_number="SN-001",
            lab_code="LC-001",
            quantity=2,
            location="Lab A",
            remark="test remark",
            register_type="measurement",
            status="normal",
            category="other",
        )
        _db.session.add(item)
        _db.session.commit()
        item_id = item.id
        yield item_id
        eq = _db.session.get(Equipment, item_id)
        if eq:
            _db.session.delete(eq)
            _db.session.commit()


@pytest.fixture()
def _waste_item(app):
    """Create a ChemicalWaste row."""
    with app.app_context():
        w = ChemicalWaste(
            name_mn="Тест хаягдал",
            name_en="Test waste",
            monthly_amount=5.0,
            unit="л",
            disposal_method="sewer",
            disposal_location="Бохирын шугам",
            is_hazardous=True,
            hazard_type="corrosive",
            lab_type="all",
            is_active=True,
        )
        _db.session.add(w)
        _db.session.commit()
        wid = w.id
        yield wid
        # cleanup
        ChemicalWasteRecord.query.filter_by(waste_id=wid).delete()
        obj = _db.session.get(ChemicalWaste, wid)
        if obj:
            _db.session.delete(obj)
        _db.session.commit()


@pytest.fixture()
def _chemical_item(app):
    """Create a Chemical row."""
    with app.app_context():
        c = Chemical(
            name="Test HCl",
            cas_number="7647-01-0",
            formula="HCl",
            quantity=100.0,
            unit="mL",
            lab_type="coal",
            category="acid",
            status="active",
        )
        _db.session.add(c)
        _db.session.commit()
        cid = c.id
        yield cid
        # cleanup
        ChemicalUsage.query.filter_by(chemical_id=cid).delete()
        ChemicalLog.query.filter_by(chemical_id=cid).delete()
        obj = _db.session.get(Chemical, cid)
        if obj:
            _db.session.delete(obj)
        _db.session.commit()


@pytest.fixture()
def _spare_category(app):
    """Create a SparePartCategory."""
    with app.app_context():
        code = _unique("cat")
        cat = SparePartCategory(
            code=code,
            name="Test Category",
            is_active=True,
            sort_order=0,
        )
        _db.session.add(cat)
        _db.session.commit()
        cid = cat.id
        yield cid, code
        obj = _db.session.get(SparePartCategory, cid)
        if obj:
            _db.session.delete(obj)
            _db.session.commit()


@pytest.fixture()
def _spare_part(app):
    """Create a SparePart."""
    with app.app_context():
        sp = SparePart(
            name="Test Filter",
            part_number="FLT-001",
            quantity=10.0,
            unit="pcs",
            reorder_level=2,
            category="general",
            status="active",
        )
        _db.session.add(sp)
        _db.session.commit()
        spid = sp.id
        yield spid
        obj = _db.session.get(SparePart, spid)
        if obj:
            _db.session.delete(obj)
            _db.session.commit()


# =====================================================
# 1. SIMULATOR API TESTS
# =====================================================

class TestSimulatorApiHelpers:
    """Test pure helper functions in simulator_api.py."""

    def test_classify_wtl_fraction(self, app):
        from app.routes.api.simulator_api import _classify_wtl_sample
        cat, size, density = _classify_wtl_sample("26_01_/+16.0/_F1.300")
        assert cat == "fraction"
        assert size == "+16.0"
        assert density == 1.300

    def test_classify_wtl_fraction_unknown_density(self, app):
        from app.routes.api.simulator_api import _classify_wtl_sample
        cat, size, density = _classify_wtl_sample("26_01_/+16.0/_FUNKNOWN")
        assert cat == "fraction"
        assert density is None

    def test_classify_wtl_dry_screen(self, app):
        from app.routes.api.simulator_api import _classify_wtl_sample
        cat, size, density = _classify_wtl_sample("26_01_DRY_/+16.0")
        assert cat == "dry_screen"
        assert size == "+16.0"
        assert density is None

    def test_classify_wtl_wet_screen(self, app):
        from app.routes.api.simulator_api import _classify_wtl_sample
        cat, size, density = _classify_wtl_sample("26_01_WET_/+16.0")
        assert cat == "wet_screen"

    def test_classify_wtl_composite(self, app):
        from app.routes.api.simulator_api import _classify_wtl_sample
        cat, size, density = _classify_wtl_sample("26_01_COMP")
        assert cat == "composite"

    def test_classify_wtl_flotation_c(self, app):
        from app.routes.api.simulator_api import _classify_wtl_sample
        cat, _, _ = _classify_wtl_sample("26_01_C1")
        assert cat == "flotation"

    def test_classify_wtl_flotation_t(self, app):
        from app.routes.api.simulator_api import _classify_wtl_sample
        cat, _, _ = _classify_wtl_sample("26_01_T2")
        assert cat == "flotation"

    def test_classify_wtl_unknown(self, app):
        from app.routes.api.simulator_api import _classify_wtl_sample
        cat, _, _ = _classify_wtl_sample("a/b/c/d")
        assert cat == "unknown"

    def test_classify_two_part_no_dry_wet(self, app):
        """Two-part code with neither DRY nor WET returns unknown."""
        from app.routes.api.simulator_api import _classify_wtl_sample
        cat, _, _ = _classify_wtl_sample("26_01_OTHER/+16.0")
        assert cat == "unknown"

    def test_send_to_simulator_connection_error(self, app):
        from app.routes.api.simulator_api import _send_to_simulator
        with app.app_context():
            with patch("app.routes.api.simulator_api.requests.post", side_effect=__import__("requests").ConnectionError):
                data, err = _send_to_simulator("http://bad", {})
                assert data is None
                assert err is not None

    def test_send_to_simulator_timeout(self, app):
        from app.routes.api.simulator_api import _send_to_simulator
        with app.app_context():
            with patch("app.routes.api.simulator_api.requests.post", side_effect=__import__("requests").Timeout):
                data, err = _send_to_simulator("http://bad", {})
                assert data is None
                assert "хугацаа" in err

    def test_send_to_simulator_http_error(self, app):
        import requests as req
        from app.routes.api.simulator_api import _send_to_simulator
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_resp.raise_for_status.side_effect = req.HTTPError(response=mock_resp)
        with app.app_context():
            with patch("app.routes.api.simulator_api.requests.post", return_value=mock_resp):
                data, err = _send_to_simulator("http://bad", {})
                assert data is None
                assert "500" in err

    def test_send_to_simulator_success(self, app):
        from app.routes.api.simulator_api import _send_to_simulator
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"ok": True}
        with app.app_context():
            with patch("app.routes.api.simulator_api.requests.post", return_value=mock_resp):
                data, err = _send_to_simulator("http://ok", {"x": 1})
                assert data == {"ok": True}
                assert err is None


class TestSimulatorChppRoute:
    """Test send_chpp_to_simulator route."""

    def test_chpp_not_logged_in(self, client, app):
        resp = client.post("/api/send_to_simulator/chpp/1")
        # Should redirect to login
        assert resp.status_code in (302, 401)

    def test_chpp_sample_not_found(self, admin_client, app):
        resp = admin_client.post("/api/send_to_simulator/chpp/999999")
        assert resp.status_code == 404

    def test_chpp_non_chpp_sample(self, admin_client, app):
        with app.app_context():
            user = User.query.filter_by(username="admin").first()
            s = Sample(sample_code=_unique("NCHP"), user_id=user.id, client_name="QC")
            _db.session.add(s)
            _db.session.commit()
            sid = s.id

        resp = admin_client.post(f"/api/send_to_simulator/chpp/{sid}")
        assert resp.status_code == 400

        with app.app_context():
            obj = _db.session.get(Sample, sid)
            if obj:
                _db.session.delete(obj)
                _db.session.commit()

    def test_chpp_no_approved_results(self, admin_client, app):
        with app.app_context():
            user = User.query.filter_by(username="admin").first()
            s = Sample(sample_code=_unique("CHPP"), user_id=user.id, client_name="CHPP")
            _db.session.add(s)
            _db.session.commit()
            sid = s.id

        resp = admin_client.post(f"/api/send_to_simulator/chpp/{sid}")
        assert resp.status_code == 400

        with app.app_context():
            obj = _db.session.get(Sample, sid)
            if obj:
                _db.session.delete(obj)
                _db.session.commit()

    def test_chpp_success(self, admin_client, app):
        with app.app_context():
            user = User.query.filter_by(username="admin").first()
            code = _unique("CHPP")
            s = Sample(sample_code=code, user_id=user.id, client_name="CHPP", sample_type="Feed")
            _db.session.add(s)
            _db.session.flush()
            ar = AnalysisResult(
                sample_id=s.id, analysis_code="Mad",
                final_result=5.5, status="approved",
            )
            _db.session.add(ar)
            _db.session.commit()
            sid = s.id

        with patch("app.routes.api.simulator_api._send_to_simulator", return_value=({"ok": True}, None)):
            resp = admin_client.post(f"/api/send_to_simulator/chpp/{sid}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

        # cleanup
        with app.app_context():
            AnalysisResult.query.filter_by(sample_id=sid).delete()
            obj = _db.session.get(Sample, sid)
            if obj:
                _db.session.delete(obj)
            _db.session.commit()

    def test_chpp_simulator_error(self, admin_client, app):
        with app.app_context():
            user = User.query.filter_by(username="admin").first()
            code = _unique("CHPP")
            s = Sample(sample_code=code, user_id=user.id, client_name="CHPP")
            _db.session.add(s)
            _db.session.flush()
            ar = AnalysisResult(
                sample_id=s.id, analysis_code="Aad",
                final_result=10.0, status="approved",
            )
            _db.session.add(ar)
            _db.session.commit()
            sid = s.id

        with patch("app.routes.api.simulator_api._send_to_simulator", return_value=(None, "Connection refused")):
            resp = admin_client.post(f"/api/send_to_simulator/chpp/{sid}")
        assert resp.status_code == 502

        with app.app_context():
            AnalysisResult.query.filter_by(sample_id=sid).delete()
            obj = _db.session.get(Sample, sid)
            if obj:
                _db.session.delete(obj)
            _db.session.commit()


class TestSimulatorWtlRoute:
    """Test send_wtl_to_simulator route."""

    def test_wtl_not_logged_in(self, client):
        resp = client.post("/api/send_to_simulator/wtl/26_01")
        assert resp.status_code in (302, 401)

    def test_wtl_no_samples(self, admin_client, app):
        resp = admin_client.post("/api/send_to_simulator/wtl/NONEXISTENT_LAB_99")
        assert resp.status_code == 404

    def test_wtl_success_fractions(self, admin_client, app):
        """WTL with fraction + composite samples."""
        lab_num = _unique("WTL")
        with app.app_context():
            user = User.query.filter_by(username="admin").first()
            # Fraction sample
            s1 = Sample(
                sample_code=f"{lab_num}/+16.0/_F1.300",
                user_id=user.id, client_name="WTL", weight=5.0,
            )
            # Composite sample
            s2 = Sample(
                sample_code=f"{lab_num}_COMP",
                user_id=user.id, client_name="WTL", weight=10.0,
            )
            # Dry screen
            s3 = Sample(
                sample_code=f"{lab_num}_DRY_/+16.0",
                user_id=user.id, client_name="WTL", weight=3.0,
            )
            # Wet screen
            s4 = Sample(
                sample_code=f"{lab_num}_WET_/+8.0",
                user_id=user.id, client_name="WTL", weight=2.0,
            )
            # Flotation
            s5 = Sample(
                sample_code=f"{lab_num}_C1",
                user_id=user.id, client_name="WTL", weight=1.0,
            )
            _db.session.add_all([s1, s2, s3, s4, s5])
            _db.session.flush()
            # Add approved results for fraction
            ar1 = AnalysisResult(sample_id=s1.id, analysis_code="Aad", final_result=8.0, status="approved")
            ar2 = AnalysisResult(sample_id=s2.id, analysis_code="Mad", final_result=3.0, status="approved")
            ar3 = AnalysisResult(sample_id=s5.id, analysis_code="Vad", final_result=25.0, status="approved")
            _db.session.add_all([ar1, ar2, ar3])
            _db.session.commit()
            sids = [s1.id, s2.id, s3.id, s4.id, s5.id]

        with patch("app.routes.api.simulator_api._send_to_simulator", return_value=({"ok": True}, None)):
            resp = admin_client.post(f"/api/send_to_simulator/wtl/{lab_num}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

        # cleanup
        with app.app_context():
            for sid in sids:
                AnalysisResult.query.filter_by(sample_id=sid).delete()
                obj = _db.session.get(Sample, sid)
                if obj:
                    _db.session.delete(obj)
            _db.session.commit()

    def test_wtl_no_data_to_send(self, admin_client, app):
        """WTL samples exist but none have data."""
        lab_num = _unique("WTL")
        with app.app_context():
            user = User.query.filter_by(username="admin").first()
            # Fraction with unknown density (will be skipped)
            s1 = Sample(
                sample_code=f"{lab_num}/+16.0/_FUNKNOWN",
                user_id=user.id, client_name="WTL", weight=0,
            )
            _db.session.add(s1)
            _db.session.commit()
            sid = s1.id

        resp = admin_client.post(f"/api/send_to_simulator/wtl/{lab_num}")
        assert resp.status_code == 400

        with app.app_context():
            obj = _db.session.get(Sample, sid)
            if obj:
                _db.session.delete(obj)
            _db.session.commit()

    def test_wtl_simulator_error(self, admin_client, app):
        lab_num = _unique("WTL")
        with app.app_context():
            user = User.query.filter_by(username="admin").first()
            s1 = Sample(
                sample_code=f"{lab_num}/+16.0/_F1.300",
                user_id=user.id, client_name="WTL", weight=5.0,
            )
            _db.session.add(s1)
            _db.session.flush()
            ar = AnalysisResult(sample_id=s1.id, analysis_code="Aad", final_result=8.0, status="approved")
            _db.session.add(ar)
            _db.session.commit()
            sid = s1.id

        with patch("app.routes.api.simulator_api._send_to_simulator", return_value=(None, "timeout")):
            resp = admin_client.post(f"/api/send_to_simulator/wtl/{lab_num}")
        assert resp.status_code == 502

        with app.app_context():
            AnalysisResult.query.filter_by(sample_id=sid).delete()
            obj = _db.session.get(Sample, sid)
            if obj:
                _db.session.delete(obj)
            _db.session.commit()


# =====================================================
# 2. EQUIPMENT REGISTERS TESTS
# =====================================================

class TestEquipmentJournal:

    def test_hub_requires_login(self, client):
        resp = client.get("/equipment_journal")
        assert resp.status_code in (302, 401)

    def test_hub_page(self, admin_client):
        resp = admin_client.get("/equipment_journal")
        assert resp.status_code == 200

    def test_grid_page_default(self, admin_client):
        resp = admin_client.get("/equipment_journal/grid")
        assert resp.status_code == 200

    def test_grid_page_category(self, admin_client):
        resp = admin_client.get("/equipment_journal/grid?category=furnace")
        assert resp.status_code == 200

    def test_grid_page_unknown_category(self, admin_client):
        resp = admin_client.get("/equipment_journal/grid?category=nonexist")
        assert resp.status_code == 200


class TestEquipmentJournalSpecial:

    def test_measurement_journal(self, admin_client, _equipment_item):
        resp = admin_client.get("/equipment_journal/measurement")
        assert resp.status_code == 200

    def test_glassware_journal(self, admin_client):
        resp = admin_client.get("/equipment_journal/glassware")
        assert resp.status_code == 200

    def test_internal_check_journal(self, admin_client):
        resp = admin_client.get("/equipment_journal/internal_check")
        assert resp.status_code == 200

    def test_new_equipment_journal(self, admin_client):
        resp = admin_client.get("/equipment_journal/new_equipment")
        assert resp.status_code == 200

    def test_out_of_service_journal(self, admin_client):
        resp = admin_client.get("/equipment_journal/out_of_service")
        assert resp.status_code == 200

    def test_balances_register_journal(self, admin_client):
        resp = admin_client.get("/equipment_journal/balances_register")
        assert resp.status_code == 200

    def test_unknown_journal_redirects(self, admin_client):
        resp = admin_client.get("/equipment_journal/nonexist")
        assert resp.status_code == 302

    def test_spares_register_redirects(self, admin_client):
        resp = admin_client.get("/equipment_journal/spares_register")
        assert resp.status_code == 302


class TestEquipmentRegisterCRUD:

    def test_add_register_item(self, admin_client, app):
        resp = admin_client.post("/add_register_item/measurement", data={
            "name": "Test Item",
            "manufacturer": "Mfg",
            "model": "M1",
            "serial_number": "SN1",
            "lab_code": "LC1",
            "quantity": "3",
            "location": "Lab B",
            "remark": "test",
        })
        assert resp.status_code == 302

        # cleanup
        with app.app_context():
            item = Equipment.query.filter_by(name="Test Item", register_type="measurement").first()
            if item:
                _db.session.delete(item)
                _db.session.commit()

    def test_add_register_item_invalid_quantity(self, admin_client):
        resp = admin_client.post("/add_register_item/measurement", data={
            "name": "Bad Qty",
            "quantity": "abc",
        })
        assert resp.status_code == 302  # redirect with flash error

    def test_add_register_item_unauthorized(self, chemist_client):
        resp = chemist_client.post("/add_register_item/measurement", data={
            "name": "Nope",
        })
        assert resp.status_code == 302

    def test_add_register_item_qty_field(self, admin_client, app):
        """Test qty→quantity conversion."""
        resp = admin_client.post("/add_register_item/glassware", data={
            "name": "Qty Test",
            "qty": "5",
        })
        assert resp.status_code == 302

        with app.app_context():
            item = Equipment.query.filter_by(name="Qty Test", register_type="glassware").first()
            if item:
                assert item.quantity == 5
                _db.session.delete(item)
                _db.session.commit()

    def test_edit_register_item(self, admin_client, app, _equipment_item):
        resp = admin_client.post(f"/edit_register_item/{_equipment_item}", data={
            "name": "Updated Name",
            "manufacturer": "NewMfg",
            "model": "NM-200",
            "serial_number": "SN-002",
            "lab_code": "LC-002",
            "quantity": "5",
            "location": "Lab C",
            "remark": "updated",
        })
        assert resp.status_code == 302

    def test_edit_register_item_not_found(self, admin_client):
        resp = admin_client.post("/edit_register_item/999999", data={"name": "X"})
        assert resp.status_code == 404

    def test_edit_register_item_unauthorized(self, chemist_client, _equipment_item):
        resp = chemist_client.post(f"/edit_register_item/{_equipment_item}", data={"name": "X"})
        assert resp.status_code == 302

    def test_edit_register_item_invalid_quantity(self, admin_client, _equipment_item):
        resp = admin_client.post(f"/edit_register_item/{_equipment_item}", data={
            "name": "Test",
            "quantity": "not_a_number",
        })
        assert resp.status_code == 302

    def test_edit_register_item_qty_field(self, admin_client, _equipment_item):
        """Test qty→quantity conversion on edit."""
        resp = admin_client.post(f"/edit_register_item/{_equipment_item}", data={
            "name": "Updated",
            "qty": "7",
        })
        assert resp.status_code == 302

    def test_delete_register_items(self, admin_client, app, _equipment_item):
        resp = admin_client.post("/delete_register_items", data={
            "item_ids": [str(_equipment_item)],
            "register_type": "measurement",
        })
        assert resp.status_code == 302

    def test_delete_register_items_no_ids(self, admin_client):
        resp = admin_client.post("/delete_register_items", data={
            "register_type": "measurement",
        })
        assert resp.status_code == 302

    def test_delete_register_items_unauthorized(self, chemist_client):
        resp = chemist_client.post("/delete_register_items", data={
            "item_ids": ["1"],
            "register_type": "measurement",
        })
        assert resp.status_code == 302

    def test_delete_register_items_wrong_type(self, admin_client, _equipment_item):
        """Item register_type doesn't match, so nothing deleted."""
        resp = admin_client.post("/delete_register_items", data={
            "item_ids": [str(_equipment_item)],
            "register_type": "glassware",  # doesn't match 'measurement'
        })
        assert resp.status_code == 302

    def test_add_register_item_with_extra_data(self, admin_client, app):
        resp = admin_client.post("/add_register_item/measurement", data={
            "name": "Extra Data Item",
            "manufacturer": "Mfg",
            "quantity": "1",
            "custom_field": "custom_value",
        })
        assert resp.status_code == 302
        with app.app_context():
            item = Equipment.query.filter_by(name="Extra Data Item").first()
            if item:
                assert item.extra_data is not None
                _db.session.delete(item)
                _db.session.commit()

    def test_add_register_db_error(self, admin_client):
        with patch("app.routes.equipment.registers.db.session.commit", side_effect=__import__("sqlalchemy").exc.SQLAlchemyError("DB error")):
            resp = admin_client.post("/add_register_item/measurement", data={
                "name": "DB Error Test",
            })
        assert resp.status_code == 302

    def test_edit_register_db_error(self, admin_client, _equipment_item):
        with patch("app.routes.equipment.registers.db.session.commit", side_effect=__import__("sqlalchemy").exc.SQLAlchemyError("DB error")):
            resp = admin_client.post(f"/edit_register_item/{_equipment_item}", data={
                "name": "DB Error Edit",
            })
        assert resp.status_code == 302

    def test_delete_register_db_error(self, admin_client, _equipment_item):
        with patch("app.routes.equipment.registers.db.session.commit", side_effect=__import__("sqlalchemy").exc.SQLAlchemyError("DB error")):
            resp = admin_client.post("/delete_register_items", data={
                "item_ids": [str(_equipment_item)],
                "register_type": "measurement",
            })
        assert resp.status_code == 302


# =====================================================
# 3. CHEMICALS WASTE TESTS
# =====================================================

class TestWasteList:

    def test_waste_list_requires_login(self, client):
        resp = client.get("/chemicals/waste")
        assert resp.status_code in (302, 401)

    def test_waste_list_default(self, admin_client, _waste_item):
        resp = admin_client.get("/chemicals/waste")
        assert resp.status_code == 200

    def test_waste_list_filter_lab(self, admin_client, _waste_item):
        resp = admin_client.get("/chemicals/waste?lab=coal")
        assert resp.status_code == 200

    def test_waste_list_filter_year(self, admin_client, _waste_item):
        resp = admin_client.get("/chemicals/waste?year=2025")
        assert resp.status_code == 200


class TestWasteAdd:

    def test_add_waste_get(self, admin_client):
        resp = admin_client.get("/chemicals/waste/add")
        assert resp.status_code == 200

    def test_add_waste_post(self, admin_client, app):
        resp = admin_client.post("/chemicals/waste/add", data={
            "name_mn": "Шинэ хаягдал",
            "name_en": "New waste",
            "monthly_amount": "10",
            "unit": "л",
            "disposal_method": "sewer",
            "disposal_location": "drain",
            "is_hazardous": "on",
            "hazard_type": "toxic",
            "lab_type": "all",
            "notes": "test",
        })
        assert resp.status_code == 302

        with app.app_context():
            w = ChemicalWaste.query.filter_by(name_mn="Шинэ хаягдал").first()
            if w:
                _db.session.delete(w)
                _db.session.commit()

    def test_add_waste_unauthorized(self, client, app):
        """User with no role (not logged in) cannot add."""
        resp = client.get("/chemicals/waste/add")
        assert resp.status_code in (302, 401)

    def test_add_waste_invalid_amount(self, admin_client):
        resp = admin_client.post("/chemicals/waste/add", data={
            "name_mn": "Bad",
            "monthly_amount": "not_a_number",
        })
        # Should flash error but still show form (200)
        assert resp.status_code == 200

    def test_add_waste_role_check(self, client, app):
        """Login as user with insufficient role (senior has access, let's test the boundary)."""
        # Create a user with role='analyst' which isn't in the allowed list
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            original_role = u.role
            u.role = "analyst"
            _db.session.commit()

        _login(client, "chemist")
        resp = client.post("/chemicals/waste/add", data={"name_mn": "X"})
        assert resp.status_code == 302  # redirected due to no permission

        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            u.role = original_role
            _db.session.commit()
        client.get("/logout")


class TestWasteEdit:

    def test_edit_waste_get(self, admin_client, _waste_item):
        resp = admin_client.get(f"/chemicals/waste/edit/{_waste_item}")
        assert resp.status_code == 200

    def test_edit_waste_post(self, admin_client, _waste_item):
        resp = admin_client.post(f"/chemicals/waste/edit/{_waste_item}", data={
            "name_mn": "Updated waste",
            "name_en": "Updated",
            "monthly_amount": "20",
            "unit": "кг",
            "disposal_method": "special",
            "lab_type": "coal",
        })
        assert resp.status_code == 302

    def test_edit_waste_not_found(self, admin_client):
        resp = admin_client.get("/chemicals/waste/edit/999999")
        assert resp.status_code == 404

    def test_edit_waste_invalid_amount(self, admin_client, _waste_item):
        resp = admin_client.post(f"/chemicals/waste/edit/{_waste_item}", data={
            "name_mn": "Bad Edit",
            "monthly_amount": "bad",
        })
        assert resp.status_code == 200  # form re-shown

    def test_edit_waste_unauthorized(self, client, app, _waste_item):
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            original_role = u.role
            u.role = "analyst"
            _db.session.commit()
        _login(client, "chemist")
        resp = client.post(f"/chemicals/waste/edit/{_waste_item}", data={"name_mn": "X"})
        assert resp.status_code == 302
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            u.role = original_role
            _db.session.commit()
        client.get("/logout")


class TestWasteDelete:

    def test_delete_waste(self, admin_client, _waste_item):
        resp = admin_client.post(f"/chemicals/waste/delete/{_waste_item}")
        assert resp.status_code == 302

    def test_delete_waste_not_found(self, admin_client):
        resp = admin_client.post("/chemicals/waste/delete/999999")
        assert resp.status_code == 404

    def test_delete_waste_unauthorized(self, chemist_client, _waste_item):
        resp = chemist_client.post(f"/chemicals/waste/delete/{_waste_item}")
        assert resp.status_code == 302


class TestWasteRecord:

    def test_save_waste_record_new(self, admin_client, _waste_item):
        resp = admin_client.post("/chemicals/waste/api/save_record",
            json={"waste_id": _waste_item, "year": 2026, "month": 3, "quantity": 5.0},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_save_waste_record_update(self, admin_client, app, _waste_item):
        """Save then update same record."""
        admin_client.post("/chemicals/waste/api/save_record",
            json={"waste_id": _waste_item, "year": 2026, "month": 4, "quantity": 3.0},
            content_type="application/json",
        )
        resp = admin_client.post("/chemicals/waste/api/save_record",
            json={"waste_id": _waste_item, "year": 2026, "month": 4, "quantity": 7.0, "ending_balance": 10.0},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_save_waste_record_invalid_quantity(self, admin_client, _waste_item):
        resp = admin_client.post("/chemicals/waste/api/save_record",
            json={"waste_id": _waste_item, "year": 2026, "month": 1, "quantity": "bad"},
            content_type="application/json",
        )
        assert resp.status_code == 500

    def test_save_waste_record_db_error(self, admin_client, _waste_item):
        with patch("app.routes.chemicals.waste.db.session.commit", side_effect=__import__("sqlalchemy").exc.SQLAlchemyError("DB")):
            resp = admin_client.post("/chemicals/waste/api/save_record",
                json={"waste_id": _waste_item, "year": 2026, "month": 5, "quantity": 1.0},
                content_type="application/json",
            )
        assert resp.status_code == 500

    def test_save_waste_record_not_logged_in(self, client):
        resp = client.post("/chemicals/waste/api/save_record",
            json={"waste_id": 1, "year": 2026, "month": 1, "quantity": 1},
            content_type="application/json",
        )
        assert resp.status_code in (302, 401)


class TestWasteReport:

    def test_waste_report_default(self, admin_client, _waste_item):
        resp = admin_client.get("/chemicals/waste/report")
        assert resp.status_code == 200

    def test_waste_report_filter(self, admin_client, _waste_item):
        resp = admin_client.get("/chemicals/waste/report?year=2025&lab=coal")
        assert resp.status_code == 200


# =====================================================
# 4. SPARE PARTS CRUD TESTS
# =====================================================

def _make_stats(**overrides):
    """Create a stats object with default values that templates can access as attributes."""
    defaults = {"total": 0, "low_stock": 0, "out_of_stock": 0, "expired": 0}
    defaults.update(overrides)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    # Also support dict-like access
    obj.__getitem__ = lambda self, key: getattr(self, key)
    return obj


class TestSparePartList:

    def test_list_requires_login(self, client):
        resp = client.get("/spare_parts/")
        assert resp.status_code in (302, 401)

    @patch("app.routes.spare_parts.crud.get_spare_parts_filtered", return_value=[])
    @patch("app.routes.spare_parts.crud.get_list_stats")
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.get_categories_dict", return_value={})
    def test_list_page(self, m1, m2, m3, m4, admin_client):
        m3.return_value = _make_stats()
        resp = admin_client.get("/spare_parts/")
        assert resp.status_code == 200

    @patch("app.routes.spare_parts.crud.get_spare_parts_filtered", return_value=[])
    @patch("app.routes.spare_parts.crud.get_list_stats")
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.get_categories_dict", return_value={})
    def test_list_with_filters(self, m1, m2, m3, m4, admin_client):
        m3.return_value = _make_stats()
        resp = admin_client.get("/spare_parts/?category=general&status=active&view=low_stock")
        assert resp.status_code == 200


class TestSparePartDetail:

    @patch("app.routes.spare_parts.crud.get_detail_data", return_value=(None, [], []))
    def test_detail_not_found(self, mock_detail, admin_client):
        resp = admin_client.get("/spare_parts/999999")
        assert resp.status_code == 404

    def test_detail_found(self, admin_client, app, _spare_part):
        """Test detail page with real DB object."""
        resp = admin_client.get(f"/spare_parts/{_spare_part}")
        assert resp.status_code == 200


class TestSparePartCategoryRoutes:

    @patch("app.routes.spare_parts.crud.get_all_categories_ordered", return_value=[])
    def test_category_list_admin(self, mock_cats, admin_client):
        resp = admin_client.get("/spare_parts/categories")
        assert resp.status_code == 200

    def test_category_list_unauthorized(self, chemist_client):
        resp = chemist_client.get("/spare_parts/categories")
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    def test_add_category_get(self, mock_eq, admin_client):
        resp = admin_client.get("/spare_parts/categories/add")
        assert resp.status_code == 200

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    @patch("app.routes.spare_parts.crud.create_category")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    def test_add_category_post_success(self, mock_commit, mock_create, mock_eq, admin_client):
        mock_create.return_value = (MagicMock(), None)
        resp = admin_client.post("/spare_parts/categories/add", data={
            "code": "test_cat",
            "name": "Test Cat",
            "sort_order": "0",
            "is_active": "on",
        })
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    @patch("app.routes.spare_parts.crud.create_category")
    def test_add_category_post_error(self, mock_create, mock_eq, admin_client):
        mock_create.return_value = (None, "Duplicate code")
        resp = admin_client.post("/spare_parts/categories/add", data={
            "code": "dup", "name": "Dup",
        })
        assert resp.status_code == 200  # form re-shown

    def test_add_category_unauthorized(self, chemist_client):
        resp = chemist_client.post("/spare_parts/categories/add", data={"code": "x", "name": "X"})
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    def test_edit_category_get(self, mock_eq, admin_client, _spare_category):
        cat_id, _ = _spare_category
        resp = admin_client.get(f"/spare_parts/categories/edit/{cat_id}")
        assert resp.status_code == 200

    def test_edit_category_not_found(self, admin_client):
        resp = admin_client.get("/spare_parts/categories/edit/999999")
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    @patch("app.routes.spare_parts.crud.update_category")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    def test_edit_category_post_success(self, mock_commit, mock_update, mock_eq, admin_client, _spare_category):
        cat_id, _ = _spare_category
        mock_update.return_value = (MagicMock(), None)
        resp = admin_client.post(f"/spare_parts/categories/edit/{cat_id}", data={
            "name": "Updated", "sort_order": "1",
        })
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    @patch("app.routes.spare_parts.crud.update_category")
    def test_edit_category_post_not_found(self, mock_update, mock_eq, admin_client, _spare_category):
        cat_id, _ = _spare_category
        mock_update.return_value = (None, "not_found")
        resp = admin_client.post(f"/spare_parts/categories/edit/{cat_id}", data={
            "name": "X",
        })
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    @patch("app.routes.spare_parts.crud.update_category")
    def test_edit_category_post_error(self, mock_update, mock_eq, admin_client, _spare_category):
        cat_id, _ = _spare_category
        mock_update.return_value = (None, "Some error")
        resp = admin_client.post(f"/spare_parts/categories/edit/{cat_id}", data={
            "name": "X",
        })
        assert resp.status_code == 200

    def test_edit_category_unauthorized(self, chemist_client, _spare_category):
        cat_id, _ = _spare_category
        resp = chemist_client.post(f"/spare_parts/categories/edit/{cat_id}", data={"name": "X"})
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.svc_delete_category")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    def test_delete_category_success(self, mock_commit, mock_del, admin_client, _spare_category):
        cat_id, _ = _spare_category
        mock_del.return_value = ("Cat Name", None)
        resp = admin_client.post(f"/spare_parts/categories/delete/{cat_id}")
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.svc_delete_category")
    def test_delete_category_not_found(self, mock_del, admin_client):
        mock_del.return_value = (None, "not_found")
        resp = admin_client.post("/spare_parts/categories/delete/999999")
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.svc_delete_category")
    def test_delete_category_error(self, mock_del, admin_client, _spare_category):
        cat_id, _ = _spare_category
        mock_del.return_value = (None, "Has items")
        resp = admin_client.post(f"/spare_parts/categories/delete/{cat_id}")
        assert resp.status_code == 302

    def test_delete_category_unauthorized_senior(self, senior_client, _spare_category):
        cat_id, _ = _spare_category
        resp = senior_client.post(f"/spare_parts/categories/delete/{cat_id}")
        assert resp.status_code == 302


class TestSparePartCRUD:

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    def test_add_spare_part_get(self, mc, me, admin_client):
        resp = admin_client.get("/spare_parts/add")
        assert resp.status_code == 200

    def test_add_spare_part_unauthorized(self, client, app):
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            orig = u.role
            u.role = "analyst"
            _db.session.commit()
        _login(client, "chemist")
        resp = client.post("/spare_parts/add", data={"name": "X"})
        assert resp.status_code == 302
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            u.role = orig
            _db.session.commit()
        client.get("/logout")

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.create_spare_part")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    def test_add_spare_part_post_success(self, mc, mock_create, me, meq, admin_client):
        mock_sp = MagicMock()
        mock_sp.name = "New Part"
        mock_create.return_value = (mock_sp, None)
        resp = admin_client.post("/spare_parts/add", data={
            "name": "New Part",
            "quantity": "10",
            "unit": "pcs",
            "category": "general",
        })
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.create_spare_part")
    def test_add_spare_part_post_error(self, mock_create, me, meq, admin_client):
        mock_create.return_value = (None, "Name required")
        resp = admin_client.post("/spare_parts/add", data={
            "name": "",
        })
        assert resp.status_code == 200

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    def test_edit_spare_part_get(self, mc, me, admin_client, _spare_part):
        resp = admin_client.get(f"/spare_parts/edit/{_spare_part}")
        assert resp.status_code == 200

    def test_edit_spare_part_not_found(self, admin_client):
        resp = admin_client.get("/spare_parts/edit/999999")
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.update_spare_part")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    def test_edit_spare_part_post_success(self, mc, mock_update, me, meq, admin_client, _spare_part):
        mock_update.return_value = (MagicMock(), None)
        resp = admin_client.post(f"/spare_parts/edit/{_spare_part}", data={
            "name": "Updated Part",
            "quantity": "5",
        })
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.update_spare_part")
    def test_edit_spare_part_post_not_found(self, mock_update, me, meq, admin_client, _spare_part):
        mock_update.return_value = (None, "not_found")
        resp = admin_client.post(f"/spare_parts/edit/{_spare_part}", data={"name": "X"})
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.update_spare_part")
    def test_edit_spare_part_post_error(self, mock_update, me, meq, admin_client, _spare_part):
        mock_update.return_value = (None, "Validation failed")
        resp = admin_client.post(f"/spare_parts/edit/{_spare_part}", data={"name": "X"})
        assert resp.status_code == 200

    def test_edit_spare_part_unauthorized(self, client, app, _spare_part):
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            orig = u.role
            u.role = "analyst"
            _db.session.commit()
        _login(client, "chemist")
        resp = client.post(f"/spare_parts/edit/{_spare_part}", data={"name": "X"})
        assert resp.status_code == 302
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            u.role = orig
            _db.session.commit()
        client.get("/logout")

    @patch("app.routes.spare_parts.crud.receive_stock")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    def test_receive_spare_part(self, mc, mock_recv, admin_client, _spare_part):
        mock_recv.return_value = ({"quantity_added": 5, "unit": "pcs", "new_total": 15}, None)
        resp = admin_client.post(f"/spare_parts/receive/{_spare_part}", data={
            "quantity": "5",
            "notes": "test receive",
        })
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.receive_stock")
    def test_receive_spare_part_not_found(self, mock_recv, admin_client, _spare_part):
        mock_recv.return_value = (None, "not_found")
        resp = admin_client.post(f"/spare_parts/receive/{_spare_part}", data={"quantity": "5"})
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.receive_stock")
    def test_receive_spare_part_error(self, mock_recv, admin_client, _spare_part):
        mock_recv.return_value = (None, "Invalid quantity")
        resp = admin_client.post(f"/spare_parts/receive/{_spare_part}", data={"quantity": "5"})
        assert resp.status_code == 302

    def test_receive_spare_part_unauthorized(self, client, app, _spare_part):
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            orig = u.role
            u.role = "analyst"
            _db.session.commit()
        _login(client, "chemist")
        resp = client.post(f"/spare_parts/receive/{_spare_part}", data={"quantity": "1"})
        assert resp.status_code == 302
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            u.role = orig
            _db.session.commit()
        client.get("/logout")

    def test_receive_spare_part_value_error(self, admin_client, _spare_part):
        resp = admin_client.post(f"/spare_parts/receive/{_spare_part}", data={
            "quantity": "not_number",
        })
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.consume_stock")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    def test_consume_spare_part(self, mc, mock_consume, admin_client, _spare_part):
        mock_consume.return_value = ({"consumed": 2, "unit": "pcs", "remaining": 8}, None)
        resp = admin_client.post(f"/spare_parts/consume/{_spare_part}", data={
            "quantity": "2",
            "purpose": "maintenance",
        })
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.consume_stock")
    def test_consume_spare_part_not_found(self, mock_consume, admin_client, _spare_part):
        mock_consume.return_value = (None, "not_found")
        resp = admin_client.post(f"/spare_parts/consume/{_spare_part}", data={"quantity": "1"})
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.consume_stock")
    def test_consume_spare_part_insufficient(self, mock_consume, admin_client, _spare_part):
        mock_consume.return_value = (None, "Тоо хэмжээ хүрэлцэхгүй")
        resp = admin_client.post(f"/spare_parts/consume/{_spare_part}", data={"quantity": "999"})
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.consume_stock")
    def test_consume_spare_part_other_error(self, mock_consume, admin_client, _spare_part):
        mock_consume.return_value = (None, "Unknown error")
        resp = admin_client.post(f"/spare_parts/consume/{_spare_part}", data={"quantity": "1"})
        assert resp.status_code == 302

    def test_consume_spare_part_value_error(self, admin_client, _spare_part):
        resp = admin_client.post(f"/spare_parts/consume/{_spare_part}", data={
            "quantity": "bad",
        })
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.svc_dispose")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    def test_dispose_spare_part(self, mc, mock_dispose, admin_client, _spare_part):
        mock_dispose.return_value = ("Test Part", None)
        resp = admin_client.post(f"/spare_parts/dispose/{_spare_part}", data={"reason": "worn out"})
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.svc_dispose")
    def test_dispose_spare_part_not_found(self, mock_dispose, admin_client, _spare_part):
        mock_dispose.return_value = (None, "not_found")
        resp = admin_client.post(f"/spare_parts/dispose/{_spare_part}", data={"reason": "test"})
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.svc_dispose")
    def test_dispose_spare_part_error(self, mock_dispose, admin_client, _spare_part):
        mock_dispose.return_value = (None, "Cannot dispose")
        resp = admin_client.post(f"/spare_parts/dispose/{_spare_part}", data={"reason": "test"})
        assert resp.status_code == 302

    def test_dispose_spare_part_unauthorized(self, chemist_client, _spare_part):
        resp = chemist_client.post(f"/spare_parts/dispose/{_spare_part}", data={"reason": "test"})
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.delete_spare_part_permanently")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    def test_delete_spare_part(self, mc, mock_del, admin_client, _spare_part):
        mock_del.return_value = ("Test Part", None)
        resp = admin_client.post(f"/spare_parts/delete/{_spare_part}")
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.delete_spare_part_permanently")
    def test_delete_spare_part_not_found(self, mock_del, admin_client):
        mock_del.return_value = (None, "not_found")
        resp = admin_client.post("/spare_parts/delete/999999")
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.delete_spare_part_permanently")
    def test_delete_spare_part_error(self, mock_del, admin_client, _spare_part):
        mock_del.return_value = (None, "Has usages")
        resp = admin_client.post(f"/spare_parts/delete/{_spare_part}")
        assert resp.status_code == 302

    def test_delete_spare_part_unauthorized(self, senior_client, _spare_part):
        resp = senior_client.post(f"/spare_parts/delete/{_spare_part}")
        assert resp.status_code == 302


class TestSparePartImageHandling:

    @patch("app.routes.spare_parts.crud.EquipmentRepository.get_all_active", return_value=[])
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.update_spare_part")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=False)
    def test_edit_with_image_upload_no_file(self, mc, mock_update, me, meq, admin_client, _spare_part):
        """POST edit with no actual image file uploaded - covers the image handling branches."""
        mock_update.return_value = (MagicMock(), None)
        resp = admin_client.post(f"/spare_parts/edit/{_spare_part}", data={
            "name": "No Image Upload",
        })
        # safe_commit returns False so form is re-shown
        assert resp.status_code == 200


# =====================================================
# 5. CHEMICALS CRUD TESTS
# =====================================================

class TestChemicalList:

    def test_list_requires_login(self, client):
        resp = client.get("/chemicals/")
        assert resp.status_code in (302, 401)

    @patch("app.routes.chemicals.crud.get_chemical_list", return_value=[])
    @patch("app.routes.chemicals.crud.get_chemical_stats_summary")
    def test_list_default(self, ms, ml, admin_client):
        ms.return_value = _make_stats()
        resp = admin_client.get("/chemicals/")
        assert resp.status_code == 200

    @patch("app.routes.chemicals.crud.get_chemical_list", return_value=[])
    @patch("app.routes.chemicals.crud.get_chemical_stats_summary")
    def test_list_with_filters(self, ms, ml, admin_client):
        ms.return_value = _make_stats()
        resp = admin_client.get("/chemicals/list?lab=coal&category=acid&status=active&view=low_stock")
        assert resp.status_code == 200


class TestChemicalDetail:

    def test_detail_not_found(self, admin_client):
        resp = admin_client.get("/chemicals/999999")
        assert resp.status_code == 404

    def test_detail_found(self, admin_client, _chemical_item):
        resp = admin_client.get(f"/chemicals/{_chemical_item}")
        assert resp.status_code == 200


class TestChemicalAdd:

    def test_add_get(self, admin_client):
        resp = admin_client.get("/chemicals/add")
        assert resp.status_code == 200

    def test_add_get_with_lab(self, admin_client):
        resp = admin_client.get("/chemicals/add?lab=water")
        assert resp.status_code == 200

    @patch("app.routes.chemicals.crud.create_chemical")
    @patch("app.routes.chemicals.crud.safe_commit", return_value=True)
    def test_add_post_success(self, mc, mock_create, admin_client):
        mock_chem = MagicMock()
        mock_chem.name = "New Chem"
        mock_chem.id = 99
        mock_create.return_value = mock_chem
        resp = admin_client.post("/chemicals/add", data={
            "name": "New Chem",
            "quantity": "100",
            "unit": "mL",
            "category": "acid",
            "lab_type": "coal",
        })
        assert resp.status_code == 302

    @patch("app.routes.chemicals.crud.create_chemical", side_effect=ValueError("Bad value"))
    def test_add_post_value_error(self, mock_create, admin_client):
        resp = admin_client.post("/chemicals/add", data={
            "name": "Bad",
            "quantity": "abc",
        })
        assert resp.status_code == 200

    @patch("app.routes.chemicals.crud.create_chemical", side_effect=__import__("sqlalchemy").exc.SQLAlchemyError("DB"))
    def test_add_post_db_error(self, mock_create, admin_client):
        resp = admin_client.post("/chemicals/add", data={
            "name": "DB Error",
        })
        assert resp.status_code == 200

    def test_add_unauthorized(self, client, app):
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            orig = u.role
            u.role = "analyst"
            _db.session.commit()
        _login(client, "chemist")
        resp = client.post("/chemicals/add", data={"name": "X"})
        assert resp.status_code == 302
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            u.role = orig
            _db.session.commit()
        client.get("/logout")


class TestChemicalEdit:

    def test_edit_get(self, admin_client, _chemical_item):
        resp = admin_client.get(f"/chemicals/edit/{_chemical_item}")
        assert resp.status_code == 200

    def test_edit_not_found(self, admin_client):
        resp = admin_client.get("/chemicals/edit/999999")
        assert resp.status_code == 404

    @patch("app.routes.chemicals.crud.update_chemical")
    @patch("app.routes.chemicals.crud.safe_commit", return_value=True)
    def test_edit_post_success(self, mc, mock_update, admin_client, _chemical_item):
        resp = admin_client.post(f"/chemicals/edit/{_chemical_item}", data={
            "name": "Updated Chem",
            "quantity": "50",
            "unit": "mL",
        })
        assert resp.status_code == 302

    @patch("app.routes.chemicals.crud.update_chemical", side_effect=ValueError("Bad"))
    def test_edit_post_value_error(self, mock_update, admin_client, _chemical_item):
        resp = admin_client.post(f"/chemicals/edit/{_chemical_item}", data={
            "name": "Bad",
        })
        assert resp.status_code == 200

    @patch("app.routes.chemicals.crud.update_chemical", side_effect=__import__("sqlalchemy").exc.SQLAlchemyError("DB"))
    def test_edit_post_db_error(self, mock_update, admin_client, _chemical_item):
        resp = admin_client.post(f"/chemicals/edit/{_chemical_item}", data={
            "name": "DB Error",
        })
        assert resp.status_code == 200

    def test_edit_unauthorized(self, client, app, _chemical_item):
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            orig = u.role
            u.role = "analyst"
            _db.session.commit()
        _login(client, "chemist")
        resp = client.post(f"/chemicals/edit/{_chemical_item}", data={"name": "X"})
        assert resp.status_code == 302
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            u.role = orig
            _db.session.commit()
        client.get("/logout")


class TestChemicalReceive:

    def test_receive_not_found(self, admin_client):
        resp = admin_client.post("/chemicals/receive/999999", data={"quantity_add": "10"})
        assert resp.status_code == 404

    @patch("app.routes.chemicals.crud.receive_stock")
    @patch("app.routes.chemicals.crud.safe_commit", return_value=True)
    def test_receive_success(self, mc, mock_recv, admin_client, _chemical_item):
        mock_recv.return_value = (True, "Added 10 mL")
        resp = admin_client.post(f"/chemicals/receive/{_chemical_item}", data={
            "quantity_add": "10",
            "lot_number": "LOT-001",
        })
        assert resp.status_code == 302

    @patch("app.routes.chemicals.crud.receive_stock")
    def test_receive_fail(self, mock_recv, admin_client, _chemical_item):
        mock_recv.return_value = (False, "Invalid quantity")
        resp = admin_client.post(f"/chemicals/receive/{_chemical_item}", data={
            "quantity_add": "0",
        })
        assert resp.status_code == 302

    def test_receive_value_error(self, admin_client, _chemical_item):
        resp = admin_client.post(f"/chemicals/receive/{_chemical_item}", data={
            "quantity_add": "not_number",
        })
        assert resp.status_code == 302

    def test_receive_unauthorized(self, client, app, _chemical_item):
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            orig = u.role
            u.role = "analyst"
            _db.session.commit()
        _login(client, "chemist")
        resp = client.post(f"/chemicals/receive/{_chemical_item}", data={"quantity_add": "1"})
        assert resp.status_code == 302
        with app.app_context():
            u = User.query.filter_by(username="chemist").first()
            u.role = orig
            _db.session.commit()
        client.get("/logout")


class TestChemicalConsume:

    def test_consume_not_found(self, admin_client):
        resp = admin_client.post("/chemicals/consume/999999", data={"quantity_used": "5"})
        assert resp.status_code == 404

    @patch("app.routes.chemicals.crud.consume_chemical_stock")
    @patch("app.routes.chemicals.crud.safe_commit", return_value=True)
    def test_consume_success(self, mc, mock_consume, admin_client, _chemical_item):
        mock_result = MagicMock()
        mock_result.success = True
        mock_consume.return_value = mock_result
        resp = admin_client.post(f"/chemicals/consume/{_chemical_item}", data={
            "quantity_used": "5",
            "purpose": "testing",
            "analysis_code": "Mad",
            "sample_id": "123",
        })
        assert resp.status_code == 302

    @patch("app.routes.chemicals.crud.consume_chemical_stock")
    def test_consume_fail(self, mock_consume, admin_client, _chemical_item):
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Insufficient stock"
        mock_consume.return_value = mock_result
        resp = admin_client.post(f"/chemicals/consume/{_chemical_item}", data={
            "quantity_used": "999",
        })
        assert resp.status_code == 302

    def test_consume_value_error(self, admin_client, _chemical_item):
        resp = admin_client.post(f"/chemicals/consume/{_chemical_item}", data={
            "quantity_used": "bad",
        })
        assert resp.status_code == 302

    def test_consume_invalid_sample_id(self, admin_client, _chemical_item):
        """sample_id is non-numeric, should be ignored not crash."""
        with patch("app.routes.chemicals.crud.consume_chemical_stock") as mock_consume:
            mock_result = MagicMock()
            mock_result.success = True
            mock_consume.return_value = mock_result
            with patch("app.routes.chemicals.crud.safe_commit", return_value=True):
                resp = admin_client.post(f"/chemicals/consume/{_chemical_item}", data={
                    "quantity_used": "1",
                    "sample_id": "not_a_number",
                })
            assert resp.status_code == 302
            # sample_id should be None
            call_kwargs = mock_consume.call_args
            assert call_kwargs[1]["sample_id"] is None


class TestChemicalDispose:

    def test_dispose_not_found(self, admin_client):
        resp = admin_client.post("/chemicals/dispose/999999", data={"reason": "test"})
        assert resp.status_code == 404

    @patch("app.routes.chemicals.crud.svc_dispose_chemical")
    @patch("app.routes.chemicals.crud.safe_commit", return_value=True)
    def test_dispose_success(self, mc, mock_dispose, admin_client, _chemical_item):
        resp = admin_client.post(f"/chemicals/dispose/{_chemical_item}", data={
            "reason": "Expired",
        })
        assert resp.status_code == 302

    @patch("app.routes.chemicals.crud.svc_dispose_chemical", side_effect=__import__("sqlalchemy").exc.SQLAlchemyError("DB"))
    def test_dispose_db_error(self, mock_dispose, admin_client, _chemical_item):
        resp = admin_client.post(f"/chemicals/dispose/{_chemical_item}", data={
            "reason": "test",
        })
        assert resp.status_code == 302

    def test_dispose_unauthorized(self, chemist_client, _chemical_item):
        resp = chemist_client.post(f"/chemicals/dispose/{_chemical_item}", data={"reason": "test"})
        assert resp.status_code == 302


class TestChemicalJournal:

    @patch("app.routes.chemicals.crud.get_journal_rows", return_value=[])
    def test_journal_default(self, mock_rows, admin_client):
        resp = admin_client.get("/chemicals/journal")
        assert resp.status_code == 200

    @patch("app.routes.chemicals.crud.get_journal_rows", return_value=[])
    def test_journal_with_filters(self, mock_rows, admin_client):
        resp = admin_client.get("/chemicals/journal?lab=coal&start_date=2026-01-01&end_date=2026-03-10")
        assert resp.status_code == 200
