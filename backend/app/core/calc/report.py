"""Pure calculations behind the lender report: the per-year projection table
and the Table 8 style summary statistics."""

from dataclasses import dataclass

from app.core.calc.ffb import YearFFBRow


@dataclass(frozen=True)
class ProjectionYear:
    year: int
    start_balance: float | None
    interest: float | None
    contribution: float
    special_contribution: float
    costs: float
    end_balance: float | None
    ffb: float
    percent_funded: float | None
    inflation_rate: float
    interest_rate: float


@dataclass(frozen=True)
class Extreme:
    value: float
    year: int


@dataclass(frozen=True)
class ProjectionSummary:
    balance_min: Extreme | None
    balance_max: Extreme | None
    contribution_min: Extreme | None
    contribution_max: Extreme | None
    percent_funded_min: Extreme | None
    percent_funded_max: Extreme | None
    percent_funded_avg: float | None
    first_shortfall_year: int | None  # first year ending with a negative balance
    total_contributions: float
    total_special_contributions: float
    total_costs: float


def build_projection_years(
    rows: list[YearFFBRow],
    inflation_by_year: dict[int, float],
    interest_by_year: dict[int, float],
    contribution_by_year: dict[int, float],
    surprise_by_year: dict[int, float],
) -> list[ProjectionYear]:
    """One row per year with the full January 1 -> December 31 rollforward.
    ``end_balance`` is next year's start balance by construction."""
    years = []
    for row in rows:
        rate = interest_by_year.get(row.year, 0.0)
        contribution = contribution_by_year.get(row.year, 0.0)
        special = surprise_by_year.get(row.year, 0.0)
        if row.actual_balance is None:
            interest = end_balance = None
        else:
            interest = row.actual_balance * rate
            end_balance = (
                row.actual_balance + interest + contribution + special - row.total_cost
            )
        years.append(
            ProjectionYear(
                year=row.year,
                start_balance=row.actual_balance,
                interest=interest,
                contribution=contribution,
                special_contribution=special,
                costs=row.total_cost,
                end_balance=end_balance,
                ffb=row.ffb_target,
                percent_funded=row.percent_funded,
                inflation_rate=inflation_by_year.get(row.year, 0.0),
                interest_rate=rate,
            )
        )
    return years


def _extremes(
    pairs: list[tuple[int, float]],
) -> tuple[Extreme | None, Extreme | None]:
    if not pairs:
        return None, None
    low = min(pairs, key=lambda p: p[1])
    high = max(pairs, key=lambda p: p[1])
    return Extreme(low[1], low[0]), Extreme(high[1], high[0])


def summarize_projection(years: list[ProjectionYear]) -> ProjectionSummary:
    """Min/max start-of-year balance, annual contribution and percent funded,
    plus the average percent funded, over the given years."""
    balance_min, balance_max = _extremes(
        [(y.year, y.start_balance) for y in years if y.start_balance is not None]
    )
    contribution_min, contribution_max = _extremes(
        [(y.year, y.contribution) for y in years]
    )
    percents = [(y.year, y.percent_funded) for y in years if y.percent_funded is not None]
    percent_min, percent_max = _extremes(percents)
    shortfall = next(
        (y.year for y in years if y.end_balance is not None and y.end_balance < 0),
        None,
    )
    return ProjectionSummary(
        balance_min=balance_min,
        balance_max=balance_max,
        contribution_min=contribution_min,
        contribution_max=contribution_max,
        percent_funded_min=percent_min,
        percent_funded_max=percent_max,
        percent_funded_avg=(
            sum(p for _, p in percents) / len(percents) if percents else None
        ),
        first_shortfall_year=shortfall,
        total_contributions=sum(y.contribution for y in years),
        total_special_contributions=sum(y.special_contribution for y in years),
        total_costs=sum(y.costs for y in years),
    )
