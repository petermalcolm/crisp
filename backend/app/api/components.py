from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import require_forecast_branch
from app.config import settings
from app.core.calc.costs import Component
from app.data import csv_store
from app.services.autosave import autosave_service

router = APIRouter(prefix="/api/components", tags=["components"])


class ComponentIn(BaseModel):
    name: str = Field(min_length=1)
    estimated_cost: float = Field(gt=0)
    initial_year: int
    expected_life_years: int = Field(gt=0)
    category_code: str | None = None
    notes: str | None = None


class ComponentOut(ComponentIn):
    id: str


def _to_out(component: Component) -> ComponentOut:
    return ComponentOut(
        id=component.id,
        name=component.name,
        estimated_cost=component.estimated_cost,
        initial_year=component.initial_year,
        expected_life_years=component.expected_life_years,
        category_code=component.category_code,
        notes=component.notes,
    )


def _validate_category_code(category_code: str | None) -> None:
    if category_code is None:
        return
    known_codes = {c.code for c in csv_store.read_categories(settings.data_repo_path)}
    if category_code not in known_codes:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown category_code '{category_code}'. See GET /api/categories.",
        )


@router.get("", response_model=list[ComponentOut])
def list_components() -> list[ComponentOut]:
    components = csv_store.read_components(settings.data_repo_path)
    return [_to_out(c) for c in sorted(components, key=lambda c: c.name.lower())]


@router.post(
    "",
    response_model=ComponentOut,
    status_code=201,
    dependencies=[Depends(require_forecast_branch)],
)
def create_component(payload: ComponentIn) -> ComponentOut:
    _validate_category_code(payload.category_code)
    components = csv_store.read_components(settings.data_repo_path)
    new_component = Component(
        id=csv_store.new_id(),
        name=payload.name,
        estimated_cost=payload.estimated_cost,
        initial_year=payload.initial_year,
        expected_life_years=payload.expected_life_years,
        category_code=payload.category_code,
        notes=payload.notes,
    )
    components.append(new_component)
    csv_store.write_components(settings.data_repo_path, components)
    autosave_service.notify_change()
    return _to_out(new_component)


@router.put(
    "/{component_id}",
    response_model=ComponentOut,
    dependencies=[Depends(require_forecast_branch)],
)
def update_component(component_id: str, payload: ComponentIn) -> ComponentOut:
    _validate_category_code(payload.category_code)
    components = csv_store.read_components(settings.data_repo_path)
    index = next((i for i, c in enumerate(components) if c.id == component_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Component not found")

    updated = Component(
        id=component_id,
        name=payload.name,
        estimated_cost=payload.estimated_cost,
        initial_year=payload.initial_year,
        expected_life_years=payload.expected_life_years,
        category_code=payload.category_code,
        notes=payload.notes,
    )
    components[index] = updated
    csv_store.write_components(settings.data_repo_path, components)
    autosave_service.notify_change()
    return _to_out(updated)


@router.delete(
    "/{component_id}",
    status_code=204,
    dependencies=[Depends(require_forecast_branch)],
)
def delete_component(component_id: str) -> None:
    components = csv_store.read_components(settings.data_repo_path)
    remaining = [c for c in components if c.id != component_id]
    if len(remaining) == len(components):
        raise HTTPException(status_code=404, detail="Component not found")
    csv_store.write_components(settings.data_repo_path, remaining)
    autosave_service.notify_change()
