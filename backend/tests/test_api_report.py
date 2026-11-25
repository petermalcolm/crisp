import json
import subprocess

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.autosave import autosave_service


def _commit_all(repo):
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "data"], cwd=repo, check=True)


@pytest.fixture
def repo(bare_git_repo, monkeypatch):
    """Data on main: a roof due 2027 (with an internal note), a gutter that has
    an actual with a comment, an anchored 2026 balance."""
    (bare_git_repo / "components.csv").write_text(
        "id,name,estimated_cost,initial_year,expected_life_years,category_code,notes\n"
        "roof,Roof,100000,2027,20,CH,INTERNAL: board argued about this\n"
        "gutter,Gutter,1000,2026,10,IN,\n"
    )
    (bare_git_repo / "year_parameters.csv").write_text(
        "year,num_contributors,inflation_rate,interest_rate,"
        "yoy_contribution_change_pct,total_annual_contribution,"
        "current_reserve_balance,notes\n"
        "2026,,0.0,0.0,,40000,20000,\n"
    )
    (bare_git_repo / "actual_costs.csv").write_text(
        "component_id,year,cost,comment\ngutter,2026,950,INTERNAL: plumber cheated us\n"
    )
    _commit_all(bare_git_repo)
    monkeypatch.setattr(settings, "data_repo_path", bare_git_repo)
    monkeypatch.setattr(autosave_service, "notify_change", lambda: None)
    return bare_git_repo


@pytest.fixture
def client(repo):
    return TestClient(app)


def test_report_projection_summary_and_schedule(client):
    body = client.get(
        "/api/report", params={"start_year": 2026, "end_year": 2028}
    ).json()

    years = {y["year"]: y for y in body["projection"]}
    assert years[2026]["start_balance"] == 20_000.0
    assert years[2026]["costs"] == 950.0  # the gutter actual replaces its estimate
    assert years[2026]["end_balance"] == pytest.approx(20_000 + 40_000 - 950)
    assert years[2027]["start_balance"] == pytest.approx(59_050.0)
    assert years[2027]["end_balance"] == pytest.approx(59_050 + 40_000 - 100_000)
    assert years[2028]["start_balance"] == pytest.approx(-950.0)

    summary = body["summary"]
    assert summary["balance_min"] == {"value": pytest.approx(-950.0), "year": 2028}
    assert summary["balance_max"]["year"] == 2027
    assert summary["contribution_min"]["value"] == 40_000.0
    assert summary["first_shortfall_year"] == 2027
    assert any(w["code"] == "shortfall" for w in body["warnings"])

    schedule = {s["year"]: s for s in body["schedule"]}
    assert schedule[2026]["term"] == "near"
    assert schedule[2026]["items"][0]["is_actual"] is True
    assert schedule[2027]["items"][0]["component_name"] == "Roof"
    assert schedule[2027]["items"][0]["category_name"] == "Common House"
    assert 2028 not in schedule  # nothing scheduled

    assert body["meta"]["branch"] == "main"
    assert body["meta"]["is_draft"] is False
    assert body["meta"]["data_commit"]
    assert body["meta"]["cost_base_year"] == 2026


def test_report_never_exposes_internal_notes_or_comments(client):
    text = client.get("/api/report").text
    assert "INTERNAL" not in text


def test_report_inventory_and_completed(client):
    body = client.get(
        "/api/report", params={"start_year": 2026, "end_year": 2055}
    ).json()
    inventory = {i["component_name"]: i for i in body["inventory"]}
    assert inventory["Roof"]["next_year"] == 2027
    assert inventory["Roof"]["occurrences_in_window"] == 2  # 2027, 2047
    assert body["completed_projects"] == [
        {"year": 2026, "component_name": "Gutter", "category_name": "Infrastructure", "cost": 950.0}
    ]


def test_report_flags_a_forecast_branch_as_draft(repo):
    subprocess.run(["git", "checkout", "-qb", "scenario"], cwd=repo, check=True)
    body = TestClient(app).get("/api/report").json()
    assert body["meta"]["is_draft"] is True
    assert body["meta"]["branch"] == "scenario"
    assert any(w["code"] == "not_main" for w in body["warnings"])


def test_report_warns_about_uncommitted_changes(client, repo):
    (repo / "categories.csv").write_text("code,name\nCH,Common House\n")
    body = client.get("/api/report").json()
    assert any(w["code"] == "uncommitted" for w in body["warnings"])


def test_report_settings_roundtrip_stored_as_json_and_drive_the_report(client, repo):
    # main is read-only
    assert client.put("/api/report-settings", json={}).status_code == 403

    subprocess.run(["git", "checkout", "-qb", "edit"], cwd=repo, check=True)
    put = client.put(
        "/api/report-settings",
        json={
            "association_name": "Emerson Commons",
            "budget": {"year": 2026, "operating": 60_000.0, "reserves": 40_000.0},
            "window_start": 2026,
            "window_end": 2030,
        },
    )
    assert put.status_code == 200
    assert put.json()["association_name"] == "Emerson Commons"
    assert "Board of Directors" in put.json()["basis_statement"]  # default kept

    stored = json.loads((repo / "report_settings.json").read_text())
    assert stored["association_name"] == "Emerson Commons"
    assert stored["budget"] == {"year": 2026, "operating": 60_000.0, "reserves": 40_000.0}

    body = client.get("/api/report").json()
    assert (body["meta"]["window_start"], body["meta"]["window_end"]) == (2026, 2030)
    budget = body["at_a_glance"]["budget"]
    assert budget["total"] == 100_000.0
    assert budget["reserve_share"] == pytest.approx(0.40)
    codes = {w["code"] for w in body["warnings"]}
    assert "no_budget" not in codes
    assert "budget_mismatch" not in codes  # model contribution is 40,000 too


def test_report_warns_when_budget_disagrees_with_the_model(client, repo):
    subprocess.run(["git", "checkout", "-qb", "edit"], cwd=repo, check=True)
    client.put(
        "/api/report-settings",
        json={"budget": {"year": 2026, "operating": 60_000.0, "reserves": 45_000.0}},
    )
    codes = {w["code"] for w in client.get("/api/report").json()["warnings"]}
    assert "budget_mismatch" in codes


def test_report_survives_a_corrupt_settings_file(client, repo):
    (repo / "report_settings.json").write_text("{not json")
    body = client.get("/api/report").json()
    assert any(w["code"] == "bad_settings" for w in body["warnings"])
    assert body["settings"]["association_name"] == ""
