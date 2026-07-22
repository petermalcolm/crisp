import pytest

from app.data import git_ops


def test_current_branch_and_list_branches(bare_git_repo):
    assert git_ops.current_branch(bare_git_repo) == "main"
    assert git_ops.list_branches(bare_git_repo) == ["main"]


def test_create_branch_checks_it_out(bare_git_repo):
    git_ops.create_branch(bare_git_repo, "forecast-2027")
    assert git_ops.current_branch(bare_git_repo) == "forecast-2027"
    assert set(git_ops.list_branches(bare_git_repo)) == {"main", "forecast-2027"}


def test_create_branch_that_already_exists_raises(bare_git_repo):
    git_ops.create_branch(bare_git_repo, "forecast-2027")
    git_ops.checkout(bare_git_repo, "main")
    with pytest.raises(git_ops.BranchExistsError):
        git_ops.create_branch(bare_git_repo, "forecast-2027")


def test_checkout_missing_branch_raises(bare_git_repo):
    with pytest.raises(git_ops.BranchNotFoundError):
        git_ops.checkout(bare_git_repo, "does-not-exist")


def test_commit_all_returns_false_when_nothing_to_commit(bare_git_repo):
    assert git_ops.commit_all(bare_git_repo, "no-op") is False


def test_commit_all_stages_and_commits_changes(bare_git_repo):
    (bare_git_repo / "components.csv").write_text(
        "id,name,estimated_cost,initial_year,expected_life_years,notes\n"
        "roof,Roof,100000,2026,15,\n"
    )
    assert git_ops.is_dirty(bare_git_repo) is True
    assert git_ops.commit_all(bare_git_repo, "Add roof") is True
    assert git_ops.is_dirty(bare_git_repo) is False


def test_squash_merge_lands_as_single_commit_on_main(bare_git_repo):
    git_ops.create_branch(bare_git_repo, "forecast")
    (bare_git_repo / "components.csv").write_text(
        "id,name,estimated_cost,initial_year,expected_life_years,notes\n"
        "roof,Roof,100000,2026,15,\n"
    )
    git_ops.commit_all(bare_git_repo, "Add roof on forecast")
    (bare_git_repo / "components.csv").write_text(
        "id,name,estimated_cost,initial_year,expected_life_years,notes\n"
        "roof,Roof,100000,2026,15,\n"
        "pool,Pool,20000,2028,10,\n"
    )
    git_ops.commit_all(bare_git_repo, "Add pool on forecast")

    git_ops.squash_merge_to_main(bare_git_repo, "forecast")

    assert git_ops.current_branch(bare_git_repo) == "main"
    content = (bare_git_repo / "components.csv").read_text()
    assert "roof" in content and "pool" in content

    import subprocess

    log = subprocess.run(
        ["git", "log", "--oneline", "main"],
        cwd=bare_git_repo,
        capture_output=True,
        text=True,
    ).stdout
    # 1 initial commit + 1 squash commit == 2 lines, not 3 (the two
    # forecast-branch commits were squashed into one)
    assert len(log.strip().splitlines()) == 2


def test_squash_merge_missing_branch_raises(bare_git_repo):
    with pytest.raises(git_ops.BranchNotFoundError):
        git_ops.squash_merge_to_main(bare_git_repo, "does-not-exist")


def test_squash_merge_conflict_aborts_cleanly(bare_git_repo):
    git_ops.create_branch(bare_git_repo, "forecast")
    (bare_git_repo / "components.csv").write_text("forecast version\n")
    git_ops.commit_all(bare_git_repo, "Forecast edit")

    git_ops.checkout(bare_git_repo, "main")
    (bare_git_repo / "components.csv").write_text("main version\n")
    git_ops.commit_all(bare_git_repo, "Main edit")

    with pytest.raises(git_ops.MergeConflictError):
        git_ops.squash_merge_to_main(bare_git_repo, "forecast")

    # repo left clean, not mid-conflict
    assert git_ops.is_dirty(bare_git_repo) is False
    assert git_ops.current_branch(bare_git_repo) == "main"
    assert (bare_git_repo / "components.csv").read_text() == "main version\n"
