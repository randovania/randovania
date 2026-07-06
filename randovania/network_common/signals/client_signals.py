from __future__ import annotations

from typing import TYPE_CHECKING, Never

from randovania.network_common.async_race_room import AsyncRaceRoomEntry
from randovania.network_common.multiplayer_session import (
    MultiplayerSessionActions,
    MultiplayerSessionAuditLog,
    MultiplayerSessionEntry,
    MultiplayerWorldPickups,
)
from randovania.network_common.remote_inventory import RemoteInventory
from randovania.network_common.signals.common import TypedBytes, TypedJsonObject, args_to_sio_data

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from socketio import AsyncClient

    from randovania.lib.type_lib import AsyncCallable
    from randovania.server.server_app import ServerApp


class ClientSignal[**P]:
    def __init__(self, fn: AsyncCallable[P, None], message: str):
        self.fn = fn
        self.message = message

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Never:
        raise TypeError(
            f"Cannot call ClientSignal {self.fn.__name__} directly. "
            f"Did you mean to call {self.fn.__name__}.emit() instead?"
        )

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
            await sa.sio.emit(
                self.message,
                args_to_sio_data(*args),  # type: ignore[arg-type]
                to=to,
                room=room,
                namespace=namespace,
            )

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

    Can be registered with a callback with `signal.register()` or
    called from the server using `signal.emit()`.

    Example usage::

        @client_signal("multiplayer_binary_inventory")
        async def WorldBinaryInventory(entry_id: str, user_id: int, raw_inventory: bytes) -> None: ...

        class NetworkClient:
            def __init__(self, sio: AsyncClient):
                self.sio = sio

                WorldBinaryInventory.register(self.sio, self._on_world_user_inventory_raw)

            def _on_world_user_inventory_raw(self, entry_id: str, user_id: int, raw_inventory: bytes) -> None:
                print(entry_id, user_id, raw_inventory)

        # prints "'entry', 1234, b'4321'"
        await WorldBinaryInventory.emit(ServerApp())("entry", 1234, b"4321")

    """

    def decorator(fn: AsyncCallable[P, None]) -> ClientSignal[P]:
        return ClientSignal(fn, message)

    return decorator


@client_signal("user_session_update")
async def UserSessionUpdate(new_session: dict) -> None: ...


@client_signal("multiplayer_session_meta_update")
async def SessionMetaUpdate(data: TypedJsonObject[MultiplayerSessionEntry]) -> None: ...


@client_signal("multiplayer_session_actions_update")
async def SessionActionsUpdate(data: TypedBytes[MultiplayerSessionActions]) -> None: ...


@client_signal("multiplayer_session_audit_update")
async def SessionAuditUpdate(data: TypedBytes[MultiplayerSessionAuditLog]) -> None: ...


@client_signal("world_pickups_update")
async def WorldPickupsUpdate(data: TypedJsonObject[MultiplayerWorldPickups]) -> None: ...


@client_signal("multiplayer_json_inventory")
async def WorldJsonInventory(*args: Any, **kwargs: Any) -> None: ...


@client_signal("multiplayer_binary_inventory")
async def WorldBinaryInventory(entry_id: str, user_id: int, raw_inventory: TypedBytes[RemoteInventory]) -> None: ...


@client_signal("async_race_room_update")
async def AsyncRaceRoomUpdate(data: TypedJsonObject[AsyncRaceRoomEntry]) -> None: ...
