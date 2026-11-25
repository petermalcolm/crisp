from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import ValidationError
from pydantic import BaseModel

from app.api.deps import require_forecast_branch
from app.config import settings
from app.core.calc.costs import get_component_occurrences
from app.core.calc.report import (
    Extreme,
    ProjectionSummary,
    build_projection_years,
    summarize_projection,
)
from app.data import csv_store, git_ops, json_store
from app.services.autosave import autosave_service
from app.services.projection import compute_ffb_projection

router = APIRouter(prefix="/api", tags=["report"])

DEFAULT_BASIS_STATEMENT = (
    "This report was prepared by the association's Board of Directors using the "
    "association's reserve planning model, which updates the independent reserve "
    "study referenced below with actual costs and current balances. It is a "
    "planning projection based on stated assumptions, not an audit, and actual "
    "costs and balances will differ."
)
DEFAULT_FINANCIAL_DISCLOSURES = "The association has no loans."
# Years in the window counted as near-term / mid-term; the rest are long-term.
NEAR_TERM_YEARS = 5
MID_TERM_YEARS = 15


# --- report settings -------------------------------------------------------


class Budget(BaseModel):
    """The adopted annual budget, split the way the board reports it."""

    year: int
    operating: float
    reserves: float


class ReportSettings(BaseModel):
    association_name: str = ""
    association_address: str = ""
    prepared_by: str = ""
    study_reference: str = ""
    basis_statement: str = DEFAULT_BASIS_STATEMENT
    financial_disclosures: str = DEFAULT_FINANCIAL_DISCLOSURES
    budget: Budget | None = None
    window_start: int | None = None  # defaults to the current year
    window_end: int | None = None  # defaults to start + 29 (a 30-year window)


def _read_report_settings() -> tuple[ReportSettings, str | None]:
    """Settings from report_settings.json, plus an error message if the file
    exists but can't be used (the defaults apply in that case)."""
    try:
        raw = json_store.read_report_settings(settings.data_repo_path)
        return ReportSettings(**raw), None
    except (ValueError, ValidationError) as exc:
        return ReportSettings(), f"report_settings.json could not be read: {exc}"


@router.get("/report-settings", response_model=ReportSettings)
def get_report_settings() -> ReportSettings:
    return _read_report_settings()[0]


@router.put(
    "/report-settings",
    response_model=ReportSettings,
    dependencies=[Depends(require_forecast_branch)],
)
def put_report_settings(payload: ReportSettings) -> ReportSettings:
    json_store.write_report_settings(
        settings.data_repo_path, payload.model_dump(mode="json")
    )
    autosave_service.notify_change()
    return _read_report_settings()[0]


# --- the report -------------------------------------------------------------


class ExtremeOut(BaseModel):
    value: float
    year: int


class SummaryOut(BaseModel):
    balance_min: ExtremeOut | None
    balance_max: ExtremeOut | None
    contribution_min: ExtremeOut | None
    contribution_max: ExtremeOut | None
    percent_funded_min: ExtremeOut | None
    percent_funded_max: ExtremeOut | None
    percent_funded_avg: float | None
    first_shortfall_year: int | None
    total_contributions: float
    total_special_contributions: float
    total_costs: float


class ProjectionYearOut(BaseModel):
    year: int
    start_balance: float | None
    interest: float | None
    contribution: float
    special_contribution: float
    costs: float
    end_balance: float | None
    ffb: float
    percent_funded: float | None
    inflation_rate: float
    interest_rate: float


class ScheduleItemOut(BaseModel):
    component_name: str
    category_code: str | None
    category_name: str | None
    cost: float
    is_actual: bool


class ScheduleYearOut(BaseModel):
    year: int
    term: str  # "near" | "mid" | "long"
    total: float
    items: list[ScheduleItemOut]


class CompletedProjectOut(BaseModel):
    year: int
    component_name: str
    category_name: str | None
    cost: float


class InventoryItemOut(BaseModel):
    component_name: str
    category_name: str | None
    estimated_cost: float  # in cost_base_year dollars
    expected_life_years: int
    next_year: int | None  # first scheduled replacement within the window
    occurrences_in_window: int


class MetaOut(BaseModel):
    generated_on: str
    branch: str
    data_commit: str | None
    is_draft: bool  # anything other than main is a scenario, not the record
    cost_base_year: int
    balance_year: int | None
    window_start: int
    window_end: int


class BudgetOut(BaseModel):
    year: int
    operating: float
    reserves: float
    total: float
    reserve_share: float  # reserves / total, 0.40 = 40%


class AtAGlanceOut(BaseModel):
    start_balance: float | None
    start_ffb: float
    start_percent_funded: float | None
    annual_contribution: float  # modelled contribution in the first year
    budget: BudgetOut | None


class WarningOut(BaseModel):
    code: str
    message: str


class ReportOut(BaseModel):
    meta: MetaOut
    settings: ReportSettings
    at_a_glance: AtAGlanceOut
    summary: SummaryOut
    projection: list[ProjectionYearOut]
    schedule: list[ScheduleYearOut]
    completed_projects: list[CompletedProjectOut]
    inventory: list[InventoryItemOut]
    warnings: list[WarningOut]


def _extreme_out(e: Extreme | None) -> ExtremeOut | None:
    return ExtremeOut(value=e.value, year=e.year) if e else None


def _summary_out(s: ProjectionSummary) -> SummaryOut:
    return SummaryOut(
        balance_min=_extreme_out(s.balance_min),
        balance_max=_extreme_out(s.balance_max),
        contribution_min=_extreme_out(s.contribution_min),
        contribution_max=_extreme_out(s.contribution_max),
        percent_funded_min=_extreme_out(s.percent_funded_min),
        percent_funded_max=_extreme_out(s.percent_funded_max),
        percent_funded_avg=s.percent_funded_avg,
        first_shortfall_year=s.first_shortfall_year,
        total_contributions=s.total_contributions,
        total_special_contributions=s.total_special_contributions,
        total_costs=s.total_costs,
    )


def _term(year: int, window_start: int) -> str:
    if year < window_start + NEAR_TERM_YEARS:
        return "near"
    if year < window_start + MID_TERM_YEARS:
        return "mid"
    return "long"


@router.get("/report", response_model=ReportOut)
def get_report(
    start_year: int | None = Query(default=None),
    end_year: int | None = Query(default=None),
) -> ReportOut:
    repo = settings.data_repo_path
    report_settings, settings_error = _read_report_settings()

    today_year = date.today().year
    window_start = (
        start_year
        if start_year is not None
        else report_settings.window_start
        if report_settings.window_start is not None
        else today_year
    )
    window_end = (
        end_year
        if end_year is not None
        else report_settings.window_end
        if report_settings.window_end is not None
        else window_start + 29
    )

    comp = compute_ffb_projection(window_start, window_end)
    categories = {c.code: c.name for c in csv_store.read_categories(repo)}
    components_by_id = {c.id: c for c in comp.components}

    years = build_projection_years(
        comp.rows,
        comp.inflation_by_year,
        comp.interest_by_year,
        comp.contribution_by_year,
        comp.surprise_by_year,
    )
    summary = summarize_projection(years)

    schedule = []
    for row in comp.cost_rows:
        if not (window_start <= row.year <= window_end) or not row.line_items:
            continue
        items = []
        for item in sorted(row.line_items, key=lambda i: -i.cost):
            component = components_by_id.get(item.component_id)
            code = component.category_code if component else None
            items.append(
                ScheduleItemOut(
                    component_name=item.component_name,
                    category_code=code,
                    category_name=categories.get(code) if code else None,
                    cost=item.cost,
                    is_actual=item.is_actual,
                )
            )
        schedule.append(
            ScheduleYearOut(
                year=row.year,
                term=_term(row.year, window_start),
                total=row.total,
                items=items,
            )
        )

    # Internal notes and actual-cost comments are deliberately left out of
    # everything below: this report is for outside readers.
    completed = []
    for actual in sorted(comp.actual_costs, key=lambda a: (-a.year, a.component_id)):
        component = components_by_id.get(actual.component_id)
        if component is None:
            continue
        completed.append(
            CompletedProjectOut(
                year=actual.year,
                component_name=component.name,
                category_name=categories.get(component.category_code or ""),
                cost=actual.cost,
            )
        )

    inventory = []
    for component in comp.components:
        occurrences = get_component_occurrences(component, window_start, window_end)
        inventory.append(
            InventoryItemOut(
                component_name=component.name,
                category_name=categories.get(component.category_code or ""),
                estimated_cost=component.estimated_cost,
                expected_life_years=component.expected_life_years,
                next_year=occurrences[0] if occurrences else None,
                occurrences_in_window=len(occurrences),
            )
        )
    inventory.sort(key=lambda i: (i.category_name or "", i.component_name))

    first = years[0] if years else None
    annual_contribution = first.contribution if first else 0.0
    budget = report_settings.budget
    budget_out = None
    if budget is not None:
        total = budget.operating + budget.reserves
        budget_out = BudgetOut(
            year=budget.year,
            operating=budget.operating,
            reserves=budget.reserves,
            total=total,
            reserve_share=budget.reserves / total if total else 0.0,
        )
    at_a_glance = AtAGlanceOut(
        start_balance=first.start_balance if first else None,
        start_ffb=first.ffb if first else 0.0,
        start_percent_funded=first.percent_funded if first else None,
        annual_contribution=annual_contribution,
        budget=budget_out,
    )

    branch = git_ops.current_branch(repo)
    warnings = []
    if branch != "main":
        warnings.append(
            WarningOut(
                code="not_main",
                message=f"Generated from forecast branch '{branch}', not main. "
                "This is a scenario, not the association's record.",
            )
        )
    if git_ops.is_dirty(repo):
        warnings.append(
            WarningOut(
                code="uncommitted",
                message="The data repo has uncommitted changes; the report may "
                "include edits that are not yet saved to a commit.",
            )
        )
    if comp.current_reserve_balance is None:
        warnings.append(
            WarningOut(
                code="no_balance",
                message="No reserve balance is set, so balances and percent "
                "funded cannot be computed.",
            )
        )
    if summary.first_shortfall_year is not None:
        warnings.append(
            WarningOut(
                code="shortfall",
                message=f"The projected reserve balance goes negative in "
                f"{summary.first_shortfall_year}.",
            )
        )
    if settings_error:
        warnings.append(WarningOut(code="bad_settings", message=settings_error))
    if budget is None:
        warnings.append(
            WarningOut(
                code="no_budget",
                message="The annual budget (operating and reserves) is not set "
                "in the report settings; the budget lines will be omitted.",
            )
        )
    else:
        modelled = comp.contribution_by_year.get(budget.year)
        if modelled is not None and abs(modelled - budget.reserves) > 1.0:
            warnings.append(
                WarningOut(
                    code="budget_mismatch",
                    message=f"The {budget.year} reserve budget "
                    f"(${budget.reserves:,.2f}) differs from the model's "
                    f"{budget.year} contribution (${modelled:,.2f}). Align them "
                    "on the Income/Expenses page or correct the budget.",
                )
            )
    if not report_settings.association_name:
        warnings.append(
            WarningOut(
                code="no_association_name",
                message="Association name is not set in the report settings.",
            )
        )

    return ReportOut(
        meta=MetaOut(
            generated_on=today_iso(),
            branch=branch,
            data_commit=git_ops.head_commit(repo),
            is_draft=branch != "main",
            cost_base_year=comp.base_year,
            balance_year=comp.anchor_year if comp.current_reserve_balance is not None else None,
            window_start=comp.start_year,
            window_end=comp.end_year,
        ),
        settings=report_settings,
        at_a_glance=at_a_glance,
        summary=_summary_out(summary),
        projection=[ProjectionYearOut(**vars(y)) for y in years],
        schedule=schedule,
        completed_projects=completed,
        inventory=inventory,
        warnings=warnings,
    )


def today_iso() -> str:
    return date.today().isoformat()
