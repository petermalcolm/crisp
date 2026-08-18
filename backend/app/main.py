from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import branches, categories, components, parameters, projections
from app.config import settings
from app.data import git_ops


@asynccontextmanager
async def lifespan(app: FastAPI):
    # If the server was killed mid-debounce, commit whatever was pending on
    # startup so no edits are silently lost.
    try:
        if git_ops.is_dirty(settings.data_repo_path):
            git_ops.commit_all(settings.data_repo_path, "Recovered autosave")
    except git_ops.GitOpsError:
        pass
    yield


app = FastAPI(title="CRISP API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(components.router)
app.include_router(projections.router)
app.include_router(parameters.router)
app.include_router(branches.router)
app.include_router(categories.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
