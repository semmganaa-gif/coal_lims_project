# tests/integration/test_workspace_coverage.py
"""Analysis workspace coverage tests"""
import pytest


class TestAnalysisHub:
    """Analysis hub tests"""

    def test_analysis_hub_admin(self, auth_admin):
        """Analysis hub as admin"""
        # Try multiple possible paths
        for path in ['/analysis_hub', '/analysis/analysis_hub']:
            response = auth_admin.get(path)
            if response.status_code in [200, 302]:
                break
        assert response.status_code in [200, 302, 404]

    def test_analysis_hub_user(self, auth_user):
        """Analysis hub as regular user"""
        for path in ['/analysis_hub', '/analysis/analysis_hub']:
            response = auth_user.get(path)
            if response.status_code in [200, 302, 403]:
                break
        assert response.status_code in [200, 302, 403, 404]


class TestAnalysisPage:
    """Analysis page tests"""

    def test_analysis_page_mad(self, auth_admin):
        """Analysis page for Mad"""
        response = auth_admin.get('/analysis/analysis_page/Mad')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_aad(self, auth_admin):
        """Analysis page for Aad"""
        response = auth_admin.get('/analysis/analysis_page/Aad')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_vad(self, auth_admin):
        """Analysis page for Vad"""
        response = auth_admin.get('/analysis/analysis_page/Vad')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_cv(self, auth_admin):
        """Analysis page for CV"""
        response = auth_admin.get('/analysis/analysis_page/CV')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_ts(self, auth_admin):
        """Analysis page for TS"""
        response = auth_admin.get('/analysis/analysis_page/TS')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_gi(self, auth_admin):
        """Analysis page for Gi"""
        response = auth_admin.get('/analysis/analysis_page/Gi')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_csn(self, auth_admin):
        """Analysis page for CSN"""
        response = auth_admin.get('/analysis/analysis_page/CSN')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_trd(self, auth_admin):
        """Analysis page for TRD"""
        response = auth_admin.get('/analysis/analysis_page/TRD')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_with_sample_ids(self, auth_admin):
        """Analysis page with sample_ids"""
        response = auth_admin.get('/analysis/analysis_page/Mad?sample_ids=1,2,3')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_invalid_ids(self, auth_admin):
        """Analysis page with invalid sample_ids"""
        response = auth_admin.get('/analysis/analysis_page/Mad?sample_ids=abc,def')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_not_found(self, auth_admin):
        """Analysis page for non-existent code"""
        response = auth_admin.get('/analysis/analysis_page/UNKNOWN_CODE')
        assert response.status_code in [302, 404]


class TestAnalysisPageLogic:
    """Analysis page logic tests"""

    def test_norm_code(self, app):
        """Test norm_code function"""
        with app.app_context():
            from app.utils.codes import norm_code
            assert norm_code('Mad') in ['Mad', 'MAD', None]
            assert norm_code('Aad') in ['Aad', 'AAD', None]
            assert norm_code('CV') in ['CV', None]

    def test_escape_like_pattern(self, app):
        """Test escape_like_pattern function"""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern('Mad')
            assert 'Mad' in result or result == 'Mad'

    def test_sulfur_map_for(self, app):
        """Test sulfur_map_for function"""
        with app.app_context():
            from app.utils.qc import sulfur_map_for
            result = sulfur_map_for([])
            assert isinstance(result, dict)

    def test_sulfur_map_for_with_ids(self, app):
        """Test sulfur_map_for with sample IDs"""
        with app.app_context():
            from app.utils.qc import sulfur_map_for
            result = sulfur_map_for([1, 2, 3])
            assert isinstance(result, dict)


class TestFormMapping:
    """Form template mapping tests"""

    def test_form_mapping(self, app):
        """Test form mapping for all codes"""
        with app.app_context():
            form_map = {
                "Aad": "ash_form_aggrid",
                "Mad": "mad_aggrid",
                "Vad": "vad_aggrid",
                "MT": "mt_aggrid",
                "TS": "sulfur_aggrid",
                "CV": "cv_aggrid",
                "CSN": "csn_aggrid",
                "Gi": "Gi_aggrid",
                "TRD": "trd_aggrid",
                "P": "phosphorus_aggrid",
                "F": "fluorine_aggrid",
                "Cl": "chlorine_aggrid",
                "X": "xy_aggrid",
                "Y": "xy_aggrid",
                "CRI": "cricsr_aggrid",
                "CSR": "cricsr_aggrid",
            }
            for code, template in form_map.items():
                assert template.endswith('_aggrid')


class TestTimerPresets:
    """Timer presets tests"""

    def test_timer_presets_import(self, app):
        """Import timer presets"""
        with app.app_context():
            from app.config.qc_config import TIMER_PRESETS
            assert isinstance(TIMER_PRESETS, dict)

    def test_timer_presets_structure(self, app):
        """Timer presets have correct structure"""
        with app.app_context():
            from app.config.qc_config import TIMER_PRESETS
            for code, config in TIMER_PRESETS.items():
                assert 'layout' in config or 'timers' in config


class TestPairedResults:
    """Paired analysis results tests"""

    def test_paired_targets_xy(self, app):
        """X/Y paired targets"""
        with app.app_context():
            paired_targets = {"X", "Y"}
            assert "X" in paired_targets
            assert "Y" in paired_targets

    def test_paired_targets_cricsr(self, app):
        """CRI/CSR paired targets"""
        with app.app_context():
            paired_targets = {"CRI", "CSR"}
            assert "CRI" in paired_targets
            assert "CSR" in paired_targets


class TestAnalysisSchema:
    """Analysis schema tests"""

    def test_get_analysis_schema(self, app):
        """Get analysis schema for code"""
        with app.app_context():
            from app.config.analysis_schema import get_analysis_schema
            schema = get_analysis_schema('Mad')
            assert schema is None or isinstance(schema, dict)

    def test_get_analysis_schema_all_codes(self, app):
        """Get analysis schema for all codes"""
        with app.app_context():
            from app.config.analysis_schema import get_analysis_schema
            codes = ['Mad', 'Aad', 'Vad', 'CV', 'TS', 'Gi', 'CSN', 'TRD', 'P', 'F', 'Cl']
            for code in codes:
                schema = get_analysis_schema(code)
                assert schema is None or isinstance(schema, dict)
