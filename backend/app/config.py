from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_repo_path: Path = Path(__file__).resolve().parents[2] / "version-controlled-data"
    autosave_debounce_seconds: float = 5.0
    default_horizon_years_forward: int = 30
    default_horizon_years_back: int = 5
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
