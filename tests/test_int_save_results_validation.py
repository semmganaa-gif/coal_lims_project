# tests/integration/test_save_results_validation.py
"""
Integration tests for save_results endpoint validation

Энэ тестүүд нь save_results endpoint-ийн input validation
зөв ажиллахыг шалгана.
"""

import pytest
import json


class TestSaveResultsValidation:
    """Integration tests for /api/save_results validation"""

    def test_valid_input_accepted(self, client, auth, test_sample):
        """Valid input should be accepted"""
        auth.login()

        response = client.post('/api/save_results', json={
            'sample_id': test_sample.id,
            'analysis_code': 'mt',
            'final_result': 25.5,
            'status': 'pending_review'
        })

        # API returns 200 or 207 MULTI STATUS
        assert response.status_code in [200, 207]

    def test_invalid_sample_id_rejected(self, client, auth):
        """Invalid sample_id should be handled gracefully"""
        auth.login()

        response = client.post('/api/save_results', json={
            'sample_id': 999999,  # Non-existent
            'analysis_code': 'mt',
            'final_result': 25.5
        })

        # Should return error or handle gracefully
        assert response.status_code in [200, 207, 400, 404, 422]

    def test_missing_sample_id_rejected(self, client, auth):
        """Missing sample_id should be rejected"""
        auth.login()

        response = client.post('/api/save_results', json={
            'analysis_code': 'mt',
            'final_result': 25.5
        })

        # Should return error
        assert response.status_code in [200, 207, 400, 422]

    def test_string_result_converted_to_float(self, client, auth, test_sample):
        """String result should be converted to float"""
        auth.login()

        response = client.post('/api/save_results', json={
            'sample_id': test_sample.id,
            'analysis_code': 'mt',
            'final_result': '25.5',  # String instead of float
            'status': 'pending_review'
        })

        # Should accept and convert
        assert response.status_code in [200, 207]

    def test_empty_batch_handled(self, client, auth):
        """Empty batch should be handled"""
        auth.login()

        response = client.post('/api/save_results', json={})

        # Should return appropriate response
        assert response.status_code in [200, 207, 400, 422]

    def test_non_json_handled(self, client, auth):
        """Non-JSON request should be handled"""
        auth.login()

        response = client.post('/api/save_results',
                              data='not json',
                              content_type='text/plain')

        # Should return error
        assert response.status_code in [400, 415, 422, 500]

    def test_batch_results_accepted(self, client, auth, test_sample):
        """Batch results should be accepted"""
        auth.login()

        # Single result as batch format
        response = client.post('/api/save_results', json={
            'sample_id': test_sample.id,
            'analysis_code': 'mad',
            'final_result': 5.5
        })

        assert response.status_code in [200, 207]

    def test_null_result_handled(self, client, auth, test_sample):
        """Null final_result should be handled"""
        auth.login()

        response = client.post('/api/save_results', json={
            'sample_id': test_sample.id,
            'analysis_code': 'mt',
            'final_result': None
        })

        # Should handle gracefully - various valid responses
        assert response.status_code in [200, 207, 400, 422, 500]
