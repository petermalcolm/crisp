import pytest

from app.core.calc.ffb import YearFFBRow
from app.core.calc.report import build_projection_years, summarize_projection


def _rows():
    # start balances 1000, 700, 1500; costs 400 in 2026 (after a 100 contribution)
    return [
        YearFFBRow(2026, False, 2000.0, 400.0, 1000.0, 0.50),
        YearFFBRow(2027, True, 2500.0, 0.0, 700.0, 0.28),
        YearFFBRow(2028, True, 3000.0, 2500.0, 1500.0, 0.50),
    ]


def _years():
    return build_projection_years(
        _rows(),
        inflation_by_year={2026: 0.03},
        interest_by_year={2026: 0.01, 2027: 0.0, 2028: 0.0},
        contribution_by_year={2026: 100.0, 2027: 800.0, 2028: 900.0},
        surprise_by_year={2027: 50.0},
    )


def test_end_balance_is_the_full_year_rollforward():
    years = {y.year: y for y in _years()}
    assert years[2026].interest == pytest.approx(10.0)
    assert years[2026].end_balance == pytest.approx(1000 + 10 + 100 - 400)  # 710
    assert years[2027].end_balance == pytest.approx(700 + 800 + 50)  # 1550
    assert years[2028].end_balance == pytest.approx(1500 + 900 - 2500)  # -100
    assert years[2026].inflation_rate == 0.03


def test_summary_extremes_average_and_shortfall():
    s = summarize_projection(_years())
    assert (s.balance_min.value, s.balance_min.year) == (700.0, 2027)
    assert (s.balance_max.value, s.balance_max.year) == (1500.0, 2028)
    assert (s.contribution_min.value, s.contribution_min.year) == (100.0, 2026)
    assert (s.contribution_max.value, s.contribution_max.year) == (900.0, 2028)
    assert (s.percent_funded_min.value, s.percent_funded_min.year) == (0.28, 2027)
    assert s.percent_funded_max.value == 0.50
    assert s.percent_funded_avg == pytest.approx((0.50 + 0.28 + 0.50) / 3)
    assert s.first_shortfall_year == 2028
    assert s.total_contributions == 1800.0
    assert s.total_special_contributions == 50.0
    assert s.total_costs == 2900.0


def test_summary_handles_no_balance():
    rows = [YearFFBRow(2026, True, 2000.0, 0.0, None, None)]
    years = build_projection_years(rows, {}, {}, {2026: 100.0}, {})
    s = summarize_projection(years)
    assert s.balance_min is None
    assert s.percent_funded_avg is None
    assert s.first_shortfall_year is None
    assert s.contribution_min.value == 100.0
