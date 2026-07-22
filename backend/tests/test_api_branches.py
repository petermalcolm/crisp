import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.autosave import autosave_service


@pytest.fixture
def client_on_main(bare_git_repo, monkeypatch):
    """Data repo still on main — the state right after opening the app."""
    monkeypatch.setattr(settings, "data_repo_path", bare_git_repo)
    monkeypatch.setattr(autosave_service, "notify_change", lambda: None)
    return TestClient(app), bare_git_repo


@pytest.fixture
def client(git_data_repo, monkeypatch):
    """Data repo already on a forecast branch — for tests that don't care
    about the main/forecast distinction itself."""
    monkeypatch.setattr(settings, "data_repo_path", git_data_repo)
    monkeypatch.setattr(autosave_service, "notify_change", lambda: None)
    return TestClient(app)


def _new_component_payload(name="Roof"):
    return {
        "name": name,
        "estimated_cost": 100000,
        "initial_year": 2026,
        "expected_life_years": 15,
    }


def test_editing_disallowed_on_main(client_on_main):
    client, _ = client_on_main
    resp = client.post("/api/components", json=_new_component_payload())
    assert resp.status_code == 403


def test_branch_list_starts_with_main_only(client_on_main):
    client, _ = client_on_main
    resp = client.get("/api/branches")
    assert resp.status_code == 200
    assert resp.json() == {"current": "main", "branches": ["main"]}


def test_create_branch_switches_current_and_allows_editing(client_on_main):
    client, _ = client_on_main
    create_resp = client.post("/api/branches", json={"name": "forecast-a"})
    assert create_resp.status_code == 201
    assert create_resp.json()["current"] == "forecast-a"
    assert set(create_resp.json()["branches"]) == {"main", "forecast-a"}

    write_resp = client.post("/api/components", json=_new_component_payload())
    assert write_resp.status_code == 201


def test_create_duplicate_branch_name_conflicts(client_on_main):
    client, _ = client_on_main
    client.post("/api/branches", json={"name": "forecast-a"})
    client.post("/api/branches/checkout", json={"name": "main"})
    resp = client.post("/api/branches", json={"name": "forecast-a"})
    assert resp.status_code == 409


def test_checkout_switches_branch(client_on_main):
    client, _ = client_on_main
    client.post("/api/branches", json={"name": "forecast-a"})
    resp = client.post("/api/branches/checkout", json={"name": "main"})
    assert resp.status_code == 200
    assert resp.json()["current"] == "main"

    # editing is disallowed again now that we're back on main
    write_resp = client.post("/api/components", json=_new_component_payload())
    assert write_resp.status_code == 403


def test_checkout_missing_branch_404s(client_on_main):
    client, _ = client_on_main
    resp = client.post("/api/branches/checkout", json={"name": "does-not-exist"})
    assert resp.status_code == 404


def test_merge_forecast_branch_lands_on_main(client_on_main):
    client, repo = client_on_main
    client.post("/api/branches", json={"name": "forecast-a"})
    create_resp = client.post("/api/components", json=_new_component_payload("Roof"))
    assert create_resp.status_code == 201

    merge_resp = client.post("/api/branches/forecast-a/merge", json={})
    assert merge_resp.status_code == 200
    assert merge_resp.json()["current"] == "main"

    # back on main, the merged component is now visible (and read-only)
    list_resp = client.get("/api/components")
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["name"] == "Roof"


def test_merge_missing_branch_404s(client_on_main):
    client, _ = client_on_main
    resp = client.post("/api/branches/does-not-exist/merge", json={})
    assert resp.status_code == 404


def test_merge_conflict_returns_409_and_leaves_repo_usable(client_on_main):
    client, repo = client_on_main
    client.post("/api/branches", json={"name": "forecast-a"})
    client.post("/api/components", json=_new_component_payload("Forecast Roof"))

    client.post("/api/branches/checkout", json={"name": "main"})
    client.post("/api/branches", json={"name": "forecast-b"})
    client.post("/api/components", json=_new_component_payload("Forecast B Roof"))
    client.post("/api/branches/checkout", json={"name": "main"})
    client.post("/api/branches/forecast-b/merge", json={})  # succeeds, main now has one component

    # merging forecast-a (branched off the ORIGINAL empty main) conflicts
    # with the components.csv main now has after the first merge
    merge_resp = client.post("/api/branches/forecast-a/merge", json={})
    assert merge_resp.status_code == 409

    # repo still usable afterwards
    resp = client.get("/api/branches")
    assert resp.status_code == 200
    assert resp.json()["current"] == "main"
