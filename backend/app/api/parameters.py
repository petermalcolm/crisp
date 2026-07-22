from dataclasses import replace

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import require_forecast_branch
from app.config import settings
from app.core.calc.parameters import resolve_horizon, resolve_effective_base_year
from app.core.calc.sticky import resolve_sticky_series
from app.data import csv_store
from app.models import SurpriseContribution, YearParameterRow
from app.services.autosave import autosave_service

router = APIRouter(prefix="/api", tags=["parameters"])

STICKY_FLAT_FIELDS = ["inflation_rate", "interest_rate", "yoy_contribution_change_pct"]


class ResolvedFieldOut(BaseModel):
    value: float | None
    is_explicit: bool
    source_year: int | None


class YearParametersOut(BaseModel):
    year: int
    num_contributors: int | None
    inflation_rate: ResolvedFieldOut
    interest_rate: ResolvedFieldOut
    yoy_contribution_change_pct: ResolvedFieldOut
    total_annual_contribution: ResolvedFieldOut
    current_reserve_balance: float | None
    notes: str | None


class YearParameterPatch(BaseModel):
    num_contributors: int | None = None
    inflation_rate: float | None = None
    interest_rate: float | None = None
    yoy_contribution_change_pct: float | None = None
    total_annual_contribution: float | None = None
    current_reserve_balance: float | None = None
    notes: str | None = None


def _build_year_parameters_out(
    rows: list[YearParameterRow], start_year: int, end_year: int
) -> list[YearParametersOut]:
    explicit_by_year = {row.year: row for row in rows}

    resolved_by_field = {}
    for field in STICKY_FLAT_FIELDS:
        explicit = {row.year: getattr(row, field) for row in rows}
        resolved_by_field[field] = resolve_sticky_series(
            explicit, start_year, end_year, mode="flat"
        )

    yoy_resolved = {
        year: (r.value or 0.0)
        for year, r in resolved_by_field["yoy_contribution_change_pct"].items()
    }
    contribution_explicit = {
        row.year: row.total_annual_contribution for row in rows
    }
    resolved_by_field["total_annual_contribution"] = resolve_sticky_series(
        contribution_explicit,
        start_year,
        end_year,
        mode="growth",
        growth_rate_by_year=yoy_resolved,
    )

    def _out(field: str, year: int) -> ResolvedFieldOut:
        resolved = resolved_by_field[field][year]
        return ResolvedFieldOut(
            value=resolved.value,
            is_explicit=resolved.is_explicit,
            source_year=resolved.source_year,
        )

    out = []
    for year in range(start_year, end_year + 1):
        row = explicit_by_year.get(year)
        out.append(
            YearParametersOut(
                year=year,
                num_contributors=row.num_contributors if row else None,
                inflation_rate=_out("inflation_rate", year),
                interest_rate=_out("interest_rate", year),
                yoy_contribution_change_pct=_out(
                    "yoy_contribution_change_pct", year
                ),
                total_annual_contribution=_out(
                    "total_annual_contribution", year
                ),
                current_reserve_balance=row.current_reserve_balance if row else None,
                notes=row.notes if row else None,
            )
        )
    return out


@router.get("/parameters", response_model=list[YearParametersOut])
def list_year_parameters(
    start_year: int | None = Query(default=None),
    end_year: int | None = Query(default=None),
) -> list[YearParametersOut]:
    rows = csv_store.read_year_parameters(settings.data_repo_path)
    base_year = resolve_effective_base_year(rows)
    resolved_start, resolved_end = resolve_horizon(base_year, start_year, end_year)
    return _build_year_parameters_out(rows, resolved_start, resolved_end)


@router.patch(
    "/parameters/{year}",
    response_model=YearParametersOut,
    dependencies=[Depends(require_forecast_branch)],
)
def patch_year_parameters(year: int, payload: YearParameterPatch) -> YearParametersOut:
    rows = csv_store.read_year_parameters(settings.data_repo_path)
    existing = next((r for r in rows if r.year == year), None)
    current = existing or YearParameterRow(year=year)

    updates = payload.model_dump(exclude_unset=True)
    updated = replace(current, **updates)

    rows = [r for r in rows if r.year != year] + [updated]
    csv_store.write_year_parameters(settings.data_repo_path, rows)
    autosave_service.notify_change()

    # Resolve from the earliest known year so carry-forward context isn't
    # lost when only the patched year is requested back.
    earliest_year = min([r.year for r in rows] + [year])
    return _build_year_parameters_out(rows, earliest_year, year)[-1]


class SurpriseContributionIn(BaseModel):
    year: int
    amount: float
    description: str | None = None


class SurpriseContributionOut(SurpriseContributionIn):
    id: str


@router.get("/surprise-contributions", response_model=list[SurpriseContributionOut])
def list_surprise_contributions(
    start_year: int | None = Query(default=None),
    end_year: int | None = Query(default=None),
) -> list[SurpriseContributionOut]:
    rows = csv_store.read_surprise_contributions(settings.data_repo_path)
    if start_year is not None:
        rows = [r for r in rows if r.year >= start_year]
    if end_year is not None:
        rows = [r for r in rows if r.year <= end_year]
    return [
        SurpriseContributionOut(
            id=r.id, year=r.year, amount=r.amount, description=r.description
        )
        for r in sorted(rows, key=lambda r: r.year)
    ]


@router.post(
    "/surprise-contributions",
    response_model=SurpriseContributionOut,
    status_code=201,
    dependencies=[Depends(require_forecast_branch)],
)
def create_surprise_contribution(
    payload: SurpriseContributionIn,
) -> SurpriseContributionOut:
    rows = csv_store.read_surprise_contributions(settings.data_repo_path)
    new_row = SurpriseContribution(
        id=csv_store.new_id(),
        year=payload.year,
        amount=payload.amount,
        description=payload.description,
    )
    rows.append(new_row)
    csv_store.write_surprise_contributions(settings.data_repo_path, rows)
    autosave_service.notify_change()
    return SurpriseContributionOut(
        id=new_row.id, year=new_row.year, amount=new_row.amount, description=new_row.description
    )


@router.delete(
    "/surprise-contributions/{contribution_id}",
    status_code=204,
    dependencies=[Depends(require_forecast_branch)],
)
def delete_surprise_contribution(contribution_id: str) -> None:
    rows = csv_store.read_surprise_contributions(settings.data_repo_path)
    remaining = [r for r in rows if r.id != contribution_id]
    if len(remaining) == len(rows):
        raise HTTPException(status_code=404, detail="Surprise contribution not found")
    csv_store.write_surprise_contributions(settings.data_repo_path, remaining)
    autosave_service.notify_change()
