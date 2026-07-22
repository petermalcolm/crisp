from app.core.calc.costs import (
    Component,
    component_age_in_year,
    get_component_occurrences,
    inflate_cost,
    project_costs,
)

ROOF = Component(
    id="roof", name="Roof", estimated_cost=100_000.0, initial_year=2026, expected_life_years=15
)


def test_occurrences_recur_every_expected_life():
    assert get_component_occurrences(ROOF, 2026, 2056) == [2026, 2041, 2056]


def test_occurrences_before_initial_year_are_excluded_and_first_hit_after_start():
    late_start = Component(
        id="pool", name="Pool", estimated_cost=20_000.0, initial_year=2020, expected_life_years=10
    )
    # initial_year 2020, life 10 -> occurrences 2020, 2030, 2040...
    # querying window starting after 2020 should find the next occurrence, not 2020
    assert get_component_occurrences(late_start, 2026, 2045) == [2030, 2040]


def test_age_resets_to_zero_in_replacement_year():
    assert component_age_in_year(ROOF, 2026) == 0
    assert component_age_in_year(ROOF, 2030) == 4
    assert component_age_in_year(ROOF, 2040) == 14
    assert component_age_in_year(ROOF, 2041) == 0
    assert component_age_in_year(ROOF, 2025) is None


def test_inflate_cost_no_adjustment_at_or_before_base_year():
    inflation = {2027: 0.03, 2028: 0.03}
    assert inflate_cost(1000.0, 2026, 2026, inflation) == 1000.0
    assert inflate_cost(1000.0, 2026, 2020, inflation) == 1000.0


def test_inflate_cost_compounds_forward():
    inflation = {2027: 0.10, 2028: 0.10}
    result = inflate_cost(1000.0, 2026, 2028, inflation)
    assert round(result, 4) == round(1000 * 1.10 * 1.10, 4)


def test_project_costs_groups_by_year_with_sums_and_estimate_flag():
    walkway = Component(
        id="walkway", name="Walkway", estimated_cost=5_000.0, initial_year=2026, expected_life_years=20
    )
    rows = project_costs(
        [ROOF, walkway],
        start_year=2026,
        end_year=2027,
        base_year=2026,
        inflation_by_year={2027: 0.05},
    )
    year_2026 = rows[0]
    assert year_2026.year == 2026
    assert year_2026.is_estimate is False
    assert {item.component_id for item in year_2026.line_items} == {"roof", "walkway"}
    assert year_2026.total == 105_000.0

    year_2027 = rows[1]
    assert year_2027.is_estimate is True
    assert year_2027.line_items == []
    assert year_2027.total == 0.0
