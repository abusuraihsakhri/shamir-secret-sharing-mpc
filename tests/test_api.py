"""HTTP smoke tests for both retained API entry points."""
import os

from fastapi.testclient import TestClient


def test_enterprise_audit_api(monkeypatch):
    monkeypatch.setenv("AUDIT_SECRET_KEY", "test-only-hmac-key-0123456789abcdef")
    from agents.api import app
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    response = client.post("/api/audit", json={
        "task_id": "API-001", "target_identifier": "TARGET-001",
        "primary_metric": 3.0, "secondary_metric": 2.0,
        "status_descriptor": "NOMINAL"
    })
    assert response.status_code == 200, response.text
    assert response.json()["task_id"] == "API-001"
    rejected = client.post("/api/audit", json={
        "task_id": "API-BAD", "target_identifier": "TARGET-002",
        "primary_metric": 3.0, "attributes": {"contact": "test@example.org"}
    })
    assert rejected.status_code == 422
    log = client.get("/api/audit/logs")
    assert log.status_code == 200
    assert log.json()["verified"] is True


def test_legacy_api_health_and_audit():
    from shamir_mpc_agent.server import create_app
    app = create_app()
    assert app is not None
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    response = client.post("/api/audit", json={
        "task_id": "LEGACY-001", "target_identifier": "DEMO",
        "primary_metric": 10.0, "secondary_metric": 1.0,
        "status_descriptor": "NOMINAL"
    })
    assert response.status_code == 200, response.text
    assert response.json()["overall_status"] == "NOMINAL_OPTIMAL"
