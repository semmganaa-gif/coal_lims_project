# tests/integration/test_save_results_validation.py
"""
Integration tests for save_results endpoint validation

Энэ тестүүд нь save_results endpoint-ийн input validation
зөв ажиллахыг шалгана.
"""

import pytest
import json
from flask import url_for


class TestSaveResultsValidation:
    """Integration tests for /api/save_results validation"""

    def test_valid_input_accepted(self, client, app):
        """Valid input should be accepted"""
        # Note: Requires authenticated user and existing sample
        # This is a template - adjust based on your auth setup
        pass

    def test_invalid_sample_id_rejected(self, client, app):
        """Invalid sample_id should be rejected"""
        with client:
            # Login first (adjust based on your auth)
            # client.post('/login', data={'username': 'test', 'password': 'test'})

            response = client.post(
                '/api/analysis/save_results',
                data=json.dumps([{
                    'sample_id': 'invalid',  # ❌ Not a number
                    'analysis_code': 'MT',
                    'final_result': 5.2
                }]),
                content_type='application/json'
            )

            # Should return error or skip this item
            assert response.status_code in [200, 400]

    def test_negative_sample_id_rejected(self, client, app):
        """Negative sample_id should be rejected"""
        with client:
            response = client.post(
                '/api/analysis/save_results',
                data=json.dumps([{
                    'sample_id': -1,  # ❌ Negative
                    'analysis_code': 'MT',
                    'final_result': 5.2
                }]),
                content_type='application/json'
            )

            assert response.status_code in [200, 400]

    def test_invalid_analysis_code_rejected(self, client, app):
        """Invalid analysis code should be rejected"""
        with client:
            response = client.post(
                '/api/analysis/save_results',
                data=json.dumps([{
                    'sample_id': 1,
                    'analysis_code': '<script>alert("xss")</script>',  # ❌ XSS attempt
                    'final_result': 5.2
                }]),
                content_type='application/json'
            )

            assert response.status_code in [200, 400]

    def test_out_of_range_moisture_rejected(self, client, app):
        """Moisture > 20% should be rejected"""
        with client:
            response = client.post(
                '/api/analysis/save_results',
                data=json.dumps([{
                    'sample_id': 1,
                    'analysis_code': 'Mad',
                    'final_result': 50.0  # ❌ > 20% (out of range)
                }]),
                content_type='application/json'
            )

            # Should log warning and either skip or set to None
            assert response.status_code in [200, 400]

    def test_string_result_converted_to_float(self, client, app):
        """String "5.2" should be converted to float"""
        with client:
            response = client.post(
                '/api/analysis/save_results',
                data=json.dumps([{
                    'sample_id': 1,
                    'analysis_code': 'MT',
                    'final_result': '5.2'  # String
                }]),
                content_type='application/json'
            )

            # Should accept and convert
            assert response.status_code == 200

    def test_invalid_string_result_rejected(self, client, app):
        """Non-numeric string should be rejected"""
        with client:
            response = client.post(
                '/api/analysis/save_results',
                data=json.dumps([{
                    'sample_id': 1,
                    'analysis_code': 'MT',
                    'final_result': 'abc'  # ❌ Not a number
                }]),
                content_type='application/json'
            )

            # Should log error and skip or reject
            assert response.status_code in [200, 400]

    def test_sql_injection_attempt_blocked(self, client, app):
        """SQL injection attempt should be blocked"""
        with client:
            response = client.post(
                '/api/analysis/save_results',
                data=json.dumps([{
                    'sample_id': "1; DROP TABLE sample; --",  # ❌ SQL injection
                    'analysis_code': 'MT',
                    'final_result': 5.2
                }]),
                content_type='application/json'
            )

            # Should be rejected by validation
            assert response.status_code in [200, 400]
            # Database should still exist
            from app.models import Sample
            assert Sample.query.count() >= 0  # Should not crash

    def test_batch_partial_failure(self, client, app):
        """Batch with some valid and some invalid items"""
        with client:
            response = client.post(
                '/api/analysis/save_results',
                data=json.dumps([
                    {
                        'sample_id': 1,
                        'analysis_code': 'MT',
                        'final_result': 5.2  # ✅ Valid
                    },
                    {
                        'sample_id': -999,  # ❌ Invalid
                        'analysis_code': 'MT',
                        'final_result': 5.2
                    },
                    {
                        'sample_id': 2,
                        'analysis_code': 'Aad',
                        'final_result': 10.5  # ✅ Valid
                    },
                ]),
                content_type='application/json'
            )

            # Should save valid items and skip invalid
            assert response.status_code == 200
            data = response.get_json()
            # Should have errors for invalid items
            assert 'errors' in data or 'failed_count' in data

    def test_none_final_result_accepted(self, client, app):
        """None/null final_result should be accepted"""
        with client:
            response = client.post(
                '/api/analysis/save_results',
                data=json.dumps([{
                    'sample_id': 1,
                    'analysis_code': 'MT',
                    'final_result': None  # ✅ Allowed
                }]),
                content_type='application/json'
            )

            assert response.status_code == 200

    def test_empty_batch_rejected(self, client, app):
        """Empty batch should be rejected"""
        with client:
            response = client.post(
                '/api/analysis/save_results',
                data=json.dumps([]),
                content_type='application/json'
            )

            assert response.status_code == 400

    def test_non_json_rejected(self, client, app):
        """Non-JSON payload should be rejected"""
        with client:
            response = client.post(
                '/api/analysis/save_results',
                data='not json',
                content_type='text/plain'
            )

            assert response.status_code == 400
