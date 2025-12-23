# tests/integration/test_control_charts_extended.py
"""Control charts extended coverage tests"""
import pytest
from datetime import datetime


class TestControlChartsHelpers:
    """Helper functions tests"""

    def test_convert_to_dry_basis_normal(self, app):
        """Normal dry basis conversion"""
        with app.app_context():
            from app.routes.quality.control_charts import convert_to_dry_basis
            result = convert_to_dry_basis(10.0, 5.0)
            # dry = 10.0 * 100 / (100 - 5) = 10.526
            assert abs(result - 10.526) < 0.01

    def test_convert_to_dry_basis_zero_moisture(self, app):
        """Dry basis with zero moisture"""
        with app.app_context():
            from app.routes.quality.control_charts import convert_to_dry_basis
            result = convert_to_dry_basis(10.0, 0.0)
            assert result == 10.0

    def test_convert_to_dry_basis_none_moisture(self, app):
        """Dry basis with None moisture"""
        with app.app_context():
            from app.routes.quality.control_charts import convert_to_dry_basis
            result = convert_to_dry_basis(10.0, None)
            assert result == 10.0

    def test_convert_to_dry_basis_high_moisture(self, app):
        """Dry basis with 100% moisture"""
        with app.app_context():
            from app.routes.quality.control_charts import convert_to_dry_basis
            result = convert_to_dry_basis(10.0, 100)
            assert result == 10.0

    def test_get_qc_samples(self, app):
        """Get QC samples query"""
        with app.app_context():
            from app.routes.quality.control_charts import _get_qc_samples
            samples = _get_qc_samples()
            assert isinstance(samples, list)

    def test_get_qc_results_empty(self, app):
        """Get QC results with empty sample list"""
        with app.app_context():
            from app.routes.quality.control_charts import _get_qc_results
            results = _get_qc_results([])
            assert results == []

    def test_get_qc_results_with_code(self, app):
        """Get QC results with analysis code filter"""
        with app.app_context():
            from app.routes.quality.control_charts import _get_qc_results
            results = _get_qc_results([1, 2, 3], analysis_code='Mad')
            assert isinstance(results, list)

    def test_get_qc_results_from_log_empty(self, app):
        """Get QC results from log with empty list"""
        with app.app_context():
            from app.routes.quality.control_charts import _get_qc_results_from_log
            results = _get_qc_results_from_log([])
            assert results == []

    def test_get_qc_results_from_log_with_code(self, app):
        """Get QC results from log with analysis code"""
        with app.app_context():
            from app.routes.quality.control_charts import _get_qc_results_from_log
            results = _get_qc_results_from_log([1, 2], analysis_code='Aad')
            assert isinstance(results, list)

    def test_get_active_cm_standard_name(self, app):
        """Get active CM standard name"""
        with app.app_context():
            from app.routes.quality.control_charts import _get_active_cm_standard_name
            name = _get_active_cm_standard_name()
            assert isinstance(name, str)

    def test_extract_standard_name_empty(self, app):
        """Extract standard name from empty"""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('')
            assert result == ''

    def test_extract_standard_name_none(self, app):
        """Extract standard name from None"""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name(None)
            assert result == ''

    def test_extract_standard_name_old_cm_format(self, app):
        """Extract from old CM format"""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('CM_20251219_N')
            # Returns active CM standard name
            assert isinstance(result, str)

    def test_extract_standard_name_new_cm_format(self, app):
        """Extract from new CM format"""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('CM-2025-Q4_20251219_N')
            assert result == 'CM-2025-Q4'

    def test_extract_standard_name_gbw(self, app):
        """Extract from GBW format"""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('GBW11135a_20241213A')
            assert result == 'GBW11135a'

    def test_extract_standard_name_single_part(self, app):
        """Extract from single part"""
        with app.app_context():
            from app.routes.quality.control_charts import _extract_standard_name
            result = _extract_standard_name('CM2025')
            assert result == 'CM2025'


class TestControlChartsTargetTolerance:
    """Target and tolerance tests"""

    def test_get_target_empty_sample_code(self, app):
        """Get target with empty sample code"""
        with app.app_context():
            from app.routes.quality.control_charts import _get_target_and_tolerance
            from app.models import Sample
            sample = Sample(sample_code='')
            target, ucl, lcl, sd = _get_target_and_tolerance(sample, 'Mad')
            assert target is None

    def test_get_target_no_standard(self, app):
        """Get target when no standard exists"""
        with app.app_context():
            from app.routes.quality.control_charts import _get_target_and_tolerance
            from app.models import Sample
            sample = Sample(sample_code='UNKNOWN_20251219')
            target, ucl, lcl, sd = _get_target_and_tolerance(sample, 'Mad')
            # May or may not find target
            assert target is None or isinstance(target, float)

    def test_get_target_cm_sample(self, app):
        """Get target for CM sample"""
        with app.app_context():
            from app.routes.quality.control_charts import _get_target_and_tolerance
            from app.models import Sample
            sample = Sample(sample_code='CM_20251219_N')
            target, ucl, lcl, sd = _get_target_and_tolerance(sample, 'Mad')
            # May return values if CM standard exists
            assert target is None or isinstance(target, float)

    def test_get_target_gbw_sample(self, app):
        """Get target for GBW sample"""
        with app.app_context():
            from app.routes.quality.control_charts import _get_target_and_tolerance
            from app.models import Sample
            sample = Sample(sample_code='GBW11135a_20251219A')
            target, ucl, lcl, sd = _get_target_and_tolerance(sample, 'Mad')
            assert target is None or isinstance(target, float)


class TestControlChartsRoutes:
    """Control charts routes tests"""

    def test_control_charts_list(self, auth_admin):
        """Control charts list page"""
        response = auth_admin.get('/quality/control_charts')
        assert response.status_code in [200, 302]

    def test_westgard_summary_api(self, auth_admin):
        """Westgard summary API"""
        response = auth_admin.get('/quality/api/westgard_summary')
        assert response.status_code == 200
        data = response.get_json()
        assert 'qc_samples' in data

    def test_westgard_detail_cm_mad(self, auth_admin):
        """Westgard detail for CM Mad"""
        response = auth_admin.get('/quality/api/westgard_detail/CM/Mad')
        assert response.status_code == 200
        data = response.get_json()
        assert 'qc_type' in data or 'error' in data

    def test_westgard_detail_gbw_aad(self, auth_admin):
        """Westgard detail for GBW Aad"""
        response = auth_admin.get('/quality/api/westgard_detail/GBW/Aad')
        assert response.status_code == 200
        data = response.get_json()
        assert 'qc_type' in data or 'error' in data

    def test_westgard_detail_cm_ad(self, auth_admin):
        """Westgard detail for CM Ad (dry basis)"""
        response = auth_admin.get('/quality/api/westgard_detail/CM/Ad')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)

    def test_westgard_detail_unknown_type(self, auth_admin):
        """Westgard detail for unknown type"""
        response = auth_admin.get('/quality/api/westgard_detail/UNKNOWN/Mad')
        assert response.status_code == 200
        data = response.get_json()
        # May return error or empty data
        assert isinstance(data, dict)


class TestDryBasisMapping:
    """Dry basis mapping tests"""

    def test_dry_basis_mapping_exists(self, app):
        """DRY_BASIS_MAPPING constant exists"""
        with app.app_context():
            from app.routes.quality.control_charts import DRY_BASIS_MAPPING
            assert 'Ad' in DRY_BASIS_MAPPING
            assert 'Vd' in DRY_BASIS_MAPPING
            assert 'CV,d' in DRY_BASIS_MAPPING

    def test_db_to_standard_code(self, app):
        """DB_TO_STANDARD_CODE mapping"""
        with app.app_context():
            from app.routes.quality.control_charts import DB_TO_STANDARD_CODE
            assert 'Aad' in DB_TO_STANDARD_CODE
            assert DB_TO_STANDARD_CODE['Aad'] == 'Ad'

    def test_mapping_conversion(self, app):
        """Test mapping conversion values"""
        with app.app_context():
            from app.routes.quality.control_charts import DRY_BASIS_MAPPING
            # Check that Aad needs conversion
            assert DRY_BASIS_MAPPING['Ad'][0] == 'Aad'
            assert DRY_BASIS_MAPPING['Ad'][1] == True
            # Check that CSN doesn't need conversion
            assert DRY_BASIS_MAPPING['CSN'][1] == False
