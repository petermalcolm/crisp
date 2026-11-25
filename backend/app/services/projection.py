from dataclasses import dataclass

from app.config import settings
from app.core.calc.costs import Component, YearCostRow, project_costs
from app.core.calc.ffb import YearFFBRow, project_ffb
from app.core.calc.parameters import (
    aggregate_surprise_by_year,
    resolve_base_year,
    resolve_contribution_series,
    resolve_cost_base_year,
    resolve_effective_base_year,
    resolve_horizon,
    resolve_rate_series,
)
from app.data import csv_store
from app.models import ActualCost, YearParameterRow


@dataclass(frozen=True)
class FFBComputation:
    """Everything the FFB view and the lender report derive from the data repo
    for one window, so both read the same numbers.

    The ``*_by_year`` series and ``cost_rows`` cover the whole span from
    ``span_start`` (which can precede the window, as the balance rolls forward
    from the anchor and inflation compounds from the cost base year); ``rows``
    covers only [start_year, end_year].
    """

    components: list[Component]
    year_parameters: list[YearParameterRow]
    actual_costs: list[ActualCost]
    anchor_year: int
    base_year: int
    current_reserve_balance: float | None
    start_year: int
    end_year: int
    span_start: int
    inflation_by_year: dict[int, float]
    interest_by_year: dict[int, float]
    contribution_by_year: dict[int, float]
    surprise_by_year: dict[int, float]
    cost_rows: list[YearCostRow]
    rows: list[YearFFBRow]


def compute_ffb_projection(
    start_year: int | None, end_year: int | None
) -> FFBComputation:
    repo = settings.data_repo_path
    components = csv_store.read_components(repo)
    year_parameters = csv_store.read_year_parameters(repo)
    surprise_rows = csv_store.read_surprise_contributions(repo)
    actual_costs = csv_store.read_actual_costs(repo)

    # anchor_year: the year the reserve balance is stated at the start of
    # (today's year if none is set, in which case no balance is computed).
    # base_year: the dollars estimated_cost is denominated in.
    _, current_reserve_balance = resolve_base_year(year_parameters)
    anchor_year = resolve_effective_base_year(year_parameters)
    base_year = resolve_cost_base_year(
        year_parameters, csv_store.read_study_settings(repo)
    )
    resolved_start, resolved_end = resolve_horizon(anchor_year, start_year, end_year)

    # Rates and costs are resolved from the earliest year anything depends on
    # (the balance rolls forward from the anchor; inflation compounds from the
    # cost base year) and the result is trimmed to the requested window.
    span_start = min(resolved_start, anchor_year, base_year)

    inflation_by_year = resolve_rate_series(
        year_parameters, "inflation_rate", span_start, resolved_end
    )
    interest_by_year = resolve_rate_series(
        year_parameters, "interest_rate", span_start, resolved_end
    )
    contribution_by_year = resolve_contribution_series(
        year_parameters, span_start, resolved_end
    )
    surprise_by_year = aggregate_surprise_by_year(
        surprise_rows, span_start, resolved_end
    )

    cost_rows = project_costs(
        components,
        span_start,
        resolved_end,
        base_year,
        inflation_by_year,
        actual_costs,
    )
    costs_by_year = {row.year: row.total for row in cost_rows}

    rows = project_ffb(
        components,
        resolved_start,
        resolved_end,
        base_year,
        current_reserve_balance,
        inflation_by_year,
        interest_by_year,
        contribution_by_year,
        surprise_by_year,
        costs_by_year,
        actual_costs,
        anchor_year=anchor_year,
        as_of_year=anchor_year,
    )
    return FFBComputation(
        components=components,
        year_parameters=year_parameters,
        actual_costs=actual_costs,
        anchor_year=anchor_year,
        base_year=base_year,
        current_reserve_balance=current_reserve_balance,
        start_year=resolved_start,
        end_year=resolved_end,
        span_start=span_start,
        inflation_by_year=inflation_by_year,
        interest_by_year=interest_by_year,
        contribution_by_year=contribution_by_year,
        surprise_by_year=surprise_by_year,
        cost_rows=cost_rows,
        rows=rows,
    )
