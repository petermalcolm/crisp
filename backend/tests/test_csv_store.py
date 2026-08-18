from pathlib import Path

from app.core.calc.costs import Component
from app.data import csv_store
from app.models import Category, SurpriseContribution, YearParameterRow


def _init_repo(tmp_path: Path) -> Path:
    (tmp_path / "components.csv").write_text(
        "id,name,estimated_cost,initial_year,expected_life_years,category_code,notes\n"
    )
    (tmp_path / "year_parameters.csv").write_text(
        "year,num_contributors,inflation_rate,interest_rate,"
        "yoy_contribution_change_pct,total_annual_contribution,"
        "current_reserve_balance,notes\n"
    )
    (tmp_path / "surprise_contributions.csv").write_text("id,year,amount,description\n")
    return tmp_path


def test_components_round_trip_sorted_by_id(tmp_path):
    repo = _init_repo(tmp_path)
    components = [
        Component(
            id="b-roof", name="Roof", estimated_cost=100_000.0,
            initial_year=2026, expected_life_years=15,
        ),
        Component(
            id="a-pool", name="Pool", estimated_cost=20_000.0,
            initial_year=2028, expected_life_years=10,
            category_code="PO", notes="resurface",
        ),
    ]
    csv_store.write_components(repo, components)
    loaded = csv_store.read_components(repo)

    assert [c.id for c in loaded] == ["a-pool", "b-roof"]
    assert loaded[0].notes == "resurface"
    assert loaded[0].category_code == "PO"
    assert loaded[1].name == "Roof"
    assert loaded[1].estimated_cost == 100_000.0
    assert loaded[1].category_code is None


def test_categories_round_trip_sorted_by_code(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "categories.csv").write_text("code,name\n")
    categories = [
        Category(code="PO", name="Pool"),
        Category(code="CH", name="Common House"),
    ]
    csv_store.write_categories(repo, categories)
    loaded = csv_store.read_categories(repo)

    assert [c.code for c in loaded] == ["CH", "PO"]
    assert loaded[0].name == "Common House"


def test_read_categories_missing_file_returns_empty_list(tmp_path):
    repo = _init_repo(tmp_path)
    assert csv_store.read_categories(repo) == []


def test_year_parameters_round_trip_preserves_blanks(tmp_path):
    repo = _init_repo(tmp_path)
    rows = [
        YearParameterRow(year=2027, inflation_rate=0.03),
        YearParameterRow(
            year=2026,
            num_contributors=50,
            inflation_rate=0.025,
            current_reserve_balance=10_000.0,
        ),
    ]
    csv_store.write_year_parameters(repo, rows)
    loaded = csv_store.read_year_parameters(repo)

    assert [r.year for r in loaded] == [2026, 2027]
    assert loaded[0].num_contributors == 50
    assert loaded[0].current_reserve_balance == 10_000.0
    assert loaded[1].num_contributors is None
    assert loaded[1].current_reserve_balance is None
    assert round(loaded[1].inflation_rate, 3) == 0.03


def test_surprise_contributions_round_trip(tmp_path):
    repo = _init_repo(tmp_path)
    rows = [
        SurpriseContribution(id="x", year=2030, amount=5_000.0, description="insurance payout"),
        SurpriseContribution(id="y", year=2029, amount=1_200.5),
    ]
    csv_store.write_surprise_contributions(repo, rows)
    loaded = csv_store.read_surprise_contributions(repo)

    assert [r.year for r in loaded] == [2029, 2030]
    assert loaded[1].description == "insurance payout"
    assert loaded[0].description is None
    assert loaded[0].amount == 1_200.5


def test_reading_header_only_csvs_returns_empty_lists(tmp_path):
    repo = _init_repo(tmp_path)
    assert csv_store.read_components(repo) == []
    assert csv_store.read_year_parameters(repo) == []
    assert csv_store.read_surprise_contributions(repo) == []
