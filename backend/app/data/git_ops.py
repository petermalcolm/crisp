import subprocess
from pathlib import Path


class GitOpsError(Exception):
    pass


class BranchExistsError(GitOpsError):
    pass


class BranchNotFoundError(GitOpsError):
    pass


class MergeConflictError(GitOpsError):
    pass


def _run(repo_path: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )


def current_branch(repo_path: Path) -> str:
    result = _run(repo_path, "rev-parse", "--abbrev-ref", "HEAD")
    if result.returncode != 0:
        raise GitOpsError(result.stderr.strip())
    return result.stdout.strip()


def list_branches(repo_path: Path) -> list[str]:
    result = _run(repo_path, "branch", "--format=%(refname:short)")
    if result.returncode != 0:
        raise GitOpsError(result.stderr.strip())
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_dirty(repo_path: Path) -> bool:
    result = _run(repo_path, "status", "--porcelain")
    if result.returncode != 0:
        raise GitOpsError(result.stderr.strip())
    return bool(result.stdout.strip())


def commit_all(repo_path: Path, message: str) -> bool:
    """Stage and commit everything. Returns False (no-op) if there was
    nothing to commit."""
    add_result = _run(repo_path, "add", "-A")
    if add_result.returncode != 0:
        raise GitOpsError(add_result.stderr.strip())
    if not is_dirty(repo_path):
        return False
    commit_result = _run(repo_path, "commit", "-m", message)
    if commit_result.returncode != 0:
        raise GitOpsError(commit_result.stderr.strip())
    return True


def create_branch(repo_path: Path, name: str, from_branch: str = "main") -> None:
    if name in list_branches(repo_path):
        raise BranchExistsError(f"Branch '{name}' already exists")
    result = _run(repo_path, "checkout", "-b", name, from_branch)
    if result.returncode != 0:
        raise GitOpsError(result.stderr.strip())


def checkout(repo_path: Path, name: str) -> None:
    if name not in list_branches(repo_path):
        raise BranchNotFoundError(f"Branch '{name}' not found")
    result = _run(repo_path, "checkout", name)
    if result.returncode != 0:
        raise GitOpsError(result.stderr.strip())


def squash_merge_to_main(
    repo_path: Path, source_branch: str, message: str | None = None
) -> None:
    if source_branch not in list_branches(repo_path):
        raise BranchNotFoundError(f"Branch '{source_branch}' not found")
    if source_branch == "main":
        raise GitOpsError("Cannot merge main into itself")

    if current_branch(repo_path) != "main":
        checkout(repo_path, "main")

    merge_result = _run(repo_path, "merge", "--squash", source_branch)
    if merge_result.returncode != 0:
        # `git merge --squash` never sets MERGE_HEAD, so `git merge --abort`
        # is a no-op here; a hard reset is what actually clears the
        # conflicted/staged state it leaves behind.
        _run(repo_path, "reset", "--hard", "HEAD")
        raise MergeConflictError(
            f"Merge conflict squashing '{source_branch}' into main; aborted cleanly. "
            "Recommended fix: recreate the forecast branch from the latest main."
        )

    if not is_dirty(repo_path):
        raise GitOpsError(
            f"Nothing to merge — '{source_branch}' has no changes relative to main"
        )

    commit_message = message or f"Merge forecast branch '{source_branch}' into main"
    commit_result = _run(repo_path, "commit", "-m", commit_message)
    if commit_result.returncode != 0:
        raise GitOpsError(commit_result.stderr.strip())
