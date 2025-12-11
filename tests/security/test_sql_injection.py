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
def test_sql_injection_in_username(client):
    """Username-д SQL injection оролдох"""
    # SQL injection payload
    malicious_username = "admin'; DROP TABLE user; --"
    malicious_password = "TestPass123"

    # Нэвтрэх оролдлого
    response = client.post('/login', data={
        'username': malicious_username,
        'password': malicious_password
    }, follow_redirects=True)

    # 1. Response амжилттай ирэх ёстой (алдаагүй)
    assert response.status_code == 200

    # 2. Нэвтрэх амжилтгүй байх ёстой (буруу username)
    html = response.get_data(as_text=True).lower()
    # Login хуудас дахин харагдах эсвэл алдааны мессеж
    assert 'login' in html or 'нэвтрэх' in html or 'password' in html


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

    # Response ирэх ёстой (алдаа эсвэл validation error эсвэл success)
    assert response.status_code in [200, 207, 400, 422]


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
        # Алдаа гарахгүй - query амжилттай


@pytest.mark.security
def test_sql_injection_in_search(client, auth):
    """Хайлтын өгөгдөлд SQL injection оролдох"""
    auth.login()

    # SQL injection payload хайлтад оруулах
    malicious_search = "' OR '1'='1"

    response = client.get(f'/api/data?columns[2][search][value]={malicious_search}')

    # Response амжилттай ирэх ёстой
    assert response.status_code == 200
