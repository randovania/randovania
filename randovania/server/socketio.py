from __future__ import annotations

from collections.abc import Sequence
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from prometheus_client import Gauge
from socketio.exceptions import ConnectionRefusedError
from socketio_handler import BaseSocketHandler, SocketManager, register_handler

import randovania
from randovania.lib.json_lib import JsonObject_RO, JsonType_RO
from randovania.server import client_check

if TYPE_CHECKING:
    from randovania.server.server_app import Lifespan, RdvFastAPI, ServerApp

SioDataType = str | bytes | JsonObject_RO | Sequence[JsonType_RO]
EventHandlerReturnType = SioDataType | tuple[SioDataType, ...] | None


@asynccontextmanager
async def fastapi_socketio_lifespan(_app: RdvFastAPI) -> Lifespan[SocketManager]:
    async with SocketManager(socketio_path=None) as manager:
        manager.mount_to_app(_app, _app.sa.configuration["server_config"].get("socketio_path", "/socket.io/"))
        register_handler()(get_socket_handler(_app.sa))
        manager.register_handlers()

        yield manager


def get_socket_handler(sa: ServerApp) -> type[BaseSocketHandler]:
    from randovania.server.multiplayer import world_api

    version_checking = client_check.ClientVersionCheck(sa.configuration["server_config"]["client_version_checking"])

    connected_clients = Gauge("connected_clients", "How many clients are connected right now.")

    class RdvSocketHandler(BaseSocketHandler):
        def on_connect(self, sid: str, environ: dict) -> None:
            try:
                if "HTTP_X_RANDOVANIA_VERSION" not in environ:
                    raise ConnectionRefusedError("unknown client version")

                client_app_version = environ["HTTP_X_RANDOVANIA_VERSION"]
                error_message = client_check.check_client_version(
                    version_checking, client_app_version, randovania.VERSION
                )
                if error_message is None and not randovania.is_dev_version():
                    error_message = client_check.check_client_headers(sa.expected_headers, environ)

                forwarded_for = environ.get("HTTP_X_FORWARDED_FOR")

                if error_message is not None:
                    sa.logger.info(
                        f"Client {sid} at {environ['REMOTE_ADDR']} ({forwarded_for}) with "
                        f"version {client_app_version} tried to connect, but refused with {error_message}."
                    )
                    raise ConnectionRefusedError(error_message)

                connected_clients.inc()

                sa.logger.info(
                    f"Client {sid} at {environ['REMOTE_ADDR']} ({forwarded_for}) with "
                    f"version {client_app_version} connected."
                )

            except ConnectionRefusedError:
                # Do not wrap if it's already a ConnectionRefusedError
                raise

            except Exception as e:
                sa.logger.exception(f"Unknown exception when testing the client's headers: {e}")
                raise ConnectionRefusedError(f"Unable to check if request is valid: {e}.\nPlease file a bug report.")

        async def on_disconnect(self, sid: str) -> None:
            sa.logger.info(f"Client at {sa.current_client_ip(sid)} disconnected.")
            connected_clients.dec()

            session = await sa.sio.get_session(sid)
            await world_api.report_disconnect(sa, session)

    return RdvSocketHandler
