from dataclasses import dataclass

from app.core.calc.costs import Component, component_age_in_year, inflate_cost


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
) -> float:
    target = 0.0
    for component in components:
        age = component_age_in_year(component, year)
        if age is None:
            continue
        inflated_cost = inflate_cost(
            component.estimated_cost, base_year, year, inflation_by_year
        )
        target += (age / component.expected_life_years) * inflated_cost
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
) -> list[YearFFBRow]:
    """Project FFB target and actual-balance rollforward for each year.

    The actual balance is only computable from base_year forward (it's
    anchored by current_reserve_balance at base_year); years before
    base_year, an entire series when base_year falls outside
    [start_year, end_year], or every year when current_reserve_balance
    hasn't been set at all, report actual_balance=None.
    """
    rows = []
    balance: float | None = None
    anchored = False

    for year in range(start_year, end_year + 1):
        target = _ffb_target_for_year(components, year, base_year, inflation_by_year)

        if year == base_year and current_reserve_balance is not None:
            balance = current_reserve_balance
            anchored = True
        elif year > base_year and anchored:
            balance = (
                (balance or 0.0) * (1 + interest_by_year.get(year, 0.0))
                + contribution_by_year.get(year, 0.0)
                + surprise_by_year.get(year, 0.0)
                - costs_by_year.get(year, 0.0)
            )
        else:
            balance = None

        percent_funded = (balance / target) if (balance is not None and target) else None

        rows.append(
            YearFFBRow(
                year=year,
                is_estimate=year > base_year,
                ffb_target=target,
                total_cost=costs_by_year.get(year, 0.0),
                actual_balance=balance,
                percent_funded=percent_funded,
            )
        )

    return rows
