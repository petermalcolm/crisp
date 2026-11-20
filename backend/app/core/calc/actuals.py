from dataclasses import dataclass

from app.core.calc.costs import Component, inflate_cost, is_scheduled_occurrence
from app.models import ActualCost


@dataclass(frozen=True)
class RecordingPlan:
    year_estimate: float
    backfill: list[tuple[int, float]]
    new_initial_year: int


def plan_recording(
    component: Component,
    year: int,
    existing_actuals: list[ActualCost],
    base_year: int,
    inflation_by_year: dict[int, float],
) -> RecordingPlan:
    """What recording an actual for `year` will do: the estimate shown for
    that year, earlier scheduled occurrences that never got an actual (to be
    backfilled at their estimates), and the component's next initial_year."""
    recorded = {a.year for a in existing_actuals if a.component_id == component.id}
    backfill = [
        (
            y,
            inflate_cost(component.estimated_cost, base_year, y, inflation_by_year),
        )
        for y in range(component.initial_year, year, component.expected_life_years)
        if y not in recorded
    ]
    return RecordingPlan(
        year_estimate=inflate_cost(
            component.estimated_cost, base_year, year, inflation_by_year
        ),
        backfill=backfill,
        new_initial_year=year + component.expected_life_years,
    )


def is_recordable(
    component: Component, year: int, existing_actuals: list[ActualCost]
) -> bool:
    already = any(
        a.component_id == component.id and a.year == year for a in existing_actuals
    )
    return is_scheduled_occurrence(component, year) and not already


def base_year_estimate(
    actual_cost: float,
    year: int,
    base_year: int,
    inflation_by_year: dict[int, float],
) -> float:
    """Express an actual spent in `year` in base-year dollars, the unit
    components.csv stores estimates in, so inflating it forward to the next
    occurrence reproduces the actual plus inflation since it was spent."""
    return actual_cost / inflate_cost(1.0, base_year, year, inflation_by_year)


def schedule_revert_year(
    component: Component, deleted_year: int, other_actual_years: set[int]
) -> int | None:
    """When an actual is removed, the year the component's schedule should
    return to, or None to leave it alone. Only reverts when the actual sat
    in an unbroken chain of actuals leading up to initial_year, so a
    schedule the user pushed out by hand is never overridden."""
    life = component.expected_life_years
    gap = component.initial_year - deleted_year
    if gap <= 0 or gap % life:
        return None
    for y in range(deleted_year + life, component.initial_year, life):
        if y not in other_actual_years:
            return None
    return deleted_year
