from app.core.calc.parameters import (
    aggregate_surprise_by_year,
    resolve_base_year,
    resolve_contribution_series,
    resolve_rate_series,
)
from app.models import SurpriseContribution, YearParameterRow


def test_resolve_base_year_picks_the_row_with_explicit_balance():
    rows = [
        YearParameterRow(year=2026, current_reserve_balance=10_000.0),
        YearParameterRow(year=2027, inflation_rate=0.03),
    ]
    base_year, balance = resolve_base_year(rows)
    assert base_year == 2026
    assert balance == 10_000.0


def test_resolve_base_year_none_when_never_set():
    rows = [YearParameterRow(year=2026, inflation_rate=0.03)]
    assert resolve_base_year(rows) == (None, None)


def test_resolve_base_year_latest_wins_on_multiple_anchors():
    rows = [
        YearParameterRow(year=2026, current_reserve_balance=10_000.0),
        YearParameterRow(year=2027, current_reserve_balance=20_000.0),
    ]
    base_year, balance = resolve_base_year(rows)
    assert base_year == 2027
    assert balance == 20_000.0


def test_resolve_rate_series_flat_carry_forward_defaults_to_zero():
    rows = [YearParameterRow(year=2027, inflation_rate=0.03)]
    resolved = resolve_rate_series(rows, "inflation_rate", 2026, 2028)
    assert resolved[2026] == 0.0  # no anchor yet
    assert resolved[2027] == 0.03
    assert resolved[2028] == 0.03


def test_resolve_contribution_series_compounds_with_yoy():
    rows = [
        YearParameterRow(
            year=2026, total_annual_contribution=50_000.0, yoy_contribution_change_pct=0.0
        ),
        YearParameterRow(year=2027, yoy_contribution_change_pct=0.02),
    ]
    resolved = resolve_contribution_series(rows, 2026, 2027)
    assert resolved[2026] == 50_000.0
    assert round(resolved[2027], 2) == 51_000.0


def test_aggregate_surprise_by_year_sums_multiple_entries_and_defaults_zero():
    contributions = [
        SurpriseContribution(id="a", year=2027, amount=1_000.0),
        SurpriseContribution(id="b", year=2027, amount=500.0),
        SurpriseContribution(id="c", year=2030, amount=200.0),  # outside window
    ]
    totals = aggregate_surprise_by_year(contributions, 2026, 2028)
    assert totals == {2026: 0.0, 2027: 1_500.0, 2028: 0.0}
