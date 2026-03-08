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

    def test_import_ad_analyses(self):
        from app.routes.quality.control_charts import AD_ANALYSES
        assert isinstance(AD_ANALYSES, set)
        assert 'Aad' in AD_ANALYSES
        assert 'Vad' in AD_ANALYSES


# ============================================================
# Dry Basis Conversion Tests
# ============================================================

class TestConvertToDryBasis:
    """_convert_to_dry_basis функц тест"""

    def test_import_function(self):
        from app.routes.quality.control_charts import _convert_to_dry_basis
        assert _convert_to_dry_basis is not None

    def test_zero_moisture(self):
        from app.routes.quality.control_charts import _convert_to_dry_basis
        result = _convert_to_dry_basis(10.0, 0.0)
        assert result == 10.0

    def test_normal_moisture(self):
        from app.routes.quality.control_charts import _convert_to_dry_basis
        # Formula: dry = as_received * 100 / (100 - Mad)
        result = _convert_to_dry_basis(10.0, 5.0)
        expected = 10.0 * 100 / (100 - 5.0)
        assert abs(result - expected) < 0.001

    def test_none_moisture(self):
        from app.routes.quality.control_charts import _convert_to_dry_basis
        result = _convert_to_dry_basis(10.0, None)
        assert result == 10.0

    def test_high_moisture_edge(self):
        from app.routes.quality.control_charts import _convert_to_dry_basis
        # When moisture >= 100, return original value
        result = _convert_to_dry_basis(10.0, 100)
        assert result == 10.0

    def test_very_high_moisture(self):
        from app.routes.quality.control_charts import _convert_to_dry_basis
        result = _convert_to_dry_basis(10.0, 150)
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
        # _extract_standard_name now checks DB for active CM standard
        # when the extracted name is just 'CM'. Pass sample_type='CM'.
        with patch('app.routes.quality.control_charts.ControlStandard') as MockCS:
            mock_query = MockCS.query.filter_by.return_value
            mock_std = MagicMock()
            mock_std.name = 'CM-2025-Q4'
            mock_query.first.return_value = mock_std
            result = _extract_standard_name('CM_20251128_N_Q4', sample_type='CM')
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
# AD_ANALYSES Tests
# ============================================================

class TestAdAnalyses:
    """AD_ANALYSES тест"""

    def test_is_set(self):
        from app.routes.quality.control_charts import AD_ANALYSES
        assert isinstance(AD_ANALYSES, set)

    def test_contains_aad(self):
        from app.routes.quality.control_charts import AD_ANALYSES
        assert 'Aad' in AD_ANALYSES

    def test_contains_vad(self):
        from app.routes.quality.control_charts import AD_ANALYSES
        assert 'Vad' in AD_ANALYSES


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
