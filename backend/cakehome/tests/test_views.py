
import pytest


@pytest.mark.django_db
def test_health_returns_ok(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.django_db
def test_cakes_api_returns_list(client):
    response = client.get("/api/cakes/")
    assert response.status_code == 200
    assert "results" in response.json()