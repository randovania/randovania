from __future__ import annotations


class AbortBackgroundTask(Exception):
    """Raised when the user requested a task to be cancelled."""
