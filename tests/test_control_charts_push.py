# -*- coding: utf-8 -*-
"""
Control Charts модулийн coverage тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock


# ============================================================
# Import Tests
# ============================================================

class TestControlChartsImports:
    """control_charts модулийн импорт тест"""

    def test_import_module(self):
        from app.routes.quality import control_charts
        assert control_charts is not None

    def test_import_dry_basis_mapping(self):
        from app.routes.quality.control_charts import DRY_BASIS_MAPPING
        assert isinstance(DRY_BASIS_MAPPING, dict)
        assert 'Ad' in DRY_BASIS_MAPPING
        assert 'Vd' in DRY_BASIS_MAPPING
        assert 'CV,d' in DRY_BASIS_MAPPING

    def test_import_db_to_standard_code(self):
        from app.routes.quality.control_charts import DB_TO_STANDARD_CODE
        assert isinstance(DB_TO_STANDARD_CODE, dict)
        assert 'Aad' in DB_TO_STANDARD_CODE
        assert 'Vad' in DB_TO_STANDARD_CODE


# ============================================================
# Dry Basis Conversion Tests
# ============================================================

class TestConvertToDryBasis:
    """convert_to_dry_basis функц тест"""

    def test_import_function(self):
        from app.routes.quality.control_charts import convert_to_dry_basis
        assert convert_to_dry_basis is not None

    def test_zero_moisture(self):
        from app.routes.quality.control_charts import convert_to_dry_basis
        result = convert_to_dry_basis(10.0, 0.0)
        assert result == 10.0

    def test_normal_moisture(self):
        from app.routes.quality.control_charts import convert_to_dry_basis
        # Formula: dry = as_received * 100 / (100 - Mad)
        result = convert_to_dry_basis(10.0, 5.0)
        expected = 10.0 * 100 / (100 - 5.0)
        assert abs(result - expected) < 0.001

    def test_none_moisture(self):
        from app.routes.quality.control_charts import convert_to_dry_basis
        result = convert_to_dry_basis(10.0, None)
        assert result == 10.0

    def test_high_moisture_edge(self):
        from app.routes.quality.control_charts import convert_to_dry_basis
        # When moisture >= 100, return original value
        result = convert_to_dry_basis(10.0, 100)
        assert result == 10.0

    def test_very_high_moisture(self):
        from app.routes.quality.control_charts import convert_to_dry_basis
        result = convert_to_dry_basis(10.0, 150)
        assert result == 10.0


# ============================================================
# Helper Function Tests
# ============================================================

class TestGetQcSamples:
    """_get_qc_samples функц тест"""

    def test_import_function(self):
        from app.routes.quality.control_charts import _get_qc_samples
        assert _get_qc_samples is not None


class TestGetQcResults:
    """_get_qc_results функц тест"""

    def test_import_function(self):
        from app.routes.quality.control_charts import _get_qc_results
        assert _get_qc_results is not None


class TestGetQcResultsFromLog:
    """_get_qc_results_from_log функц тест"""

    def test_import_function(self):
        from app.routes.quality.control_charts import _get_qc_results_from_log
        assert _get_qc_results_from_log is not None


class TestGetActiveCmStandardName:
    """_get_active_cm_standard_name функц тест"""

    def test_import_function(self):
        from app.routes.quality.control_charts import _get_active_cm_standard_name
        assert _get_active_cm_standard_name is not None


class TestExtractStandardName:
    """_extract_standard_name функц тест"""

    def test_import_function(self):
        from app.routes.quality.control_charts import _extract_standard_name
        assert _extract_standard_name is not None

    def test_empty_sample_code(self):
        from app.routes.quality.control_charts import _extract_standard_name
        result = _extract_standard_name('')
        assert result == ''

    def test_none_sample_code(self):
        from app.routes.quality.control_charts import _extract_standard_name
        result = _extract_standard_name(None)
        assert result == ''

    def test_new_cm_format(self):
        from app.routes.quality.control_charts import _extract_standard_name
        result = _extract_standard_name('CM-2025-Q4_20251219_N')
        assert result == 'CM-2025-Q4'

    def test_old_cm_format(self):
        from app.routes.quality.control_charts import _extract_standard_name
        with patch('app.routes.quality.control_charts._get_active_cm_standard_name') as mock:
            mock.return_value = 'CM-2025-Q4'
            result = _extract_standard_name('CM_20251128_N_Q4')
            assert result == 'CM-2025-Q4'

    def test_gbw_format(self):
        from app.routes.quality.control_charts import _extract_standard_name
        result = _extract_standard_name('GBW11135a_20241213A')
        assert result == 'GBW11135a'

    def test_simple_code(self):
        from app.routes.quality.control_charts import _extract_standard_name
        result = _extract_standard_name('SimpleCode')
        assert result == 'SimpleCode'


class TestGetTargetAndTolerance:
    """_get_target_and_tolerance функц тест"""

    def test_import_function(self):
        from app.routes.quality.control_charts import _get_target_and_tolerance
        assert _get_target_and_tolerance is not None


# ============================================================
# Dry Basis Mapping Tests
# ============================================================

class TestDryBasisMapping:
    """DRY_BASIS_MAPPING тест"""

    def test_mapping_structure(self):
        from app.routes.quality.control_charts import DRY_BASIS_MAPPING
        for key, value in DRY_BASIS_MAPPING.items():
            assert isinstance(value, tuple)
            assert len(value) == 2
            assert isinstance(value[0], str)
            assert isinstance(value[1], bool)

    def test_ash_mapping(self):
        from app.routes.quality.control_charts import DRY_BASIS_MAPPING
        assert DRY_BASIS_MAPPING['Ad'] == ('Aad', True)

    def test_volatile_mapping(self):
        from app.routes.quality.control_charts import DRY_BASIS_MAPPING
        assert DRY_BASIS_MAPPING['Vd'] == ('Vad', True)

    def test_cv_mapping(self):
        from app.routes.quality.control_charts import DRY_BASIS_MAPPING
        assert DRY_BASIS_MAPPING['CV,d'] == ('CV', True)

    def test_sulfur_mapping(self):
        from app.routes.quality.control_charts import DRY_BASIS_MAPPING
        assert DRY_BASIS_MAPPING['St,d'] == ('TS', True)

    def test_trd_no_conversion(self):
        from app.routes.quality.control_charts import DRY_BASIS_MAPPING
        assert DRY_BASIS_MAPPING['TRD,d'] == ('TRD', False)

    def test_csn_no_conversion(self):
        from app.routes.quality.control_charts import DRY_BASIS_MAPPING
        assert DRY_BASIS_MAPPING['CSN'] == ('CSN', False)

    def test_gi_no_conversion(self):
        from app.routes.quality.control_charts import DRY_BASIS_MAPPING
        assert DRY_BASIS_MAPPING['Gi'] == ('Gi', False)

    def test_mad_no_conversion(self):
        from app.routes.quality.control_charts import DRY_BASIS_MAPPING
        assert DRY_BASIS_MAPPING['Mad'] == ('Mad', False)


class TestDbToStandardCode:
    """DB_TO_STANDARD_CODE тест"""

    def test_reverse_mapping(self):
        from app.routes.quality.control_charts import DB_TO_STANDARD_CODE
        assert DB_TO_STANDARD_CODE['Aad'] == 'Ad'
        assert DB_TO_STANDARD_CODE['Vad'] == 'Vd'
        assert DB_TO_STANDARD_CODE['CV'] == 'CV,d'
        assert DB_TO_STANDARD_CODE['TS'] == 'St,d'


# ============================================================
# Route Tests (if blueprint is registered)
# ============================================================

class TestQcChartsRoute:
    """qc_charts route тест"""

    def test_route_accessible(self, client, logged_in_user):
        # Try to access QC charts page
        response = client.get('/quality/qc_charts')
        # Could be 200 or 302 (redirect) depending on login
        assert response.status_code in [200, 302, 404]


class TestQcDataApiRoute:
    """qc_data API route тест"""

    def test_route_accessible(self, client, logged_in_user):
        response = client.get('/quality/api/qc_data?analysis_code=CV')
        assert response.status_code in [200, 302, 404]


class TestQcSamplesApiRoute:
    """qc_samples API route тест"""

    def test_route_accessible(self, client, logged_in_user):
        response = client.get('/quality/api/qc_samples')
        assert response.status_code in [200, 302, 404]


class TestCheckWestgardApiRoute:
    """check_westgard API route тест"""

    def test_route_accessible(self, client, logged_in_user):
        response = client.get('/quality/api/check_westgard?analysis_code=CV')
        assert response.status_code in [200, 302, 404]


# ============================================================
# Fixtures - conftest.py дээрээс app, client, auth_user авна
# ============================================================

@pytest.fixture
def logged_in_user(auth_user):
    """auth_user-г ашиглана (chemist role)"""
    return auth_user
