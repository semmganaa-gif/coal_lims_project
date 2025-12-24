# tests/test_qc_routes_full.py
# -*- coding: utf-8 -*-
"""Complete tests for app/routes/analysis/qc.py"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date


class TestAutoFindHourlySamples:

    def test_empty_ids(self, app, db):
        with app.app_context():
            from app.routes.analysis.qc import _auto_find_hourly_samples
            result = _auto_find_hourly_samples([])
            assert result == []

    def test_with_sample_ids(self, app, db):
        with app.app_context():
            from app.routes.analysis.qc import _auto_find_hourly_samples
            from app.models import Sample, User
            
            user = User.query.first()
            if user:
                sample = Sample(
                    sample_code='SC20251225_D_COM',
                    client_name='CHPP',
                    sample_type='com',
                    user_id=user.id,
                    sample_date=date.today()
                )
                db.session.add(sample)
                db.session.commit()
                
                result = _auto_find_hourly_samples([sample.id])
                assert isinstance(result, list)


class TestGetQcStreamData:

    def test_empty_ids(self, app, db):
        with app.app_context():
            from app.routes.analysis.qc import _get_qc_stream_data
            result = _get_qc_stream_data([])
            assert result == []

    def test_with_sample_ids(self, app, db):
        with app.app_context():
            from app.routes.analysis.qc import _get_qc_stream_data
            from app.models import Sample, User
            
            user = User.query.first()
            if user:
                sample = Sample(
                    sample_code='QC_TEST_001',
                    client_name='CHPP',
                    sample_type='2 hourly',
                    user_id=user.id,
                    sample_date=date.today()
                )
                db.session.add(sample)
                db.session.commit()
                
                result = _get_qc_stream_data([sample.id])
                assert isinstance(result, list)


class TestCompositeCheck:

    def test_composite_check_requires_login(self, client):
        response = client.get('/qc/composite_check')
        assert response.status_code == 302


class TestNormLimit:

    def test_norm_limit_requires_login(self, client):
        response = client.get('/qc/norm_limit')
        assert response.status_code == 302


class TestCorrelationCheck:

    def test_correlation_check_requires_login(self, client):
        response = client.get('/correlation_check')
        assert response.status_code == 302


class TestQcHelpers:

    def test_qc_split_family(self, app):
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family('SC20251225_D1')
            assert family is not None or family == ''

    def test_qc_split_family_com(self, app):
        with app.app_context():
            from app.utils.qc import qc_split_family
            family, slot = qc_split_family('SC20251225_D_COM')
            assert family is not None


class TestQcConfigImports:

    def test_qc_param_codes(self, app):
        with app.app_context():
            from app.config.qc_config import QC_PARAM_CODES
            assert isinstance(QC_PARAM_CODES, (list, tuple, set))

    def test_qc_tolerance(self, app):
        with app.app_context():
            from app.config.qc_config import QC_TOLERANCE
            assert isinstance(QC_TOLERANCE, dict)
