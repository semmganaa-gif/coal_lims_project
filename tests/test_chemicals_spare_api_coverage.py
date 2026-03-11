# tests/test_chemicals_spare_api_coverage.py
# -*- coding: utf-8 -*-
"""
Coverage tests for:
  - app/routes/chemicals/api.py
  - app/routes/spare_parts/api.py

Targets 80%+ line coverage via mocked service functions.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def logged_in_client(app, client, db):
    """Create and log in a test user for API tests."""
    with app.app_context():
        from app.models import User
        user = User.query.filter_by(username='testapi').first()
        if not user:
            user = User(username='testapi', role='analyst')
            user.set_password('TestPass123!')
            db.session.add(user)
            db.session.commit()
        client.post('/login', data={'username': 'testapi', 'password': 'TestPass123!'})
        return client


# ===========================================================================
# CHEMICALS API  — /chemicals/api/...
# ===========================================================================


class TestChemicalApiList:
    """GET /chemicals/api/list"""

    @patch('app.services.chemical_service.get_chemical_api_list')
    def test_list_default_params(self, mock_fn, logged_in_client):
        mock_fn.return_value = [{'id': 1, 'name': 'HCl'}]
        resp = logged_in_client.get('/chemicals/api/list')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        mock_fn.assert_called_once_with(
            lab='all', category='all', status='all', include_disposed=False
        )

    @patch('app.services.chemical_service.get_chemical_api_list')
    def test_list_with_filters(self, mock_fn, logged_in_client):
        mock_fn.return_value = []
        resp = logged_in_client.get(
            '/chemicals/api/list?lab=coal&category=acid&status=low_stock&include_disposed=true'
        )
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(
            lab='coal', category='acid', status='low_stock', include_disposed=True
        )

    @patch('app.services.chemical_service.get_chemical_api_list')
    def test_list_include_disposed_false_explicit(self, mock_fn, logged_in_client):
        mock_fn.return_value = []
        resp = logged_in_client.get('/chemicals/api/list?include_disposed=false')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(
            lab='all', category='all', status='all', include_disposed=False
        )

    def test_list_unauthenticated(self, client):
        resp = client.get('/chemicals/api/list')
        assert resp.status_code in (302, 401)


class TestChemicalApiLowStock:
    """GET /chemicals/api/low_stock"""

    @patch('app.services.chemical_service.get_low_stock_chemicals')
    def test_low_stock_default(self, mock_fn, logged_in_client):
        mock_fn.return_value = [{'id': 2, 'name': 'NaOH', 'quantity': 5}]
        resp = logged_in_client.get('/chemicals/api/low_stock')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(lab='all')

    @patch('app.services.chemical_service.get_low_stock_chemicals')
    def test_low_stock_with_lab(self, mock_fn, logged_in_client):
        mock_fn.return_value = []
        resp = logged_in_client.get('/chemicals/api/low_stock?lab=water')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(lab='water')


class TestChemicalApiExpiring:
    """GET /chemicals/api/expiring"""

    @patch('app.services.chemical_service.get_expiring_chemicals')
    def test_expiring_default_days(self, mock_fn, logged_in_client):
        mock_fn.return_value = []
        resp = logged_in_client.get('/chemicals/api/expiring')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(lab='all', days=30)

    @patch('app.services.chemical_service.get_expiring_chemicals')
    def test_expiring_custom_days(self, mock_fn, logged_in_client):
        mock_fn.return_value = [{'id': 3}]
        resp = logged_in_client.get('/chemicals/api/expiring?days=7&lab=coal')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(lab='coal', days=7)

    @patch('app.services.chemical_service.get_expiring_chemicals')
    def test_expiring_invalid_days_falls_back(self, mock_fn, logged_in_client):
        mock_fn.return_value = []
        resp = logged_in_client.get('/chemicals/api/expiring?days=abc')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(lab='all', days=30)

    @patch('app.services.chemical_service.get_expiring_chemicals')
    def test_expiring_none_days_falls_back(self, mock_fn, logged_in_client):
        """days=None (TypeError branch)."""
        mock_fn.return_value = []
        # A request with days= empty string triggers ValueError in int()
        resp = logged_in_client.get('/chemicals/api/expiring?days=')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(lab='all', days=30)


class TestChemicalApiConsume:
    """POST /chemicals/api/consume"""

    @patch('app.routes.chemicals.api.db')
    @patch('app.services.chemical_service.consume_chemical_stock')
    @patch('app.routes.chemicals.api.Chemical')
    def test_consume_success(self, MockChemical, mock_consume, mock_db, logged_in_client):
        chem = MagicMock()
        chem.unit = 'mL'
        mock_db.session.get.return_value = chem
        result = MagicMock(success=True, new_quantity=90.0, chemical_status='active')
        mock_consume.return_value = result

        resp = logged_in_client.post('/chemicals/api/consume', json={
            'chemical_id': 1, 'quantity_used': 10.0, 'purpose': 'test'
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['new_quantity'] == 90.0

    @patch('app.routes.chemicals.api.db')
    @patch('app.services.chemical_service.consume_chemical_stock')
    @patch('app.routes.chemicals.api.Chemical')
    def test_consume_with_sample_id(self, MockChemical, mock_consume, mock_db, logged_in_client):
        chem = MagicMock(unit='g')
        mock_db.session.get.return_value = chem
        result = MagicMock(success=True, new_quantity=45.0, chemical_status='active')
        mock_consume.return_value = result

        resp = logged_in_client.post('/chemicals/api/consume', json={
            'chemical_id': 1, 'quantity_used': 5.0, 'sample_id': 42,
            'analysis_code': 'St,d'
        })
        assert resp.status_code == 200
        # Verify sample_id was parsed as int
        call_kwargs = mock_consume.call_args[1]
        assert call_kwargs['sample_id'] == 42

    @patch('app.routes.chemicals.api.db')
    @patch('app.services.chemical_service.consume_chemical_stock')
    @patch('app.routes.chemicals.api.Chemical')
    def test_consume_invalid_sample_id_ignored(self, MockChemical, mock_consume, mock_db, logged_in_client):
        chem = MagicMock(unit='mL')
        mock_db.session.get.return_value = chem
        result = MagicMock(success=True, new_quantity=80.0, chemical_status='active')
        mock_consume.return_value = result

        resp = logged_in_client.post('/chemicals/api/consume', json={
            'chemical_id': 1, 'quantity_used': 5.0, 'sample_id': 'bad'
        })
        assert resp.status_code == 200
        call_kwargs = mock_consume.call_args[1]
        assert call_kwargs['sample_id'] is None

    def test_consume_missing_chemical_id(self, logged_in_client):
        resp = logged_in_client.post('/chemicals/api/consume', json={
            'quantity_used': 10.0
        })
        data = resp.get_json()
        assert data['success'] is False

    def test_consume_zero_quantity(self, logged_in_client):
        resp = logged_in_client.post('/chemicals/api/consume', json={
            'chemical_id': 1, 'quantity_used': 0
        })
        data = resp.get_json()
        assert data['success'] is False

    def test_consume_negative_quantity(self, logged_in_client):
        resp = logged_in_client.post('/chemicals/api/consume', json={
            'chemical_id': 1, 'quantity_used': -5
        })
        data = resp.get_json()
        assert data['success'] is False

    def test_consume_invalid_quantity_string(self, logged_in_client):
        resp = logged_in_client.post('/chemicals/api/consume', json={
            'chemical_id': 1, 'quantity_used': 'abc'
        })
        data = resp.get_json()
        assert data['success'] is False
        assert 'Invalid quantity' in data.get('error', '')

    @patch('app.routes.chemicals.api.db')
    @patch('app.routes.chemicals.api.Chemical')
    def test_consume_chemical_not_found(self, MockChemical, mock_db, logged_in_client):
        mock_db.session.get.return_value = None
        resp = logged_in_client.post('/chemicals/api/consume', json={
            'chemical_id': 999, 'quantity_used': 10.0
        })
        assert resp.status_code == 404
        data = resp.get_json()
        assert data['success'] is False

    @patch('app.routes.chemicals.api.db')
    @patch('app.services.chemical_service.consume_chemical_stock')
    @patch('app.routes.chemicals.api.Chemical')
    def test_consume_service_returns_failure(self, MockChemical, mock_consume, mock_db, logged_in_client):
        chem = MagicMock(unit='mL')
        mock_db.session.get.return_value = chem
        result = MagicMock(success=False, error='Insufficient stock')
        mock_consume.return_value = result

        resp = logged_in_client.post('/chemicals/api/consume', json={
            'chemical_id': 1, 'quantity_used': 10.0
        })
        data = resp.get_json()
        assert data['success'] is False
        assert 'Insufficient stock' in data.get('error', '')

    @patch('app.routes.chemicals.api.db')
    @patch('app.services.chemical_service.consume_chemical_stock')
    @patch('app.routes.chemicals.api.Chemical')
    def test_consume_commit_error(self, MockChemical, mock_consume, mock_db, logged_in_client):
        chem = MagicMock(unit='mL')
        mock_db.session.get.return_value = chem
        result = MagicMock(success=True, new_quantity=90.0, chemical_status='active')
        mock_consume.return_value = result
        mock_db.session.commit.side_effect = SQLAlchemyError('DB error')

        resp = logged_in_client.post('/chemicals/api/consume', json={
            'chemical_id': 1, 'quantity_used': 10.0
        })
        assert resp.status_code == 500
        data = resp.get_json()
        assert data['success'] is False

    def test_consume_empty_json(self, logged_in_client):
        resp = logged_in_client.post('/chemicals/api/consume',
                                     data='', content_type='application/json')
        data = resp.get_json()
        assert data['success'] is False

    @patch('app.routes.chemicals.api.db')
    @patch('app.routes.chemicals.api.Chemical')
    def test_consume_outer_valueerror(self, MockChemical, mock_db, logged_in_client):
        """Trigger the outer (ValueError, TypeError) except block."""
        mock_db.session.get.side_effect = ValueError('unexpected')
        resp = logged_in_client.post('/chemicals/api/consume', json={
            'chemical_id': 1, 'quantity_used': 5.0
        })
        assert resp.status_code == 500
        data = resp.get_json()
        assert data['success'] is False
        assert 'consumption failed' in data.get('error', '').lower()


class TestChemicalApiSearch:
    """GET /chemicals/api/search"""

    @patch('app.services.chemical_service.search_chemicals')
    def test_search_default(self, mock_fn, logged_in_client):
        mock_fn.return_value = []
        resp = logged_in_client.get('/chemicals/api/search')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(q='', lab='all', limit=20)

    @patch('app.services.chemical_service.search_chemicals')
    def test_search_with_query(self, mock_fn, logged_in_client):
        mock_fn.return_value = [{'id': 1, 'name': 'HCl'}]
        resp = logged_in_client.get('/chemicals/api/search?q=HCl&lab=coal&limit=5')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(q='HCl', lab='coal', limit=5)

    @patch('app.services.chemical_service.search_chemicals')
    def test_search_invalid_limit(self, mock_fn, logged_in_client):
        mock_fn.return_value = []
        resp = logged_in_client.get('/chemicals/api/search?q=test&limit=xyz')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(q='test', lab='all', limit=20)

    @patch('app.services.chemical_service.search_chemicals')
    def test_search_strips_whitespace(self, mock_fn, logged_in_client):
        mock_fn.return_value = []
        resp = logged_in_client.get('/chemicals/api/search?q=%20NaOH%20')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(q='NaOH', lab='all', limit=20)


class TestChemicalApiStats:
    """GET /chemicals/api/stats"""

    @patch('app.services.chemical_service.get_chemical_stats')
    def test_stats_default(self, mock_fn, logged_in_client):
        mock_fn.return_value = {'total': 50, 'low_stock': 3}
        resp = logged_in_client.get('/chemicals/api/stats')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(lab='all')

    @patch('app.services.chemical_service.get_chemical_stats')
    def test_stats_with_lab(self, mock_fn, logged_in_client):
        mock_fn.return_value = {'total': 10}
        resp = logged_in_client.get('/chemicals/api/stats?lab=water')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(lab='water')


class TestChemicalApiUsageHistory:
    """GET /chemicals/api/usage_history"""

    @patch('app.services.chemical_service.get_usage_history')
    def test_usage_history_default(self, mock_fn, logged_in_client):
        mock_fn.return_value = {'items': [], 'count': 0}
        resp = logged_in_client.get('/chemicals/api/usage_history')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(
            chemical_id=None, lab='all',
            start_date=None, end_date=None, limit=100
        )

    @patch('app.services.chemical_service.get_usage_history')
    def test_usage_history_with_chemical_id(self, mock_fn, logged_in_client):
        mock_fn.return_value = {'items': [{'id': 1}], 'count': 1}
        resp = logged_in_client.get('/chemicals/api/usage_history?chemical_id=5&limit=10')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(
            chemical_id=5, lab='all',
            start_date=None, end_date=None, limit=10
        )

    @patch('app.services.chemical_service.get_usage_history')
    def test_usage_history_with_dates(self, mock_fn, logged_in_client):
        mock_fn.return_value = {'items': [], 'count': 0}
        resp = logged_in_client.get(
            '/chemicals/api/usage_history?start_date=2026-01-01&end_date=2026-03-01'
        )
        assert resp.status_code == 200
        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs['start_date'] == '2026-01-01'
        assert call_kwargs['end_date'] == '2026-03-01'

    def test_usage_history_invalid_chemical_id(self, logged_in_client):
        """Invalid chemical_id returns empty result, no service call."""
        resp = logged_in_client.get('/chemicals/api/usage_history?chemical_id=abc')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['items'] == []
        assert data['count'] == 0

    @patch('app.services.chemical_service.get_usage_history')
    def test_usage_history_invalid_limit_fallback(self, mock_fn, logged_in_client):
        mock_fn.return_value = {'items': [], 'count': 0}
        resp = logged_in_client.get('/chemicals/api/usage_history?limit=bad')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(
            chemical_id=None, lab='all',
            start_date=None, end_date=None, limit=100
        )

    @patch('app.services.chemical_service.get_usage_history')
    def test_usage_history_service_value_error(self, mock_fn, logged_in_client):
        """Service raises ValueError for bad date format."""
        mock_fn.side_effect = ValueError('Bad date')
        resp = logged_in_client.get(
            '/chemicals/api/usage_history?start_date=bad-date'
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False

    @patch('app.services.chemical_service.get_usage_history')
    def test_usage_history_with_lab(self, mock_fn, logged_in_client):
        mock_fn.return_value = {'items': [], 'count': 0}
        resp = logged_in_client.get('/chemicals/api/usage_history?lab=coal')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(
            chemical_id=None, lab='coal',
            start_date=None, end_date=None, limit=100
        )


class TestChemicalApiConsumeBulk:
    """POST /chemicals/api/consume_bulk"""

    @patch('app.routes.chemicals.api.db')
    @patch('app.services.chemical_service.consume_bulk')
    def test_bulk_consume_success(self, mock_consume, mock_db, logged_in_client):
        result = MagicMock(success=True, error=None, count=2, errors=[])
        mock_consume.return_value = result

        resp = logged_in_client.post('/chemicals/api/consume_bulk', json={
            'items': [
                {'chemical_id': 1, 'quantity_used': 5.0},
                {'chemical_id': 2, 'quantity_used': 3.0},
            ],
            'purpose': 'Analysis',
            'analysis_code': 'Mad',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['count'] == 2

    @patch('app.routes.chemicals.api.db')
    @patch('app.services.chemical_service.consume_bulk')
    def test_bulk_consume_with_sample_id(self, mock_consume, mock_db, logged_in_client):
        result = MagicMock(success=True, error=None, count=1, errors=[])
        mock_consume.return_value = result

        resp = logged_in_client.post('/chemicals/api/consume_bulk', json={
            'items': [{'chemical_id': 1, 'quantity_used': 5.0}],
            'sample_id': 99,
        })
        assert resp.status_code == 200
        call_kwargs = mock_consume.call_args[1]
        assert call_kwargs['sample_id'] == 99

    @patch('app.routes.chemicals.api.db')
    @patch('app.services.chemical_service.consume_bulk')
    def test_bulk_consume_invalid_sample_id(self, mock_consume, mock_db, logged_in_client):
        result = MagicMock(success=True, error=None, count=1, errors=[])
        mock_consume.return_value = result

        resp = logged_in_client.post('/chemicals/api/consume_bulk', json={
            'items': [{'chemical_id': 1, 'quantity_used': 5.0}],
            'sample_id': 'bad',
        })
        assert resp.status_code == 200
        call_kwargs = mock_consume.call_args[1]
        assert call_kwargs['sample_id'] is None

    @patch('app.services.chemical_service.consume_bulk')
    def test_bulk_consume_service_error(self, mock_consume, logged_in_client):
        result = MagicMock(success=False, error='No items provided')
        mock_consume.return_value = result

        resp = logged_in_client.post('/chemicals/api/consume_bulk', json={
            'items': [],
        })
        data = resp.get_json()
        assert data['success'] is False

    @patch('app.routes.chemicals.api.db')
    @patch('app.services.chemical_service.consume_bulk')
    def test_bulk_consume_commit_error(self, mock_consume, mock_db, logged_in_client):
        result = MagicMock(success=True, error=None, count=1, errors=[])
        mock_consume.return_value = result
        mock_db.session.commit.side_effect = SQLAlchemyError('DB error')

        resp = logged_in_client.post('/chemicals/api/consume_bulk', json={
            'items': [{'chemical_id': 1, 'quantity_used': 5.0}],
        })
        assert resp.status_code == 500
        data = resp.get_json()
        assert data['success'] is False

    @patch('app.routes.chemicals.api.db')
    @patch('app.services.chemical_service.consume_bulk')
    def test_bulk_consume_outer_exception(self, mock_consume, mock_db, logged_in_client):
        """Trigger the outer (ValueError, TypeError) except block."""
        mock_consume.side_effect = ValueError('unexpected')

        resp = logged_in_client.post('/chemicals/api/consume_bulk', json={
            'items': [{'chemical_id': 1, 'quantity_used': 5.0}],
        })
        assert resp.status_code == 500
        data = resp.get_json()
        assert data['success'] is False
        assert 'failed' in data.get('error', '').lower()

    @patch('app.routes.chemicals.api.db')
    @patch('app.services.chemical_service.consume_bulk')
    def test_bulk_consume_empty_json_body(self, mock_consume, mock_db, logged_in_client):
        """Empty JSON body => items=[], service handles it."""
        result = MagicMock(success=True, error=None, count=0, errors=[])
        mock_consume.return_value = result

        resp = logged_in_client.post('/chemicals/api/consume_bulk',
                                     data='', content_type='application/json')
        assert resp.status_code == 200

    @patch('app.routes.chemicals.api.db')
    @patch('app.services.chemical_service.consume_bulk')
    def test_bulk_consume_partial_errors(self, mock_consume, mock_db, logged_in_client):
        result = MagicMock(
            success=True, error=None, count=1,
            errors=['Chemical 2 not found']
        )
        mock_consume.return_value = result

        resp = logged_in_client.post('/chemicals/api/consume_bulk', json={
            'items': [
                {'chemical_id': 1, 'quantity_used': 5.0},
                {'chemical_id': 2, 'quantity_used': 3.0},
            ],
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['data']['errors']) == 1

    @patch('app.routes.chemicals.api.db')
    @patch('app.services.chemical_service.consume_bulk')
    def test_bulk_consume_sample_id_none_not_present(self, mock_consume, mock_db, logged_in_client):
        """sample_id key not in JSON at all => sample_id=None."""
        result = MagicMock(success=True, error=None, count=1, errors=[])
        mock_consume.return_value = result

        resp = logged_in_client.post('/chemicals/api/consume_bulk', json={
            'items': [{'chemical_id': 1, 'quantity_used': 5.0}],
        })
        assert resp.status_code == 200
        call_kwargs = mock_consume.call_args[1]
        assert call_kwargs['sample_id'] is None


# ===========================================================================
# SPARE PARTS API  — /spare_parts/api/...
# ===========================================================================


class TestSparePartApiList:
    """GET /spare_parts/api/list"""

    @patch('app.services.spare_parts_service.get_spare_parts_list_simple')
    def test_list_success(self, mock_fn, logged_in_client):
        mock_fn.return_value = [{'id': 1, 'name': 'O-ring'}]
        resp = logged_in_client.get('/spare_parts/api/list')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    @patch('app.services.spare_parts_service.get_spare_parts_list_simple')
    def test_list_empty(self, mock_fn, logged_in_client):
        mock_fn.return_value = []
        resp = logged_in_client.get('/spare_parts/api/list')
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_list_unauthenticated(self, client):
        resp = client.get('/spare_parts/api/list')
        assert resp.status_code in (302, 401)


class TestSparePartApiLowStock:
    """GET /spare_parts/api/low_stock"""

    @patch('app.services.spare_parts_service.get_low_stock_parts')
    def test_low_stock(self, mock_fn, logged_in_client):
        mock_fn.return_value = [{'id': 2, 'quantity': 1}]
        resp = logged_in_client.get('/spare_parts/api/low_stock')
        assert resp.status_code == 200


class TestSparePartApiStats:
    """GET /spare_parts/api/stats"""

    @patch('app.services.spare_parts_service.get_full_stats')
    def test_stats(self, mock_fn, logged_in_client):
        mock_fn.return_value = {'total': 20, 'low_stock': 2}
        resp = logged_in_client.get('/spare_parts/api/stats')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] == 20


class TestSparePartApiConsume:
    """POST /spare_parts/api/consume"""

    @patch('app.routes.spare_parts.api.db')
    @patch('app.services.spare_parts_service.consume_stock')
    def test_consume_success(self, mock_consume, mock_db, logged_in_client):
        mock_consume.return_value = (
            {'consumed': 2.0, 'unit': 'pcs', 'remaining': 8.0, 'status': 'active'},
            None,
        )
        resp = logged_in_client.post('/spare_parts/api/consume', json={
            'spare_part_id': 1, 'quantity': 2.0, 'purpose': 'Repair'
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['remaining'] == 8.0

    @patch('app.routes.spare_parts.api.db')
    @patch('app.services.spare_parts_service.consume_stock')
    def test_consume_with_equipment_and_maintenance(self, mock_consume, mock_db, logged_in_client):
        mock_consume.return_value = (
            {'consumed': 1.0, 'unit': 'pcs', 'remaining': 5.0, 'status': 'active'},
            None,
        )
        resp = logged_in_client.post('/spare_parts/api/consume', json={
            'spare_part_id': 1, 'quantity': 1.0,
            'equipment_id': 10, 'maintenance_log_id': 20,
            'purpose': 'Scheduled',
        })
        assert resp.status_code == 200
        call_kwargs = mock_consume.call_args[1]
        assert call_kwargs['equipment_id'] == 10
        assert call_kwargs['maintenance_log_id'] == 20

    def test_consume_missing_spare_part_id(self, logged_in_client):
        resp = logged_in_client.post('/spare_parts/api/consume', json={
            'quantity': 5.0
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False

    def test_consume_zero_quantity(self, logged_in_client):
        resp = logged_in_client.post('/spare_parts/api/consume', json={
            'spare_part_id': 1, 'quantity': 0
        })
        assert resp.status_code == 400

    def test_consume_negative_quantity(self, logged_in_client):
        resp = logged_in_client.post('/spare_parts/api/consume', json={
            'spare_part_id': 1, 'quantity': -3
        })
        assert resp.status_code == 400

    def test_consume_invalid_quantity_string(self, logged_in_client):
        resp = logged_in_client.post('/spare_parts/api/consume', json={
            'spare_part_id': 1, 'quantity': 'abc'
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'Invalid quantity' in data.get('message', '')

    @patch('app.services.spare_parts_service.consume_stock')
    def test_consume_not_found(self, mock_consume, logged_in_client):
        mock_consume.return_value = (None, 'not_found')
        resp = logged_in_client.post('/spare_parts/api/consume', json={
            'spare_part_id': 999, 'quantity': 1.0
        })
        assert resp.status_code == 404
        data = resp.get_json()
        assert data['success'] is False

    @patch('app.services.spare_parts_service.consume_stock')
    def test_consume_other_error(self, mock_consume, logged_in_client):
        mock_consume.return_value = (None, 'Insufficient stock')
        resp = logged_in_client.post('/spare_parts/api/consume', json={
            'spare_part_id': 1, 'quantity': 100.0
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False

    @patch('app.routes.spare_parts.api.db')
    @patch('app.services.spare_parts_service.consume_stock')
    def test_consume_commit_error(self, mock_consume, mock_db, logged_in_client):
        mock_consume.return_value = (
            {'consumed': 1.0, 'unit': 'pcs', 'remaining': 9.0, 'status': 'active'},
            None,
        )
        mock_db.session.commit.side_effect = SQLAlchemyError('DB error')

        resp = logged_in_client.post('/spare_parts/api/consume', json={
            'spare_part_id': 1, 'quantity': 1.0
        })
        assert resp.status_code == 500
        data = resp.get_json()
        assert data['success'] is False

    @patch('app.routes.spare_parts.api.db')
    @patch('app.services.spare_parts_service.consume_stock')
    def test_consume_outer_exception(self, mock_consume, mock_db, logged_in_client):
        """Trigger the outer (ValueError, TypeError, SQLAlchemyError) except."""
        mock_consume.side_effect = ValueError('unexpected')

        resp = logged_in_client.post('/spare_parts/api/consume', json={
            'spare_part_id': 1, 'quantity': 1.0
        })
        assert resp.status_code == 500
        data = resp.get_json()
        assert data['success'] is False

    def test_consume_quantity_none_type_error(self, logged_in_client):
        """quantity=None triggers TypeError in float()."""
        resp = logged_in_client.post('/spare_parts/api/consume', json={
            'spare_part_id': 1, 'quantity': None
        })
        assert resp.status_code == 400


class TestSparePartApiConsumeBulk:
    """POST /spare_parts/api/consume_bulk"""

    @patch('app.routes.spare_parts.api.db')
    @patch('app.services.spare_parts_service.consume_stock_bulk')
    def test_bulk_consume_success(self, mock_bulk, mock_db, logged_in_client):
        mock_bulk.return_value = (
            [{'spare_part_id': 1, 'consumed': 2.0}],
            [],
        )
        resp = logged_in_client.post('/spare_parts/api/consume_bulk', json={
            'items': [{'spare_part_id': 1, 'quantity': 2.0}],
            'purpose': 'Maintenance',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert len(data['results']) == 1

    def test_bulk_consume_empty_items(self, logged_in_client):
        resp = logged_in_client.post('/spare_parts/api/consume_bulk', json={
            'items': []
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False
        assert 'required' in data.get('message', '').lower()

    def test_bulk_consume_over_100_items(self, logged_in_client):
        items = [{'spare_part_id': i, 'quantity': 1.0} for i in range(101)]
        resp = logged_in_client.post('/spare_parts/api/consume_bulk', json={
            'items': items
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False
        assert '100' in data.get('message', '')

    @patch('app.routes.spare_parts.api.db')
    @patch('app.services.spare_parts_service.consume_stock_bulk')
    def test_bulk_consume_exactly_100_items(self, mock_bulk, mock_db, logged_in_client):
        """Exactly 100 items should be allowed."""
        mock_bulk.return_value = (
            [{'spare_part_id': i} for i in range(100)],
            [],
        )
        items = [{'spare_part_id': i, 'quantity': 1.0} for i in range(100)]
        resp = logged_in_client.post('/spare_parts/api/consume_bulk', json={
            'items': items,
        })
        assert resp.status_code == 200

    @patch('app.routes.spare_parts.api.db')
    @patch('app.services.spare_parts_service.consume_stock_bulk')
    def test_bulk_consume_commit_error(self, mock_bulk, mock_db, logged_in_client):
        mock_bulk.return_value = ([{'id': 1}], [])
        mock_db.session.commit.side_effect = SQLAlchemyError('DB error')

        resp = logged_in_client.post('/spare_parts/api/consume_bulk', json={
            'items': [{'spare_part_id': 1, 'quantity': 1.0}],
        })
        assert resp.status_code == 500
        data = resp.get_json()
        assert data['success'] is False

    @patch('app.routes.spare_parts.api.db')
    @patch('app.services.spare_parts_service.consume_stock_bulk')
    def test_bulk_consume_outer_exception(self, mock_bulk, mock_db, logged_in_client):
        mock_bulk.side_effect = ValueError('unexpected')

        resp = logged_in_client.post('/spare_parts/api/consume_bulk', json={
            'items': [{'spare_part_id': 1, 'quantity': 1.0}],
        })
        assert resp.status_code == 500
        data = resp.get_json()
        assert data['success'] is False

    @patch('app.routes.spare_parts.api.db')
    @patch('app.services.spare_parts_service.consume_stock_bulk')
    def test_bulk_consume_with_equipment_id(self, mock_bulk, mock_db, logged_in_client):
        mock_bulk.return_value = ([{'id': 1}], [])
        resp = logged_in_client.post('/spare_parts/api/consume_bulk', json={
            'items': [{'spare_part_id': 1, 'quantity': 1.0}],
            'equipment_id': 5,
            'maintenance_log_id': 10,
        })
        assert resp.status_code == 200
        call_kwargs = mock_bulk.call_args[1]
        assert call_kwargs['equipment_id'] == 5
        assert call_kwargs['maintenance_log_id'] == 10

    @patch('app.routes.spare_parts.api.db')
    @patch('app.services.spare_parts_service.consume_stock_bulk')
    def test_bulk_consume_with_errors(self, mock_bulk, mock_db, logged_in_client):
        mock_bulk.return_value = (
            [{'spare_part_id': 1, 'consumed': 2.0}],
            ['Part 2 not found'],
        )
        resp = logged_in_client.post('/spare_parts/api/consume_bulk', json={
            'items': [
                {'spare_part_id': 1, 'quantity': 2.0},
                {'spare_part_id': 2, 'quantity': 1.0},
            ],
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert len(data['errors']) == 1


class TestSparePartApiSearch:
    """GET /spare_parts/api/search"""

    @patch('app.services.spare_parts_service.search_spare_parts')
    def test_search_default(self, mock_fn, logged_in_client):
        mock_fn.return_value = []
        resp = logged_in_client.get('/spare_parts/api/search')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with('')

    @patch('app.services.spare_parts_service.search_spare_parts')
    def test_search_with_query(self, mock_fn, logged_in_client):
        mock_fn.return_value = [{'id': 1, 'name': 'O-ring'}]
        resp = logged_in_client.get('/spare_parts/api/search?q=O-ring')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with('O-ring')

    @patch('app.services.spare_parts_service.search_spare_parts')
    def test_search_strips_whitespace(self, mock_fn, logged_in_client):
        mock_fn.return_value = []
        resp = logged_in_client.get('/spare_parts/api/search?q=%20seal%20')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with('seal')


class TestSparePartApiUsageHistory:
    """GET /spare_parts/api/usage_history/<int:id>"""

    @patch('app.services.spare_parts_service.get_usage_history')
    def test_usage_history(self, mock_fn, logged_in_client):
        mock_fn.return_value = {'items': [{'id': 1}], 'count': 1}
        resp = logged_in_client.get('/spare_parts/api/usage_history/5')
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(5)

    @patch('app.services.spare_parts_service.get_usage_history')
    def test_usage_history_empty(self, mock_fn, logged_in_client):
        mock_fn.return_value = {'items': [], 'count': 0}
        resp = logged_in_client.get('/spare_parts/api/usage_history/999')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['count'] == 0

    def test_usage_history_invalid_id_404(self, logged_in_client):
        """Non-integer id returns 404 (Flask URL routing rejects it)."""
        resp = logged_in_client.get('/spare_parts/api/usage_history/abc')
        assert resp.status_code == 404

    def test_usage_history_unauthenticated(self, client):
        resp = client.get('/spare_parts/api/usage_history/1')
        assert resp.status_code in (302, 401)
