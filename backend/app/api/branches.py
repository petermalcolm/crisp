from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.data import git_ops
from app.services.autosave import autosave_service

router = APIRouter(prefix="/api/branches", tags=["branches"])


class BranchesOut(BaseModel):
    current: str
    branches: list[str]


class CreateBranchIn(BaseModel):
    name: str


class CheckoutBranchIn(BaseModel):
    name: str


class MergeBranchIn(BaseModel):
    message: str | None = None


def _state() -> BranchesOut:
    return BranchesOut(
        current=git_ops.current_branch(settings.data_repo_path),
        branches=git_ops.list_branches(settings.data_repo_path),
    )


@router.get("", response_model=BranchesOut)
def get_branches() -> BranchesOut:
    return _state()


@router.post("", response_model=BranchesOut, status_code=201)
def create_branch(payload: CreateBranchIn) -> BranchesOut:
    autosave_service.flush()
    try:
        git_ops.create_branch(settings.data_repo_path, payload.name)
    except git_ops.BranchExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except git_ops.GitOpsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _state()


@router.post("/checkout", response_model=BranchesOut)
def checkout_branch(payload: CheckoutBranchIn) -> BranchesOut:
    autosave_service.flush()
    try:
        git_ops.checkout(settings.data_repo_path, payload.name)
    except git_ops.BranchNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except git_ops.GitOpsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _state()


@router.post("/{branch_name}/merge", response_model=BranchesOut)
def merge_branch(branch_name: str, payload: MergeBranchIn) -> BranchesOut:
    autosave_service.flush()
    try:
        git_ops.squash_merge_to_main(
            settings.data_repo_path, branch_name, payload.message
        )
    except git_ops.BranchNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except git_ops.MergeConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except git_ops.GitOpsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _state()
