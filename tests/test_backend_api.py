"""
Integration tests for MetaOracle FastAPI REST endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import Base, engine, init_db


@pytest.fixture(scope="module")
def client():
    """Initializes the database and returns a FastAPI TestClient."""
    init_db()
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    """Verifies that the /api/health endpoint returns 200 OK."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


def test_get_presets(client):
    """Verifies retrieval of algorithm presets."""
    response = client.get("/api/tests/presets")
    assert response.status_code == 200
    presets = response.json()
    assert len(presets) > 0
    assert any(p["category"] == "Sorting" for p in presets)


def test_run_metamorphic_tests_api(client):
    """Verifies executing a test run through the API endpoint."""
    payload = {
        "category": "Sorting",
        "variant": "Bug: Reverse Input Bias",
        "input_type": "list",
        "selected_relation_ids": ["MR_REVERSE_INVARIANCE", "MR_PERMUTATION_INVARIANCE"],
        "test_budget": 10,
        "seed": 42,
    }
    response = client.post("/api/tests/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] in ["PASSED", "VIOLATED"]
    assert data["total_tests"] > 0
    assert "relation_summary" in data


def test_test_history_and_detail(client):
    """Verifies retrieving test history and run details."""
    response = client.get("/api/tests/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) > 0

    latest_id = history[0]["id"]
    detail_res = client.get(f"/api/tests/{latest_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == latest_id


def test_relations_catalog_and_suggest(client):
    """Verifies relations catalog list and AST suggestion."""
    # List relations
    response = client.get("/api/relations")
    assert response.status_code == 200
    relations = response.json()
    assert len(relations) >= 10

    # Auto-suggest relations
    suggest_payload = {
        "category": "Sorting",
        "variant": "Correct Reference",
    }
    sug_res = client.post("/api/relations/suggest", json=suggest_payload)
    assert sug_res.status_code == 200
    sug_data = sug_res.json()
    assert len(sug_data["suggestions"]) > 0


def test_snippets_crud(client):
    """Verifies creating and listing code snippets."""
    snippet_payload = {
        "title": "API Test Snippet",
        "category": "Sorting",
        "code": "def sample(x): return sorted(x)",
        "input_type": "list",
    }
    create_res = client.post("/api/snippets", json=snippet_payload)
    assert create_res.status_code == 200
    snippet = create_res.json()
    assert snippet["title"] == "API Test Snippet"

    list_res = client.get("/api/snippets")
    assert list_res.status_code == 200
    snippets = list_res.json()
    assert any(s["title"] == "API Test Snippet" for s in snippets)


def test_dashboard_stats(client):
    """Verifies dashboard metrics endpoint."""
    response = client.get("/api/stats/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_runs" in data
    assert "total_tests_executed" in data
    assert "overall_pass_rate" in data
