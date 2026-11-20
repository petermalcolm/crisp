from app.core.calc.actuals import (
    base_year_estimate,
    is_recordable,
    plan_recording,
    schedule_revert_year,
)
from app.core.calc.costs import Component, component_age_in_year, project_costs
from app.core.calc.ffb import project_ffb
from app.models import ActualCost

ROOF = Component(
    id="roof", name="Roof", estimated_cost=100_000.0, initial_year=2026, expected_life_years=15
)
# recurs 2020, 2022, 2024, 2026, ...
GUTTER = Component(
    id="gutter", name="Gutter", estimated_cost=1_000.0, initial_year=2020, expected_life_years=2
)


def test_actual_replaces_estimate_on_its_line_and_in_year_total():
    rows = project_costs(
        [ROOF],
        2026,
        2026,
        base_year=2026,
        inflation_by_year={},
        actual_costs=[ActualCost("roof", 2026, 92_500.0, "came in under")],
    )
    item = rows[0].line_items[0]
    assert item.is_actual is True
    assert item.cost == 92_500.0
    assert item.comment == "came in under"
    assert rows[0].total == 92_500.0


def test_line_without_actual_stays_an_estimate():
    rows = project_costs([ROOF], 2026, 2026, base_year=2026, inflation_by_year={})
    assert rows[0].line_items[0].is_actual is False
    assert rows[0].line_items[0].comment is None


def test_actual_in_an_unscheduled_year_still_appears():
    # after recording a 2026 actual the roof's schedule moves to 2041, but the
    # 2026 spend must remain visible
    moved = Component("roof", "Roof", 100_000.0, 2041, 15)
    rows = project_costs(
        [moved],
        2026,
        2027,
        base_year=2026,
        inflation_by_year={},
        actual_costs=[ActualCost("roof", 2026, 92_500.0)],
    )
    assert [i.is_actual for i in rows[0].line_items] == [True]
    assert rows[1].line_items == []


def test_actual_for_unknown_component_is_ignored():
    rows = project_costs(
        [ROOF], 2026, 2026, base_year=2026, inflation_by_year={},
        actual_costs=[ActualCost("ghost", 2026, 5.0)],
    )
    assert [i.component_id for i in rows[0].line_items] == ["roof"]


def test_age_counts_from_latest_actual_when_schedule_is_ahead():
    moved = Component("roof", "Roof", 100_000.0, 2041, 15)
    assert component_age_in_year(moved, 2030) is None  # no actuals known
    assert component_age_in_year(moved, 2030, [2026]) == 4
    assert component_age_in_year(moved, 2041, [2026]) == 0  # schedule resumes


def test_age_unchanged_without_actuals():
    assert component_age_in_year(ROOF, 2030) == 4
    assert component_age_in_year(ROOF, 2041) == 0
    assert component_age_in_year(ROOF, 2025) is None


def test_ffb_target_keeps_aging_after_schedule_moves_past_an_actual():
    moved = Component("roof", "Roof", 150_000.0, 2036, 10)  # actual in 2026, L=10
    rows = project_ffb(
        [moved], 2026, 2030, base_year=2026, current_reserve_balance=None,
        inflation_by_year={}, interest_by_year={}, contribution_by_year={},
        surprise_by_year={}, costs_by_year={},
        actual_costs=[ActualCost("roof", 2026, 150_000.0)],
    )
    by_year = {r.year: r for r in rows}
    assert by_year[2026].ffb_target == 0.0
    assert by_year[2028].ffb_target == 150_000.0 * 2 / 10
    assert by_year[2030].ffb_target == 150_000.0 * 4 / 10


def test_ffb_target_capped_at_full_cost_when_schedule_pushed_past_life():
    pushed = Component("roof", "Roof", 100_000.0, 2060, 10)
    rows = project_ffb(
        [pushed], 2040, 2040, base_year=2026, current_reserve_balance=None,
        inflation_by_year={}, interest_by_year={}, contribution_by_year={},
        surprise_by_year={}, costs_by_year={},
        actual_costs=[ActualCost("roof", 2026, 100_000.0)],
    )
    assert rows[0].ffb_target == 100_000.0  # age 14 > life 10, capped


def test_plan_recording_backfills_missed_earlier_occurrences_at_estimates():
    plan = plan_recording(GUTTER, 2024, [], base_year=2026, inflation_by_year={})
    assert plan.backfill == [(2020, 1_000.0), (2022, 1_000.0)]
    assert plan.new_initial_year == 2026
    assert plan.year_estimate == 1_000.0


def test_plan_recording_has_no_backfill_for_the_first_occurrence():
    plan = plan_recording(ROOF, 2026, [], base_year=2026, inflation_by_year={})
    assert plan.backfill == []
    assert plan.new_initial_year == 2041


def test_plan_recording_backfill_uses_inflated_estimates_and_skips_recorded():
    plan = plan_recording(
        GUTTER, 2028, [ActualCost("gutter", 2020, 900.0)],
        base_year=2024, inflation_by_year={2025: 0.10, 2026: 0.10},
    )
    years = [y for y, _ in plan.backfill]
    assert years == [2022, 2024, 2026]  # 2020 already has an actual
    assert round(dict(plan.backfill)[2026], 2) == 1_210.0  # 1000 * 1.1 * 1.1


def test_is_recordable_requires_scheduled_year_and_no_existing_actual():
    assert is_recordable(ROOF, 2026, [])
    assert not is_recordable(ROOF, 2027, [])
    assert not is_recordable(ROOF, 2025, [])
    assert not is_recordable(ROOF, 2026, [ActualCost("roof", 2026, 1.0)])


def test_base_year_estimate_deflates_to_base_year_dollars():
    inflation = {2027: 0.10, 2028: 0.10}
    assert round(base_year_estimate(121.0, 2028, 2026, inflation), 6) == 100.0
    assert base_year_estimate(121.0, 2026, 2026, inflation) == 121.0  # no adjustment


def test_schedule_revert_when_removing_most_recent_actual():
    moved = Component("gutter", "Gutter", 1_000.0, 2026, 2)
    assert schedule_revert_year(moved, 2024, {2020, 2022}) == 2024


def test_schedule_revert_walks_back_through_an_unbroken_chain():
    moved = Component("gutter", "Gutter", 1_000.0, 2026, 2)
    assert schedule_revert_year(moved, 2020, {2022, 2024}) == 2020


def test_schedule_revert_refuses_when_chain_is_broken_or_misaligned():
    moved = Component("gutter", "Gutter", 1_000.0, 2026, 2)
    assert schedule_revert_year(moved, 2020, {2024}) is None  # 2022 missing
    assert schedule_revert_year(moved, 2025, set()) is None  # not a multiple of L
    pushed_by_hand = Component("roof", "Roof", 1.0, 2085, 50)  # 2025 + 60, off-cycle
    assert schedule_revert_year(pushed_by_hand, 2025, set()) is None
    assert schedule_revert_year(moved, 2030, set()) is None  # not before initial_year


def test_schedule_revert_for_the_ordinary_single_actual_case():
    roof = Component("roof", "Roof", 1.0, 2075, 50)  # actual in 2025 moved it here
    assert schedule_revert_year(roof, 2025, set()) == 2025
