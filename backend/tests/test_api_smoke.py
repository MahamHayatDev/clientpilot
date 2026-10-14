from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_all_phase_routes_are_registered():
    paths = set(app.openapi()["paths"].keys())

    expected = [
        "/research/{company_id}",
        "/score/{company_id}",
        "/draft/{company_id}",
        "/pipeline/{company_id}",
        "/pipeline-batch",
        "/companies",
        "/drafts",
        "/stats",
        "/outbox",
    ]

    for path in expected:
        assert path in paths, f"missing route: {path}"
