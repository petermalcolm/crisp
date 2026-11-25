from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.config import settings
from app.core.calc.costs import project_costs
from app.core.calc.parameters import (
    resolve_cost_base_year,
    resolve_effective_base_year,
    resolve_horizon,
    resolve_rate_series,
)
from app.data import csv_store
from app.services.projection import compute_ffb_projection

router = APIRouter(prefix="/api/projections", tags=["projections"])


class CostLineItemOut(BaseModel):
    component_id: str
    component_name: str
    cost: float
    is_actual: bool
    comment: str | None


class YearCostRowOut(BaseModel):
    year: int
    is_estimate: bool
    line_items: list[CostLineItemOut]
    total: float


class YearFFBRowOut(BaseModel):
    year: int
    is_estimate: bool
    ffb_target: float
    total_cost: float
    actual_balance: float | None
    percent_funded: float | None


@router.get("/costs", response_model=list[YearCostRowOut])
def get_costs_projection(
    start_year: int | None = Query(default=None),
    end_year: int | None = Query(default=None),
) -> list[YearCostRowOut]:
    components = csv_store.read_components(settings.data_repo_path)
    year_parameters = csv_store.read_year_parameters(settings.data_repo_path)

    as_of_year = resolve_effective_base_year(year_parameters)
    base_year = resolve_cost_base_year(
        year_parameters, csv_store.read_study_settings(settings.data_repo_path)
    )
    resolved_start, resolved_end = resolve_horizon(as_of_year, start_year, end_year)

    # Resolve inflation from the cost base year, not just the window start, so
    # carry-forward rates set before a narrow window still apply to it.
    inflation_by_year = resolve_rate_series(
        year_parameters, "inflation_rate", min(resolved_start, base_year), resolved_end
    )

    rows = project_costs(
        components,
        resolved_start,
        resolved_end,
        base_year,
        inflation_by_year,
        csv_store.read_actual_costs(settings.data_repo_path),
    )
    return [
        YearCostRowOut(
            year=row.year,
            is_estimate=row.year > as_of_year,
            line_items=[
                CostLineItemOut(
                    component_id=item.component_id,
                    component_name=item.component_name,
                    cost=item.cost,
                    is_actual=item.is_actual,
                    comment=item.comment,
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
    computation = compute_ffb_projection(start_year, end_year)
    return [
        YearFFBRowOut(
            year=row.year,
            is_estimate=row.is_estimate,
            ffb_target=row.ffb_target,
            total_cost=row.total_cost,
            actual_balance=row.actual_balance,
            percent_funded=row.percent_funded,
        )
        for row in computation.rows
    ]
