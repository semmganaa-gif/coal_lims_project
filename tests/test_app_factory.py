def test_app_created(app):
    assert app is not None
    assert app.config["TESTING"] is True


def test_index_accessible(client):
    resp = client.get("/")
    assert resp.status_code in (200, 302)
