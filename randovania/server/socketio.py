from __future__ import annotations

import typing
from contextlib import asynccontextmanager
from functools import partial
from typing import TYPE_CHECKING, Concatenate, Protocol, Self, overload

from prometheus_client import Gauge
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


class ServerEventHandler[**P, RetT](Protocol):
    message: str

    async def __call__(self, sa: ServerApp, sid: str, *args: P.args, **kwargs: P.kwargs) -> RetT: ...

    def call_server(
        self,
        network_client: NetworkClient,
        namespace: str | None = None,
        handle_invalid_session: bool = True,
    ) -> AsyncCallable[P, RetT]:
        """
        Returns an async callable which, when called and awaited, uses the `NetworkClient` to call
        this function on the server, and returns the result.
        """


def server_event_handler[**P, RetT](
    message: str,
) -> Callable[[AsyncCallable[Concatenate[ServerApp, str, P], RetT]], ServerEventHandler[P, RetT]]:
    """
    Transforms a function into a `ServerEventHandler` so that it can be registered via
    `ServerApp.on()` or called from the client using `fn.server_call()`.
    """

    def decorator(fn: AsyncCallable[Concatenate[ServerApp, str, P], RetT]) -> ServerEventHandler[P, RetT]:
        handler = typing.cast("ServerEventHandler[P, RetT]", fn)
        handler.message = message

        def call_server(
            network_client: NetworkClient,
            namespace: str | None = None,
            handle_invalid_session: bool = True,
        ) -> AsyncCallable[P, RetT]:
            async def inner(*args: P.args, **kwargs: P.kwargs) -> RetT:
                data = typing.cast("tuple[SioDataType, ...]", args)
                result = await network_client.server_call(
                    handler.message, data, namespace=namespace, handle_invalid_session=handle_invalid_session
                )
                return typing.cast("RetT", result)

            return inner

        handler.call_server = call_server  # type: ignore[method-assign]

        return handler

    return decorator


class ClientEventHandler[**P]:
    name: str
    message: str

    def __init__(self, fn: AsyncCallable[Concatenate[NetworkClient, P], None], message: str) -> None:
        self.fn = fn
        self.message = message

    @overload
    def __get__(self, obj: NetworkClient, owner: type[NetworkClient] | None = None) -> AsyncCallable[P, None]: ...
    @overload
    def __get__(self, obj: None, owner: type[NetworkClient] | None = None) -> Self: ...

    def __get__(
        self, obj: NetworkClient | None, owner: type[NetworkClient] | None = None
    ) -> AsyncCallable[P, None] | Self:
        if obj is not None:
            return partial(self.fn, obj)
        return self

    def __set_name__(self, owner: type[NetworkClient], name: str) -> None:
        self.name = name
        owner._event_handlers += (self,)

    def emit(
        self,
        sa: ServerApp,
        to: str | None = None,
        room: str | None = None,
        namespace: str | None = None,
    ) -> AsyncCallable[P, None]:
        """ """

        async def inner(*args: P.args, **kwargs: P.kwargs) -> None:
            data = typing.cast("tuple[SioDataType, ...]", args)
            await sa.sio.emit(self.message, data, to=to, room=room, namespace=namespace)

        return inner


def client_event_handler[**P](
    message: str,
) -> Callable[[AsyncCallable[Concatenate[NetworkClient, P], None]], ClientEventHandler[P]]:
    def decorator(fn: AsyncCallable[Concatenate[NetworkClient, P], None]) -> ClientEventHandler[P]:
        return ClientEventHandler(fn, message)

    return decorator
