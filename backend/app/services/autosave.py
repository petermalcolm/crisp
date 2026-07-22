import threading

from app.config import settings
from app.data import git_ops


class AutosaveService:
    """Debounced auto-commit for edits on a forecast branch. Every mutating
    request should call notify_change() after writing; a commit fires a few
    seconds after the last change. Call flush() before any branch checkout
    so pending edits never bleed across branches."""

    def __init__(self) -> None:
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def notify_change(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(
                settings.autosave_debounce_seconds, self._commit
            )
            self._timer.daemon = True
            self._timer.start()

    def flush(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
        self._commit()

    def _commit(self) -> None:
        git_ops.commit_all(settings.data_repo_path, "Autosave")


autosave_service = AutosaveService()
