from dataclasses import dataclass

from app.models import ActualCost


@dataclass(frozen=True)
class Component:
    id: str
    name: str
    estimated_cost: float
    initial_year: int
    expected_life_years: int
    category_code: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class CostLineItem:
    component_id: str
    component_name: str
    cost: float
    is_actual: bool = False
    comment: str | None = None


@dataclass(frozen=True)
class YearCostRow:
    year: int
    is_estimate: bool
    line_items: list[CostLineItem]
    total: float


def get_component_occurrences(
    component: Component, start_year: int, end_year: int
) -> list[int]:
    """Years in [start_year, end_year] the component recurs, starting at
    initial_year and repeating every expected_life_years thereafter."""
    life = component.expected_life_years
    year = component.initial_year
    if year < start_year:
        periods_missed = -(-(start_year - year) // life)  # ceil division
        year += periods_missed * life
    occurrences = []
    while year <= end_year:
        occurrences.append(year)
        year += life
    return occurrences


def is_scheduled_occurrence(component: Component, year: int) -> bool:
    return (
        year >= component.initial_year
        and (year - component.initial_year) % component.expected_life_years == 0
    )


def component_age_at_start_of_year(
    component: Component, year: int, actual_years: tuple[int, ...] | list[int] = ()
) -> int:
    """Effective age of a component at the *start* of the given year, in years.

    This is the convention reserve studies (and lenders) use for the Fully
    Funded Balance:

    * If the component has already been replaced (on schedule, or by a
      recorded actual) before this year, age is the time since the latest
      such replacement. A replacement happening *during* ``year`` is not yet
      counted, so a component due this year is at its full useful life.
    * If it has not been replaced yet, age is useful life minus remaining
      life, clamped to [0, useful life]: a component due in 3 years with a
      20-year life is already 17 years old. An actual recorded for a later
      year counts as the upcoming replacement (recording an actual pushes
      ``initial_year`` out by one life, which would otherwise erase the wear
      accrued before it).
    """
    life = component.expected_life_years
    initial = component.initial_year

    prior = [y for y in actual_years if y <= year - 1]
    if initial <= year - 1:
        prior.append(initial + ((year - 1 - initial) // life) * life)
    if prior:
        return year - max(prior)

    due = min([initial, *[y for y in actual_years if y >= year]])
    return max(0, min(life, life - (due - year)))


def inflate_cost(
    base_cost: float,
    base_year: int,
    target_year: int,
    inflation_by_year: dict[int, float],
) -> float:
    """Compound base_cost forward from base_year to target_year using the
    per-year inflation rate. No adjustment for target_year <= base_year."""
    if target_year <= base_year:
        return base_cost
    cost = base_cost
    for year in range(base_year + 1, target_year + 1):
        cost *= 1 + inflation_by_year.get(year, 0.0)
    return cost


def project_costs(
    components: list[Component],
    start_year: int,
    end_year: int,
    base_year: int,
    inflation_by_year: dict[int, float],
    actual_costs: list[ActualCost] | None = None,
) -> list[YearCostRow]:
    """Per-year cost lines. A recorded actual replaces the inflated estimate
    for its component-year, and an actual in a year with no scheduled
    occurrence still shows up (the schedule moves on after an actual is
    recorded, but the spend itself must stay visible)."""
    actual_by_key = {(a.component_id, a.year): a for a in actual_costs or []}
    line_items_by_year: dict[int, list[CostLineItem]] = {
        year: [] for year in range(start_year, end_year + 1)
    }
    for component in components:
        years = set(get_component_occurrences(component, start_year, end_year))
        years.update(
            a.year
            for (cid, _), a in actual_by_key.items()
            if cid == component.id and start_year <= a.year <= end_year
        )
        for year in sorted(years):
            actual = actual_by_key.get((component.id, year))
            if actual is not None:
                item = CostLineItem(
                    component.id,
                    component.name,
                    actual.cost,
                    is_actual=True,
                    comment=actual.comment,
                )
            else:
                inflated = inflate_cost(
                    component.estimated_cost, base_year, year, inflation_by_year
                )
                item = CostLineItem(component.id, component.name, inflated)
            line_items_by_year[year].append(item)

    rows = []
    for year in range(start_year, end_year + 1):
        items = line_items_by_year[year]
        rows.append(
            YearCostRow(
                year=year,
                is_estimate=year > base_year,
                line_items=items,
                total=sum(item.cost for item in items),
            )
        )
    return rows
