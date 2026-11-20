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
    assert rows[2025]["ffb_target"] == pytest.approx(100_000 * 14 / 15)
    assert rows[2026]["actual_balance"] == 10_000.0  # Jan 1 2026
    assert rows[2026]["ffb_target"] == 100_000.0  # roof due 2026: fully aged
    assert rows[2026]["total_cost"] == 100_000.0  # roof replaced this year
    assert rows[2026]["percent_funded"] == pytest.approx(0.10)

    # Jan 1 2027 = 10000*1.02 (2026 interest) + 10000 (2026 contribution) - 100000
    assert rows[2027]["actual_balance"] == pytest.approx(-79_800.0)
    assert rows[2027]["total_cost"] == 0.0
    assert rows[2027]["is_estimate"] is True


def test_ffb_balance_carries_into_a_window_after_the_anchor(client):
    resp = client.get(
        "/api/projections/ffb", params={"start_year": 2028, "end_year": 2028}
    )
    rows = {row["year"]: row for row in resp.json()}
    # Jan 1 2028 = (-79800)*1.02 (no 2027 interest set: sticky .02) + 5000
    assert rows[2028]["actual_balance"] == pytest.approx(-79_800 * 1.02 + 5_000)


def test_cost_base_year_setting_decouples_inflation_from_the_anchor(client, tmp_path):
    (tmp_path / "year_parameters.csv").write_text(
        "year,num_contributors,inflation_rate,interest_rate,"
        "yoy_contribution_change_pct,total_annual_contribution,"
        "current_reserve_balance,notes\n"
        "2024,,0.03,0.0,,0,,\n"
        "2026,,,,,0,10000,\n"
    )
    params = {"start_year": 2026, "end_year": 2026}

    # No setting: costs are in the anchor year's (2026) dollars, no inflation.
    rows = client.get("/api/projections/ffb", params=params).json()
    assert rows[0]["ffb_target"] == pytest.approx(100_000.0)

    # Explicit setting: estimates are 2024 dollars, so 2025 and 2026 inflation
    # (carried forward from the 2024 row, outside the requested window) applies.
    (tmp_path / "study_settings.csv").write_text("key,value\ncost_base_year,2024\n")
    rows = client.get("/api/projections/ffb", params=params).json()
    assert rows[0]["ffb_target"] == pytest.approx(100_000 * 1.03**2)
    assert rows[0]["actual_balance"] == 10_000.0


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
