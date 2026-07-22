from dataclasses import dataclass


@dataclass(frozen=True)
class YearParameterRow:
    year: int
    num_contributors: int | None = None
    inflation_rate: float | None = None
    interest_rate: float | None = None
    yoy_contribution_change_pct: float | None = None
    total_annual_contribution: float | None = None
    current_reserve_balance: float | None = None
    notes: str | None = None


@dataclass(frozen=True)
class SurpriseContribution:
    id: str
    year: int
    amount: float
    description: str | None = None
