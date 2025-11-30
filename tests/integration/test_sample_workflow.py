# tests/integration/test_sample_workflow.py
# -*- coding: utf-8 -*-
"""
Дээжний бүтэн workflow тест

Дараах үйл явцыг шалгана:
1. Дээж үүсгэх
2. Дээж засах
3. Дээжид шинжилгээ хийх
4. Дээж архивлах
"""

import pytest
import json
from app import db
from app.models import Sample, AnalysisResult


@pytest.mark.integration
def test_sample_creation_workflow(client, auth, test_user):
    """Дээж үүсгэх бүтэн workflow"""
    # 1. Нэвтрэх
    auth.login()

    # 2. Дээж үүсгэх хуудас руу очих
    response = client.get('/create_sample')
    assert response.status_code == 200

    # 3. Дээж үүсгэх
    response = client.post('/create_sample', data={
        'sample_code': 'TEST-001',
        'client_name': 'Test Client',
        'sample_type': 'Нүүрс',
        'weight': 2500,
        'sample_condition': 'Хуурай',
        'analyses_to_perform': json.dumps(['m', 'mt', 'a', 'v']),
        'received_date': '2025-01-15 10:00'
    }, follow_redirects=True)

    assert response.status_code == 200

    # 4. Database-ээс шалгах
    sample = Sample.query.filter_by(sample_code='TEST-001').first()
    assert sample is not None
    assert sample.client_name == 'Test Client'
    assert sample.weight == 2500


@pytest.mark.integration
def test_sample_edit_workflow(client, auth, test_sample):
    """Дээж засах workflow"""
    # 1. Нэвтрэх
    auth.login()

    # 2. Дээж засах
    response = client.post(f'/edit_sample/{test_sample.id}', data={
        'sample_code': test_sample.sample_code,
        'client_name': 'Updated Client Name',
        'sample_type': test_sample.sample_type,
        'weight': 3000,
        'analyses_to_perform': json.dumps(['m', 'mt']),
    }, follow_redirects=True)

    assert response.status_code == 200

    # 3. Өөрчлөлт хадгалагдсан эсэхийг шалгах
    db.session.refresh(test_sample)
    assert test_sample.client_name == 'Updated Client Name'
    assert test_sample.weight == 3000


@pytest.mark.integration
def test_sample_archive_workflow(client, auth, test_sample):
    """Дээж архивлах workflow"""
    # 1. Нэвтрэх
    auth.login()

    # 2. Дээж архивлах
    response = client.post('/api/sample_summary', data={
        'action': 'archive',
        'sample_ids': str(test_sample.id)
    }, follow_redirects=True)

    assert response.status_code == 200

    # 3. Статус шалгах
    db.session.refresh(test_sample)
    assert test_sample.status == 'archived'


@pytest.mark.integration
def test_complete_sample_lifecycle(client, auth, test_user):
    """
    Дээжний бүтэн амьдралын мөчлөг:
    Үүсгэх → Шинжилгээ хийх → Баталгаажуулах → Архивлах
    """
    # 1. Нэвтрэх
    auth.login()

    # 2. Дээж үүсгэх
    response = client.post('/create_sample', data={
        'sample_code': 'LIFECYCLE-001',
        'client_name': 'Lifecycle Test',
        'sample_type': 'Нүүрс',
        'weight': 2000,
        'analyses_to_perform': json.dumps(['mt']),
        'received_date': '2025-01-15 10:00'
    }, follow_redirects=True)
    assert response.status_code == 200

    sample = Sample.query.filter_by(sample_code='LIFECYCLE-001').first()
    assert sample is not None

    # 3. Шинжилгээний үр дүн бүртгэх (API ашиглах)
    response = client.post('/api/save_results', json={
        'sample_id': sample.id,
        'analysis_code': 'mt',
        'final_result': 25.5,
        'status': 'pending_review'
    })
    assert response.status_code == 200

    # 4. Үр дүн баталгаажуулах
    result = AnalysisResult.query.filter_by(
        sample_id=sample.id,
        analysis_code='mt'
    ).first()
    assert result is not None

    response = client.put(f'/api/update_result_status/{result.id}/approved')
    assert response.status_code == 200

    # 5. Дээж архивлах
    response = client.post('/api/sample_summary', data={
        'action': 'archive',
        'sample_ids': str(sample.id)
    }, follow_redirects=True)
    assert response.status_code == 200

    db.session.refresh(sample)
    assert sample.status == 'archived'


@pytest.mark.integration
def test_bulk_sample_operations(client, auth):
    """Олон дээжийг нэг дор ажиллуулах"""
    # 1. Нэвтрэх
    auth.login()

    # 2. Олон дээж үүсгэх
    sample_ids = []
    for i in range(5):
        response = client.post('/create_sample', data={
            'sample_code': f'BULK-{i:03d}',
            'client_name': f'Bulk Client {i}',
            'sample_type': 'Нүүрс',
            'weight': 2000 + i * 100,
            'analyses_to_perform': json.dumps(['mt']),
            'received_date': '2025-01-15 10:00'
        }, follow_redirects=True)
        assert response.status_code == 200

        sample = Sample.query.filter_by(sample_code=f'BULK-{i:03d}').first()
        sample_ids.append(sample.id)

    # 3. Бүх дээжийг архивлах
    response = client.post('/api/sample_summary', data={
        'action': 'archive',
        'sample_ids': ','.join(map(str, sample_ids))
    }, follow_redirects=True)
    assert response.status_code == 200

    # 4. Бүх дээж архивлагдсан эсэхийг шалгах
    for sid in sample_ids:
        sample = Sample.query.get(sid)
        assert sample.status == 'archived'
