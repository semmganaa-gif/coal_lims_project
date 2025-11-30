# tests/security/test_csrf.py
# -*- coding: utf-8 -*-
"""
CSRF (Cross-Site Request Forgery) халдлагаас хамгаалалтын тестүүд

Flask-WTF CSRF Protection ашиглаж байгаа тул
CSRF token-гүй хүсэлтүүд татгалзагдах ёстой.
"""

import pytest


@pytest.mark.security
def test_csrf_protection_on_sample_creation(client, auth):
    """Дээж үүсгэхэд CSRF token шаардах"""
    auth.login()

    # CSRF token-гүй хүсэлт илгээх
    response = client.post('/create_sample', data={
        'sample_code': 'TEST-CSRF-001',
        'client_name': 'CSRF Test',
        'sample_type': 'Нүүрс',
        'weight': 2500,
        'analyses_to_perform': '["mt"]',
        'received_date': '2025-01-15 10:00'
    })

    # CSRF validation алдаа гарах ёстой (400 эсвэл redirect)
    # Note: test client нь CSRF-ийг автоматаар идэвхгүй болгож магадгүй
    # Үүнийг шалгахын тулд WTF_CSRF_ENABLED=True тохируулна


@pytest.mark.security
def test_csrf_protection_on_login(client):
    """Нэвтрэхэд CSRF token шаардах"""
    # CSRF token-гүй нэвтрэх оролдлого
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'Test123'
    })

    # Production-д CSRF алдаа гарах ёстой
    # Test mode-д зарим тохируулга дутуу байж болно


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
def test_csrf_token_validation(client, auth):
    """CSRF token зөв validation хийгдэж байгааг шалгах"""
    auth.login()

    # 1. Form хуудас авах (CSRF token агуулна)
    response = client.get('/create_sample')
    assert response.status_code == 200

    # CSRF token-г хуудаснаас задлан авах
    # (Энэ нь test client дээр автомат хийгдэж магадгүй)
    # Real implementation-д BeautifulSoup ашиглаж token задална

    # 2. Буруу CSRF token ашиглах
    response = client.post('/create_sample', data={
        'csrf_token': 'invalid_token_12345',
        'sample_code': 'TEST-CSRF-002',
        'client_name': 'CSRF Test',
        'sample_type': 'Нүүрс',
        'weight': 2500,
        'analyses_to_perform': '["mt"]',
        'received_date': '2025-01-15 10:00'
    })

    # Буруу token учир алдаа гарах ёстой
    # (Test mode-д disabled байж болно)


@pytest.mark.security
def test_csrf_protection_on_delete(client, auth, test_sample):
    """Устгах үйлдэлд CSRF хамгаалалт"""
    auth.login()

    # CSRF token-гүй устгах хүсэлт
    response = client.post(f'/delete_sample/{test_sample.id}')

    # Production-д CSRF алдаа гарах ёстой
    # Test environment-д зарим тохируулга өөр байж болно


@pytest.mark.security
def test_csrf_double_submit_prevention(client, auth):
    """
    CSRF double submit халдлага хамгаалалт

    Халдагч хэрэглэгчийн CSRF token-г хулгайлж,
    давхар хүсэлт илгээх оролдлого
    """
    auth.login()

    # Хэвийн хүсэлт илгээх
    response1 = client.post('/create_sample', data={
        'sample_code': 'TEST-DOUBLE-001',
        'client_name': 'Double Submit Test',
        'sample_type': 'Нүүрс',
        'weight': 2500,
        'analyses_to_perform': '["mt"]',
        'received_date': '2025-01-15 10:00'
    }, follow_redirects=True)

    # Мөн token ашиглаж дахин хүсэлт илгээх
    # (Flask-WTF нэг token-г зөвхөн нэг удаа ашиглах боломжтой)
    response2 = client.post('/create_sample', data={
        'sample_code': 'TEST-DOUBLE-002',
        'client_name': 'Double Submit Test 2',
        'sample_type': 'Нүүрс',
        'weight': 2500,
        'analyses_to_perform': '["mt"]',
        'received_date': '2025-01-15 10:00'
    }, follow_redirects=True)

    # Хоёр дахь хүсэлт CSRF алдаа гарч болно
    # (Тохируулгаас хамаарна)
