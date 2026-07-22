import uuid
from pathlib import Path

import pandas as pd

from app.core.calc.costs import Component
from app.models import SurpriseContribution, YearParameterRow

COMPONENTS_COLUMNS = [
    "id",
    "name",
    "estimated_cost",
    "initial_year",
    "expected_life_years",
    "notes",
]
YEAR_PARAMETERS_COLUMNS = [
    "year",
    "num_contributors",
    "inflation_rate",
    "interest_rate",
    "yoy_contribution_change_pct",
    "total_annual_contribution",
    "current_reserve_balance",
    "notes",
]
SURPRISE_CONTRIBUTIONS_COLUMNS = ["id", "year", "amount", "description"]


def new_id() -> str:
    return str(uuid.uuid4())


def _components_path(repo_path: Path) -> Path:
    return repo_path / "components.csv"


def _year_parameters_path(repo_path: Path) -> Path:
    return repo_path / "year_parameters.csv"


def _surprise_contributions_path(repo_path: Path) -> Path:
    return repo_path / "surprise_contributions.csv"


def _opt_float(value) -> float | None:
    return None if pd.isna(value) else float(value)


def _opt_int(value) -> int | None:
    return None if pd.isna(value) else int(value)


def _opt_str(value) -> str | None:
    return None if pd.isna(value) or value == "" else str(value)


def read_components(repo_path: Path) -> list[Component]:
    df = pd.read_csv(_components_path(repo_path))
    return [
        Component(
            id=str(row["id"]),
            name=str(row["name"]),
            estimated_cost=float(row["estimated_cost"]),
            initial_year=int(row["initial_year"]),
            expected_life_years=int(row["expected_life_years"]),
            notes=_opt_str(row.get("notes")),
        )
        for _, row in df.iterrows()
    ]


def write_components(repo_path: Path, components: list[Component]) -> None:
    ordered = sorted(components, key=lambda c: c.id)
    df = pd.DataFrame(
        [
            {
                "id": c.id,
                "name": c.name,
                "estimated_cost": f"{c.estimated_cost:.2f}",
                "initial_year": c.initial_year,
                "expected_life_years": c.expected_life_years,
                "notes": c.notes or "",
            }
            for c in ordered
        ],
        columns=COMPONENTS_COLUMNS,
    )
    df.to_csv(_components_path(repo_path), index=False)


def read_year_parameters(repo_path: Path) -> list[YearParameterRow]:
    df = pd.read_csv(_year_parameters_path(repo_path))
    return [
        YearParameterRow(
            year=int(row["year"]),
            num_contributors=_opt_int(row.get("num_contributors")),
            inflation_rate=_opt_float(row.get("inflation_rate")),
            interest_rate=_opt_float(row.get("interest_rate")),
            yoy_contribution_change_pct=_opt_float(row.get("yoy_contribution_change_pct")),
            total_annual_contribution=_opt_float(row.get("total_annual_contribution")),
            current_reserve_balance=_opt_float(row.get("current_reserve_balance")),
            notes=_opt_str(row.get("notes")),
        )
        for _, row in df.iterrows()
    ]


def write_year_parameters(repo_path: Path, rows: list[YearParameterRow]) -> None:
    ordered = sorted(rows, key=lambda r: r.year)

    def fmt(value: float | None, decimals: int) -> str:
        return "" if value is None else f"{value:.{decimals}f}"

    df = pd.DataFrame(
        [
            {
                "year": r.year,
                "num_contributors": "" if r.num_contributors is None else r.num_contributors,
                "inflation_rate": fmt(r.inflation_rate, 6),
                "interest_rate": fmt(r.interest_rate, 6),
                "yoy_contribution_change_pct": fmt(r.yoy_contribution_change_pct, 6),
                "total_annual_contribution": fmt(r.total_annual_contribution, 2),
                "current_reserve_balance": fmt(r.current_reserve_balance, 2),
                "notes": r.notes or "",
            }
            for r in ordered
        ],
        columns=YEAR_PARAMETERS_COLUMNS,
    )
    df.to_csv(_year_parameters_path(repo_path), index=False)


def read_surprise_contributions(repo_path: Path) -> list[SurpriseContribution]:
    df = pd.read_csv(_surprise_contributions_path(repo_path))
    return [
        SurpriseContribution(
            id=str(row["id"]),
            year=int(row["year"]),
            amount=float(row["amount"]),
            description=_opt_str(row.get("description")),
        )
        for _, row in df.iterrows()
    ]


def write_surprise_contributions(
    repo_path: Path, rows: list[SurpriseContribution]
) -> None:
    ordered = sorted(rows, key=lambda r: (r.year, r.id))
    df = pd.DataFrame(
        [
            {
                "id": r.id,
                "year": r.year,
                "amount": f"{r.amount:.2f}",
                "description": r.description or "",
            }
            for r in ordered
        ],
        columns=SURPRISE_CONTRIBUTIONS_COLUMNS,
    )
    df.to_csv(_surprise_contributions_path(repo_path), index=False)
