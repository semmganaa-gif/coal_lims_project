# tests/test_services_chemical_spare.py
# -*- coding: utf-8 -*-
"""
Comprehensive tests for chemical_service.py and spare_parts_service.py.
"""

import os
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

from sqlalchemy.exc import SQLAlchemyError


# =====================================================================
# CHEMICAL SERVICE TESTS
# =====================================================================

class TestChemicalServiceDataClasses:
    """Test ConsumeResult and BulkConsumeResult dataclasses."""

    def test_consume_result_defaults(self, app):
        from app.services.chemical_service import ConsumeResult
        r = ConsumeResult(success=True)
        assert r.success is True
        assert r.new_quantity == 0.0
        assert r.chemical_status == ""
        assert r.error == ""

    def test_consume_result_with_values(self, app):
        from app.services.chemical_service import ConsumeResult
        r = ConsumeResult(success=False, new_quantity=5.0,
                          chemical_status="low_stock", error="test error")
        assert r.success is False
        assert r.new_quantity == 5.0
        assert r.chemical_status == "low_stock"
        assert r.error == "test error"

    def test_bulk_consume_result_defaults(self, app):
        from app.services.chemical_service import BulkConsumeResult
        r = BulkConsumeResult(success=True)
        assert r.success is True
        assert r.count == 0
        assert r.errors == []
        assert r.error == ""

    def test_bulk_consume_result_with_values(self, app):
        from app.services.chemical_service import BulkConsumeResult
        r = BulkConsumeResult(success=True, count=3, errors=["e1"], error="")
        assert r.count == 3
        assert r.errors == ["e1"]


class TestParseDate:
    """Test _parse_date helper."""

    def test_valid_date(self, app):
        from app.services.chemical_service import _parse_date
        result = _parse_date("2026-01-15")
        assert result == date(2026, 1, 15)

    def test_none_input(self, app):
        from app.services.chemical_service import _parse_date
        assert _parse_date(None) is None

    def test_empty_string(self, app):
        from app.services.chemical_service import _parse_date
        assert _parse_date("") is None

    def test_invalid_format(self, app):
        from app.services.chemical_service import _parse_date
        with pytest.raises(ValueError):
            _parse_date("15/01/2026")


class TestCreateChemicalLog:
    """Test create_chemical_log audit helper."""

    def test_creates_log_entry(self, app, db):
        from app.services.chemical_service import create_chemical_log
        from app.models import Chemical, ChemicalLog

        with app.app_context():
            chem = Chemical(name="TestChem", quantity=100, unit="mL")
            db.session.add(chem)
            db.session.flush()

            log = create_chemical_log(
                chemical_id=chem.id, user_id=1, action='created',
                quantity_change=100, quantity_before=0, quantity_after=100,
                details="Test log"
            )

            assert log.chemical_id == chem.id
            assert log.action == 'created'
            assert log.quantity_change == 100
            assert log.data_hash is not None
            assert len(log.data_hash) > 0

            db.session.rollback()


class TestLabConditions:
    """Test _lab_conditions helper (SQLAlchemy 2.0 — Select conditions буцаах)."""

    def test_lab_all_returns_empty(self, app):
        from app.services.chemical_service import _lab_conditions
        with app.app_context():
            assert _lab_conditions("all") == []

    def test_lab_empty_returns_empty(self, app):
        from app.services.chemical_service import _lab_conditions
        with app.app_context():
            assert _lab_conditions("") == []

    def test_lab_specific_returns_condition(self, app):
        from app.services.chemical_service import _lab_conditions
        with app.app_context():
            conds = _lab_conditions("coal")
            assert len(conds) == 1
            # Condition нь or_() — SQL expression
            from sqlalchemy.sql.elements import BooleanClauseList
            assert isinstance(conds[0], BooleanClauseList)


class TestGetChemicalList:
    """Test get_chemical_list function."""

    def test_returns_list(self, app, db):
        from app.services.chemical_service import get_chemical_list
        with app.app_context():
            result = get_chemical_list()
            assert isinstance(result, list)

    def test_with_category_filter(self, app, db):
        from app.services.chemical_service import get_chemical_list
        with app.app_context():
            result = get_chemical_list(category="acid")
            assert isinstance(result, list)

    def test_with_status_filter(self, app, db):
        from app.services.chemical_service import get_chemical_list
        with app.app_context():
            result = get_chemical_list(status="active")
            assert isinstance(result, list)

    def test_expiring_view(self, app, db):
        from app.services.chemical_service import get_chemical_list
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(
                name="Expiring", quantity=10, unit="mL",
                expiry_date=date.today() + timedelta(days=10),
                status='active'
            )
            db.session.add(chem)
            db.session.flush()

            result = get_chemical_list(view="expiring")
            assert isinstance(result, list)
            # Should include the expiring chemical
            names = [r['name'] for r in result]
            assert "Expiring" in names

            db.session.rollback()

    def test_low_stock_view(self, app, db):
        from app.services.chemical_service import get_chemical_list
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(
                name="LowStock", quantity=1, unit="mL",
                reorder_level=5, status='low_stock'
            )
            db.session.add(chem)
            db.session.flush()

            result = get_chemical_list(view="low_stock")
            names = [r['name'] for r in result]
            assert "LowStock" in names

            db.session.rollback()

    def test_disposed_view_shows_disposed(self, app, db):
        from app.services.chemical_service import get_chemical_list
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(
                name="Disposed", quantity=0, unit="mL", status='disposed'
            )
            db.session.add(chem)
            db.session.flush()

            result = get_chemical_list(view="disposed")
            names = [r['name'] for r in result]
            assert "Disposed" in names

            db.session.rollback()


class TestChemicalToListDict:
    """Test _chemical_to_list_dict."""

    def test_all_fields_present(self, app, db):
        from app.services.chemical_service import _chemical_to_list_dict
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(
                name="Test", formula="H2O", cas_number="7732-18-5",
                manufacturer="Sigma", supplier="Fisher", catalog_number="C123",
                lot_number="L001", grade="AR", quantity=50, unit="mL",
                reorder_level=10, received_date=date(2026, 1, 1),
                expiry_date=date(2027, 1, 1), opened_date=date(2026, 2, 1),
                storage_location="Shelf A", storage_conditions="Room temp",
                hazard_class="corrosive", lab_type="coal", category="acid",
                status="active"
            )

            d = _chemical_to_list_dict(chem)
            assert d['name'] == "Test"
            assert d['formula'] == "H2O"
            assert d['received_date'] == "2026-01-01"
            assert d['expiry_date'] == "2027-01-01"
            assert d['opened_date'] == "2026-02-01"

    def test_none_dates(self, app):
        from app.services.chemical_service import _chemical_to_list_dict
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="NoDates", quantity=5, unit="g")
            d = _chemical_to_list_dict(chem)
            assert d['received_date'] is None
            assert d['expiry_date'] is None
            assert d['opened_date'] is None


class TestGetChemicalStatsSummary:
    """Test get_chemical_stats_summary."""

    def test_returns_dict_with_keys(self, app, db):
        from app.services.chemical_service import get_chemical_stats_summary
        with app.app_context():
            result = get_chemical_stats_summary()
            assert 'total' in result
            assert 'low_stock' in result
            assert 'expired' in result


class TestGetChemicalApiList:
    """Test get_chemical_api_list."""

    def test_returns_list_with_flags(self, app, db):
        from app.services.chemical_service import get_chemical_api_list
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(
                name="ApiTest", quantity=10, unit="mL",
                expiry_date=date.today() + timedelta(days=15),
                status='active'
            )
            db.session.add(chem)
            db.session.flush()

            result = get_chemical_api_list()
            api_item = next((r for r in result if r['name'] == 'ApiTest'), None)
            assert api_item is not None
            assert api_item['is_expiring'] is True
            assert api_item['is_expired'] is False
            assert 'is_low_stock' in api_item

            db.session.rollback()

    def test_expired_flag(self, app, db):
        from app.services.chemical_service import get_chemical_api_list
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(
                name="ExpiredApi", quantity=10, unit="mL",
                expiry_date=date.today() - timedelta(days=5),
                status='active'  # not yet updated
            )
            db.session.add(chem)
            db.session.flush()

            result = get_chemical_api_list()
            item = next((r for r in result if r['name'] == 'ExpiredApi'), None)
            assert item is not None
            assert item['is_expired'] is True

            db.session.rollback()

    def test_include_disposed(self, app, db):
        from app.services.chemical_service import get_chemical_api_list
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="DisposedApi", quantity=0, unit="mL", status='disposed')
            db.session.add(chem)
            db.session.flush()

            # Without include_disposed
            result = get_chemical_api_list(include_disposed=False)
            names = [r['name'] for r in result]
            assert "DisposedApi" not in names

            # With include_disposed
            result = get_chemical_api_list(include_disposed=True)
            names = [r['name'] for r in result]
            assert "DisposedApi" in names

            db.session.rollback()

    def test_lab_and_category_filters(self, app, db):
        from app.services.chemical_service import get_chemical_api_list
        with app.app_context():
            result = get_chemical_api_list(lab="coal", category="acid", status="active")
            assert isinstance(result, list)

    def test_no_expiry_date(self, app, db):
        from app.services.chemical_service import get_chemical_api_list
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="NoExpiry", quantity=10, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            result = get_chemical_api_list()
            item = next((r for r in result if r['name'] == 'NoExpiry'), None)
            assert item is not None
            assert item['is_expiring'] is False
            assert item['is_expired'] is False
            assert item['expiry_date'] == ""

            db.session.rollback()


class TestGetLowStockChemicals:
    """Test get_low_stock_chemicals."""

    def test_returns_count_and_items(self, app, db):
        from app.services.chemical_service import get_low_stock_chemicals
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="LowChem", quantity=1, unit="mL",
                            reorder_level=5, status='low_stock', lab_type='coal')
            db.session.add(chem)
            db.session.flush()

            result = get_low_stock_chemicals(lab="coal")
            assert 'count' in result
            assert 'items' in result
            assert result['count'] >= 1

            db.session.rollback()


class TestGetExpiringChemicals:
    """Test get_expiring_chemicals."""

    def test_returns_expiring(self, app, db):
        from app.services.chemical_service import get_expiring_chemicals
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(
                name="ExpSoon", quantity=10, unit="mL",
                expiry_date=date.today() + timedelta(days=10),
                status='active'
            )
            db.session.add(chem)
            db.session.flush()

            result = get_expiring_chemicals(days=30)
            assert result['count'] >= 1
            item = next((i for i in result['items'] if i['name'] == 'ExpSoon'), None)
            assert item is not None
            assert item['days_left'] == 10

            db.session.rollback()

    def test_excludes_disposed(self, app, db):
        from app.services.chemical_service import get_expiring_chemicals
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(
                name="DisposedExp", quantity=0, unit="mL",
                expiry_date=date.today() + timedelta(days=5),
                status='disposed'
            )
            db.session.add(chem)
            db.session.flush()

            result = get_expiring_chemicals()
            names = [i['name'] for i in result['items']]
            assert "DisposedExp" not in names

            db.session.rollback()


class TestSearchChemicals:
    """Test search_chemicals."""

    def test_short_query_returns_empty(self, app, db):
        from app.services.chemical_service import search_chemicals
        with app.app_context():
            result = search_chemicals("a")
            assert result == []

    def test_search_by_name(self, app, db):
        from app.services.chemical_service import search_chemicals
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="Hydrochloric Acid", formula="HCl",
                            quantity=50, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            result = search_chemicals("hydro")
            assert len(result) >= 1
            assert result[0]['name'] == "Hydrochloric Acid"
            assert 'label' in result[0]

            db.session.rollback()

    def test_search_by_formula(self, app, db):
        from app.services.chemical_service import search_chemicals
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="Water", formula="H2O",
                            quantity=100, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            result = search_chemicals("H2O")
            assert len(result) >= 1

            db.session.rollback()

    def test_label_with_formula(self, app, db):
        from app.services.chemical_service import search_chemicals
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="Acid", formula="HCl",
                            quantity=10, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            result = search_chemicals("Acid")
            item = next((r for r in result if r['name'] == 'Acid'), None)
            assert item is not None
            assert item['label'] == "Acid (HCl)"

            db.session.rollback()

    def test_label_without_formula(self, app, db):
        from app.services.chemical_service import search_chemicals
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="Generic Reagent", formula=None,
                            quantity=10, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            result = search_chemicals("Generic")
            item = next((r for r in result if r['name'] == 'Generic Reagent'), None)
            assert item is not None
            assert item['label'] == "Generic Reagent"

            db.session.rollback()

    def test_search_with_lab_filter(self, app, db):
        from app.services.chemical_service import search_chemicals
        with app.app_context():
            result = search_chemicals("test", lab="coal")
            assert isinstance(result, list)


class TestGetChemicalStats:
    """Test get_chemical_stats."""

    def test_returns_all_keys(self, app, db):
        from app.services.chemical_service import get_chemical_stats
        with app.app_context():
            result = get_chemical_stats()
            assert 'total' in result
            assert 'low_stock' in result
            assert 'expired' in result
            assert 'expiring' in result
            assert 'by_category' in result

    def test_with_lab_filter(self, app, db):
        from app.services.chemical_service import get_chemical_stats
        with app.app_context():
            result = get_chemical_stats(lab="water")
            assert isinstance(result['by_category'], dict)


class TestGetUsageHistory:
    """Test get_usage_history."""

    def test_returns_items_and_count(self, app, db):
        from app.services.chemical_service import get_usage_history
        with app.app_context():
            result = get_usage_history()
            assert 'items' in result
            assert 'count' in result

    def test_with_date_filters(self, app, db):
        from app.services.chemical_service import get_usage_history
        with app.app_context():
            result = get_usage_history(
                start_date="2026-01-01",
                end_date="2026-12-31"
            )
            assert 'items' in result

    def test_invalid_date_raises(self, app, db):
        from app.services.chemical_service import get_usage_history
        with app.app_context():
            with pytest.raises(ValueError):
                get_usage_history(start_date="bad-date")

    def test_with_chemical_id(self, app, db):
        from app.services.chemical_service import get_usage_history
        with app.app_context():
            result = get_usage_history(chemical_id=9999)
            assert result['count'] == 0

    def test_with_lab_filter(self, app, db):
        from app.services.chemical_service import get_usage_history
        with app.app_context():
            result = get_usage_history(lab="coal")
            assert isinstance(result['items'], list)


class TestGetJournalRows:
    """Test get_journal_rows."""

    def test_returns_list(self, app, db):
        from app.services.chemical_service import get_journal_rows
        with app.app_context():
            result = get_journal_rows()
            assert isinstance(result, list)

    def test_with_date_filters(self, app, db):
        from app.services.chemical_service import get_journal_rows
        with app.app_context():
            result = get_journal_rows(
                start_date="2026-01-01", end_date="2026-12-31"
            )
            assert isinstance(result, list)

    def test_with_lab_filter(self, app, db):
        from app.services.chemical_service import get_journal_rows
        with app.app_context():
            result = get_journal_rows(lab="water")
            assert isinstance(result, list)


class TestCreateChemical:
    """Test create_chemical."""

    def test_creates_chemical_success(self, app, db):
        from app.services.chemical_service import create_chemical
        with app.app_context():
            data = {
                "name": "Sulfuric Acid",
                "formula": "H2SO4",
                "quantity": 100,
                "unit": "mL",
                "reorder_level": "20",
                "received_date": "2026-01-01",
                "expiry_date": "2027-01-01",
                "lab_type": "coal",
                "category": "acid",
            }
            chem = create_chemical(data, user_id=1)
            assert chem.name == "Sulfuric Acid"
            assert chem.quantity == 100
            assert chem.id is not None  # flushed

            db.session.rollback()

    def test_default_values(self, app, db):
        from app.services.chemical_service import create_chemical
        with app.app_context():
            data = {"name": "Minimal"}
            chem = create_chemical(data, user_id=1)
            assert chem.quantity == 0
            assert chem.unit == "mL"
            assert chem.lab_type == "all"
            assert chem.category == "other"
            assert chem.reorder_level is None

            db.session.rollback()

    def test_empty_quantity_string(self, app, db):
        from app.services.chemical_service import create_chemical
        with app.app_context():
            data = {"name": "EmptyQty", "quantity": ""}
            chem = create_chemical(data, user_id=1)
            assert chem.quantity == 0

            db.session.rollback()


class TestUpdateChemical:
    """Test update_chemical."""

    def test_updates_fields(self, app, db):
        from app.services.chemical_service import update_chemical
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="Old", quantity=50, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            data = {
                "name": "New Name",
                "quantity": 50,
                "unit": "g",
                "reorder_level": "10",
                "lab_type": "water",
                "category": "base",
            }
            update_chemical(chem, data, user_id=1)
            assert chem.name == "New Name"
            assert chem.unit == "g"
            assert chem.reorder_level == 10.0

            db.session.rollback()

    def test_quantity_change_creates_adjusted_log(self, app, db):
        from app.services.chemical_service import update_chemical
        from app.models import Chemical, ChemicalLog

        with app.app_context():
            chem = Chemical(name="AdjTest", quantity=50, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()
            chem_id = chem.id

            data = {"name": "AdjTest", "quantity": 75}
            update_chemical(chem, data, user_id=1)

            logs = ChemicalLog.query.filter_by(chemical_id=chem_id).all()
            actions = [l.action for l in logs]
            assert 'adjusted' in actions
            assert 'updated' in actions

            db.session.rollback()

    def test_no_reorder_level_sets_none(self, app, db):
        from app.services.chemical_service import update_chemical
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="NoReorder", quantity=10, unit="mL",
                            reorder_level=5, status='active')
            db.session.add(chem)
            db.session.flush()

            data = {"name": "NoReorder", "quantity": 10, "reorder_level": ""}
            update_chemical(chem, data, user_id=1)
            assert chem.reorder_level is None

            db.session.rollback()


class TestReceiveStock:
    """Test receive_stock."""

    def test_success(self, app, db):
        from app.services.chemical_service import receive_stock
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="ReceiveTest", quantity=10, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            ok, msg = receive_stock(chem, 50, user_id=1)
            assert ok is True
            assert chem.quantity == 60
            assert "+50" in msg

            db.session.rollback()

    def test_negative_quantity_fails(self, app, db):
        from app.services.chemical_service import receive_stock
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="NegRecv", quantity=10, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            ok, msg = receive_stock(chem, -5, user_id=1)
            assert ok is False

            db.session.rollback()

    def test_zero_quantity_fails(self, app, db):
        from app.services.chemical_service import receive_stock
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="ZeroRecv", quantity=10, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            ok, msg = receive_stock(chem, 0, user_id=1)
            assert ok is False

            db.session.rollback()

    def test_with_lot_and_expiry(self, app, db):
        from app.services.chemical_service import receive_stock
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="LotRecv", quantity=10, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            ok, msg = receive_stock(chem, 5, user_id=1,
                                    lot_number="L999", expiry_date_str="2027-06-01")
            assert ok is True
            assert chem.lot_number == "L999"
            assert chem.expiry_date == date(2027, 6, 1)
            assert chem.received_date == date.today()

            db.session.rollback()


class TestConsumeChemicalStock:
    """Test consume_chemical_stock."""

    def test_success(self, app, db):
        from app.services.chemical_service import consume_chemical_stock
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="ConsumeTest", quantity=100, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            result = consume_chemical_stock(chem, 30, user_id=1, purpose="Testing")
            assert result.success is True
            assert result.new_quantity == 70
            assert chem.quantity == 70

            db.session.rollback()

    def test_negative_quantity_fails(self, app, db):
        from app.services.chemical_service import consume_chemical_stock
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="NegCons", quantity=100, unit="mL", status='active')
            result = consume_chemical_stock(chem, -5, user_id=1)
            assert result.success is False

    def test_zero_quantity_fails(self, app, db):
        from app.services.chemical_service import consume_chemical_stock
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="ZeroCons", quantity=100, unit="mL", status='active')
            result = consume_chemical_stock(chem, 0, user_id=1)
            assert result.success is False

    def test_insufficient_stock(self, app, db):
        from app.services.chemical_service import consume_chemical_stock
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="InsCons", quantity=10, unit="mL", status='active')
            result = consume_chemical_stock(chem, 50, user_id=1)
            assert result.success is False
            assert "Insufficient" in result.error

    def test_sets_opened_date(self, app, db):
        from app.services.chemical_service import consume_chemical_stock
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="OpenDate", quantity=100, unit="mL",
                            status='active', opened_date=None)
            db.session.add(chem)
            db.session.flush()

            consume_chemical_stock(chem, 5, user_id=1)
            assert chem.opened_date == date.today()

            db.session.rollback()

    def test_does_not_override_opened_date(self, app, db):
        from app.services.chemical_service import consume_chemical_stock
        from app.models import Chemical

        with app.app_context():
            orig_date = date(2026, 1, 1)
            chem = Chemical(name="KeepOpen", quantity=100, unit="mL",
                            status='active', opened_date=orig_date)
            db.session.add(chem)
            db.session.flush()

            consume_chemical_stock(chem, 5, user_id=1)
            assert chem.opened_date == orig_date

            db.session.rollback()

    def test_with_sample_id(self, app, db):
        from app.services.chemical_service import consume_chemical_stock
        from app.models import Chemical, ChemicalUsage

        with app.app_context():
            chem = Chemical(name="SampleCons", quantity=100, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            result = consume_chemical_stock(
                chem, 10, user_id=1,
                analysis_code="PH", sample_id=42
            )
            assert result.success is True

            db.session.rollback()


class TestConsumeBulk:
    """Test consume_bulk."""

    def test_empty_items(self, app, db):
        from app.services.chemical_service import consume_bulk
        with app.app_context():
            result = consume_bulk([], user_id=1)
            assert result.success is False
            assert "No items" in result.error

    def test_too_many_items(self, app, db):
        from app.services.chemical_service import consume_bulk
        with app.app_context():
            items = [{"chemical_id": 1, "quantity_used": 1}] * 101
            result = consume_bulk(items, user_id=1)
            assert result.success is False
            assert "100" in result.error

    def test_success(self, app, db):
        from app.services.chemical_service import consume_bulk
        from app.models import Chemical

        with app.app_context():
            c1 = Chemical(name="Bulk1", quantity=100, unit="mL", status='active')
            c2 = Chemical(name="Bulk2", quantity=50, unit="g", status='active')
            db.session.add_all([c1, c2])
            db.session.flush()

            items = [
                {"chemical_id": c1.id, "quantity_used": 10},
                {"chemical_id": c2.id, "quantity_used": 5},
            ]
            result = consume_bulk(items, user_id=1, purpose="Bulk test")
            assert result.success is True
            assert result.count == 2

            db.session.rollback()

    def test_chemical_not_found(self, app, db):
        from app.services.chemical_service import consume_bulk
        with app.app_context():
            items = [{"chemical_id": 99999, "quantity_used": 5}]
            result = consume_bulk(items, user_id=1)
            assert result.success is True
            assert result.count == 0
            assert len(result.errors) == 1

    def test_insufficient_stock_in_bulk(self, app, db):
        from app.services.chemical_service import consume_bulk
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="BulkIns", quantity=5, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            items = [{"chemical_id": chem.id, "quantity_used": 50}]
            result = consume_bulk(items, user_id=1)
            assert result.count == 0
            assert len(result.errors) == 1

            db.session.rollback()

    def test_invalid_quantity_skipped(self, app, db):
        from app.services.chemical_service import consume_bulk
        with app.app_context():
            items = [{"chemical_id": 1, "quantity_used": "abc"}]
            result = consume_bulk(items, user_id=1)
            assert result.count == 0

    def test_zero_quantity_skipped(self, app, db):
        from app.services.chemical_service import consume_bulk
        with app.app_context():
            items = [{"chemical_id": 1, "quantity_used": 0}]
            result = consume_bulk(items, user_id=1)
            assert result.count == 0

    def test_missing_chemical_id_skipped(self, app, db):
        from app.services.chemical_service import consume_bulk
        with app.app_context():
            items = [{"quantity_used": 5}]
            result = consume_bulk(items, user_id=1)
            assert result.count == 0


class TestDisposeChemical:
    """Test dispose_chemical."""

    def test_disposes(self, app, db):
        from app.services.chemical_service import dispose_chemical
        from app.models import Chemical

        with app.app_context():
            chem = Chemical(name="DisposeTest", quantity=50, unit="mL", status='active')
            db.session.add(chem)
            db.session.flush()

            dispose_chemical(chem, user_id=1, reason="Expired")
            assert chem.status == 'disposed'
            assert chem.quantity == 0

            db.session.rollback()


# =====================================================================
# SPARE PARTS SERVICE TESTS
# =====================================================================

class TestAllowedFile:
    """Test allowed_file helper."""

    def test_valid_extensions(self, app):
        from app.services.spare_parts_service import allowed_file
        assert allowed_file("photo.jpg") is True
        assert allowed_file("photo.jpeg") is True
        assert allowed_file("photo.png") is True
        assert allowed_file("photo.gif") is True
        assert allowed_file("photo.webp") is True

    def test_invalid_extensions(self, app):
        from app.services.spare_parts_service import allowed_file
        assert allowed_file("file.exe") is False
        assert allowed_file("file.pdf") is False
        assert allowed_file("file.txt") is False

    def test_no_extension(self, app):
        from app.services.spare_parts_service import allowed_file
        assert allowed_file("noext") is False

    def test_case_insensitive(self, app):
        from app.services.spare_parts_service import allowed_file
        assert allowed_file("PHOTO.JPG") is True
        assert allowed_file("photo.PNG") is True


class TestSaveImageToDisk:
    """Test save_image_to_disk."""

    def test_none_file(self, app):
        from app.services.spare_parts_service import save_image_to_disk
        assert save_image_to_disk(None, "/tmp") is None

    def test_empty_filename(self, app):
        from app.services.spare_parts_service import save_image_to_disk
        mock_file = MagicMock()
        mock_file.filename = ""
        assert save_image_to_disk(mock_file, "/tmp") is None

    def test_invalid_extension(self, app):
        from app.services.spare_parts_service import save_image_to_disk
        mock_file = MagicMock()
        mock_file.filename = "file.exe"
        assert save_image_to_disk(mock_file, "/tmp") is None

    def test_success(self, app, tmp_path):
        from app.services.spare_parts_service import save_image_to_disk
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"

        result = save_image_to_disk(mock_file, str(tmp_path))
        assert result is not None
        assert result.startswith("uploads/spare_parts/")
        assert result.endswith(".jpg")
        mock_file.save.assert_called_once()


class TestDeleteImageFromDisk:
    """Test delete_image_from_disk."""

    def test_none_path(self, app):
        from app.services.spare_parts_service import delete_image_from_disk
        delete_image_from_disk(None, "/tmp")  # should not raise

    def test_empty_path(self, app):
        from app.services.spare_parts_service import delete_image_from_disk
        delete_image_from_disk("", "/tmp")  # should not raise

    def test_deletes_existing_file(self, app, tmp_path):
        from app.services.spare_parts_service import delete_image_from_disk
        # Create a test file
        static_dir = tmp_path / "static" / "uploads" / "spare_parts"
        static_dir.mkdir(parents=True)
        test_file = static_dir / "test.jpg"
        test_file.write_text("fake image")

        delete_image_from_disk("uploads/spare_parts/test.jpg", str(tmp_path))
        assert not test_file.exists()

    def test_nonexistent_file(self, app, tmp_path):
        from app.services.spare_parts_service import delete_image_from_disk
        # Should not raise even if file doesn't exist
        delete_image_from_disk("uploads/spare_parts/nonexistent.jpg", str(tmp_path))


class TestLogSparePartAction:
    """Test log_spare_part_action audit function."""

    def test_creates_log(self, app, db):
        from app.services.spare_parts_service import log_spare_part_action
        from app.models import SparePart, SparePartLog

        with app.app_context():
            sp = SparePart(name="LogTest", quantity=10, unit="pcs")
            db.session.add(sp)
            db.session.flush()

            log_spare_part_action(sp, 'created', user_id=1,
                                  quantity_change=10, quantity_before=0,
                                  quantity_after=10, details="Test")

            logs = SparePartLog.query.filter_by(spare_part_id=sp.id).all()
            assert len(logs) == 1
            assert logs[0].action == 'created'
            assert logs[0].data_hash is not None

            db.session.rollback()


class TestGetCategories:
    """Test category query functions."""

    def test_get_categories(self, app, db):
        from app.services.spare_parts_service import get_categories
        from app.models import SparePartCategory

        with app.app_context():
            cat = SparePartCategory(code="test_cat", name="Test Cat", is_active=True, sort_order=0)
            db.session.add(cat)
            db.session.flush()

            result = get_categories()
            assert isinstance(result, list)
            codes = [c[0] for c in result]
            assert "test_cat" in codes

            db.session.rollback()

    def test_get_categories_dict(self, app, db):
        from app.services.spare_parts_service import get_categories_dict
        from app.models import SparePartCategory

        with app.app_context():
            cat = SparePartCategory(code="dict_cat", name="Dict Cat", is_active=True)
            db.session.add(cat)
            db.session.flush()

            result = get_categories_dict()
            assert isinstance(result, dict)
            assert "dict_cat" in result
            assert result["dict_cat"] == "Dict Cat"

            db.session.rollback()

    def test_get_all_categories_ordered(self, app, db):
        from app.services.spare_parts_service import get_all_categories_ordered
        with app.app_context():
            result = get_all_categories_ordered()
            assert isinstance(result, list)


class TestCreateCategory:
    """Test create_category."""

    def test_success(self, app, db):
        from app.services.spare_parts_service import create_category
        with app.app_context():
            cat, err = create_category("new_cat", "New Category",
                                       name_en="New Cat EN", sort_order=5)
            assert cat is not None
            assert err is None
            assert cat.code == "new_cat"
            assert cat.name == "New Category"

            db.session.rollback()

    def test_missing_code(self, app, db):
        from app.services.spare_parts_service import create_category
        with app.app_context():
            cat, err = create_category("", "Name")
            assert cat is None
            assert err is not None

    def test_missing_name(self, app, db):
        from app.services.spare_parts_service import create_category
        with app.app_context():
            cat, err = create_category("code", "")
            assert cat is None
            assert err is not None

    def test_duplicate_code(self, app, db):
        from app.services.spare_parts_service import create_category
        from app.models import SparePartCategory

        with app.app_context():
            existing = SparePartCategory(code="dup_cat", name="Existing", is_active=True)
            db.session.add(existing)
            db.session.flush()

            cat, err = create_category("dup_cat", "Another")
            assert cat is None
            assert "dup_cat" in err

            db.session.rollback()


class TestUpdateCategory:
    """Test update_category."""

    def test_success(self, app, db):
        from app.services.spare_parts_service import update_category
        from app.models import SparePartCategory

        with app.app_context():
            cat = SparePartCategory(code="upd_cat", name="Old", is_active=True)
            db.session.add(cat)
            db.session.flush()

            result, err = update_category(cat.id, "Updated Name",
                                          name_en="Updated EN", sort_order=10)
            assert result is not None
            assert err is None
            assert result.name == "Updated Name"

            db.session.rollback()

    def test_not_found(self, app, db):
        from app.services.spare_parts_service import update_category
        with app.app_context():
            result, err = update_category(99999, "Name")
            assert result is None
            assert err == 'not_found'


class TestDeleteCategory:
    """Test delete_category."""

    def test_success(self, app, db):
        from app.services.spare_parts_service import delete_category
        from app.models import SparePartCategory

        with app.app_context():
            cat = SparePartCategory(code="del_cat", name="To Delete", is_active=True)
            db.session.add(cat)
            db.session.flush()

            name, err = delete_category(cat.id)
            assert name == "To Delete"
            assert err is None

            db.session.rollback()

    def test_not_found(self, app, db):
        from app.services.spare_parts_service import delete_category
        with app.app_context():
            name, err = delete_category(99999)
            assert name is None
            assert err == 'not_found'

    def test_has_spare_parts(self, app, db):
        from app.services.spare_parts_service import delete_category
        from app.models import SparePartCategory, SparePart

        with app.app_context():
            cat = SparePartCategory(code="used_cat", name="Used", is_active=True)
            db.session.add(cat)
            db.session.flush()

            sp = SparePart(name="Part", quantity=1, unit="pcs", category="used_cat")
            db.session.add(sp)
            db.session.flush()

            name, err = delete_category(cat.id)
            assert name is None
            assert "used_cat" in err or "Used" in err

            db.session.rollback()


class TestGetSparePartsFiltered:
    """Test get_spare_parts_filtered."""

    def test_returns_list(self, app, db):
        from app.services.spare_parts_service import get_spare_parts_filtered
        with app.app_context():
            result = get_spare_parts_filtered()
            assert isinstance(result, list)

    def test_with_category(self, app, db):
        from app.services.spare_parts_service import get_spare_parts_filtered
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="Filter1", quantity=10, unit="pcs",
                           category="filter", status="active")
            db.session.add(sp)
            db.session.flush()

            result = get_spare_parts_filtered(category="filter")
            names = [r['name'] for r in result]
            assert "Filter1" in names

            db.session.rollback()

    def test_with_status(self, app, db):
        from app.services.spare_parts_service import get_spare_parts_filtered
        with app.app_context():
            result = get_spare_parts_filtered(status="active")
            assert isinstance(result, list)

    def test_low_stock_view(self, app, db):
        from app.services.spare_parts_service import get_spare_parts_filtered
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="LowSP", quantity=0, unit="pcs",
                           status="out_of_stock")
            db.session.add(sp)
            db.session.flush()

            result = get_spare_parts_filtered(view="low_stock")
            names = [r['name'] for r in result]
            assert "LowSP" in names

            db.session.rollback()

    def test_disposed_view(self, app, db):
        from app.services.spare_parts_service import get_spare_parts_filtered
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="DisposedSP", quantity=0, unit="pcs",
                           status="disposed")
            db.session.add(sp)
            db.session.flush()

            result = get_spare_parts_filtered(view="disposed")
            names = [r['name'] for r in result]
            assert "DisposedSP" in names

            db.session.rollback()

    def test_hides_disposed_by_default(self, app, db):
        from app.services.spare_parts_service import get_spare_parts_filtered
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="HiddenDisposed", quantity=0, unit="pcs",
                           status="disposed")
            db.session.add(sp)
            db.session.flush()

            result = get_spare_parts_filtered()
            names = [r['name'] for r in result]
            assert "HiddenDisposed" not in names

            db.session.rollback()

    def test_equipment_name(self, app, db):
        from app.services.spare_parts_service import get_spare_parts_filtered
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="NoEquip", quantity=10, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()

            result = get_spare_parts_filtered()
            item = next((r for r in result if r['name'] == 'NoEquip'), None)
            assert item is not None
            assert item['equipment_name'] is None

            db.session.rollback()


class TestGetSparePartsListSimple:
    """Test get_spare_parts_list_simple."""

    def test_returns_list(self, app, db):
        from app.services.spare_parts_service import get_spare_parts_list_simple
        with app.app_context():
            result = get_spare_parts_list_simple()
            assert isinstance(result, list)


class TestGetLowStockParts:
    """Test get_low_stock_parts."""

    def test_returns_low_stock(self, app, db):
        from app.services.spare_parts_service import get_low_stock_parts
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="LowPart", quantity=0, unit="pcs",
                           status="out_of_stock")
            db.session.add(sp)
            db.session.flush()

            result = get_low_stock_parts()
            names = [r['name'] for r in result]
            assert "LowPart" in names

            db.session.rollback()


class TestSearchSpareParts:
    """Test search_spare_parts."""

    def test_short_query(self, app, db):
        from app.services.spare_parts_service import search_spare_parts
        with app.app_context():
            assert search_spare_parts("a") == []

    def test_none_query(self, app, db):
        from app.services.spare_parts_service import search_spare_parts
        with app.app_context():
            assert search_spare_parts(None) == []

    def test_empty_query(self, app, db):
        from app.services.spare_parts_service import search_spare_parts
        with app.app_context():
            assert search_spare_parts("") == []

    def test_search_by_name(self, app, db):
        from app.services.spare_parts_service import search_spare_parts
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="HEPA Filter XL", quantity=5, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()

            result = search_spare_parts("HEPA")
            assert len(result) >= 1
            assert result[0]['name'] == "HEPA Filter XL"

            db.session.rollback()


class TestGetListStats:
    """Test get_list_stats."""

    def test_returns_keys(self, app, db):
        from app.services.spare_parts_service import get_list_stats
        with app.app_context():
            result = get_list_stats()
            assert 'total' in result
            assert 'low_stock' in result
            assert 'out_of_stock' in result


class TestGetFullStats:
    """Test get_full_stats."""

    def test_returns_all_keys(self, app, db):
        from app.services.spare_parts_service import get_full_stats
        with app.app_context():
            result = get_full_stats()
            assert 'total' in result
            assert 'active' in result
            assert 'low_stock' in result
            assert 'out_of_stock' in result
            assert 'total_value' in result
            assert isinstance(result['total_value'], float)


class TestParseIntSafe:
    """Test _parse_int_safe helper."""

    def test_valid_string(self, app):
        from app.services.spare_parts_service import _parse_int_safe
        assert _parse_int_safe("42") == 42

    def test_int_input(self, app):
        from app.services.spare_parts_service import _parse_int_safe
        assert _parse_int_safe(10) == 10

    def test_empty_string(self, app):
        from app.services.spare_parts_service import _parse_int_safe
        assert _parse_int_safe("") is None

    def test_none(self, app):
        from app.services.spare_parts_service import _parse_int_safe
        assert _parse_int_safe(None) is None

    def test_whitespace_string(self, app):
        from app.services.spare_parts_service import _parse_int_safe
        assert _parse_int_safe("  ") is None

    def test_float_input(self, app):
        from app.services.spare_parts_service import _parse_int_safe
        # float is not str and not int -> None
        assert _parse_int_safe(3.5) is None


class TestCreateSparePart:
    """Test create_spare_part."""

    def test_success(self, app, db):
        from app.services.spare_parts_service import create_spare_part
        with app.app_context():
            data = {
                'name': 'Test Part',
                'name_en': 'Test Part EN',
                'part_number': 'TP-001',
                'quantity': '10',
                'unit': 'pcs',
                'reorder_level': '3',
                'unit_price': '25.50',
                'category': 'filter',
                'storage_location': 'Shelf B',
            }
            sp, err = create_spare_part(data, user_id=1)
            assert sp is not None
            assert err is None
            assert sp.name == 'Test Part'
            assert sp.id is not None

            db.session.rollback()

    def test_with_equipment_id(self, app, db):
        from app.services.spare_parts_service import create_spare_part
        from app.models import Equipment

        with app.app_context():
            equip = Equipment(name="TestEquip")
            db.session.add(equip)
            db.session.flush()

            data = {
                'name': 'Equip Part',
                'quantity': '5',
                'equipment_id': str(equip.id),
            }
            sp, err = create_spare_part(data, user_id=1)
            assert sp is not None
            assert sp.equipment_id == equip.id

            db.session.rollback()

    def test_with_image_path(self, app, db):
        from app.services.spare_parts_service import create_spare_part
        with app.app_context():
            data = {
                'name': 'Image Part',
                'quantity': '1',
                'image_path': 'uploads/spare_parts/test.jpg',
            }
            sp, err = create_spare_part(data, user_id=1)
            assert sp is not None
            assert sp.image_path == 'uploads/spare_parts/test.jpg'

            db.session.rollback()

    def test_default_values(self, app, db):
        from app.services.spare_parts_service import create_spare_part
        with app.app_context():
            data = {'name': 'MinimalPart'}
            sp, err = create_spare_part(data, user_id=1)
            assert sp is not None
            assert sp.unit == 'pcs'
            assert sp.category == 'general'
            assert sp.quantity == 0

            db.session.rollback()


class TestUpdateSparePart:
    """Test update_spare_part."""

    def test_success(self, app, db):
        from app.services.spare_parts_service import update_spare_part
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="Old Part", quantity=10, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()
            sp_id = sp.id

            data = {
                'name': 'Updated Part',
                'quantity': '15',
                'unit': 'set',
                'category': 'belt',
            }
            result, err = update_spare_part(sp_id, data, user_id=1)
            assert result is not None
            assert err is None
            assert result.name == 'Updated Part'

            db.session.rollback()

    def test_not_found(self, app, db):
        from app.services.spare_parts_service import update_spare_part
        with app.app_context():
            result, err = update_spare_part(99999, {'name': 'X'}, user_id=1)
            assert result is None
            assert err == 'not_found'

    def test_quantity_change_logs(self, app, db):
        from app.services.spare_parts_service import update_spare_part
        from app.models import SparePart, SparePartLog

        with app.app_context():
            sp = SparePart(name="QtyChange", quantity=10, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()
            sp_id = sp.id

            data = {'name': 'QtyChange', 'quantity': '20'}
            update_spare_part(sp_id, data, user_id=1)

            logs = SparePartLog.query.filter_by(spare_part_id=sp_id).all()
            actions = [l.action for l in logs]
            assert 'adjusted' in actions

            db.session.rollback()

    def test_with_image_path_in_data(self, app, db):
        from app.services.spare_parts_service import update_spare_part
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="ImgPart", quantity=5, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()

            data = {
                'name': 'ImgPart',
                'quantity': '5',
                'image_path': 'uploads/spare_parts/new.jpg',
            }
            result, err = update_spare_part(sp.id, data, user_id=1)
            assert result.image_path == 'uploads/spare_parts/new.jpg'

            db.session.rollback()

    def test_clear_equipment_id(self, app, db):
        from app.services.spare_parts_service import update_spare_part
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="ClearEquip", quantity=5, unit="pcs",
                           status="active", equipment_id=1)
            db.session.add(sp)
            db.session.flush()

            data = {'name': 'ClearEquip', 'quantity': '5', 'equipment_id': ''}
            result, err = update_spare_part(sp.id, data, user_id=1)
            assert result.equipment_id is None

            db.session.rollback()


class TestSpareReceiveStock:
    """Test spare_parts_service.receive_stock."""

    def test_success(self, app, db):
        from app.services.spare_parts_service import receive_stock
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="RecvPart", quantity=10, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()

            result, err = receive_stock(sp.id, 5, user_id=1, notes="New batch")
            assert result is not None
            assert err is None
            assert result['new_total'] == 15
            assert result['quantity_added'] == 5

            db.session.rollback()

    def test_not_found(self, app, db):
        from app.services.spare_parts_service import receive_stock
        with app.app_context():
            result, err = receive_stock(99999, 5, user_id=1)
            assert result is None
            assert err == 'not_found'

    def test_zero_quantity(self, app, db):
        from app.services.spare_parts_service import receive_stock
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="ZeroRecv", quantity=10, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()

            result, err = receive_stock(sp.id, 0, user_id=1)
            assert result is None
            assert err is not None

            db.session.rollback()

    def test_negative_quantity(self, app, db):
        from app.services.spare_parts_service import receive_stock
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="NegRecv", quantity=10, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()

            result, err = receive_stock(sp.id, -3, user_id=1)
            assert result is None

            db.session.rollback()


class TestSpareConsumeStock:
    """Test spare_parts_service.consume_stock."""

    def test_success(self, app, db):
        from app.services.spare_parts_service import consume_stock
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="ConsPart", quantity=20, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()

            result, err = consume_stock(sp.id, 5, user_id=1, purpose="Repair")
            assert result is not None
            assert err is None
            assert result['remaining'] == 15
            assert result['consumed'] == 5

            db.session.rollback()

    def test_not_found(self, app, db):
        from app.services.spare_parts_service import consume_stock
        with app.app_context():
            result, err = consume_stock(99999, 5, user_id=1)
            assert result is None
            assert err == 'not_found'

    def test_zero_quantity(self, app, db):
        from app.services.spare_parts_service import consume_stock
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="ZeroCons", quantity=10, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()

            result, err = consume_stock(sp.id, 0, user_id=1)
            assert result is None

            db.session.rollback()

    def test_insufficient_stock(self, app, db):
        from app.services.spare_parts_service import consume_stock
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="InsCons", quantity=3, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()

            result, err = consume_stock(sp.id, 10, user_id=1)
            assert result is None
            assert "3" in err  # available quantity in message

            db.session.rollback()

    def test_with_equipment_and_maintenance(self, app, db):
        from app.services.spare_parts_service import consume_stock
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="EquipCons", quantity=20, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()

            result, err = consume_stock(
                sp.id, 2, user_id=1,
                equipment_id=1, maintenance_log_id=1,
                purpose="Scheduled maintenance", notes="Replaced filter"
            )
            assert result is not None

            db.session.rollback()


class TestConsumeStockBulk:
    """Test consume_stock_bulk."""

    def test_success(self, app, db):
        from app.services.spare_parts_service import consume_stock_bulk
        from app.models import SparePart

        with app.app_context():
            sp1 = SparePart(name="Bulk1", quantity=20, unit="pcs", status="active")
            sp2 = SparePart(name="Bulk2", quantity=15, unit="pcs", status="active")
            db.session.add_all([sp1, sp2])
            db.session.flush()

            items = [
                {'spare_part_id': sp1.id, 'quantity': 5},
                {'spare_part_id': sp2.id, 'quantity': 3},
            ]
            results, errors = consume_stock_bulk(items, user_id=1, purpose="Bulk repair")
            assert len(results) == 2
            assert len(errors) == 0

            db.session.rollback()

    def test_not_found_in_bulk(self, app, db):
        from app.services.spare_parts_service import consume_stock_bulk
        with app.app_context():
            items = [{'spare_part_id': 99999, 'quantity': 5}]
            results, errors = consume_stock_bulk(items, user_id=1)
            assert len(results) == 0
            assert len(errors) == 1

    def test_insufficient_in_bulk(self, app, db):
        from app.services.spare_parts_service import consume_stock_bulk
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="BulkIns", quantity=2, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()

            items = [{'spare_part_id': sp.id, 'quantity': 50}]
            results, errors = consume_stock_bulk(items, user_id=1)
            assert len(results) == 0
            assert len(errors) == 1

            db.session.rollback()


class TestDisposeSparePart:
    """Test dispose_spare_part."""

    def test_success(self, app, db):
        from app.services.spare_parts_service import dispose_spare_part
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="DisposePart", quantity=10, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()

            name, err = dispose_spare_part(sp.id, user_id=1, reason="Broken")
            assert name == "DisposePart"
            assert err is None
            assert sp.status == 'disposed'
            assert sp.quantity == 0

            db.session.rollback()

    def test_not_found(self, app, db):
        from app.services.spare_parts_service import dispose_spare_part
        with app.app_context():
            name, err = dispose_spare_part(99999, user_id=1)
            assert name is None
            assert err == 'not_found'


class TestDeleteSparePartPermanently:
    """Test delete_spare_part_permanently."""

    def test_success(self, app, db):
        from app.services.spare_parts_service import delete_spare_part_permanently
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="DeletePerm", quantity=0, unit="pcs", status="disposed")
            db.session.add(sp)
            db.session.flush()

            name, err = delete_spare_part_permanently(sp.id)
            assert name == "DeletePerm"
            assert err is None

            db.session.rollback()

    def test_not_found(self, app, db):
        from app.services.spare_parts_service import delete_spare_part_permanently
        with app.app_context():
            name, err = delete_spare_part_permanently(99999)
            assert name is None
            assert err == 'not_found'


class TestGetDetailData:
    """Test get_detail_data."""

    def test_found(self, app, db):
        from app.services.spare_parts_service import get_detail_data
        from app.models import SparePart

        with app.app_context():
            sp = SparePart(name="DetailPart", quantity=10, unit="pcs", status="active")
            db.session.add(sp)
            db.session.flush()

            spare_part, usages, logs = get_detail_data(sp.id)
            assert spare_part is not None
            assert spare_part.name == "DetailPart"
            assert isinstance(usages, list)
            assert isinstance(logs, list)

            db.session.rollback()

    def test_not_found(self, app, db):
        from app.services.spare_parts_service import get_detail_data
        with app.app_context():
            sp, usages, logs = get_detail_data(99999)
            assert sp is None
            assert usages is None
            assert logs is None


class TestSpareGetUsageHistory:
    """Test spare_parts_service.get_usage_history."""

    def test_returns_list(self, app, db):
        from app.services.spare_parts_service import get_usage_history
        with app.app_context():
            result = get_usage_history(spare_part_id=99999)
            assert isinstance(result, list)
            assert len(result) == 0
