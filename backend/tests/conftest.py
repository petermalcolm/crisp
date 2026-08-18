import subprocess
from pathlib import Path

import pytest


def _git(repo_path: Path, *args: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git", *args], cwd=repo_path, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result


@pytest.fixture
def bare_git_repo(tmp_path) -> Path:
    """A git-initialized data repo on main with empty CSVs committed, but
    no forecast branch checked out yet — for testing branch operations
    themselves and the main-branch edit lock."""
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")

    (tmp_path / "components.csv").write_text(
        "id,name,estimated_cost,initial_year,expected_life_years,category_code,notes\n"
    )
    (tmp_path / "year_parameters.csv").write_text(
        "year,num_contributors,inflation_rate,interest_rate,"
        "yoy_contribution_change_pct,total_annual_contribution,"
        "current_reserve_balance,notes\n"
    )
    (tmp_path / "surprise_contributions.csv").write_text(
        "id,year,amount,description\n"
    )
    (tmp_path / "categories.csv").write_text(
        "code,name\n"
        "CH,Common House\n"
        "IN,Infrastructure\n"
        "OS,Other Structures\n"
        "OB,Outbuildings\n"
        "PO,Pool\n"
    )

    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "Initial data")

    return tmp_path


@pytest.fixture
def git_data_repo(bare_git_repo) -> Path:
    """Same as bare_git_repo, but already on a forecast branch — the
    common case for tests exercising CRUD/mutation endpoints, which are
    disallowed on main."""
    _git(bare_git_repo, "checkout", "-b", "forecast")
    return bare_git_repo
