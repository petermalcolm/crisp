from dataclasses import replace
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from app.api.deps import require_forecast_branch
from app.config import settings
from app.core.calc.actuals import (
    base_year_estimate,
    is_recordable,
    plan_recording,
    schedule_revert_year,
)
from app.core.calc.costs import Component
from app.core.calc.parameters import (
    resolve_effective_base_year,
    resolve_horizon,
    resolve_rate_series,
)
from app.data import csv_store
from app.models import ActualCost
from app.services.autosave import autosave_service

router = APIRouter(prefix="/api/actual-costs", tags=["actual-costs"])

BACKFILL_COMMENT = "Backfilled from estimate"


class BackfillItem(BaseModel):
    year: int
    cost: float


class PreviewOut(BaseModel):
    component_id: str
    component_name: str
    year: int
    estimated_cost: float
    expected_life_years: int
    new_initial_year: int
    backfill: list[BackfillItem]


class Recurrence(BaseModel):
    mode: Literal["actual", "keep", "other"]
    estimate: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _other_needs_estimate(self) -> "Recurrence":
        if self.mode == "other" and self.estimate is None:
            raise ValueError("estimate is required when mode is 'other'")
        return self


class RecordIn(BaseModel):
    component_id: str
    year: int
    cost: float = Field(ge=0)
    comment: str | None = None
    recurrence: Recurrence


class ActualCostOut(BaseModel):
    component_id: str
    year: int
    cost: float
    comment: str | None


class RecordOut(BaseModel):
    actuals: list[ActualCostOut]
    new_initial_year: int
    new_estimated_cost: float


class EditIn(BaseModel):
    cost: float = Field(ge=0)
    comment: str | None = None


def _out(actual: ActualCost) -> ActualCostOut:
    return ActualCostOut(
        component_id=actual.component_id,
        year=actual.year,
        cost=actual.cost,
        comment=actual.comment,
    )


def _find_component(components: list[Component], component_id: str) -> Component:
    component = next((c for c in components if c.id == component_id), None)
    if component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    return component


def _inflation_through(year: int) -> tuple[int, dict[int, float]]:
    """Base year and the inflation series, resolved over the same window the
    Costs tab uses so figures here match what's displayed there."""
    parameters = csv_store.read_year_parameters(settings.data_repo_path)
    base_year = resolve_effective_base_year(parameters)
    start, end = resolve_horizon(base_year, None, None)
    return base_year, resolve_rate_series(
        parameters, "inflation_rate", start, max(end, year)
    )


def _check_recordable(
    component: Component, year: int, actuals: list[ActualCost]
) -> None:
    if any(a.component_id == component.id and a.year == year for a in actuals):
        raise HTTPException(
            status_code=409,
            detail=f"An actual for {component.name} in {year} is already recorded.",
        )
    if not is_recordable(component, year, actuals):
        raise HTTPException(
            status_code=400,
            detail=f"{year} is not a scheduled occurrence of {component.name}.",
        )


@router.get("/preview", response_model=PreviewOut)
def preview_recording(
    component_id: str = Query(), year: int = Query()
) -> PreviewOut:
    components = csv_store.read_components(settings.data_repo_path)
    actuals = csv_store.read_actual_costs(settings.data_repo_path)
    component = _find_component(components, component_id)
    _check_recordable(component, year, actuals)

    base_year, inflation = _inflation_through(year)
    plan = plan_recording(component, year, actuals, base_year, inflation)
    return PreviewOut(
        component_id=component.id,
        component_name=component.name,
        year=year,
        estimated_cost=plan.year_estimate,
        expected_life_years=component.expected_life_years,
        new_initial_year=plan.new_initial_year,
        backfill=[BackfillItem(year=y, cost=c) for y, c in plan.backfill],
    )


@router.post(
    "",
    response_model=RecordOut,
    status_code=201,
    dependencies=[Depends(require_forecast_branch)],
)
def record_actual(payload: RecordIn) -> RecordOut:
    components = csv_store.read_components(settings.data_repo_path)
    actuals = csv_store.read_actual_costs(settings.data_repo_path)
    component = _find_component(components, payload.component_id)
    _check_recordable(component, payload.year, actuals)

    base_year, inflation = _inflation_through(payload.year)
    plan = plan_recording(component, payload.year, actuals, base_year, inflation)

    mode = payload.recurrence.mode
    if mode == "actual":
        if payload.cost <= 0:
            raise HTTPException(
                status_code=400,
                detail="The recurring cost can't be based on a $0 actual; "
                "choose another option.",
            )
        new_estimate = base_year_estimate(
            payload.cost, payload.year, base_year, inflation
        )
    elif mode == "other":
        new_estimate = payload.recurrence.estimate
    else:
        new_estimate = component.estimated_cost

    new_actuals = [
        ActualCost(component.id, year, cost, BACKFILL_COMMENT)
        for year, cost in plan.backfill
    ] + [ActualCost(component.id, payload.year, payload.cost, payload.comment)]
    csv_store.write_actual_costs(settings.data_repo_path, actuals + new_actuals)

    updated = replace(
        component,
        initial_year=plan.new_initial_year,
        estimated_cost=new_estimate,
    )
    csv_store.write_components(
        settings.data_repo_path,
        [updated if c.id == component.id else c for c in components],
    )
    autosave_service.notify_change()
    return RecordOut(
        actuals=[_out(a) for a in new_actuals],
        new_initial_year=updated.initial_year,
        new_estimated_cost=updated.estimated_cost,
    )


@router.put(
    "/{component_id}/{year}",
    response_model=ActualCostOut,
    dependencies=[Depends(require_forecast_branch)],
)
def edit_actual(component_id: str, year: int, payload: EditIn) -> ActualCostOut:
    actuals = csv_store.read_actual_costs(settings.data_repo_path)
    index = next(
        (
            i
            for i, a in enumerate(actuals)
            if a.component_id == component_id and a.year == year
        ),
        None,
    )
    if index is None:
        raise HTTPException(status_code=404, detail="Actual cost not found")
    actuals[index] = replace(actuals[index], cost=payload.cost, comment=payload.comment)
    csv_store.write_actual_costs(settings.data_repo_path, actuals)
    autosave_service.notify_change()
    return _out(actuals[index])


@router.delete(
    "/{component_id}/{year}",
    status_code=204,
    dependencies=[Depends(require_forecast_branch)],
)
def delete_actual(component_id: str, year: int) -> None:
    actuals = csv_store.read_actual_costs(settings.data_repo_path)
    remaining = [
        a for a in actuals if not (a.component_id == component_id and a.year == year)
    ]
    if len(remaining) == len(actuals):
        raise HTTPException(status_code=404, detail="Actual cost not found")
    csv_store.write_actual_costs(settings.data_repo_path, remaining)

    # Put the scheduled occurrence back so the removed year isn't orphaned.
    components = csv_store.read_components(settings.data_repo_path)
    component = next((c for c in components if c.id == component_id), None)
    if component is not None:
        other_years = {a.year for a in remaining if a.component_id == component_id}
        revert_to = schedule_revert_year(component, year, other_years)
        if revert_to is not None:
            csv_store.write_components(
                settings.data_repo_path,
                [
                    replace(c, initial_year=revert_to) if c.id == component_id else c
                    for c in components
                ],
            )
    autosave_service.notify_change()
