import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.autosave import autosave_service


@pytest.fixture
def client(git_data_repo, monkeypatch):
    monkeypatch.setattr(settings, "data_repo_path", git_data_repo)
    monkeypatch.setattr(autosave_service, "notify_change", lambda: None)
    return TestClient(app)


def test_list_categories_returns_seeded_lookup(client):
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    codes = {c["code"] for c in resp.json()}
    assert codes == {"CH", "IN", "OS", "OB", "PO"}


def test_create_component_with_valid_category(client):
    resp = client.post(
        "/api/components",
        json={
            "name": "Clubhouse Roof",
            "estimated_cost": 50000,
            "initial_year": 2026,
            "expected_life_years": 20,
            "category_code": "CH",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["category_code"] == "CH"


def test_create_component_with_unknown_category_400s(client):
    resp = client.post(
        "/api/components",
        json={
            "name": "Mystery Item",
            "estimated_cost": 1000,
            "initial_year": 2026,
            "expected_life_years": 5,
            "category_code": "ZZ",
        },
    )
    assert resp.status_code == 400


def test_create_component_without_category_still_allowed(client):
    resp = client.post(
        "/api/components",
        json={
            "name": "Uncategorized Thing",
            "estimated_cost": 1000,
            "initial_year": 2026,
            "expected_life_years": 5,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["category_code"] is None


def test_update_component_with_unknown_category_400s(client):
    create_resp = client.post(
        "/api/components",
        json={
            "name": "Pool Pump",
            "estimated_cost": 3000,
            "initial_year": 2026,
            "expected_life_years": 8,
            "category_code": "PO",
        },
    )
    component_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/api/components/{component_id}",
        json={
            "name": "Pool Pump",
            "estimated_cost": 3000,
            "initial_year": 2026,
            "expected_life_years": 8,
            "category_code": "not-a-real-code",
        },
    )
    assert update_resp.status_code == 400
