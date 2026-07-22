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


def test_patch_sets_explicit_value_and_get_carries_it_forward(client):
    patch_resp = client.patch(
        "/api/parameters/2026", json={"inflation_rate": 0.025, "num_contributors": 50}
    )
    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["inflation_rate"] == {
        "value": 0.025,
        "is_explicit": True,
        "source_year": 2026,
    }
    assert body["num_contributors"] == 50

    list_resp = client.get(
        "/api/parameters", params={"start_year": 2026, "end_year": 2028}
    )
    rows = {row["year"]: row for row in list_resp.json()}
    assert rows[2027]["inflation_rate"] == {
        "value": 0.025,
        "is_explicit": False,
        "source_year": 2026,
    }
    assert rows[2027]["num_contributors"] is None  # not carried forward


def test_patch_override_cascades_new_anchor(client):
    client.patch("/api/parameters/2026", json={"inflation_rate": 0.025})
    client.patch("/api/parameters/2028", json={"inflation_rate": 0.03})

    resp = client.get("/api/parameters", params={"start_year": 2026, "end_year": 2029})
    rows = {row["year"]: row for row in resp.json()}
    assert rows[2027]["inflation_rate"]["value"] == 0.025
    assert rows[2028]["inflation_rate"] == {
        "value": 0.03,
        "is_explicit": True,
        "source_year": 2028,
    }
    assert rows[2029]["inflation_rate"]["value"] == 0.03
    assert rows[2029]["inflation_rate"]["source_year"] == 2028


def test_patch_merges_fields_without_clobbering_others(client):
    client.patch("/api/parameters/2026", json={"inflation_rate": 0.025})
    client.patch("/api/parameters/2026", json={"interest_rate": 0.01})

    resp = client.get("/api/parameters", params={"start_year": 2026, "end_year": 2026})
    row = resp.json()[0]
    assert row["inflation_rate"]["value"] == 0.025
    assert row["interest_rate"]["value"] == 0.01


def test_patch_null_clears_an_override(client):
    client.patch("/api/parameters/2026", json={"inflation_rate": 0.025})
    client.patch("/api/parameters/2026", json={"inflation_rate": None})

    resp = client.get("/api/parameters", params={"start_year": 2026, "end_year": 2026})
    row = resp.json()[0]
    assert row["inflation_rate"] == {"value": None, "is_explicit": False, "source_year": None}


def test_contribution_series_compounds_with_yoy(client):
    client.patch(
        "/api/parameters/2026",
        json={"total_annual_contribution": 50_000.0, "yoy_contribution_change_pct": 0.02},
    )
    resp = client.get("/api/parameters", params={"start_year": 2026, "end_year": 2027})
    rows = {row["year"]: row for row in resp.json()}
    assert round(rows[2027]["total_annual_contribution"]["value"], 2) == 51_000.0
    assert rows[2027]["total_annual_contribution"]["is_explicit"] is False


def test_surprise_contribution_crud(client):
    create_resp = client.post(
        "/api/surprise-contributions",
        json={"year": 2028, "amount": 5000, "description": "insurance payout"},
    )
    assert create_resp.status_code == 201
    contribution_id = create_resp.json()["id"]

    list_resp = client.get("/api/surprise-contributions")
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["description"] == "insurance payout"

    delete_resp = client.delete(f"/api/surprise-contributions/{contribution_id}")
    assert delete_resp.status_code == 204
    assert client.get("/api/surprise-contributions").json() == []


def test_delete_missing_surprise_contribution_404s(client):
    resp = client.delete("/api/surprise-contributions/does-not-exist")
    assert resp.status_code == 404
