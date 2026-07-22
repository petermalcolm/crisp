from datetime import date

from app.config import settings
from app.core.calc.sticky import resolve_sticky_series
from app.models import SurpriseContribution, YearParameterRow


def _explicit_map(rows: list[YearParameterRow], field: str) -> dict[int, float | None]:
    return {row.year: getattr(row, field) for row in rows}


def resolve_base_year(
    rows: list[YearParameterRow],
) -> tuple[int | None, float | None]:
    """The base year is the year an explicit current_reserve_balance is set.
    If set on more than one row (a data-entry mistake), the latest wins."""
    anchored_rows = [r for r in rows if r.current_reserve_balance is not None]
    if not anchored_rows:
        return None, None
    latest = max(anchored_rows, key=lambda r: r.year)
    return latest.year, latest.current_reserve_balance


def resolve_rate_series(
    rows: list[YearParameterRow], field: str, start_year: int, end_year: int
) -> dict[int, float]:
    """Flat carry-forward resolution for a rate-like field, defaulting
    un-set years with no prior anchor to 0.0."""
    explicit = _explicit_map(rows, field)
    resolved = resolve_sticky_series(explicit, start_year, end_year, mode="flat")
    return {year: (r.value or 0.0) for year, r in resolved.items()}


def resolve_contribution_series(
    rows: list[YearParameterRow], start_year: int, end_year: int
) -> dict[int, float]:
    """Growth carry-forward resolution for total_annual_contribution,
    compounded by the resolved yoy_contribution_change_pct series."""
    yoy = resolve_rate_series(
        rows, "yoy_contribution_change_pct", start_year, end_year
    )
    explicit = _explicit_map(rows, "total_annual_contribution")
    resolved = resolve_sticky_series(
        explicit, start_year, end_year, mode="growth", growth_rate_by_year=yoy
    )
    return {year: (r.value or 0.0) for year, r in resolved.items()}


def aggregate_surprise_by_year(
    rows: list[SurpriseContribution], start_year: int, end_year: int
) -> dict[int, float]:
    totals = {year: 0.0 for year in range(start_year, end_year + 1)}
    for row in rows:
        if start_year <= row.year <= end_year:
            totals[row.year] = totals.get(row.year, 0.0) + row.amount
    return totals


def resolve_effective_base_year(rows: list[YearParameterRow]) -> int:
    """base_year for display/calc purposes: the explicit anchor year if one
    is set, otherwise today's calendar year (so actual-vs-estimate styling
    still works before any reserve balance has been entered)."""
    base_year, _ = resolve_base_year(rows)
    return base_year if base_year is not None else date.today().year


def resolve_horizon(
    base_year: int, start_year: int | None, end_year: int | None
) -> tuple[int, int]:
    resolved_start = (
        start_year
        if start_year is not None
        else base_year - settings.default_horizon_years_back
    )
    resolved_end = (
        end_year
        if end_year is not None
        else base_year + settings.default_horizon_years_forward
    )
    return resolved_start, resolved_end
