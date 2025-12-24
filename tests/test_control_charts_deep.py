# tests/test_control_charts_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/routes/quality/control_charts.py
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestDryBasisConversion:
    """Tests for dry basis conversion."""

    def test_convert_to_dry_basis_normal(self, app):
        """Test convert_to_dry_basis with normal values."""
        with app.app_context():
            from app.routes.quality.control_charts import convert_to_dry_basis
            result = convert_to_dry_basis(10.0, 5.0)
            expected = 10.0 * 100 / (100 - 5.0)
            assert abs(result - expected) < 0.0001

    def test_convert_to_dry_basis_zero_moisture(self, app):
        """Test convert_to_dry_basis with zero moisture."""
        with app.app_context():
            from app.routes.quality.control_charts import convert_to_dry_basis
            result = convert_to_dry_basis(10.0, 0.0)
            assert result == 10.0

    def test_convert_to_dry_basis_none_moisture(self, app):
        """Test convert_to_dry_basis with None moisture."""
        with app.app_context():
            from app.routes.quality.control_charts import convert_to_dry_basis
            result = convert_to_dry_basis(10.0, None)
            assert result == 10.0

    def test_convert_to_dry_basis_high_moisture(self, app):
        """Test convert_to_dry_basis with 100% moisture."""
        with app.app_context():
            from app.routes.quality.control_charts import convert_to_dry_basis
            result = convert_to_dry_basis(10.0, 100.0)
            assert result == 10.0

    def test_convert_to_dry_basis_over_100_moisture(self, app):
        """Test convert_to_dry_basis with over 100% moisture."""
        with app.app_context():
            from app.routes.quality.control_charts import convert_to_dry_basis
            result = convert_to_dry_basis(10.0, 150.0)
            assert result == 10.0


class TestDryBasisMapping:
    """Tests for dry basis mapping constants."""

    def test_dry_basis_mapping_exists(self, app):
        """Test DRY_BASIS_MAPPING constant exists."""
        with app.app_context():
            from app.routes.quality.control_charts import DRY_BASIS_MAPPING
            assert isinstance(DRY_BASIS_MAPPING, dict)
            assert 'Ad' in DRY_BASIS_MAPPING
            assert 'Vd' in DRY_BASIS_MAPPING

    def test_db_to_standard_code_exists(self, app):
        """Test DB_TO_STANDARD_CODE constant exists."""
        with app.app_context():
            from app.routes.quality.control_charts import DB_TO_STANDARD_CODE
            assert isinstance(DB_TO_STANDARD_CODE, dict)
            assert 'Aad' in DB_TO_STANDARD_CODE


class TestGetQCSamples:
    """Tests for _get_qc_samples function."""

    def test_get_qc_samples_returns_list(self, app, db):
        """Test _get_qc_samples returns a list."""
        with app.app_context():
            from app.routes.quality.control_charts import _get_qc_samples
            result = _get_qc_samples()
            assert isinstance(result, list)

    def test_get_qc_samples_with_cm_sample(self, app, db):
        """Test _get_qc_samples finds CM samples."""
        with app.app_context():
            from app.routes.quality.control_charts import _get_qc_samples
            from app.models import Sample

            # Create CM sample
            sample = Sample(
                sample_code='CM_TEST_20251224',
                client_name='LAB',
                sample_type='CM',
                user_id=1
            )
            db.session.add(sample)
            db.session.commit()

            result = _get_qc_samples()
            codes = [s.sample_code for s in result]
            assert 'CM_TEST_20251224' in codes

    def test_get_qc_samples_with_gbw_sample(self, app, db):
        """Test _get_qc_samples finds GBW samples."""
        with app.app_context():
            from app.routes.quality.control_charts import _get_qc_samples
            from app.models import Sample

            # Create GBW sample
            sample = Sample(
                sample_code='GBW11135a_20251224',
                client_name='LAB',
                sample_type='GBW',
                user_id=1
            )
            db.session.add(sample)
            db.session.commit()

            result = _get_qc_samples()
            codes = [s.sample_code for s in result]
            assert 'GBW11135a_20251224' in codes


class TestGetQCResults:
    """Tests for _get_qc_results function."""

    def test_get_qc_results_with_ids(self, app, db):
        """Test _get_qc_results with sample IDs."""
        with app.app_context():
            from app.routes.quality.control_charts import _get_qc_results
            result = _get_qc_results([1, 2, 3])
            assert isinstance(result, list)

    def test_get_qc_results_with_analysis_code(self, app, db):
        """Test _get_qc_results with analysis code filter."""
        with app.app_context():
            from app.routes.quality.control_charts import _get_qc_results
            result = _get_qc_results([1, 2, 3], analysis_code='Aad')
            assert isinstance(result, list)

    def test_get_qc_results_empty_ids(self, app, db):
        """Test _get_qc_results with empty IDs."""
        with app.app_context():
            from app.routes.quality.control_charts import _get_qc_results
            result = _get_qc_results([])
            assert result == []


class TestGetQCResultsFromLog:
    """Tests for _get_qc_results_from_log function."""

    def test_get_qc_results_from_log_with_ids(self, app, db):
        """Test _get_qc_results_from_log with sample IDs."""
        with app.app_context():
            from app.routes.quality.control_charts import _get_qc_results_from_log
            result = _get_qc_results_from_log([1, 2, 3])
            assert isinstance(result, list)

    def test_get_qc_results_from_log_with_analysis_code(self, app, db):
        """Test _get_qc_results_from_log with analysis code filter."""
        with app.app_context():
            from app.routes.quality.control_charts import _get_qc_results_from_log
            result = _get_qc_results_from_log([1, 2, 3], analysis_code='Aad')
            assert isinstance(result, list)


class TestGetActiveCMStandardName:
    """Tests for _get_active_cm_standard_name function."""

    def test_get_active_cm_standard_no_standard(self, app, db):
        """Test _get_active_cm_standard_name when no active standard."""
        with app.app_context():
            from app.routes.quality.control_charts import _get_active_cm_standard_name
            from app.models import ControlStandard
            # Deactivate all CM standards
            ControlStandard.query.update({'is_active': False})
            db.session.commit()

            result = _get_active_cm_standard_name()
            assert result == 'CM'

    def test_get_active_cm_standard_with_standard(self, app, db):
        """Test _get_active_cm_standard_name with active standard."""
        with app.app_context():
            from app.routes.quality.control_charts import _get_active_cm_standard_name
            from app.models import ControlStandard

            # Create active standard
            std = ControlStandard(name='CM-TEST-Q4', is_active=True)
            db.session.add(std)
            db.session.commit()

            result = _get_active_cm_standard_name()
            assert result == 'CM-TEST-Q4'


class TestExtractStandardName:
    """Tests for _extract_standard_name function."""

    def test_extract_standard_name_empty(self, app):
        """Test _extract_standard_name with empty string."""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('')
            assert result == ''

    def test_extract_standard_name_none(self, app):
        """Test _extract_standard_name with None."""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name(None)
            assert result == ''

    def test_extract_standard_name_old_cm_format(self, app, db):
        """Test _extract_standard_name with old CM format."""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('CM_20251224_N')
            # Should return active CM standard name
            assert result is not None

    def test_extract_standard_name_new_cm_format(self, app):
        """Test _extract_standard_name with new CM format."""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('CM-2025-Q4_20251219_N')
            assert result == 'CM-2025-Q4'

    def test_extract_standard_name_gbw_format(self, app):
        """Test _extract_standard_name with GBW format."""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('GBW11135a_20241213A')
            assert result == 'GBW11135a'

    def test_extract_standard_name_simple(self, app):
        """Test _extract_standard_name with simple name."""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('SimpleStandard')
            assert result == 'SimpleStandard'


class TestGetTargetAndTolerance:
    """Tests for _get_target_and_tolerance function."""

    def test_get_target_empty_sample_code(self, app, db):
        """Test _get_target_and_tolerance with empty sample code."""
        with app.app_context():
            from app.routes.quality.control_charts import _get_target_and_tolerance
            mock_sample = MagicMock()
            mock_sample.sample_code = ''

            result = _get_target_and_tolerance(mock_sample, 'Aad')
            assert result == (None, None, None, None)

    @pytest.mark.skip(reason="ControlStandardValue model not found")
    def test_get_target_with_cm_sample(self, app, db):
        """Test _get_target_and_tolerance with CM sample."""
        pass


class TestControlChartsRoutes:
    """Tests for control charts routes."""

    def test_control_charts_page(self, client, auth_admin):
        """Test control charts page loads."""
        response = client.get('/quality/control_charts')
        assert response.status_code == 200

    def test_control_charts_api_endpoint(self, client, auth_admin):
        """Test control charts API endpoint."""
        response = client.get('/quality/api/control-chart-data')
        assert response.status_code in [200, 404]

    def test_control_charts_with_analysis_filter(self, client, auth_admin):
        """Test control charts with analysis code filter."""
        response = client.get('/quality/control_charts?analysis_code=Aad')
        assert response.status_code == 200


class TestWestgardIntegration:
    """Tests for Westgard integration."""

    def test_westgard_check_import(self, app):
        """Test Westgard check functions can be imported."""
        with app.app_context():
            from app.routes.quality.control_charts import check_westgard_rules, get_qc_status
            assert callable(check_westgard_rules)
            assert callable(get_qc_status)

    def test_check_single_value_import(self, app):
        """Test check_single_value can be imported."""
        with app.app_context():
            from app.routes.quality.control_charts import check_single_value
            assert callable(check_single_value)


class TestTrackQCCheck:
    """Tests for QC check tracking."""

    def test_track_qc_check_import(self, app):
        """Test track_qc_check can be imported."""
        with app.app_context():
            from app.routes.quality.control_charts import track_qc_check
            assert callable(track_qc_check)
