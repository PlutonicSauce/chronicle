from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings


def client() -> TestClient:
    return TestClient(create_app(Settings(database_url=None, use_bedrock=False)))


def test_dashboard_exposes_seeded_engineering_memory() -> None:
    response = client().get("/api/v1/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "demo"
    assert payload["stats"]["total_memories"] >= 10
    assert payload["featured_memories"][0]["importance"] >= 0.9


def test_hybrid_search_recalls_authentication_decision() -> None:
    response = client().get("/api/v1/memories", params={"q": "Why did authentication change?", "mode": "hybrid"})
    assert response.status_code == 200
    titles = [result["title"] for result in response.json()["results"]]
    assert any("session validation" in title.lower() for title in titles)


def test_memory_detail_includes_relationships() -> None:
    memory_id = "019f827f-0001-7000-8000-000000000001"
    response = client().get(f"/api/v1/memories/{memory_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["relationships"]
    assert payload["related_memories"]


def test_memory_can_be_captured() -> None:
    response = client().post(
        "/api/v1/memories",
        json={
            "title": "Documented retry policy decision",
            "summary": "Retries now use a bounded exponential policy to protect downstream services.",
            "source_kind": "architecture-decision",
            "occurred_at": datetime.now(UTC).isoformat(),
            "tags": ["retries", "resilience"],
            "confidence": 0.91,
            "importance": 0.79,
            "created_by": "test-agent",
            "repository": "acme/atlas",
        },
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Documented retry policy decision"


def test_loopback_frontend_is_allowed_by_cors() -> None:
    response = client().get(
        "/api/v1/memories",
        headers={"Origin": "http://127.0.0.1:3000"},
    )
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
