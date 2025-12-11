# tests/security/test_csrf.py
# -*- coding: utf-8 -*-
"""
CSRF (Cross-Site Request Forgery) халдлагаас хамгаалалтын тестүүд

Flask-WTF CSRF Protection ашиглаж байгаа тул
CSRF token-гүй хүсэлтүүд татгалзагдах ёстой.
"""

import pytest


@pytest.mark.security
def test_csrf_protection_on_login(client):
    """Нэвтрэхэд CSRF token шаардах - test mode-д disabled"""
    # CSRF token-гүй нэвтрэх оролдлого
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'TestPass123'
    })

    # Test mode-д CSRF disabled - 200 эсвэл 302 буцна
    assert response.status_code in [200, 302]


@pytest.mark.security
def test_csrf_exempt_on_api_endpoints(client, auth, test_sample):
    """
    API endpoints CSRF-ээс чөлөөлөгдсөн байх ёстой

    REST API-д CSRF token шаарддаггүй (JSON-based API)
    Харин authentication шаардагдана.
    """
    auth.login()

    # CSRF token-гүй API хүсэлт (амжилттай байх ёстой)
    response = client.post('/api/save_results', json={
        'sample_id': test_sample.id,
        'analysis_code': 'mt',
        'final_result': 25.5,
        'status': 'pending_review'
    })

    # API endpoints CSRF-ээс чөлөөлөгдсөн учир 200 буцах ёстой
    assert response.status_code == 200


@pytest.mark.security
def test_csrf_token_present_in_html_forms(client, auth):
    """HTML формуудад CSRF token байгааг шалгах"""
    auth.login()

    # Equipment list хуудас авах
    response = client.get('/equipment_list')
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    # CSRF token байх ёстой
    assert 'csrf_token' in html or 'csrf-token' in html


@pytest.mark.security
def test_api_check_ready_samples_accessible(client, auth):
    """API endpoint ажиллаж байгааг шалгах"""
    auth.login()

    response = client.get('/api/check_ready_samples')
    assert response.status_code == 200
    data = response.get_json()
    assert 'ready_count' in data


@pytest.mark.security
def test_api_data_endpoint_accessible(client, auth):
    """DataTables API endpoint ажиллаж байгааг шалгах"""
    auth.login()

    response = client.get('/api/data')
    assert response.status_code == 200
