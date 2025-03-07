from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.server.async_race import room_api

if TYPE_CHECKING:
    from randovania.server.server_app import ServerApp


def setup_app(sa: ServerApp) -> None:
    room_api.setup_app(sa)
