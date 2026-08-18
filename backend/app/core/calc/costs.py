from dataclasses import dataclass


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


def component_age_in_year(component: Component, year: int) -> int | None:
    """Age of the component in the given year, resetting to 0 in a
    replacement year. None if the year precedes the component's initial_year."""
    if year < component.initial_year:
        return None
    return (year - component.initial_year) % component.expected_life_years


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
) -> list[YearCostRow]:
    line_items_by_year: dict[int, list[CostLineItem]] = {
        year: [] for year in range(start_year, end_year + 1)
    }
    for component in components:
        for year in get_component_occurrences(component, start_year, end_year):
            inflated = inflate_cost(
                component.estimated_cost, base_year, year, inflation_by_year
            )
            line_items_by_year[year].append(
                CostLineItem(component.id, component.name, inflated)
            )

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
