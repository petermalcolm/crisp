import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    (tmp_path / "components.csv").write_text(
        "id,name,estimated_cost,initial_year,expected_life_years,notes\n"
        "roof,Roof,100000,2026,15,\n"
    )
    (tmp_path / "year_parameters.csv").write_text(
        "year,num_contributors,inflation_rate,interest_rate,"
        "yoy_contribution_change_pct,total_annual_contribution,"
        "current_reserve_balance,notes\n"
        "2027,,0.05,,,,, \n"
    )
    (tmp_path / "surprise_contributions.csv").write_text("id,year,amount,description\n")
    monkeypatch.setattr(settings, "data_repo_path", tmp_path)
    return TestClient(app)


def test_costs_projection_groups_by_year_and_applies_inflation(client):
    resp = client.get("/api/projections/costs", params={"start_year": 2026, "end_year": 2027})
    assert resp.status_code == 200
    rows = {row["year"]: row for row in resp.json()}

    assert rows[2026]["is_estimate"] is False
    assert rows[2026]["total"] == 100_000.0
    assert rows[2026]["line_items"][0]["component_name"] == "Roof"

    assert rows[2027]["is_estimate"] is True
    assert rows[2027]["total"] == 0.0  # roof doesn't recur until 2041
    assert rows[2027]["line_items"] == []


def test_costs_projection_defaults_horizon_around_base_year(client):
    resp = client.get("/api/projections/costs")
    assert resp.status_code == 200
    years = [row["year"] for row in resp.json()]
    assert years == list(range(min(years), max(years) + 1))
    assert 2026 in years
