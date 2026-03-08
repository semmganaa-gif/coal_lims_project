# tests/integration/test_analysis_workflow.py
# -*- coding: utf-8 -*-
"""
Шинжилгээний бүтэн workflow тест

Дараах үйл явцыг шалгана:
1. Дээж бэлтгэх
2. Шинжилгээний үр дүн оруулах
3. Senior баталгаажуулах/буцаах
4. Үр дүн засах
"""

import pytest
import json
from app import db
from app.models import Sample, AnalysisResult, User


@pytest.mark.integration
def test_analysis_result_submission(client, auth, test_sample):
    """Шинжилгээний үр дүн оруулах"""
    # 1. Химич хэрэглэгчээр нэвтрэх
    auth.login(username='chemist', password='TestPass123')

    # 2. Шинжилгээний үр дүн оруулах
    response = client.post('/api/save_results', json={
        'sample_id': test_sample.id,
        'analysis_code': 'mt',
        'raw_data': {
            'measurement_1': 25.2,
            'measurement_2': 25.4
        },
        'final_result': 25.3,
        'status': 'pending_review'
    })

    # API returns 200 or 207 MULTI STATUS
    assert response.status_code in [200, 207]
    data = response.get_json()
    assert data.get('message') or data.get('results') or data.get('success') is not None

    # 3. Database-ээс шалгах (API нь code-ийг томоор нормчилдог)
    result = AnalysisResult.query.filter_by(
        sample_id=test_sample.id,
        analysis_code='MT'
    ).first()
    assert result is not None


@pytest.mark.integration
def test_analysis_approval_workflow(client, auth, test_sample):
    """Шинжилгээний үр дүн баталгаажуулах workflow"""
    # 1. Химич хэрэглэгчээр үр дүн оруулах
    auth.login(username='chemist', password='TestPass123')

    response = client.post('/api/save_results', json={
        'sample_id': test_sample.id,
        'analysis_code': 'mt',
        'final_result': 25.5,
        'status': 'pending_review'
    })
    assert response.status_code in [200, 207]

    # API нь code-ийг томоор нормчилдог
    result = AnalysisResult.query.filter_by(
        sample_id=test_sample.id,
        analysis_code='MT'
    ).first()
    assert result is not None

    # 2. Гарах
    auth.logout()

    # 3. Ахлахаар нэвтрэх (ahlah role - батлах эрхтэй)
    auth.login(username='senior', password='TestPass123')

    # 4. Үр дүн баталгаажуулах
    response = client.post(f'/api/update_result_status/{result.id}/approved')
    # 200 эсвэл redirect (302) бол амжилттай
    assert response.status_code in [200, 302]


@pytest.mark.integration
def test_analysis_rejection_workflow(client, auth, test_sample):
    """Шинжилгээний үр дүн буцаах workflow"""
    # 1. Үр дүн оруулах
    auth.login(username='chemist', password='TestPass123')

    response = client.post('/api/save_results', json={
        'sample_id': test_sample.id,
        'analysis_code': 'mt',
        'final_result': 25.5,
        'status': 'pending_review'
    })
    assert response.status_code in [200, 207]

    result = AnalysisResult.query.filter_by(
        sample_id=test_sample.id,
        analysis_code='MT'
    ).first()
    assert result is not None

    # 2. Ахлахаар нэвтрэх
    auth.logout()
    auth.login(username='senior', password='TestPass123')

    # 3. Үр дүн буцаах
    response = client.post(f'/api/update_result_status/{result.id}/rejected')
    assert response.status_code in [200, 302]


@pytest.mark.integration
def test_multiple_analysis_workflow(client, auth, test_sample):
    """Олон шинжилгээ нэг дээж дээр хийх"""
    # 1. Нэвтрэх (himich)
    auth.login(username='chemist', password='TestPass123')

    # 2. Олон шинжилгээний үр дүн оруулах
    analyses = [
        {'code': 'mt', 'result': 25.5},
        {'code': 'aad', 'result': 15.2},
        {'code': 'vad', 'result': 35.8},
    ]

    for analysis in analyses:
        response = client.post('/api/save_results', json={
            'sample_id': test_sample.id,
            'analysis_code': analysis['code'],
            'final_result': analysis['result'],
            'status': 'pending_review'
        })
        assert response.status_code in [200, 207]

    # 3. Бүх шинжилгээ бүртгэгдсэн эсэхийг шалгах
    results = AnalysisResult.query.filter_by(sample_id=test_sample.id).all()
    assert len(results) >= 3

    # 4. Гарах ба ахлахаар нэвтрэх (senior role шаардагдана)
    auth.logout()
    auth.login(username='senior', password='TestPass123')

    # 5. Бүх үр дүнг баталгаажуулах
    for result in results:
        response = client.post(f'/api/update_result_status/{result.id}/approved')
        assert response.status_code in [200, 302]


@pytest.mark.integration
def test_analysis_calculation_workflow(client, auth, test_sample):
    """
    Тооцоолол агуулсан шинжилгээний workflow

    Mt, Mad, Aad оруулаад Ad тооцоолох
    """
    # 1. Нэвтрэх
    auth.login(username='chemist', password='TestPass123')

    # 2. Үндсэн параметрүүд оруулах
    base_analyses = [
        {'code': 'mt', 'result': 10.5},
        {'code': 'mad', 'result': 2.5},
        {'code': 'aad', 'result': 15.2},
    ]

    for analysis in base_analyses:
        response = client.post('/api/save_results', json={
            'sample_id': test_sample.id,
            'analysis_code': analysis['code'],
            'final_result': analysis['result'],
            'status': 'approved'
        })
        assert response.status_code in [200, 207]

    # 3. Sample summary хуудас руу очиж тооцоолол харах
    response = client.get('/api/sample_summary')
    assert response.status_code == 200
