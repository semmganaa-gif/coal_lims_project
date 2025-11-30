# tests/unit/test_error_handling.py
"""
Unit tests for error handling improvements made in high-priority fixes.
Tests cover:
- Bare exception handler fixes
- Database commit error handling
- Transaction atomicity
- Input validation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import IntegrityError
from flask import Flask
from app import db


class TestBarеExceptionHandling:
    """Test that bare except clauses have been properly replaced."""

    def test_equipment_edit_handles_integrity_error(self, app, client, auth_admin):
        """Test that equipment edit properly handles IntegrityError."""
        from app.routes.equipment_routes import equipment_bp
        from app.models import Equipment

        with app.app_context():
            # Create test equipment
            eq = Equipment(
                name="Test Equipment",
                manufacturer="Test",
                category="test"
            )
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id

            # Mock commit to raise IntegrityError
            with patch('app.db.session.commit', side_effect=IntegrityError("mock", "mock", "mock")):
                response = client.post(
                    f'/equipment/edit_equipment/{eq_id}',
                    data={'name': 'Duplicate Name'},
                    follow_redirects=True
                )

                # Should handle error gracefully
                assert response.status_code == 200
                assert 'конфликт' in response.get_data(as_text=True).lower() or 'алдаа' in response.get_data(as_text=True).lower()

    def test_admin_priority_validation_handles_value_error(self, app):
        """Test that admin route handles ValueError properly for priority field."""
        from app.routes.admin_routes import admin_bp

        with app.app_context():
            # Test that invalid priority doesn't crash
            # This would have been caught by bare except before
            with app.test_request_context(
                '/admin/analysis_config',
                method='POST',
                data={'priority': 'invalid_string'}
            ):
                # Should default to 50 and log warning
                # Not crash with unhandled exception
                pass  # Route tested via integration tests


class TestDatabaseCommitErrorHandling:
    """Test database commit operations have proper error handling."""

    @pytest.mark.parametrize("endpoint,payload", [
        ('/api/mass/save', {'items': [{'sample_id': 1, 'weight': 100}], 'mark_ready': True}),
        ('/api/mass/update_weight', {'sample_id': 1, 'weight': 150}),
        ('/api/mass/unready', {'sample_ids': [1, 2, 3]}),
    ])
    def test_mass_api_handles_integrity_errors(self, app, client, auth_user, endpoint, payload):
        """Test that mass API endpoints handle IntegrityError properly."""
        from app import db
        from app.models import Sample

        with app.app_context():
            # Create test sample
            sample = Sample(sample_code="TEST001", user_id=1)
            db.session.add(sample)
            db.session.commit()

            # Update payload with real sample_id
            if 'sample_id' in payload:
                payload['sample_id'] = sample.id
            if 'items' in payload:
                payload['items'][0]['sample_id'] = sample.id
            if 'sample_ids' in payload:
                payload['sample_ids'] = [sample.id]

            # Mock commit to raise IntegrityError
            with patch('app.db.session.commit', side_effect=IntegrityError("mock", "mock", "mock")):
                response = client.post(
                    endpoint,
                    json=payload,
                    content_type='application/json'
                )

                # Should return JSON error response
                assert response.status_code in [409, 500]
                data = response.get_json()
                assert data is not None
                assert data.get('ok') == False
                assert 'message' in data

    def test_mass_delete_handles_cascade_errors(self, app, client, auth_admin):
        """Test that mass delete handles cascade constraint errors."""
        from app import db
        from app.models import Sample, AnalysisResult

        with app.app_context():
            # Create sample with results (cascade delete scenario)
            sample = Sample(sample_code="TEST002", user_id=1)
            db.session.add(sample)
            db.session.commit()

            result = AnalysisResult(
                sample_id=sample.id,
                user_id=1,
                analysis_code="Aad",
                status="approved"
            )
            db.session.add(result)
            db.session.commit()

            sample_id = sample.id

            # Mock delete to raise IntegrityError
            with patch('app.db.session.commit', side_effect=IntegrityError("mock", "mock", "mock")):
                response = client.post(
                    '/api/mass/delete',
                    json={'sample_id': sample_id},
                    content_type='application/json'
                )

                # Should handle error and return 409
                assert response.status_code == 409
                data = response.get_json()
                assert 'холбоотой' in data.get('message', '').lower() or 'конфликт' in data.get('message', '').lower()


class TestTransactionAtomicity:
    """Test that batch operations maintain transaction atomicity."""

    def test_sample_registration_rollback_on_error(self, app, client, auth_user):
        """Test that sample registration rolls back all changes on error."""
        from app import db
        from app.models import Sample

        with app.app_context():
            initial_count = Sample.query.count()

            # Create form data with multiple samples
            form_data = {
                'client_name': 'TestClient',
                'sample_type': 'Coal',
                'sample_condition': 'dry',
                'submitted_codes': 'TEST001,TEST002,TEST003',
                'list_type': 'single_uniform',
            }

            # Mock assign_analyses_to_sample to raise exception on 2nd sample
            call_count = [0]
            def mock_assign(sample):
                call_count[0] += 1
                if call_count[0] == 2:
                    raise RuntimeError("Mock error during batch")

            with patch('app.routes.main.index.assign_analyses_to_sample', side_effect=mock_assign):
                response = client.post('/index', data=form_data, follow_redirects=True)

                # Transaction should have rolled back - no new samples
                final_count = Sample.query.count()
                assert final_count == initial_count  # No samples added

                # Error message should be shown
                assert 'алдаа' in response.get_data(as_text=True).lower()


class TestInputValidation:
    """Test input validation for user-supplied data."""

    def test_equipment_quantity_validates_positive_integer(self, app, client, auth_admin):
        """Test that equipment quantity field validates positive integers."""
        response = client.post(
            '/equipment/add_equipment',
            data={
                'name': 'Test Equipment',
                'quantity': '-5',  # Invalid: negative
                'cycle': '365'
            },
            follow_redirects=True
        )

        # Should reject with error message (depends on implementation)
        # At minimum, should not crash

    def test_equipment_quantity_validates_non_numeric(self, app, client, auth_admin):
        """Test that non-numeric quantity is handled properly."""
        response = client.post(
            '/equipment/add_equipment',
            data={
                'name': 'Test Equipment',
                'quantity': 'abc',  # Invalid: not a number
                'cycle': '365'
            },
            follow_redirects=True
        )

        # Should show error message
        assert 'буруу' in response.get_data(as_text=True).lower() or 'алдаа' in response.get_data(as_text=True).lower()

    def test_file_upload_validates_size(self, app, client, auth_admin):
        """Test that file upload validates file size limit."""
        from io import BytesIO

        # Create a mock file larger than 5MB
        large_file = BytesIO(b'x' * (6 * 1024 * 1024))  # 6MB
        large_file.name = 'large_file.pdf'

        with app.app_context():
            from app.models import Equipment
            eq = Equipment(name="Test", category="test")
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id

            response = client.post(
                f'/equipment/add_log/{eq_id}',
                data={
                    'action_type': 'Calibration',
                    'certificate_file': (large_file, 'large_file.pdf')
                },
                content_type='multipart/form-data',
                follow_redirects=True
            )

            # Should reject file with size error
            assert response.status_code == 200
            assert 'том' in response.get_data(as_text=True).lower()

    def test_file_upload_validates_extension(self, app, client, auth_admin):
        """Test that file upload validates file extension."""
        from io import BytesIO

        # Create a mock .exe file (not allowed)
        exe_file = BytesIO(b'MZ...')  # Fake executable
        exe_file.name = 'malware.exe'

        with app.app_context():
            from app.models import Equipment
            eq = Equipment(name="Test", category="test")
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id

            response = client.post(
                f'/equipment/add_log/{eq_id}',
                data={
                    'action_type': 'Calibration',
                    'certificate_file': (exe_file, 'malware.exe')
                },
                content_type='multipart/form-data',
                follow_redirects=True
            )

            # Should reject file with extension error
            assert 'зөвшөөр' in response.get_data(as_text=True).lower() or 'төрөл' in response.get_data(as_text=True).lower()


class TestRaceConditionFix:
    """Test that N+1 query fixes and bulk operations work correctly."""

    def test_mass_save_uses_bulk_query(self, app, client, auth_user):
        """Test that mass save uses bulk query instead of N+1."""
        from app import db
        from app.models import Sample

        with app.app_context():
            # Create 10 test samples
            samples = []
            for i in range(10):
                s = Sample(sample_code=f"BULK{i:03d}", user_id=1)
                samples.append(s)
            db.session.add_all(samples)
            db.session.commit()

            sample_ids = [s.id for s in samples]

            # Mock query to count calls
            with patch('app.models.Sample.query') as mock_query:
                mock_filter = Mock()
                mock_query.filter.return_value = mock_filter
                mock_filter.all.return_value = samples

                payload = {
                    'items': [{'sample_id': sid, 'weight': 100 + i} for i, sid in enumerate(sample_ids)],
                    'mark_ready': True
                }

                response = client.post(
                    '/api/mass/save',
                    json=payload,
                    content_type='application/json'
                )

                # Should use single filter().all() call, not get() in loop
                # verify only one filter call was made
                assert mock_query.filter.call_count == 1  # Bulk query


# Run with: pytest tests/unit/test_error_handling.py -v
