from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_health_endpoint_public():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_protected_route_rejects_missing_secret():
    response = client.post(
        "/rag/query",
        json={
            "question": "What are ADA screening criteria?",
            "conversation_history": [],
            "request_id": "test-req",
        },
    )
    assert response.status_code == 401
    assert "Missing X-Internal-Secret header" in response.json()["detail"]


def test_protected_route_rejects_invalid_secret():
    response = client.post(
        "/rag/query",
        headers={"X-Internal-Secret": "invalid_secret_key"},
        json={
            "question": "What are ADA screening criteria?",
            "conversation_history": [],
            "request_id": "test-req",
        },
    )
    assert response.status_code == 401
    assert "Invalid internal secret" in response.json()["detail"]
