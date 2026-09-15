from app.core.calc.costs import Component
from app.core.calc.ffb import project_ffb

ROOF = Component(
    id="roof", name="Roof", estimated_cost=100_000.0, initial_year=2026, expected_life_years=15
)


def test_ffb_target_and_rollforward_balance():
    rows = project_ffb(
        [ROOF],
        start_year=2026,
        end_year=2028,
        base_year=2026,
        current_reserve_balance=10_000.0,
        inflation_by_year={},
        interest_by_year={2027: 0.02, 2028: 0.02},
        contribution_by_year={2027: 5_000.0, 2028: 5_000.0},
        surprise_by_year={},
        costs_by_year={2026: 100_000.0, 2027: 0.0, 2028: 0.0},
    )
    by_year = {row.year: row for row in rows}

    y2026 = by_year[2026]
    assert y2026.is_estimate is False
    assert y2026.ffb_target == 0.0  # age 0 in replacement year
    assert y2026.total_cost == 100_000.0
    assert y2026.actual_balance == 10_000.0
    assert y2026.percent_funded is None  # target is 0, guarded against div-by-zero

    y2027 = by_year[2027]
    assert y2027.is_estimate is True
    assert round(y2027.ffb_target, 2) == round(100_000 / 15, 2)
    assert y2027.total_cost == 0.0
    assert round(y2027.actual_balance, 2) == 15_200.0
    assert round(y2027.percent_funded, 4) == round(15_200.0 / (100_000 / 15), 4)

    y2028 = by_year[2028]
    assert round(y2028.ffb_target, 2) == round(200_000 / 15, 2)
    assert round(y2028.actual_balance, 2) == 20_504.0


def test_balance_is_none_before_base_year():
    rows = project_ffb(
        [ROOF],
        start_year=2024,
        end_year=2026,
        base_year=2026,
        current_reserve_balance=10_000.0,
        inflation_by_year={},
        interest_by_year={},
        contribution_by_year={},
        surprise_by_year={},
        costs_by_year={},
    )
    by_year = {row.year: row for row in rows}
    assert by_year[2024].actual_balance is None
    assert by_year[2025].actual_balance is None
    assert by_year[2026].actual_balance == 10_000.0


def test_balance_is_none_when_base_year_outside_window():
    rows = project_ffb(
        [ROOF],
        start_year=2027,
        end_year=2028,
        base_year=2026,
        current_reserve_balance=10_000.0,
        inflation_by_year={},
        interest_by_year={2027: 0.02},
        contribution_by_year={},
        surprise_by_year={},
        costs_by_year={},
    )
    assert all(row.actual_balance is None for row in rows)
    assert all(row.percent_funded is None for row in rows)


def test_balance_is_none_when_no_anchor_ever_set():
    rows = project_ffb(
        [ROOF],
        start_year=2026,
        end_year=2028,
        base_year=2026,
        current_reserve_balance=None,
        inflation_by_year={},
        interest_by_year={2027: 0.02},
        contribution_by_year={2027: 5_000.0},
        surprise_by_year={},
        costs_by_year={},
    )
    assert all(row.actual_balance is None for row in rows)
    assert all(row.percent_funded is None for row in rows)
