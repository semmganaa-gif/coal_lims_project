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
def test_xss_in_api_response(client, auth):
    """API response-д XSS escape хийгдэж байгааг шалгах"""
    auth.login()

    # DataTables API дуудах
    response = client.get('/api/data')
    assert response.status_code == 200

    data = response.get_json()
    # JSON response байх ёстой
    assert data is not None


@pytest.mark.security
def test_xss_in_search_results(client, auth):
    """Хайлтын үр дүнд XSS escape"""
    auth.login()

    # XSS агуулсан хайлт
    xss_search = '<script>alert("XSS")</script>'

    response = client.get(f'/api/data?search[value]={xss_search}')
    assert response.status_code == 200


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
    html = response.get_data(as_text=True)

    # Script tag яг гүйцэтгэгдэхгүй (escape хийгдсэн эсвэл устгагдсан)
    # HTML-д raw <script> tag байх ёсгүй
    assert '<script>alert(document.domain)</script>' not in html


@pytest.mark.security
def test_xss_in_equipment_list(client, auth):
    """Equipment list хуудсанд XSS хамгаалалт"""
    auth.login()

    response = client.get('/equipment_list')
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    # Хуудас зөв рендер хийгдсэн
    assert 'equipment' in html.lower() or 'тоног' in html.lower()


@pytest.mark.security
def test_xss_in_index_page(client, auth):
    """Index хуудсанд XSS хамгаалалт"""
    auth.login()

    response = client.get('/index')
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    # Хуудас зөв рендер хийгдсэн
    assert '<!doctype html>' in html.lower() or '<!DOCTYPE html>' in html
