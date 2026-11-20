from dataclasses import dataclass

from app.core.calc.costs import Component, component_age_at_start_of_year, inflate_cost
from app.models import ActualCost


@dataclass(frozen=True)
class YearFFBRow:
    year: int
    is_estimate: bool
    ffb_target: float
    total_cost: float
    actual_balance: float | None
    percent_funded: float | None


def _ffb_target_for_year(
    components: list[Component],
    year: int,
    base_year: int,
    inflation_by_year: dict[int, float],
    actual_years_by_component: dict[str, list[int]],
) -> float:
    """Fully Funded Balance at the start of ``year``: for each component, the
    fraction of its useful life already consumed times its replacement cost in
    that year's dollars."""
    target = 0.0
    for component in components:
        age = component_age_at_start_of_year(
            component, year, actual_years_by_component.get(component.id, ())
        )
        inflated_cost = inflate_cost(
            component.estimated_cost, base_year, year, inflation_by_year
        )
        # Capped at fully funded: a schedule pushed out past the component's
        # life shouldn't call for more than 100% of its replacement cost.
        funded_fraction = min(age / component.expected_life_years, 1.0)
        target += funded_fraction * inflated_cost
    return target


def project_ffb(
    components: list[Component],
    start_year: int,
    end_year: int,
    base_year: int,
    current_reserve_balance: float | None,
    inflation_by_year: dict[int, float],
    interest_by_year: dict[int, float],
    contribution_by_year: dict[int, float],
    surprise_by_year: dict[int, float],
    costs_by_year: dict[int, float],
    actual_costs: list[ActualCost] | None = None,
    anchor_year: int | None = None,
    as_of_year: int | None = None,
) -> list[YearFFBRow]:
    """Project the FFB target and the reserve balance for each year in
    [start_year, end_year].

    Everything is stated at the **start of the year**, the way a reserve
    study reports it: the balance on Jan 1 against the FFB on Jan 1. The
    reserve balance is the Jan 1 balance of ``anchor_year`` (``current_reserve_balance``),
    and each later Jan 1 balance is the previous one plus that year's interest,
    contribution and special contributions, minus that year's costs.

    ``base_year`` is the year component estimates are denominated in; it is
    independent of ``anchor_year`` so re-anchoring to a newer bank balance
    doesn't change what the estimates mean. ``anchor_year`` defaults to
    ``base_year``. ``as_of_year`` (default: the anchor year) is the last year
    treated as history rather than an estimate.

    Rate/cost inputs must cover every year from ``anchor_year`` through
    ``end_year`` for the balance to be right; years before the anchor, or all
    years when no balance is set, report ``actual_balance=None``.
    """
    if anchor_year is None:
        anchor_year = base_year
    if as_of_year is None:
        as_of_year = anchor_year

    actual_years_by_component: dict[str, list[int]] = {}
    for actual in actual_costs or []:
        actual_years_by_component.setdefault(actual.component_id, []).append(
            actual.year
        )

    has_anchor = current_reserve_balance is not None
    first_year = min(start_year, anchor_year) if has_anchor else start_year

    rows = []
    balance: float | None = None

    for year in range(first_year, end_year + 1):
        if has_anchor and year == anchor_year:
            balance = current_reserve_balance
        elif has_anchor and year > anchor_year:
            prev = year - 1
            balance = (
                (balance or 0.0) * (1 + interest_by_year.get(prev, 0.0))
                + contribution_by_year.get(prev, 0.0)
                + surprise_by_year.get(prev, 0.0)
                - costs_by_year.get(prev, 0.0)
            )
        else:
            balance = None

        if year < start_year:
            continue

        target = _ffb_target_for_year(
            components, year, base_year, inflation_by_year, actual_years_by_component
        )
        percent_funded = (balance / target) if (balance is not None and target) else None

        rows.append(
            YearFFBRow(
                year=year,
                is_estimate=year > as_of_year,
                ffb_target=target,
                total_cost=costs_by_year.get(year, 0.0),
                actual_balance=balance,
                percent_funded=percent_funded,
            )
        )

    return rows
