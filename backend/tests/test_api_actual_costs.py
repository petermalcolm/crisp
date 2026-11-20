import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.core.calc.costs import Component
from app.data import csv_store
from app.main import app
from app.models import YearParameterRow
from app.services.autosave import autosave_service


def _setup(repo, components):
    csv_store.write_components(repo, components)
    csv_store.write_year_parameters(
        repo,
        [
            YearParameterRow(year=2026, current_reserve_balance=1000.0),
            YearParameterRow(year=2027, inflation_rate=0.10),
        ],
    )


def _record(client, component_id, year, cost, mode="keep", estimate=None, comment=None):
    recurrence = {"mode": mode}
    if estimate is not None:
        recurrence["estimate"] = estimate
    return client.post(
        "/api/actual-costs",
        json={
            "component_id": component_id,
            "year": year,
            "cost": cost,
            "comment": comment,
            "recurrence": recurrence,
        },
    )


@pytest.fixture
def repo(git_data_repo, monkeypatch):
    monkeypatch.setattr(settings, "data_repo_path", git_data_repo)
    monkeypatch.setattr(autosave_service, "notify_change", lambda: None)
    _setup(
        git_data_repo,
        [
            Component("roof", "Roof", 100.0, 2028, 50),
            Component("gutter", "Gutter", 1000.0, 2020, 2),
        ],
    )
    return git_data_repo


@pytest.fixture
def client(repo):
    return TestClient(app)


def _component(repo, component_id):
    return next(c for c in csv_store.read_components(repo) if c.id == component_id)


def test_preview_reports_estimate_backfill_and_next_schedule(client):
    resp = client.get(
        "/api/actual-costs/preview", params={"component_id": "gutter", "year": 2024}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["component_name"] == "Gutter"
    assert body["new_initial_year"] == 2026
    assert [b["year"] for b in body["backfill"]] == [2020, 2022]


def test_recording_moves_next_occurrence_to_year_plus_life(client, repo):
    resp = _record(client, "roof", 2028, 150.0, comment="paid in full")
    assert resp.status_code == 201
    assert resp.json()["new_initial_year"] == 2078  # 2028 + 50

    assert _component(repo, "roof").initial_year == 2078
    actuals = csv_store.read_actual_costs(repo)
    assert [(a.component_id, a.year, a.cost, a.comment) for a in actuals] == [
        ("roof", 2028, 150.0, "paid in full")
    ]


def test_keep_estimate_leaves_the_estimate_alone_but_still_reschedules(client, repo):
    _record(client, "roof", 2028, 150.0, mode="keep")
    roof = _component(repo, "roof")
    assert roof.estimated_cost == 100.0
    assert roof.initial_year == 2078


def test_yes_uses_actual_deflated_to_base_year_dollars(client, repo):
    # base year 2026, 10% inflation in 2027 and 2028 -> factor 1.21
    resp = _record(client, "roof", 2028, 121.0, mode="actual")
    assert resp.status_code == 201
    assert round(_component(repo, "roof").estimated_cost, 2) == 100.0
    resp = _record(client, "gutter", 2028, 1210.0, mode="actual")
    # gutter backfills 2020..2026, then 2028 actual of 1210 -> 1000 in base dollars
    assert round(_component(repo, "gutter").estimated_cost, 2) == 1000.0


def test_other_sets_a_hand_entered_estimate(client, repo):
    _record(client, "roof", 2028, 150.0, mode="other", estimate=500.0)
    assert _component(repo, "roof").estimated_cost == 500.0


def test_other_without_an_estimate_is_rejected(client):
    resp = _record(client, "roof", 2028, 150.0, mode="other")
    assert resp.status_code == 422


def test_yes_with_a_zero_actual_is_rejected(client, repo):
    resp = _record(client, "roof", 2028, 0.0, mode="actual")
    assert resp.status_code == 400
    assert csv_store.read_actual_costs(repo) == []


def test_missed_earlier_occurrences_are_backfilled_at_their_estimates(client, repo):
    resp = _record(client, "gutter", 2024, 1100.0)
    assert resp.status_code == 201
    actuals = {a.year: a for a in csv_store.read_actual_costs(repo)}
    assert sorted(actuals) == [2020, 2022, 2024]
    assert actuals[2020].cost == 1000.0
    assert actuals[2020].comment == "Backfilled from estimate"
    assert actuals[2024].cost == 1100.0
    assert actuals[2024].comment is None
    assert _component(repo, "gutter").initial_year == 2026


def test_recording_an_unscheduled_year_is_rejected(client):
    assert _record(client, "roof", 2029, 1.0).status_code == 400
    assert _record(client, "roof", 2020, 1.0).status_code == 400  # before initial_year


def test_recording_twice_conflicts(client):
    _record(client, "gutter", 2020, 1000.0)
    # schedule moved on, so 2020 is no longer a scheduled occurrence either way
    assert _record(client, "gutter", 2020, 1000.0).status_code in (400, 409)


def test_unknown_component_404s(client):
    assert _record(client, "nope", 2028, 1.0).status_code == 404


def test_editing_is_blocked_on_main(bare_git_repo, monkeypatch):
    monkeypatch.setattr(settings, "data_repo_path", bare_git_repo)
    monkeypatch.setattr(autosave_service, "notify_change", lambda: None)
    _setup(bare_git_repo, [Component("roof", "Roof", 100.0, 2028, 50)])
    client = TestClient(app)
    assert _record(client, "roof", 2028, 1.0).status_code == 403
    assert client.delete("/api/actual-costs/roof/2028").status_code == 403
    # previewing is read-only and stays available
    assert client.get(
        "/api/actual-costs/preview", params={"component_id": "roof", "year": 2028}
    ).status_code == 200


def test_costs_view_shows_the_actual_in_place_of_the_estimate(client):
    _record(client, "roof", 2028, 150.0, comment="over")
    rows = client.get(
        "/api/projections/costs", params={"start_year": 2028, "end_year": 2028}
    ).json()
    items = rows[0]["line_items"]
    roof = next(i for i in items if i["component_id"] == "roof")
    assert roof["is_actual"] is True
    assert roof["cost"] == 150.0
    assert roof["comment"] == "over"
    assert rows[0]["total"] == sum(i["cost"] for i in items)


def test_ffb_total_cost_uses_the_actual(client):
    _record(client, "roof", 2028, 150.0)
    rows = client.get(
        "/api/projections/ffb", params={"start_year": 2026, "end_year": 2028}
    ).json()
    row_2028 = next(r for r in rows if r["year"] == 2028)
    # roof actual 150 + gutter estimate (10% inflation 2027-2028 -> 1210)
    assert round(row_2028["total_cost"], 2) == round(150.0 + 1000.0 * 1.1 * 1.1, 2)


def test_edit_changes_amount_and_comment_only(client, repo):
    _record(client, "roof", 2028, 150.0)
    resp = client.put(
        "/api/actual-costs/roof/2028", json={"cost": 175.0, "comment": "corrected"}
    )
    assert resp.status_code == 200
    actual = csv_store.read_actual_costs(repo)[0]
    assert (actual.cost, actual.comment) == (175.0, "corrected")
    assert _component(repo, "roof").initial_year == 2078  # untouched by an edit


def test_edit_missing_actual_404s(client):
    resp = client.put("/api/actual-costs/roof/2028", json={"cost": 1.0})
    assert resp.status_code == 404


def test_removing_the_latest_actual_restores_the_schedule(client, repo):
    _record(client, "roof", 2028, 150.0)
    assert client.delete("/api/actual-costs/roof/2028").status_code == 204
    assert csv_store.read_actual_costs(repo) == []
    assert _component(repo, "roof").initial_year == 2028


def test_removing_a_backfilled_actual_restores_back_through_the_chain(client, repo):
    _record(client, "gutter", 2024, 1100.0)  # backfills 2020, 2022; schedule -> 2026
    assert client.delete("/api/actual-costs/gutter/2022").status_code == 204
    assert _component(repo, "gutter").initial_year == 2022
    assert sorted(a.year for a in csv_store.read_actual_costs(repo)) == [2020, 2024]


def test_removing_leaves_a_hand_pushed_schedule_alone(client, repo):
    _record(client, "roof", 2028, 150.0)
    csv_store.write_components(
        repo,
        [
            Component("roof", "Roof", 100.0, 2090, 50),  # user pushed it by hand
            Component("gutter", "Gutter", 1000.0, 2020, 2),
        ],
    )
    client.delete("/api/actual-costs/roof/2028")
    assert _component(repo, "roof").initial_year == 2090


def test_deleting_a_component_removes_its_actuals(client, repo):
    _record(client, "roof", 2028, 150.0)
    _record(client, "gutter", 2020, 1000.0)
    assert client.delete("/api/components/roof").status_code == 204
    assert [a.component_id for a in csv_store.read_actual_costs(repo)] == ["gutter"]
