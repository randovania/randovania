from __future__ import annotations

import datetime  # noqa: TC003 no type checking box because of pydantic model

from randovania.lib.json_base_model import JsonBaseModel


class AuditEntry(JsonBaseModel):
    """A single entry of the audit log for a session or room"""

    user: str
    message: str
    time: datetime.datetime
