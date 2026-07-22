from fastapi import HTTPException

from app.config import settings
from app.data import git_ops


def require_forecast_branch() -> None:
    """Guard for mutating endpoints: main is for reviewing the current
    state of the world, not editing. Changes require an active forecast
    branch."""
    branch = git_ops.current_branch(settings.data_repo_path)
    if branch == "main":
        raise HTTPException(
            status_code=403,
            detail="Editing is disabled on main. Switch to a forecast branch to make changes.",
        )
