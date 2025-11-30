# tests/security/test_sql_injection.py
# -*- coding: utf-8 -*-
"""
SQL Injection халдлагаас хамгаалалтын тестүүд

SQLAlchemy ORM + parameterized queries ашиглаж байгаа тул
SQL injection халдлага амжилттай бус байх ёстой.
"""

import pytest
from app.models import Sample, User


@pytest.mark.security
def test_sql_injection_in_sample_code(client, auth):
    """Sample code-д SQL injection оролдох"""
    auth.login()

    # SQL injection payload
    malicious_code = "TEST'; DROP TABLE sample; --"

    response = client.post('/create_sample', data={
        'sample_code': malicious_code,
        'client_name': 'Test Client',
        'sample_type': 'Нүүрс',
        'weight': 2500,
        'analyses_to_perform': '["mt"]',
        'received_date': '2025-01-15 10:00'
    }, follow_redirects=True)

    # 1. Хуудас ажиллах ёстой (алдаагүй)
    assert response.status_code in [200, 302]

    # 2. Sample table устаагүй байх ёстой
    samples = Sample.query.all()
    # Хэрэв table устсан бол энд алдаа гарна

    # 3. Malicious дээж үүссэн эсэхийг шалгах
    sample = Sample.query.filter_by(sample_code=malicious_code).first()
    # SQLAlchemy параметрлэх учир текст нь яг хадгалагдана
    if sample:
        assert sample.sample_code == malicious_code


@pytest.mark.security
def test_sql_injection_in_search(client, auth):
    """Хайлтын өгөгдөлд SQL injection оролдох"""
    auth.login()

    # Эхлээд хэвийн дээж үүсгэх
    client.post('/create_sample', data={
        'sample_code': 'NORMAL-001',
        'client_name': 'Normal Client',
        'sample_type': 'Нүүрс',
        'weight': 2500,
        'analyses_to_perform': '["mt"]',
        'received_date': '2025-01-15 10:00'
    }, follow_redirects=True)

    # SQL injection payload хайлтад оруулах
    malicious_search = "' OR '1'='1"

    response = client.get(f'/api/data?columns[2][search][value]={malicious_search}')

    # 1. Response амжилттай ирэх ёстой
    assert response.status_code == 200

    # 2. Бүх дээж буцаагаагүй байх ёстой (escape хийгдсэн учир)
    data = response.get_json()
    if data and 'data' in data:
        # Injection амжилтгүй болсон тул бүх дээжийг буцаахгүй
        # Зөвхөн literal "' OR '1'='1" агуулсан sample code-тай дээж л буцна
        assert len(data['data']) == 0 or len(data['data']) < Sample.query.count()


@pytest.mark.security
def test_sql_injection_in_username(client):
    """Username-д SQL injection оролдох"""
    # SQL injection payload
    malicious_username = "admin'; DROP TABLE user; --"
    malicious_password = "Test123"

    # Нэвтрэх оролдлого
    response = client.post('/login', data={
        'username': malicious_username,
        'password': malicious_password
    }, follow_redirects=True)

    # 1. Response амжилттай ирэх ёстой (алдаагүй)
    assert response.status_code == 200

    # 2. User table устаагүй байх ёстой
    users = User.query.all()
    # Хэрэв table устсан бол энд алдаа гарна

    # 3. Нэвтрэх амжилтгүй байх ёстой
    assert b'login' in response.data.lower() or b'password' in response.data.lower()


@pytest.mark.security
def test_sql_injection_in_filter(client, auth):
    """Sample summary filter-д SQL injection оролдох"""
    auth.login()

    malicious_filter = "' UNION SELECT * FROM user --"

    response = client.get(f'/api/sample_summary?filter_name={malicious_filter}')

    # 1. Response амжилттай ирэх ёстой
    assert response.status_code == 200

    # 2. User мэдээлэл гарч ирээгүй байх ёстой
    # (escape_like_pattern функц ашиглаж байгаа учир)
    assert b'password_hash' not in response.data.lower()


@pytest.mark.security
def test_sql_injection_in_api_endpoint(client, auth, test_sample):
    """API endpoint-д SQL injection оролдох"""
    auth.login()

    # Malicious analysis code
    malicious_code = "mt'; DELETE FROM sample WHERE id > 0; --"

    response = client.post('/api/save_results', json={
        'sample_id': test_sample.id,
        'analysis_code': malicious_code,
        'final_result': 25.5,
        'status': 'pending_review'
    })

    # 1. Response ирэх ёстой (алдаа эсвэл validation error)
    assert response.status_code in [200, 400, 422]

    # 2. Sample устаагүй байх ёстой
    sample = Sample.query.get(test_sample.id)
    assert sample is not None

    # 3. Бусад дээжүүд ч устаагүй байх ёстой
    samples_count = Sample.query.count()
    assert samples_count > 0


@pytest.mark.security
def test_sql_injection_prevention_in_orm(app):
    """
    SQLAlchemy ORM-ийн SQL injection хамгаалалтыг шалгах

    Direct SQL бус ORM methods ашиглаж байгаа тул
    автоматаар параметрлэгдэх ёстой.
    """
    with app.app_context():
        # Malicious input
        malicious_input = "TEST'; DROP TABLE sample; --"

        # ORM ашиглаж хайх
        result = Sample.query.filter_by(sample_code=malicious_input).first()

        # Хайлт амжилттай гүйцэтгэгдэх ёстой (алдаагүй)
        # Үр дүн буцахгүй (ийм sample_code байхгүй учир)
        assert result is None

        # Sample table устаагүй байх ёстой
        all_samples = Sample.query.all()
        # Алдаа гарахгүй
