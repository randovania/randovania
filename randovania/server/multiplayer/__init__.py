from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.server.multiplayer import session_admin, session_api, web_api, world_api

if TYPE_CHECKING:
    from randovania.server.server_app import ServerApp


def setup_app(sio: ServerApp):
    session_api.setup_app(sio)
    session_admin.setup_app(sio)
    web_api.setup_app(sio)
    world_api.setup_app(sio)
