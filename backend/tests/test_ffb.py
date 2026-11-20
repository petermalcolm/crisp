import pytest

from app.core.calc.costs import Component
from app.core.calc.ffb import project_ffb

ROOF = Component(
    id="roof", name="Roof", estimated_cost=100_000.0, initial_year=2026, expected_life_years=15
)


def _project(**overrides):
    kwargs = dict(
        components=[ROOF],
        start_year=2026,
        end_year=2028,
        base_year=2026,
        current_reserve_balance=10_000.0,
        inflation_by_year={},
        interest_by_year={2026: 0.02, 2027: 0.02, 2028: 0.02},
        contribution_by_year={2026: 5_000.0, 2027: 5_000.0, 2028: 5_000.0},
        surprise_by_year={},
        costs_by_year={2026: 3_000.0},
    )
    kwargs.update(overrides)
    return {row.year: row for row in project_ffb(**kwargs)}


def test_balances_and_ffb_are_start_of_year():
    by_year = _project()

    y2026 = by_year[2026]
    assert y2026.is_estimate is False
    assert y2026.actual_balance == 10_000.0  # the anchor is the Jan 1 balance
    assert y2026.ffb_target == 100_000.0  # roof is due this year: 100% funded need
    assert y2026.total_cost == 3_000.0
    assert y2026.percent_funded == pytest.approx(0.10)

    # Jan 1 2027 = 2026's start balance + 2026 interest + 2026 contribution - 2026 costs
    y2027 = by_year[2027]
    assert y2027.is_estimate is True
    assert y2027.actual_balance == pytest.approx(10_000 * 1.02 + 5_000 - 3_000)
    assert y2027.ffb_target == pytest.approx(100_000 / 15)  # replaced in 2026, age 1
    assert y2027.percent_funded == pytest.approx(12_200 / (100_000 / 15))

    y2028 = by_year[2028]
    assert y2028.actual_balance == pytest.approx(12_200 * 1.02 + 5_000)
    assert y2028.ffb_target == pytest.approx(200_000 / 15)


def test_balance_is_none_before_the_anchor_year():
    by_year = _project(start_year=2024, base_year=2026)
    assert by_year[2024].actual_balance is None
    assert by_year[2025].actual_balance is None
    assert by_year[2026].actual_balance == 10_000.0
    # ...but wear accrued before the anchor still shows up in the target
    assert by_year[2025].ffb_target == pytest.approx(100_000 * 14 / 15)


def test_balance_rolls_forward_from_an_anchor_before_the_window():
    by_year = _project(start_year=2027, end_year=2028, anchor_year=2026)
    assert set(by_year) == {2027, 2028}
    assert by_year[2027].actual_balance == pytest.approx(12_200.0)
    assert by_year[2028].actual_balance == pytest.approx(12_200 * 1.02 + 5_000)


def test_balance_is_none_when_no_anchor_ever_set():
    by_year = _project(current_reserve_balance=None)
    assert all(row.actual_balance is None for row in by_year.values())
    assert all(row.percent_funded is None for row in by_year.values())


def test_cost_base_year_is_independent_of_the_balance_anchor():
    # Estimates are in 2024 dollars; the balance is re-anchored to 2026. The
    # 2026 FFB must still reflect two years of 3% inflation on the estimate.
    by_year = _project(
        base_year=2024,
        anchor_year=2026,
        inflation_by_year={2025: 0.03, 2026: 0.03},
    )
    assert by_year[2026].ffb_target == pytest.approx(100_000 * 1.03**2)
    assert by_year[2026].actual_balance == 10_000.0
    assert by_year[2026].is_estimate is False  # as-of defaults to the anchor


def test_percent_funded_none_when_target_is_zero():
    by_year = _project(components=[])
    assert by_year[2026].ffb_target == 0.0
    assert by_year[2026].percent_funded is None


def test_reproduces_vendor_style_calculation():
    """Hand-checked case in the shape of the vendor's 2024/2025 figures: one
    component with 4 of 20 years left (age 16), one due now, one just done."""
    components = [
        Component("a", "A", 20_000.0, 2028, 20),  # due in 4 years -> age 16
        Component("b", "B", 10_000.0, 2024, 10),  # due this year -> 100%
        Component("c", "C", 8_000.0, 2034, 10),   # replaced 2024 -> age 1 in 2025
    ]
    rows = {
        r.year: r
        for r in project_ffb(
            components, 2024, 2025, base_year=2024, current_reserve_balance=59_105.0,
            inflation_by_year={2025: 0.03}, interest_by_year={},
            contribution_by_year={2024: 37_182.0}, surprise_by_year={},
            costs_by_year={2024: 51_556.0},
        )
    }
    assert rows[2024].ffb_target == pytest.approx(20_000 * 16 / 20 + 10_000 + 8_000 * 0.0)
    # Start of 2025 balance = 59,105 + 37,182 - 51,556, the vendor's 44,731.
    assert rows[2025].actual_balance == pytest.approx(44_731.0)
