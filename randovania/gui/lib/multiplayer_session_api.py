from __future__ import annotations

import functools
import typing
import uuid

from PySide6 import QtWidgets, QtCore

from randovania.gui.lib import async_dialog
from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common.multiplayer_session import (
    MultiplayerSessionEntry, MultiplayerSessionActions,
    MultiplayerSessionAuditLog, WorldUserInventory
)
from randovania.network_client.network_client import UnableToConnect
from randovania.network_common import admin_actions
from randovania.network_common.error import (
    InvalidAction, ServerError, NotLoggedIn, NotAuthorizedForAction,
    UserNotAuthorized, UnsupportedClient, RequestTimeout
)

Param = typing.ParamSpec("Param")
RetType = typing.TypeVar("RetType")
OriginalFunc = typing.Callable[Param, RetType]


def handle_network_errors(fn: typing.Callable[typing.Concatenate[MultiplayerSessionApi, Param], RetType]
                          ) -> typing.Callable[Param, RetType]:
    @functools.wraps(fn)
    async def wrapper(self: MultiplayerSessionApi, *args, **kwargs):
        parent = self.widget_root
        try:
            return await fn(self, *args, **kwargs)

        except InvalidAction as e:
            await async_dialog.warning(parent, "Invalid action", f"{e}")

        except ServerError:
            await async_dialog.warning(parent, "Server error",
                                       "An error occurred on the server while processing your request.")

        except NotLoggedIn:
            await async_dialog.warning(parent, "Unauthenticated",
                                       "You must be logged in.")

        except NotAuthorizedForAction:
            await async_dialog.warning(parent, "Unauthorized",
                                       "You're not authorized to perform that action.")

        except UserNotAuthorized:
            await async_dialog.warning(
                parent, "Unauthorized",
                "You're not authorized to use this build.\nPlease check #dev-builds for more details.",
            )

        except UnsupportedClient as e:
            s = e.detail.replace('\n', '<br />')
            await async_dialog.warning(
                parent, "Unsupported client",
                s,
            )

        except UnableToConnect as e:
            s = e.reason.replace('\n', '<br />')
            await async_dialog.warning(parent, "Connection Error",
                                       f"<b>Unable to connect to the server:</b><br /><br />{s}")

        except RequestTimeout as e:
            await async_dialog.warning(parent, "Connection Error",
                                       f"<b>Timeout while communicating with the server:</b><br /><br />{e}"
                                       f"<br />Further attempts will wait for longer.")

        return None

    return wrapper


class MultiplayerSessionApi(QtCore.QObject):
    MetaUpdated = QtCore.Signal(MultiplayerSessionEntry)
    ActionsUpdated = QtCore.Signal(MultiplayerSessionActions)
    AuditLogUpdated = QtCore.Signal(MultiplayerSessionAuditLog)
    InventoryUpdated = QtCore.Signal(WorldUserInventory)

    current_entry: MultiplayerSessionEntry
    widget_root: QtWidgets.QWidget | None

    def __init__(self, network_client: QtNetworkClient, entry: MultiplayerSessionEntry):
        super().__init__()
        self.widget_root = None
        self.network_client = network_client
        self.current_entry = entry

    async def session_admin_global(self, action: admin_actions.SessionAdminGlobalAction, arg):
        try:
            self.widget_root.setEnabled(False)
            return await self.network_client.server_call(
                "multiplayer_admin_session",
                (self.current_entry.id, action.value, arg))
        finally:
            self.widget_root.setEnabled(True)

    async def session_admin_player(self, user_id: int, action: admin_actions.SessionAdminUserAction, arg):
        try:
            self.widget_root.setEnabled(False)
            return await self.network_client.server_call(
                "multiplayer_admin_player",
                (self.current_entry.id, user_id, action.value, arg)
            )
        finally:
            self.widget_root.setEnabled(True)

    @handle_network_errors
    async def replace_preset_for(self, world_uid: uuid.UUID, preset: VersionedPreset):
        await self.session_admin_global(
            admin_actions.SessionAdminGlobalAction.CHANGE_WORLD,
            (str(world_uid), preset.as_json),
        )

    @handle_network_errors
    async def claim_world_for(self, world_uid: uuid.UUID, owner: int):
        await self.session_admin_player(
            owner, admin_actions.SessionAdminUserAction.CLAIM,
            str(world_uid)
        )

    @handle_network_errors
    async def unclaim_world(self, world_uid: uuid.UUID, owner: int):
        await self.session_admin_player(
            owner, admin_actions.SessionAdminUserAction.UNCLAIM,
            str(world_uid)
        )

    @handle_network_errors
    async def rename_world(self, world_uid: uuid.UUID, new_name: str):
        await self.session_admin_global(
            admin_actions.SessionAdminGlobalAction.RENAME_WORLD,
            (str(world_uid), new_name),
        )

    @handle_network_errors
    async def delete_world(self, world_uid: uuid.UUID):
        await self.session_admin_global(
            admin_actions.SessionAdminGlobalAction.DELETE_WORLD,
            str(world_uid),
        )

    @handle_network_errors
    async def create_new_world(self, name: str, preset: VersionedPreset, owner: int):
        await self.session_admin_player(
            owner, admin_actions.SessionAdminUserAction.CREATE_WORLD_FOR,
            (name, preset.as_json)
        )

    @handle_network_errors
    async def create_patcher_file(self, world_uid: uuid.UUID, cosmetic_patches: dict) -> dict:
        return await self.session_admin_global(
            admin_actions.SessionAdminGlobalAction.CREATE_PATCHER_FILE,
            (str(world_uid), cosmetic_patches)
        )

    @handle_network_errors
    async def kick_player(self, kick_id: int):
        await self.session_admin_player(
            kick_id, admin_actions.SessionAdminUserAction.KICK,
            None,
        )

    @handle_network_errors
    async def switch_admin(self, new_admin_id: int):
        await self.session_admin_player(
            new_admin_id, admin_actions.SessionAdminUserAction.SWITCH_ADMIN,
            None,
        )

    async def request_session_update(self):
        await self.network_client.server_call(
            "multiplayer_request_session_update",
            self.current_entry.id
        )
