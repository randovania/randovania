from __future__ import annotations

import dataclasses
import datetime

from randovania.bitpacking.json_dataclass import JsonDataclass


@dataclasses.dataclass(frozen=True)
class AuditEntry(JsonDataclass):
    """A single entry of the audit log for a session or room"""

    user: str
    message: str
    time: datetime.datetime
