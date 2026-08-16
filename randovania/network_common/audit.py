from __future__ import annotations

import datetime

from randovania.lib.json_base_model import JsonBaseModel


class AuditEntry(JsonBaseModel):
    """A single entry of the audit log for a session or room"""

    user: str
    message: str
    time: datetime.datetime
