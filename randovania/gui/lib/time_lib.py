from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    import datetime


def format_elapsed_time(time: datetime.timedelta) -> str:
    """How long a race run took, as `1h 2min 3s`."""
    seconds = int(time.total_seconds())
    minutes, seconds = seconds // 60, seconds % 60
    hours, minutes = minutes // 60, minutes % 60

    return f"{hours}h {minutes}min {seconds}s"
