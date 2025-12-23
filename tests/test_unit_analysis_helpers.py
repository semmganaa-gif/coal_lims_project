# tests/unit/test_analysis_helpers.py
# -*- coding: utf-8 -*-
"""
Analysis helpers and routes tests
"""

import pytest
from app.routes.analysis.helpers import (
    QC_PARAM_CODES, QC_TOLERANCE, QC_SPEC_DEFAULT,
    COMPOSITE_QC_CODES, COMPOSITE_QC_LIMITS, TIMER_PRESETS,
    analysis_role_required
)


class TestQCConstants:
    """Test QC constants"""

    def test_qc_param_codes_exists(self):
        """QC_PARAM_CODES is defined"""
        assert QC_PARAM_CODES is not None
        assert isinstance(QC_PARAM_CODES, list)
        assert len(QC_PARAM_CODES) > 0

    def test_qc_param_codes_contains_mad(self):
        """QC_PARAM_CODES contains Mad"""
        assert 'Mad' in QC_PARAM_CODES

    def test_qc_param_codes_contains_aad(self):
        """QC_PARAM_CODES contains Aad"""
        assert 'Aad' in QC_PARAM_CODES

    def test_qc_tolerance_exists(self):
        """QC_TOLERANCE is defined"""
        assert QC_TOLERANCE is not None
        assert isinstance(QC_TOLERANCE, dict)

    def test_qc_tolerance_has_values(self):
        """QC_TOLERANCE has values for codes"""
        assert 'Mad' in QC_TOLERANCE
        assert 'Aad' in QC_TOLERANCE
        assert QC_TOLERANCE['Mad'] > 0

    def test_qc_spec_default_exists(self):
        """QC_SPEC_DEFAULT is defined"""
        assert QC_SPEC_DEFAULT is not None
        assert isinstance(QC_SPEC_DEFAULT, dict)


class TestCompositeQCConstants:
    """Test Composite QC constants"""

    def test_composite_qc_codes_exists(self):
        """COMPOSITE_QC_CODES is defined"""
        assert COMPOSITE_QC_CODES is not None
        assert isinstance(COMPOSITE_QC_CODES, list)

    def test_composite_qc_codes_contains_expected(self):
        """COMPOSITE_QC_CODES contains expected codes"""
        assert 'Mad' in COMPOSITE_QC_CODES
        assert 'Aad' in COMPOSITE_QC_CODES

    def test_composite_qc_limits_exists(self):
        """COMPOSITE_QC_LIMITS is defined"""
        assert COMPOSITE_QC_LIMITS is not None
        assert isinstance(COMPOSITE_QC_LIMITS, dict)

    def test_composite_qc_limits_structure(self):
        """COMPOSITE_QC_LIMITS has proper structure"""
        for code, limits in COMPOSITE_QC_LIMITS.items():
            assert 'mode' in limits
            assert 'warn' in limits
            assert 'fail' in limits

    def test_composite_qc_limits_modes(self):
        """COMPOSITE_QC_LIMITS modes are valid"""
        for code, limits in COMPOSITE_QC_LIMITS.items():
            assert limits['mode'] in ['abs', 'rel']


class TestTimerPresets:
    """Test Timer presets"""

    def test_timer_presets_exists(self):
        """TIMER_PRESETS is defined"""
        assert TIMER_PRESETS is not None
        assert isinstance(TIMER_PRESETS, dict)

    def test_timer_presets_aad(self):
        """TIMER_PRESETS has Aad"""
        assert 'Aad' in TIMER_PRESETS
        preset = TIMER_PRESETS['Aad']
        assert 'layout' in preset
        assert 'timers' in preset

    def test_timer_presets_vad(self):
        """TIMER_PRESETS has Vad"""
        assert 'Vad' in TIMER_PRESETS

    def test_timer_presets_mad(self):
        """TIMER_PRESETS has Mad"""
        assert 'Mad' in TIMER_PRESETS

    def test_timer_presets_gi(self):
        """TIMER_PRESETS has Gi"""
        assert 'Gi' in TIMER_PRESETS

    def test_timer_preset_structure(self):
        """Timer preset has proper structure"""
        preset = TIMER_PRESETS.get('Aad', {})
        assert 'layout' in preset
        assert 'digit_size' in preset
        assert 'editable' in preset
        assert 'timers' in preset

    def test_timer_preset_timers_structure(self):
        """Timer timers have proper structure"""
        preset = TIMER_PRESETS.get('Aad', {})
        timers = preset.get('timers', [])
        for timer in timers:
            assert 'label' in timer
            assert 'seconds' in timer


class TestAnalysisRoleRequired:
    """Test analysis_role_required decorator"""

    def test_decorator_exists(self):
        """analysis_role_required exists"""
        assert analysis_role_required is not None
        assert callable(analysis_role_required)

    def test_decorator_returns_callable(self):
        """analysis_role_required returns callable"""
        decorator = analysis_role_required()
        assert callable(decorator)

    def test_decorator_with_roles(self):
        """analysis_role_required with roles list"""
        decorator = analysis_role_required(['admin', 'senior'])
        assert callable(decorator)

    def test_decorator_with_single_role(self):
        """analysis_role_required with single role"""
        decorator = analysis_role_required(['chemist'])
        assert callable(decorator)

    def test_decorator_default_roles(self):
        """analysis_role_required default roles"""
        decorator = analysis_role_required()
        assert callable(decorator)


class TestQCToleranceValues:
    """Test QC tolerance specific values"""

    def test_mad_tolerance(self):
        """Mad tolerance value"""
        assert QC_TOLERANCE['Mad'] == 0.30

    def test_aad_tolerance(self):
        """Aad tolerance value"""
        assert QC_TOLERANCE['Aad'] == 0.50

    def test_vdaf_tolerance(self):
        """Vdaf tolerance value"""
        assert QC_TOLERANCE['Vdaf'] == 0.50

    def test_csn_tolerance(self):
        """CSN tolerance value"""
        assert QC_TOLERANCE['CSN'] == 0.30

    def test_gi_tolerance(self):
        """Gi tolerance value"""
        assert QC_TOLERANCE['Gi'] == 3.0


class TestQCSpecDefault:
    """Test QC spec default values"""

    def test_vdaf_spec(self):
        """Vdaf spec range"""
        spec = QC_SPEC_DEFAULT.get('Vdaf')
        assert spec is not None
        assert isinstance(spec, tuple)
        assert len(spec) == 2

    def test_aad_spec(self):
        """Aad spec range"""
        spec = QC_SPEC_DEFAULT.get('Aad')
        assert spec is not None

    def test_csn_spec(self):
        """CSN spec range"""
        spec = QC_SPEC_DEFAULT.get('CSN')
        assert spec is not None

    def test_gi_spec(self):
        """Gi spec range"""
        spec = QC_SPEC_DEFAULT.get('Gi')
        assert spec is not None
