from __future__ import annotations

import typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from typing import Any

    from socketio import AsyncClient

    from randovania.server.server_app import AsyncCallable, ServerApp


type SioDataType = str | bytes | Mapping[str, SioDataType] | Sequence[SioDataType]


def _args_to_sio_data(*args: Any) -> SioDataType | tuple[SioDataType, ...]:
    if len(args) == 1:
        return typing.cast("SioDataType", args[0])
    else:
        return typing.cast("tuple[SioDataType, ...]", args)


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


@client_signal("user_session_update")
async def USER_SESSION_UPDATE(new_session: dict) -> None: ...


@client_signal("multiplayer_session_meta_update")
async def SESSION_META_UPDATE(data: dict) -> None: ...


@client_signal("multiplayer_session_actions_update")
async def SESSION_ACTIONS_UPDATE(data: bytes) -> None: ...


@client_signal("multiplayer_session_audit_update")
async def SESSION_AUDIT_UPDATE(data: bytes) -> None: ...


@client_signal("world_pickups_update")
async def WORLD_PICKUPS_UPDATE(data: dict) -> None: ...


@client_signal("multiplayer_json_inventory")
async def WORLD_JSON_INVENTORY(*args: Any, **kwargs: Any) -> None: ...


@client_signal("multiplayer_binary_inventory")
async def WORLD_BINARY_INVENTORY(entry_id: str, user_id: int, raw_inventory: bytes) -> None: ...


@client_signal("async_race_room_update")
async def ASYNC_RACE_ROOM_UPDATE(data: dict) -> None: ...
