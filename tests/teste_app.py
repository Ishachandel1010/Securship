"""
Unit tests for the SecureShip app.

These run inside the Jenkins pipeline's "Test" stage. If any of these
fail, the pipeline stops before an image is ever built — that's the
whole point of putting tests early in the pipeline.
"""

import pytest
from app.app import app, URL_STORE, make_short_code


@pytest.fixture
def client():
    """Flask's test client — lets us call routes without a real server."""
    app.config["TESTING"] = True
    URL_STORE.clear()  # start each test with a clean store
    with app.test_client() as client:
        yield client


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_shorten_valid_url(client):
    response = client.post("/shorten", json={"url": "https://anthropic.com"})
    assert response.status_code == 201
    body = response.get_json()
    assert "short_code" in body
    assert body["original_url"] == "https://anthropic.com"


def test_shorten_rejects_invalid_url(client):
    response = client.post("/shorten", json={"url": "not-a-url"})
    assert response.status_code == 400


def test_shorten_rejects_missing_url(client):
    response = client.post("/shorten", json={})
    assert response.status_code == 400


def test_resolve_redirects(client):
    client.post("/shorten", json={"url": "https://anthropic.com"})
    code = make_short_code("https://anthropic.com")
    response = client.get(f"/{code}")
    assert response.status_code == 302
    assert response.headers["Location"] == "https://anthropic.com"


def test_resolve_unknown_code_returns_404(client):
    response = client.get("/doesnotexist")
    assert response.status_code == 404


def test_same_url_gives_same_code(client):
    """The hash-based code generation should be deterministic."""
    r1 = client.post("/shorten", json={"url": "https://example.com"})
    URL_STORE.clear()
    r2 = client.post("/shorten", json={"url": "https://example.com"})
    assert r1.get_json()["short_code"] == r2.get_json()["short_code"]
