import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.autosave import autosave_service


@pytest.fixture
def client(git_data_repo, monkeypatch):
    monkeypatch.setattr(settings, "data_repo_path", git_data_repo)
    # Autosave uses a real background timer keyed off settings.data_repo_path
    # at fire time; suppress it here so a stray timer can never fire against
    # a different path after monkeypatch reverts post-test.
    monkeypatch.setattr(autosave_service, "notify_change", lambda: None)
    return TestClient(app)


def test_create_list_update_delete_component(client):
    create_resp = client.post(
        "/api/components",
        json={
            "name": "Roof",
            "estimated_cost": 100000,
            "initial_year": 2026,
            "expected_life_years": 15,
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["name"] == "Roof"
    component_id = created["id"]

    list_resp = client.get("/api/components")
    assert list_resp.status_code == 200
    assert [c["id"] for c in list_resp.json()] == [component_id]

    update_resp = client.put(
        f"/api/components/{component_id}",
        json={
            "name": "Roof (updated)",
            "estimated_cost": 110000,
            "initial_year": 2026,
            "expected_life_years": 15,
            "notes": "shingle upgrade",
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Roof (updated)"
    assert update_resp.json()["notes"] == "shingle upgrade"

    delete_resp = client.delete(f"/api/components/{component_id}")
    assert delete_resp.status_code == 204
    assert client.get("/api/components").json() == []


def test_update_missing_component_returns_404(client):
    resp = client.put(
        "/api/components/does-not-exist",
        json={
            "name": "Ghost",
            "estimated_cost": 1,
            "initial_year": 2026,
            "expected_life_years": 1,
        },
    )
    assert resp.status_code == 404


def test_invalid_payload_rejected(client):
    resp = client.post(
        "/api/components",
        json={
            "name": "Bad life",
            "estimated_cost": 100,
            "initial_year": 2026,
            "expected_life_years": 0,
        },
    )
    assert resp.status_code == 422
