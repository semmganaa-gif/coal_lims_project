import pytest


@pytest.mark.smoke
def test_check_ready_samples(client):
    resp = client.get("/api/check_ready_samples")
    # Хамгийн багадаа сервер унахгүй, 2xx/3xx/401/403 хариу авах ёстой
    assert resp.status_code in (200, 302, 401, 403)


@pytest.mark.smoke
def test_eligible_samples_mt(client):
    resp = client.get("/api/eligible_samples/MT")
    # Auth шаардвал 302/401 болж болно, гэхдээ 500 биш
    assert resp.status_code in (200, 302, 401, 403)


@pytest.mark.smoke
def test_save_results_empty_payload(client):
    resp = client.post("/api/analysis/save_results", json=[])
    # Хоосон payload-д 400/401/403/422, эсвэл route хаалттай бол 404 байж болно; 500 биш
    assert resp.status_code in (200, 400, 401, 403, 404, 422)
