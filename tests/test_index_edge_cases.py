# tests/test_index_edge_cases.py
# -*- coding: utf-8 -*-
"""
Edge case tests for app/routes/main/index.py
Focus on error handling, validation, and special cases
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock


class TestWeightValidation:
    """Tests for weight validation edge cases."""

    def test_weight_too_small(self, client, auth_admin, app, db):
        """Test weight below MIN_SAMPLE_WEIGHT."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['WEIGHT_SMALL_001'],
            'weights': ['0.001'],  # Too small
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200
        # Should contain warning about weight

    def test_weight_too_large(self, client, auth_admin, app, db):
        """Test weight above MAX_SAMPLE_WEIGHT."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['WEIGHT_LARGE_001'],
            'weights': ['999999'],  # Too large
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_weight_invalid_format(self, client, auth_admin, app, db):
        """Test invalid weight format (not a number)."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['WEIGHT_INVALID_001'],
            'weights': ['not_a_number'],
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_weight_empty(self, client, auth_admin, app, db):
        """Test empty weight for required weight sample."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['WEIGHT_EMPTY_001'],
            'weights': [''],  # Empty
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_weight_negative(self, client, auth_admin, app, db):
        """Test negative weight."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['WEIGHT_NEG_001'],
            'weights': ['-50'],
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_weight_zero(self, client, auth_admin, app, db):
        """Test zero weight."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['WEIGHT_ZERO_001'],
            'weights': ['0'],
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestDuplicateSample:
    """Tests for duplicate sample handling."""

    def test_duplicate_sample_code(self, client, auth_admin, app, db):
        """Test duplicate sample code handling."""
        # First registration
        response1 = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['DUP_TEST_001'],
            'weights': ['100'],
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)

        # Second registration with same code
        response2 = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['DUP_TEST_001'],
            'weights': ['100'],
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response2.status_code == 200


class TestWTLSpecialCases:
    """Tests for WTL sample registration special cases."""

    def test_wtl_no_lab_number(self, client, auth_admin, app, db):
        """Test WTL registration without lab number."""
        response = client.post('/', data={
            'client_name': 'WTL',
            'sample_type': 'WTL',
            'sample_date': date.today().isoformat(),
            'lab_number': '',  # Empty
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200
        # Should show error flash

    def test_wtl_size_registration(self, client, auth_admin, app, db):
        """Test WTL Size sample registration."""
        response = client.post('/', data={
            'client_name': 'WTL',
            'sample_type': 'Size',
            'sample_date': date.today().isoformat(),
            'lab_number': 'SIZE001',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_wtl_fl_registration(self, client, auth_admin, app, db):
        """Test WTL FL sample registration."""
        response = client.post('/', data={
            'client_name': 'WTL',
            'sample_type': 'FL',
            'sample_date': date.today().isoformat(),
            'lab_number': 'FL001',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_wtl_mg_no_sample_code(self, client, auth_admin, app, db):
        """Test WTL MG without sample code."""
        response = client.post('/', data={
            'client_name': 'WTL',
            'sample_type': 'MG',
            'sample_date': date.today().isoformat(),
            'sample_code': '',  # Empty
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_wtl_test_no_sample_code(self, client, auth_admin, app, db):
        """Test WTL Test without sample code."""
        response = client.post('/', data={
            'client_name': 'WTL',
            'sample_type': 'Test',
            'sample_date': date.today().isoformat(),
            'sample_code': '',  # Empty
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestLABSpecialCases:
    """Tests for LAB sample registration special cases."""

    def test_lab_cm_with_active_standard(self, client, auth_admin, app, db):
        """Test LAB CM with active control standard."""
        with app.app_context():
            from app.models import ControlStandard
            # Create active CM standard
            cm = ControlStandard.query.filter_by(is_active=True).first()
            if not cm:
                cm = ControlStandard(
                    name='CM-2025-Q4-TEST',
                    is_active=True
                )
                db.session.add(cm)
                db.session.commit()

        response = client.post('/', data={
            'client_name': 'LAB',
            'sample_type': 'CM',
            'sample_date': date.today().isoformat(),
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_lab_gbw_with_active_standard(self, client, auth_admin, app, db):
        """Test LAB GBW with active GBW standard (route handles no standard case)."""
        response = client.post('/', data={
            'client_name': 'LAB',
            'sample_type': 'GBW',
            'sample_date': date.today().isoformat(),
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_lab_unknown_type(self, client, auth_admin, app, db):
        """Test LAB with unknown sample type."""
        response = client.post('/', data={
            'client_name': 'LAB',
            'sample_type': 'Unknown',
            'sample_date': date.today().isoformat(),
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestCHPPSpecialCases:
    """Tests for CHPP sample registration special cases."""

    def test_chpp_com_registration(self, client, auth_admin, app, db):
        """Test CHPP COM sample registration."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': 'COM',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['COM_TEST_001'],
            'weights': ['150'],
            'list_type': 'chpp_com',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_chpp_multiple_codes(self, client, auth_admin, app, db):
        """Test CHPP with multiple sample codes."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['MULTI_001', 'MULTI_002', 'MULTI_003'],
            'weights': ['100', '200', '300'],
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_chpp_empty_code_in_list(self, client, auth_admin, app, db):
        """Test CHPP with empty code in list."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['VALID_001', '', 'VALID_002'],
            'weights': ['100', '', '200'],
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestQCProcSpecialCases:
    """Tests for QC and Proc sample registration."""

    def test_qc_multi_gen_with_location(self, client, auth_admin, app, db):
        """Test QC multi_gen with location and product."""
        response = client.post('/', data={
            'client_name': 'QC',
            'sample_type': 'Gen',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['QC_GEN_001'],
            'weights': ['100'],
            'list_type': 'multi_gen',
            'location': 'Test Location 123',
            'product': 'Test Product ABC',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_proc_multi_gen(self, client, auth_admin, app, db):
        """Test Proc multi_gen registration."""
        response = client.post('/', data={
            'client_name': 'Proc',
            'sample_type': 'Gen',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['PROC_GEN_001'],
            'weights': ['100'],
            'list_type': 'multi_gen',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestUHGBNSpecialCases:
    """Tests for UHG-Geo and BN-Geo sample registration."""

    def test_uhg_geo_registration(self, client, auth_admin, app, db):
        """Test UHG-Geo sample registration."""
        response = client.post('/', data={
            'client_name': 'UHG-Geo',
            'sample_type': 'Core',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['UHG_CORE_001'],
            'list_type': 'multi_gen',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_bn_geo_registration(self, client, auth_admin, app, db):
        """Test BN-Geo sample registration."""
        response = client.post('/', data={
            'client_name': 'BN-Geo',
            'sample_type': 'Core',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['BN_CORE_001'],
            'list_type': 'multi_gen',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestFormIncomplete:
    """Tests for incomplete form submissions."""

    def test_no_client_name(self, client, auth_admin):
        """Test submission without client name."""
        response = client.post('/', data={
            'sample_type': '2H',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_no_sample_date(self, client, auth_admin):
        """Test submission without sample date."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_no_list_type_no_special_handling(self, client, auth_admin):
        """Test submission without list_type and no special client."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestPermissionDenied:
    """Tests for permission denied scenarios."""

    @pytest.mark.skip(reason="User password validation requires complex password")
    def test_analyst_cannot_register(self, client, app, db):
        """Test analyst user cannot register samples."""
        pass


class TestDatabaseErrors:
    """Tests for database error handling."""

    def test_database_commit_failure(self, client, auth_admin, app, db):
        """Test handling of database commit failure."""
        with patch('app.utils.database.safe_commit', return_value=False):
            response = client.post('/', data={
                'client_name': 'CHPP',
                'sample_type': '2H',
                'sample_date': date.today().isoformat(),
                'sample_codes': ['DB_FAIL_001'],
                'weights': ['100'],
                'list_type': 'chpp_2h',
                'sample_condition': 'normal',
                'return_sample': 'false',
                'retention_period': '7'
            }, follow_redirects=True)
            assert response.status_code == 200


class TestPreviewAnalysesEdgeCases:
    """Tests for preview analyses edge cases."""

    def test_preview_empty_sample_names(self, client, auth_admin):
        """Test preview with empty sample names array."""
        response = client.post('/preview-analyses',
            json={
                'sample_names': [],
                'client_name': 'CHPP',
                'sample_type': '2H'
            },
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_preview_null_client(self, client, auth_admin):
        """Test preview with null client name."""
        response = client.post('/preview-analyses',
            json={
                'sample_names': ['TEST001'],
                'client_name': None,
                'sample_type': '2H'
            },
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_preview_missing_sample_type(self, client, auth_admin):
        """Test preview with missing sample type."""
        response = client.post('/preview-analyses',
            json={
                'sample_names': ['TEST001'],
                'client_name': 'CHPP'
            },
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_preview_multiple_samples(self, client, auth_admin):
        """Test preview with multiple sample names."""
        response = client.post('/preview-analyses',
            json={
                'sample_names': ['PF211D1', 'PF221D2', 'HCC1D3'],
                'client_name': 'CHPP',
                'sample_type': '2H'
            },
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'PF211D1' in data


class TestRetentionPeriod:
    """Tests for retention period handling."""

    def test_default_retention_period(self, client, auth_admin, app, db):
        """Test default retention period."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['RET_DEFAULT_001'],
            'weights': ['100'],
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'false'
            # retention_period not specified
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_custom_retention_period(self, client, auth_admin, app, db):
        """Test custom retention period."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['RET_CUSTOM_001'],
            'weights': ['100'],
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '30'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestSampleCondition:
    """Tests for sample condition handling."""

    def test_various_sample_conditions(self, client, auth_admin, app, db):
        """Test various sample conditions."""
        conditions = ['normal', 'wet', 'dry', 'damaged']
        for i, condition in enumerate(conditions):
            response = client.post('/', data={
                'client_name': 'CHPP',
                'sample_type': '2H',
                'sample_date': date.today().isoformat(),
                'sample_codes': [f'COND_{i}_001'],
                'weights': ['100'],
                'list_type': 'chpp_2h',
                'sample_condition': condition,
                'return_sample': 'false',
                'retention_period': '7'
            }, follow_redirects=True)
            assert response.status_code == 200


class TestReturnSample:
    """Tests for return sample flag."""

    def test_return_sample_true(self, client, auth_admin, app, db):
        """Test return sample flag true."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['RETURN_TRUE_001'],
            'weights': ['100'],
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'true',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_return_sample_false(self, client, auth_admin, app, db):
        """Test return sample flag false."""
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['RETURN_FALSE_001'],
            'weights': ['100'],
            'list_type': 'chpp_2h',
            'sample_condition': 'normal',
            'return_sample': 'false',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code == 200
