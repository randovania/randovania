from __future__ import annotations

import typing
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Concatenate

from prometheus_client import Gauge
from socketio import AsyncClient
from socketio.exceptions import ConnectionRefusedError
from socketio_handler import BaseSocketHandler, SocketManager, register_handler

import randovania
from randovania.server import client_check

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from randovania.network_client.network_client import NetworkClient
    from randovania.server.server_app import AsyncCallable, Lifespan, RdvFastAPI, ServerApp

type SioDataType = str | bytes | Mapping[str, SioDataType] | Sequence[SioDataType]
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


def _args_to_sio_data(*args: Any) -> SioDataType | tuple[SioDataType, ...]:
    if len(args) == 1:
        return typing.cast("SioDataType", args[0])
    else:
        return typing.cast("tuple[SioDataType, ...]", args)


class ServerEventHandler[**P, RetT]:
    def __init__(self, fn: AsyncCallable[Concatenate[ServerApp, str, P], RetT], message: str):
        self.fn = fn
        self.message = message

    async def __call__(self, sa: ServerApp, sid: str, *args: P.args, **kwargs: P.kwargs) -> RetT:
        return await self.fn(sa, sid, *args, **kwargs)

    def call_server(
        self,
        network_client: NetworkClient,
        namespace: str | None = None,
        handle_invalid_session: bool = True,
    ) -> AsyncCallable[P, RetT]:
        """
        Returns an async callable which, when called and awaited, uses the `NetworkClient` to call
        this function on the server, and returns the result. Provides full typing support,
        so it's preferable to using `NetworkClient.server_call()` directly.
        """

        async def inner(*args: P.args, **kwargs: P.kwargs) -> RetT:
            result = await network_client.server_call(
                self.message,
                _args_to_sio_data(*args),
                namespace=namespace,
                handle_invalid_session=handle_invalid_session,
            )
            return typing.cast("RetT", result)

        return inner


def server_event_handler[**P, RetT](
    message: str,
) -> Callable[[AsyncCallable[Concatenate[ServerApp, str, P], RetT]], ServerEventHandler[P, RetT]]:
    """
    Transforms a function into a `ServerEventHandler` so that it can be registered via
    `ServerApp.on()` or called from the client using `fn.server_call()`.

    Example usage::

        @server_event_handler("multiplayer_list_sessions")
        async def list_sessions(sa: ServerApp, sid: str, limit: int | None) -> list[dict]:
            return [{"number": i} for i in range(limit if limit is not None else 100)]

        result = await list_sessions.call_server(NetworkClient())(2)

        # prints "[{'number': 0}, {'number': 1}, {'number': 2}]"
        print(result)
    """

    def decorator(fn: AsyncCallable[Concatenate[ServerApp, str, P], RetT]) -> ServerEventHandler[P, RetT]:
        return ServerEventHandler(fn, message)

    return decorator


class ClientSignal[**P]:
    def __init__(self, fn: AsyncCallable[P, None], message: str):
        self.fn = fn
        self.message = message

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        return await self.fn(*args, **kwargs)

    def emit(
        self,
        sa: ServerApp,
        to: str | None = None,
        room: str | None = None,
        namespace: str | None = None,
    ) -> AsyncCallable[P, None]:
        """
        Returns an async callable which, when called and awaited, uses the `ServerApp`
        to emit this signal. Provides full typing support, so it's preferred over directly
        calling `sa.sio.emit()`.
        """

        async def inner(*args: P.args, **kwargs: P.kwargs) -> None:
            await sa.sio.emit(self.message, _args_to_sio_data(*args), to=to, room=room, namespace=namespace)

        return inner

    def register(self, sio: AsyncClient, callback: AsyncCallable[P, None]) -> None:
        """
        Registers the given callback with the SIO client on this signal's message.

        Using this function allows checking that the signature of the registered callback
        is compatible with this signal's expected signature.
        """
        sio.on(self.message, callback)


def client_signal[**P](message: str) -> Callable[[AsyncCallable[P, None]], ClientSignal[P]]:
    """
    Transforms the callable into a `ClientSignal` for fully type-checked signal emission from the server.

    Example usage::

        @client_signal("multiplayer_binary_inventory")
        async def WORLD_BINARY_INVENTORY(entry_id: str, user_id: int, raw_inventory: bytes) -> None: ...

        class NetworkClient:
            def __init__(self, sio: AsyncClient):
                self.sio = sio

                WORLD_BINARY_INVENTORY.register(self.sio, self._on_world_user_inventory_raw)

            def _on_world_user_inventory_raw(self, entry_id: str, user_id: int, raw_inventory: bytes) -> None:
                print(entry_id, user_id, raw_inventory)

        # prints "'entry', 1234, b'4321'"
        await WORLD_BINARY_INVENTORY.emit(ServerApp())("entry", 1234, b"4321")

    """

    def decorator(fn: AsyncCallable[P, None]) -> ClientSignal[P]:
        return ClientSignal(fn, message)

    return decorator
