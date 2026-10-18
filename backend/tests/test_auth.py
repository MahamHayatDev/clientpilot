from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_stays_public():
    assert client.get("/health").status_code == 200


def test_missing_key_is_rejected():
    assert client.get("/stats").status_code == 401


def test_wrong_key_is_rejected():
    response = client.get("/stats", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401