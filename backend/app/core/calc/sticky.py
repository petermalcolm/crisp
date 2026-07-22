from typing import Literal, NamedTuple

StickyMode = Literal["flat", "growth"]


class Resolved(NamedTuple):
    value: float | None
    is_explicit: bool
    source_year: int | None


def resolve_sticky_series(
    explicit_values: dict[int, float | None],
    start_year: int,
    end_year: int,
    mode: StickyMode,
    growth_rate_by_year: dict[int, float] | None = None,
) -> dict[int, Resolved]:
    """Resolve a per-year value series with carry-forward for un-set years.

    mode="flat": a blank year repeats the last explicit value unchanged.
    mode="growth": a blank year compounds the last resolved value by
        growth_rate_by_year[year] (0 if that year has no rate).
    """
    if mode == "growth" and growth_rate_by_year is None:
        raise ValueError("growth_rate_by_year is required when mode='growth'")

    result: dict[int, Resolved] = {}
    carry_value: float | None = None
    carry_source: int | None = None

    for year in range(start_year, end_year + 1):
        explicit = explicit_values.get(year)
        if explicit is not None:
            result[year] = Resolved(explicit, True, year)
            carry_value = explicit
            carry_source = year
            continue

        if carry_value is None:
            result[year] = Resolved(None, False, None)
            continue

        if mode == "growth":
            rate = (growth_rate_by_year or {}).get(year, 0.0)
            carry_value = carry_value * (1 + rate)

        result[year] = Resolved(carry_value, False, carry_source)

    return result
