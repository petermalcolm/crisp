import json
from pathlib import Path


def _report_settings_path(repo_path: Path) -> Path:
    return repo_path / "report_settings.json"


def read_report_settings(repo_path: Path) -> dict:
    """Raw report settings; {} if the file doesn't exist yet. Raises
    ValueError if the file exists but isn't a JSON object."""
    path = _report_settings_path(repo_path)
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("report_settings.json must contain a JSON object")
    return data


def write_report_settings(repo_path: Path, data: dict) -> None:
    _report_settings_path(repo_path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    )
