from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.config import settings
from app.core.calc.costs import project_costs
from app.core.calc.ffb import project_ffb
from app.core.calc.parameters import (
    aggregate_surprise_by_year,
    resolve_base_year,
    resolve_contribution_series,
    resolve_effective_base_year,
    resolve_horizon,
    resolve_rate_series,
)
from app.data import csv_store

router = APIRouter(prefix="/api/projections", tags=["projections"])


class CostLineItemOut(BaseModel):
    component_id: str
    component_name: str
    cost: float


class YearCostRowOut(BaseModel):
    year: int
    is_estimate: bool
    line_items: list[CostLineItemOut]
    total: float


class YearFFBRowOut(BaseModel):
    year: int
    is_estimate: bool
    ffb_target: float
    actual_balance: float | None
    percent_funded: float | None


@router.get("/costs", response_model=list[YearCostRowOut])
def get_costs_projection(
    start_year: int | None = Query(default=None),
    end_year: int | None = Query(default=None),
) -> list[YearCostRowOut]:
    components = csv_store.read_components(settings.data_repo_path)
    year_parameters = csv_store.read_year_parameters(settings.data_repo_path)

    base_year = resolve_effective_base_year(year_parameters)
    resolved_start, resolved_end = resolve_horizon(base_year, start_year, end_year)

    inflation_by_year = resolve_rate_series(
        year_parameters, "inflation_rate", resolved_start, resolved_end
    )

    rows = project_costs(
        components, resolved_start, resolved_end, base_year, inflation_by_year
    )
    return [
        YearCostRowOut(
            year=row.year,
            is_estimate=row.is_estimate,
            line_items=[
                CostLineItemOut(
                    component_id=item.component_id,
                    component_name=item.component_name,
                    cost=item.cost,
                )
                for item in row.line_items
            ],
            total=row.total,
        )
        for row in rows
    ]


@router.get("/ffb", response_model=list[YearFFBRowOut])
def get_ffb_projection(
    start_year: int | None = Query(default=None),
    end_year: int | None = Query(default=None),
) -> list[YearFFBRowOut]:
    components = csv_store.read_components(settings.data_repo_path)
    year_parameters = csv_store.read_year_parameters(settings.data_repo_path)
    surprise_rows = csv_store.read_surprise_contributions(settings.data_repo_path)

    # resolve_effective_base_year returns the same anchor year current_reserve_balance
    # was set on (falling back to today's year only if no anchor exists yet, in which
    # case current_reserve_balance is also None and project_ffb never anchors a balance).
    _, current_reserve_balance = resolve_base_year(year_parameters)
    base_year = resolve_effective_base_year(year_parameters)
    resolved_start, resolved_end = resolve_horizon(base_year, start_year, end_year)

    inflation_by_year = resolve_rate_series(
        year_parameters, "inflation_rate", resolved_start, resolved_end
    )
    interest_by_year = resolve_rate_series(
        year_parameters, "interest_rate", resolved_start, resolved_end
    )
    contribution_by_year = resolve_contribution_series(
        year_parameters, resolved_start, resolved_end
    )
    surprise_by_year = aggregate_surprise_by_year(
        surprise_rows, resolved_start, resolved_end
    )

    cost_rows = project_costs(
        components, resolved_start, resolved_end, base_year, inflation_by_year
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
    )
    return [
        YearFFBRowOut(
            year=row.year,
            is_estimate=row.is_estimate,
            ffb_target=row.ffb_target,
            actual_balance=row.actual_balance,
            percent_funded=row.percent_funded,
        )
        for row in rows
    ]
