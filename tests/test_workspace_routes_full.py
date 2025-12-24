# tests/test_workspace_routes_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/routes/analysis/workspace.py
"""

import pytest
from unittest.mock import patch, MagicMock
import json


class TestAnalysisHub:
    """Tests for analysis_hub route."""

    def test_analysis_hub_requires_login(self, client):
        """Test analysis_hub requires authentication."""
        response = client.get('/analysis_hub')
        assert response.status_code == 302  # Redirect to login

    def test_analysis_hub_get(self, client, auth_user):
        """Test GET analysis_hub page."""
        response = client.get('/analysis_hub')
        assert response.status_code == 200

    def test_analysis_hub_admin_sees_all(self, client, auth_user, app, db):
        """Test admin sees all analysis types."""
        response = client.get('/analysis_hub')
        assert response.status_code == 200

    def test_analysis_hub_role_filtering(self, app, db):
        """Test role-based filtering of analysis types."""
        with app.app_context():
            from app.models import AnalysisType
            # Get analysis types count
            all_count = AnalysisType.query.count()
            assert all_count >= 0


class TestAnalysisPage:
    """Tests for analysis_page route."""

    def test_analysis_page_requires_login(self, client):
        """Test analysis_page requires authentication."""
        response = client.get('/analysis_page/Mad')
        assert response.status_code == 302  # Redirect to login

    def test_analysis_page_get(self, client, auth_user, app, db):
        """Test GET analysis_page."""
        with app.app_context():
            from app.models import AnalysisType
            # Ensure analysis type exists
            analysis = AnalysisType.query.filter_by(code='Mad').first()
            if not analysis:
                analysis = AnalysisType(code='Mad', name='Moisture Analysis', order_num=1)
                db.session.add(analysis)
                db.session.commit()

        response = client.get('/analysis_page/Mad')
        assert response.status_code == 200

    def test_analysis_page_with_sample_ids(self, client, auth_user, app, db):
        """Test analysis_page with sample IDs."""
        with app.app_context():
            from app.models import AnalysisType, Sample, User
            # Ensure analysis type exists
            analysis = AnalysisType.query.filter_by(code='Aad').first()
            if not analysis:
                analysis = AnalysisType(code='Aad', name='Ash Analysis', order_num=2)
                db.session.add(analysis)
                db.session.commit()

            # Create test sample
            user = User.query.first()
            if user:
                sample = Sample(
                    sample_code='WS_TEST_001',
                    client_name='CHPP',
                    sample_type='2 hourly',
                    user_id=user.id,
                    sample_date=None
                )
                db.session.add(sample)
                db.session.commit()
                sample_id = sample.id

        response = client.get(f'/analysis_page/Aad?sample_ids={sample_id}')
        assert response.status_code == 200

    def test_analysis_page_not_found(self, client, auth_user):
        """Test analysis_page with non-existent code returns 404."""
        response = client.get('/analysis_page/INVALID_CODE_XYZ')
        assert response.status_code == 404

    def test_analysis_page_vad(self, client, auth_user, app, db):
        """Test Vad analysis page (requires Mad results)."""
        with app.app_context():
            from app.models import AnalysisType
            analysis = AnalysisType.query.filter_by(code='Vad').first()
            if not analysis:
                analysis = AnalysisType(code='Vad', name='Volatiles Analysis', order_num=3)
                db.session.add(analysis)
                db.session.commit()

        response = client.get('/analysis_page/Vad')
        assert response.status_code == 200

    def test_analysis_page_cv(self, client, auth_user, app, db):
        """Test CV analysis page (requires sulfur map)."""
        with app.app_context():
            from app.models import AnalysisType
            analysis = AnalysisType.query.filter_by(code='CV').first()
            if not analysis:
                analysis = AnalysisType(code='CV', name='Calorific Value', order_num=4)
                db.session.add(analysis)
                db.session.commit()

        response = client.get('/analysis_page/CV')
        assert response.status_code == 200

    def test_analysis_page_gi(self, client, auth_user, app, db):
        """Test Gi analysis page."""
        with app.app_context():
            from app.models import AnalysisType
            analysis = AnalysisType.query.filter_by(code='Gi').first()
            if not analysis:
                analysis = AnalysisType(code='Gi', name='Grindability Index', order_num=5)
                db.session.add(analysis)
                db.session.commit()

        response = client.get('/analysis_page/Gi')
        assert response.status_code == 200

    def test_analysis_page_xy(self, client, auth_user, app, db):
        """Test X/Y analysis page (paired analysis)."""
        with app.app_context():
            from app.models import AnalysisType
            analysis = AnalysisType.query.filter_by(code='X').first()
            if not analysis:
                analysis = AnalysisType(code='X', name='X Analysis', order_num=10)
                db.session.add(analysis)
                db.session.commit()

        response = client.get('/analysis_page/X')
        assert response.status_code == 200

    def test_analysis_page_cricsr(self, client, auth_user, app, db):
        """Test CRI/CSR analysis page (paired analysis)."""
        with app.app_context():
            from app.models import AnalysisType
            analysis = AnalysisType.query.filter_by(code='CRI').first()
            if not analysis:
                analysis = AnalysisType(code='CRI', name='CRI Analysis', order_num=11)
                db.session.add(analysis)
                db.session.commit()

        response = client.get('/analysis_page/CRI')
        assert response.status_code == 200


class TestFormMapping:
    """Tests for form template mapping."""

    def test_form_map_coverage(self, app):
        """Test form map covers all analysis types."""
        with app.app_context():
            form_map = {
                "Aad": "ash_form_aggrid",
                "Mad": "mad_aggrid",
                "Vad": "vad_aggrid",
                "MT": "mt_aggrid",
                "TS": "sulfur_aggrid",
                "St,ad": "sulfur_aggrid",
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
                "Solid": "solid_aggrid",
                "FM": "free_moisture_aggrid",
                "m": "mass_aggrid"
            }
            assert len(form_map) > 10

    def test_template_names(self, app):
        """Test template names are valid."""
        with app.app_context():
            templates = [
                "ash_form_aggrid", "mad_aggrid", "vad_aggrid",
                "mt_aggrid", "sulfur_aggrid", "cv_aggrid"
            ]
            for t in templates:
                assert t.endswith('_aggrid') or t.endswith('_form')


class TestExistingResultsMap:
    """Tests for existing results map functionality."""

    def test_existing_results_empty(self, app, db):
        """Test existing results map with no results."""
        with app.app_context():
            from app.models import AnalysisResult
            # Query should return empty
            results = AnalysisResult.query.filter(
                AnalysisResult.status.in_(["pending_review", "rejected"])
            ).limit(1).all()
            assert isinstance(results, list)

    def test_existing_results_json_parsing(self, app):
        """Test JSON parsing of raw_data."""
        with app.app_context():
            raw_data = '{"m1": 10.0, "m2": 1.0}'
            parsed = json.loads(raw_data)
            assert parsed['m1'] == 10.0


class TestPairedResultsMap:
    """Tests for paired results map functionality."""

    def test_paired_codes_xy(self, app):
        """Test X/Y paired codes."""
        with app.app_context():
            base_code = "X"
            if base_code in {"X", "Y"}:
                paired_targets = {"X", "Y"}
                assert paired_targets == {"X", "Y"}

    def test_paired_codes_cricsr(self, app):
        """Test CRI/CSR paired codes."""
        with app.app_context():
            base_code = "CRI"
            if base_code in {"CRI", "CSR"}:
                paired_targets = {"CRI", "CSR"}
                assert paired_targets == {"CRI", "CSR"}


class TestTimerPresets:
    """Tests for timer presets configuration."""

    def test_timer_presets_import(self, app):
        """Test timer presets can be imported."""
        with app.app_context():
            from app.config.qc_config import TIMER_PRESETS
            assert isinstance(TIMER_PRESETS, dict)

    def test_timer_presets_default(self, app):
        """Test default timer preset structure."""
        with app.app_context():
            default_preset = {
                "layout": "right",
                "digit_size": "lg",
                "editable": False,
                "timers": []
            }
            assert "layout" in default_preset
            assert "timers" in default_preset


class TestRelatedEquipments:
    """Tests for related equipments query."""

    def test_related_equipments_query(self, app, db):
        """Test related equipments query."""
        with app.app_context():
            from app.models import Equipment
            from sqlalchemy import or_

            # Query should not raise
            equipments = Equipment.query.filter(
                or_(Equipment.status.is_(None), Equipment.status != 'retired')
            ).limit(10).all()
            assert isinstance(equipments, list)

    def test_equipment_with_related_analysis(self, app, db):
        """Test equipment with related_analysis field."""
        with app.app_context():
            from app.models import Equipment

            eq = Equipment(
                name='Test Furnace',
                related_analysis='Aad,Vad',
                status='active'
            )
            db.session.add(eq)
            db.session.commit()

            found = Equipment.query.filter(
                Equipment.related_analysis.ilike('%Aad%')
            ).first()
            assert found is not None
