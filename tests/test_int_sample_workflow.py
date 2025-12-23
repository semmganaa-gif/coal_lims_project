# tests/integration/test_sample_workflow.py
# -*- coding: utf-8 -*-
"""
Дээжний бүтэн workflow тест

Дараах үйл явцыг шалгана:
1. Дээж үүсгэх (API ашиглан)
2. Дээж засах
3. Дээжид шинжилгээ хийх
4. Дээж архивлах
"""

import pytest
import json
import uuid
from app import db
from app.models import Sample, AnalysisResult, User


@pytest.mark.integration
def test_sample_edit_workflow(app, client, auth, test_sample):
    """Дээж засах workflow"""
    # 1. Нэвтрэх
    auth.login()

    with app.app_context():
        # Re-query sample in this context
        sample = db.session.get(Sample, test_sample.id)
        sample_id = sample.id
        original_code = sample.sample_code

        # 2. Дээж засах хуудас руу очих
        response = client.get(f'/edit_sample/{sample_id}')
        # 200 эсвэл 302 (redirect) байж болно
        assert response.status_code in [200, 302]

        # 3. Edit form submit
        response = client.post(f'/edit_sample/{sample_id}', data={
            'sample_code': original_code,
            'client_name': 'QC',  # Valid client_name
            'sample_type': 'Нүүрс',
            'weight': 3000,
            'analyses_to_perform': json.dumps(['MT', 'MAD']),
        }, follow_redirects=True)

        # Should redirect or show success
        assert response.status_code == 200


@pytest.mark.integration
def test_sample_archive_workflow(app, client, auth, test_sample):
    """Дээж архивлах workflow"""
    # 1. Нэвтрэх
    auth.login()

    with app.app_context():
        sample_id = test_sample.id

        # 2. Дээж архивлах
        response = client.post('/api/sample_summary', data={
            'action': 'archive',
            'sample_ids': str(sample_id)
        }, follow_redirects=True)

        assert response.status_code == 200


@pytest.mark.integration
def test_sample_api_workflow(app, client, auth):
    """API ашиглан дээж үүсгэх workflow"""
    # 1. Нэвтрэх
    auth.login()

    with app.app_context():
        # Get user
        user = User.query.filter_by(username='chemist').first()

        # 2. Дээж үүсгэх (шууд database-д)
        unique_code = f"API-TEST-{uuid.uuid4().hex[:6]}"
        sample = Sample(
            sample_code=unique_code,
            user_id=user.id,
            client_name="QC",
            sample_type="Нүүрс",
            weight=2500
        )
        db.session.add(sample)
        db.session.commit()
        sample_id = sample.id

        # 3. Шинжилгээний үр дүн бүртгэх
        response = client.post('/api/save_results', json={
            'sample_id': sample_id,
            'analysis_code': 'mt',
            'final_result': 25.5,
            'status': 'pending_review'
        })
        assert response.status_code == 200

        # 4. Үр дүн шалгах
        result = AnalysisResult.query.filter_by(
            sample_id=sample_id,
            analysis_code='MT'
        ).first()
        assert result is not None

        # Cleanup
        db.session.delete(result)
        db.session.delete(sample)
        db.session.commit()


@pytest.mark.integration
def test_sample_summary_page(client, auth):
    """Sample summary хуудас ажиллаж байгааг шалгах"""
    auth.login()

    response = client.get('/api/sample_summary')
    assert response.status_code == 200
    # HTML хуудас буцах ёстой
    assert b'<!doctype html>' in response.data.lower() or b'<!DOCTYPE html>' in response.data


@pytest.mark.integration
def test_index_page_accessible(client, auth):
    """Index хуудас ажиллаж байгааг шалгах"""
    auth.login()

    response = client.get('/index')
    assert response.status_code == 200
