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
        "2026,,,0.02,,10000,10000,\n"
        "2027,,,,,5000,,\n"
    )
    (tmp_path / "surprise_contributions.csv").write_text("id,year,amount,description\n")
    monkeypatch.setattr(settings, "data_repo_path", tmp_path)
    return TestClient(app)


def test_ffb_projection_anchors_and_rolls_forward(client):
    resp = client.get(
        "/api/projections/ffb", params={"start_year": 2025, "end_year": 2027}
    )
    assert resp.status_code == 200
    rows = {row["year"]: row for row in resp.json()}

    assert rows[2025]["actual_balance"] is None  # before the anchor year
    assert rows[2026]["actual_balance"] == 10_000.0
    assert rows[2026]["ffb_target"] == 0.0  # age 0 at replacement year
    assert rows[2026]["total_cost"] == 100_000.0  # roof replaced this year
    assert rows[2026]["percent_funded"] is None  # target is 0, div-by-zero guarded

    # 2027: balance = 10000*1.02 + 5000 (contribution, no cost that year) = 15200
    assert round(rows[2027]["actual_balance"], 2) == 15_200.0
    assert rows[2027]["total_cost"] == 0.0
    assert rows[2027]["is_estimate"] is True


def test_ffb_projection_no_balance_when_never_anchored(client, tmp_path):
    (tmp_path / "year_parameters.csv").write_text(
        "year,num_contributors,inflation_rate,interest_rate,"
        "yoy_contribution_change_pct,total_annual_contribution,"
        "current_reserve_balance,notes\n"
    )
    resp = client.get(
        "/api/projections/ffb", params={"start_year": 2026, "end_year": 2027}
    )
    rows = resp.json()
    assert all(row["actual_balance"] is None for row in rows)
