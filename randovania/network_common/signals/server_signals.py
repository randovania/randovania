from __future__ import annotations

import typing
from collections.abc import Sequence
from typing import TYPE_CHECKING, Annotated, Any, Never

from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.layout.layout_description import LayoutDescription
from randovania.network_common.async_race_room import (
    AsyncRaceEntryData,
    AsyncRaceRoomAdminData,
    AsyncRaceRoomEntry,
    AsyncRaceRoomListEntry,
    AsyncRaceSettings,
    RaceRoomLeaderboard,
)
from randovania.network_common.audit import AuditEntry
from randovania.network_common.multiplayer_session import MultiplayerSessionEntry, MultiplayerSessionListEntry
from randovania.network_common.signals.common import TypedBytes, TypedJsonObject, args_to_sio_data
from randovania.network_common.world_sync import ServerSyncRequest, ServerSyncResponse

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Concatenate

    from randovania.lib.type_lib import AsyncCallable
    from randovania.network_client.network_client import NetworkClient
    from randovania.server.server_app import ServerApp

type ServerEventCallback[**P, RetT] = AsyncCallable[Concatenate[ServerApp, str, P], RetT]


class ServerSignal[**P, RetT]:
    def __init__(self, fn: ServerEventCallback[P, RetT], message: str):
        self.fn = fn
        self.message = message

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Never:
        raise TypeError(
            f"Cannot call ServerSignal {self.fn.__name__} directly. "
            f"Did you mean to call {self.fn.__name__}.call_server() instead?"
        )

    def call_server(
        self,
        network_client: NetworkClient,
        namespace: str | None = None,
        handle_invalid_session: bool = True,
    ) -> AsyncCallable[P, RetT]:
        """
        Returns an async callable which, when called and awaited, uses the `NetworkClient` to call
        this function on the server, and returns the result. Provides full typing support,
        so it's preferable over using `NetworkClient.server_call()` directly.
        """

        async def inner(*args: P.args, **kwargs: P.kwargs) -> RetT:
            result = await network_client.server_call(
                self.message,
                args_to_sio_data(*args),
                namespace=namespace,
                handle_invalid_session=handle_invalid_session,
            )
            return typing.cast("RetT", result)

        return inner

    def register(
        self,
        sa: ServerApp,
        callback: ServerEventCallback[P, RetT],
        *,
        namespace: str | None = None,
        with_header_check: bool = False,
    ) -> AsyncCallable[Concatenate[str, P], dict | dict[str, RetT]]:
        """
        Registers the given callback with the ServerApp's SIO server on this signal's message.

        Using this function allows checking that the signature of the registered callback
        if compatible with this signal's expected signature.
        """
        return sa.on(self.message, callback, namespace, with_header_check=with_header_check)


def server_signal[**P, RetT](
    message: str,
) -> Callable[[ServerEventCallback[P, RetT]], ServerSignal[P, RetT]]:
    """
    Transforms a function into a `ServerEventHandler` for fully typed-checked calls from the client.

    Can be registered with a callback with `signal.register()` or
    called from the client using `signal.call_server()`.

    Example usage::

        @server_signal("multiplayer_list_sessions")
        async def ListSessions(sa: ServerApp: sid: str, limit: int | None) -> Sequence[dict]:
            raise NotImplementedError

        async def list_sessions(sa: ServerApp, sid: str, limit: int | None) -> Sequence[dict]:
            return [{"number": i} for i in range(limit if limit is not None else 100)]

        ListSessions.register(ServerApp(), list_sessions)

        result = await list_sessions.call_server(NetworkClient())(2)

        # prints "[{'number': 0}, {'number': 1}, {'number': 2}]"
        print(result)
    """

    def decorator(fn: AsyncCallable[Concatenate[ServerApp, str, P], RetT]) -> ServerSignal[P, RetT]:
        return ServerSignal(fn, message)

    return decorator


@server_signal("get_sid")
async def GetSid(
    sa: ServerApp,
    sid: str,
) -> str:
    raise NotImplementedError


async def get_sid(sa: ServerApp, sid: str) -> str:
    return sid


@server_signal("restore_user_session")
async def RestoreUserSession(
    sa: ServerApp,
    sid: str,
    encrypted_session: bytes,
    _old_session_id: None = None,
) -> dict:
    raise NotImplementedError


@server_signal("logout")
async def Logout(
    sa: ServerApp,
    sid: str,
) -> None:
    raise NotImplementedError


class Multiplayer:
    @server_signal("multiplayer_admin_session")
    @staticmethod
    async def AdminSession(
        sa: ServerApp,
        sid: str,
        session_id: int,
        action: str,
        *args: Any,
    ) -> Any:
        raise NotImplementedError

    @server_signal("multiplayer_admin_player")
    @staticmethod
    async def AdminPlayer(
        sa: ServerApp,
        sid: str,
        session_id: int,
        user_id: int,
        action: str,
        *args: Any,
    ) -> Any:
        raise NotImplementedError

    @server_signal("multiplayer_list_sessions")
    @staticmethod
    async def ListSessions(
        sa: ServerApp,
        sid: str,
        limit: int | None,
    ) -> Sequence[TypedJsonObject[MultiplayerSessionListEntry]]:
        raise NotImplementedError

    @server_signal("multiplayer_join_session")
    @staticmethod
    async def JoinSession(
        sa: ServerApp,
        sid: str,
        session_id: int,
        password: str | None,
    ) -> TypedJsonObject[MultiplayerSessionEntry]:
        raise NotImplementedError

    @server_signal("multiplayer_listen_to_session")
    @staticmethod
    async def ListenToSession(
        sa: ServerApp,
        sid: str,
        session_id: int,
        listen: bool,
    ) -> None:
        raise NotImplementedError

    @server_signal("multiplayer_request_session_update")
    @staticmethod
    async def RequestSessionUpdate(
        sa: ServerApp,
        sid: str,
        session_id: int,
    ) -> None:
        raise NotImplementedError

    @server_signal("multiplayer_watch_inventory")
    @staticmethod
    async def WatchInventory(
        sa: ServerApp,
        sid: str,
        raw_world_uid: str,
        user_id: int,
        watch: bool,
        binary: bool,
    ) -> None:
        raise NotImplementedError

    @server_signal("multiplayer_world_sync")
    @staticmethod
    async def WorldSync(
        sa: ServerApp,
        sid: str,
        raw_request: TypedBytes[ServerSyncRequest],
    ) -> TypedBytes[ServerSyncResponse]:
        raise NotImplementedError


class AsyncRace:
    @server_signal("async_race_list_rooms")
    @staticmethod
    async def ListRooms(
        sa: ServerApp,
        sid: str,
        limit: int | None,
    ) -> Sequence[TypedJsonObject[AsyncRaceRoomListEntry]]:
        raise NotImplementedError

    @server_signal("async_race_create_room")
    @staticmethod
    async def CreateRoom(
        sa: ServerApp,
        sid: str,
        layout_bin: TypedBytes[LayoutDescription],
        settings_json: TypedJsonObject[AsyncRaceSettings],
    ) -> TypedJsonObject[AsyncRaceRoomEntry]:
        raise NotImplementedError

    @server_signal("async_race_change_room_settings")
    @staticmethod
    async def ChangeRoomSettings(
        sa: ServerApp,
        sid: str,
        room_id: int,
        settings_json: TypedJsonObject[AsyncRaceSettings],
    ) -> TypedJsonObject[AsyncRaceRoomEntry]:
        raise NotImplementedError

    @server_signal("async_race_listen_to_room")
    @staticmethod
    async def ListenToRoom(sa: ServerApp, sid: str, room_id: int, listen: bool) -> None: ...

    @server_signal("async_race_get_room")
    @staticmethod
    async def GetRoom(
        sa: ServerApp,
        sid: str,
        room_id: int,
        password: str | None,
    ) -> TypedJsonObject[AsyncRaceRoomEntry]:
        raise NotImplementedError

    @server_signal("async_race_refresh_room")
    @staticmethod
    async def RefreshRoom(
        sa: ServerApp,
        sid: str,
        room_id: int,
        auth_token: str,
    ) -> TypedJsonObject[AsyncRaceRoomEntry]:
        raise NotImplementedError

    @server_signal("async_race_get_leaderboard")
    @staticmethod
    async def GetLeaderboard(
        sa: ServerApp,
        sid: str,
        room_id: int,
        auth_token: str,
    ) -> TypedJsonObject[RaceRoomLeaderboard]:
        raise NotImplementedError

    @server_signal("async_race_get_layout")
    @staticmethod
    async def GetLayout(
        sa: ServerApp,
        sid: str,
        room_id: int,
        auth_token: str,
    ) -> TypedBytes[LayoutDescription]:
        raise NotImplementedError

    @server_signal("async_race_get_audit_log")
    @staticmethod
    async def GetAuditLog(
        sa: ServerApp, sid: str, room_id: int, auth_token: str
    ) -> Sequence[TypedJsonObject[AuditEntry]]:
        raise NotImplementedError

    @server_signal("async_race_admin_get_admin_data")
    @staticmethod
    async def AdminGetAdminData(
        sa: ServerApp,
        sid: str,
        room_id: int,
    ) -> TypedJsonObject[AsyncRaceRoomAdminData]:
        raise NotImplementedError

    @server_signal("async_race_admin_update_entries")
    @staticmethod
    async def AdminUpdateEntries(
        sa: ServerApp,
        sid: str,
        room_id: int,
        raw_new_entries: Sequence[TypedJsonObject[AsyncRaceEntryData]],
    ) -> TypedJsonObject[AsyncRaceRoomEntry]:
        raise NotImplementedError

    @server_signal("async_race_join_and_export")
    @staticmethod
    async def JoinAndExport(
        sa: ServerApp,
        sid: str,
        room_id: int,
        auth_token: str,
        cosmetic_json: TypedJsonObject[BaseCosmeticPatches],
    ) -> dict:
        raise NotImplementedError

    @server_signal("async_race_change_state")
    @staticmethod
    async def ChangeState(
        sa: ServerApp,
        sid: str,
        room_id: int,
        new_state: str,
    ) -> TypedJsonObject[AsyncRaceRoomEntry]:
        raise NotImplementedError

    @server_signal("async_race_get_own_proof")
    @staticmethod
    async def GetOwnProof(
        sa: ServerApp,
        sid: str,
        room_id: int,
    ) -> tuple[Annotated[str, "submission notes"], Annotated[str, "proof url"]]:
        raise NotImplementedError

    @server_signal("async_race_submit_proof")
    @staticmethod
    async def SubmitProof(
        sa: ServerApp,
        sid: str,
        room_id: int,
        submission_notes: str,
        proof_url: str,
    ) -> None:
        raise NotImplementedError

    @server_signal("async_race_get_livesplit_url")
    @staticmethod
    async def GetLivesplitUrl(
        sa: ServerApp,
        sid: str,
        room_id: int,
    ) -> str:
        raise NotImplementedError
