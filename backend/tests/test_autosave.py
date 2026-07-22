import time

from app.config import settings
from app.data import git_ops
from app.services.autosave import AutosaveService


def test_flush_commits_immediately_with_no_pending_timer(bare_git_repo, monkeypatch):
    monkeypatch.setattr(settings, "data_repo_path", bare_git_repo)
    service = AutosaveService()

    (bare_git_repo / "components.csv").write_text("changed\n")
    service.flush()

    assert git_ops.is_dirty(bare_git_repo) is False


def test_notify_change_commits_after_debounce_window(bare_git_repo, monkeypatch):
    monkeypatch.setattr(settings, "data_repo_path", bare_git_repo)
    monkeypatch.setattr(settings, "autosave_debounce_seconds", 0.05)
    service = AutosaveService()

    (bare_git_repo / "components.csv").write_text("changed\n")
    service.notify_change()

    assert git_ops.is_dirty(bare_git_repo) is True  # not committed yet
    time.sleep(0.2)
    assert git_ops.is_dirty(bare_git_repo) is False  # committed by the timer


def test_notify_change_debounces_rapid_edits_into_one_commit(bare_git_repo, monkeypatch):
    monkeypatch.setattr(settings, "data_repo_path", bare_git_repo)
    monkeypatch.setattr(settings, "autosave_debounce_seconds", 0.1)
    service = AutosaveService()

    for i in range(3):
        (bare_git_repo / "components.csv").write_text(f"edit {i}\n")
        service.notify_change()
        time.sleep(0.03)  # faster than the debounce window

    time.sleep(0.2)
    assert git_ops.is_dirty(bare_git_repo) is False

    import subprocess

    log = subprocess.run(
        ["git", "log", "--oneline", "main"],
        cwd=bare_git_repo,
        capture_output=True,
        text=True,
    ).stdout
    assert len(log.strip().splitlines()) == 2  # initial commit + one autosave
    assert (bare_git_repo / "components.csv").read_text() == "edit 2\n"


def test_flush_cancels_pending_timer_and_commits_now(bare_git_repo, monkeypatch):
    monkeypatch.setattr(settings, "data_repo_path", bare_git_repo)
    monkeypatch.setattr(settings, "autosave_debounce_seconds", 5)
    service = AutosaveService()

    (bare_git_repo / "components.csv").write_text("changed\n")
    service.notify_change()
    service.flush()

    assert git_ops.is_dirty(bare_git_repo) is False
