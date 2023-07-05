from __future__ import annotations

import functools
import logging
import typing
import uuid

from PySide6 import QtWidgets, QtCore

from randovania.gui.lib import async_dialog
from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_client.network_client import UnableToConnect
from randovania.network_common import admin_actions, error

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

        except error.InvalidActionError as e:
            await async_dialog.warning(parent, "Invalid action", f"{e}")

        except error.ServerError:
            await async_dialog.warning(parent, "Server error",
                                       "An error occurred on the server while processing your request.")

        except error.NotLoggedInError:
            await async_dialog.warning(parent, "Unauthenticated",
                                       "You must be logged in.")

        except error.NotAuthorizedForActionError:
            await async_dialog.warning(parent, "Unauthorized",
                                       "You're not authorized to perform that action.")

        except error.UserNotAuthorizedToUseServerError:
            await async_dialog.warning(
                parent, "Unauthorized",
                "You're not authorized to use this build.\nPlease check #dev-builds for more details.",
            )

        except error.UnsupportedClientError as e:
            s = e.detail.replace('\n', '<br />')
            await async_dialog.warning(
                parent, "Unsupported client",
                s,
            )

        except UnableToConnect as e:
            s = e.reason.replace('\n', '<br />')
            await async_dialog.warning(parent, "Connection Error",
                                       f"<b>Unable to connect to the server:</b><br /><br />{s}")

        except error.RequestTimeoutError as e:
            await async_dialog.warning(parent, "Connection Error",
                                       f"<b>Timeout while communicating with the server:</b><br /><br />{e}"
                                       f"<br />Further attempts will wait for longer.")

        except error.WorldDoesNotExistError:
            await async_dialog.warning(
                parent, "World does not exist",
                "The world you tried to change does not exist. "
                "If this error keeps happening, please reopen the Window and/or Randovania."
            )

        return None

    return wrapper


class SessionIdLoggingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "session_id"):
            record.msg = f"[Session {record.session_id}] {record.msg}"
        return True


class SessionIdLoggerAdapter(logging.LoggerAdapter):
    def __init__(self, logger: logging.Logger, api: MultiplayerSessionApi):
        super().__init__(logger)
        self.api = api

    def process(self, msg, kwargs):
        kwargs["extra"] = {
            "session_id": self.api.current_session_id,
        }
        return msg, kwargs


_base_logger = logging.getLogger("MultiplayerSessionApi")
_base_logger.addFilter(SessionIdLoggingFilter())


class MultiplayerSessionApi(QtCore.QObject):
    current_session_id: int
    widget_root: QtWidgets.QWidget | None

    def __init__(self, network_client: QtNetworkClient, session_id: int):
        super().__init__()
        self.widget_root = None
        self.network_client = network_client
        self.current_session_id = session_id
        self.logger = SessionIdLoggerAdapter(_base_logger, self)

    async def _session_admin_global(self, action: admin_actions.SessionAdminGlobalAction, arg):
        try:
            self.widget_root.setEnabled(False)
            return await self.network_client.server_call(
                "multiplayer_admin_session",
                (self.current_session_id, action.value, arg))
        finally:
            self.widget_root.setEnabled(True)

    async def _session_admin_player(self, user_id: int, action: admin_actions.SessionAdminUserAction, arg):
        try:
            self.widget_root.setEnabled(False)
            return await self.network_client.server_call(
                "multiplayer_admin_player",
                (self.current_session_id, user_id, action.value, arg)
            )
        finally:
            self.widget_root.setEnabled(True)

    @handle_network_errors
    async def replace_preset_for(self, world_uid: uuid.UUID, preset: VersionedPreset):
        self.logger.info("Replacing preset for %s with %s", world_uid, preset.name)
        await self._session_admin_global(
            admin_actions.SessionAdminGlobalAction.CHANGE_WORLD,
            (str(world_uid), preset.as_json),
        )

    @handle_network_errors
    async def claim_world_for(self, world_uid: uuid.UUID, owner: int):
        self.logger.info("Claiming %s for %d", world_uid, owner)
        await self._session_admin_player(
            owner, admin_actions.SessionAdminUserAction.CLAIM,
            str(world_uid)
        )

    @handle_network_errors
    async def unclaim_world(self, world_uid: uuid.UUID, owner: int):
        self.logger.info("Unclaiming %s from %d", world_uid, owner)
        await self._session_admin_player(
            owner, admin_actions.SessionAdminUserAction.UNCLAIM,
            str(world_uid)
        )

    @handle_network_errors
    async def rename_world(self, world_uid: uuid.UUID, new_name: str):
        self.logger.info("Renaming world %s to %s", world_uid, new_name)
        await self._session_admin_global(
            admin_actions.SessionAdminGlobalAction.RENAME_WORLD,
            (str(world_uid), new_name),
        )

    @handle_network_errors
    async def delete_world(self, world_uid: uuid.UUID):
        self.logger.info("Deleting world %s", world_uid)
        await self._session_admin_global(
            admin_actions.SessionAdminGlobalAction.DELETE_WORLD,
            str(world_uid),
        )

    @handle_network_errors
    async def create_new_world(self, name: str, preset: VersionedPreset, owner: int):
        self.logger.info("Creating world named '%s' with %s for %d", name, preset.name, owner)
        await self._session_admin_player(
            owner, admin_actions.SessionAdminUserAction.CREATE_WORLD_FOR,
            (name, preset.as_json)
        )

    @handle_network_errors
    async def create_patcher_file(self, world_uid: uuid.UUID, cosmetic_patches: dict) -> dict:
        self.logger.info("Requesting patcher file for %s", world_uid)
        return await self._session_admin_global(
            admin_actions.SessionAdminGlobalAction.CREATE_PATCHER_FILE,
            (str(world_uid), cosmetic_patches)
        )

    @handle_network_errors
    async def kick_player(self, kick_id: int):
        self.logger.info("Kicking player %d", kick_id)
        await self._session_admin_player(
            kick_id, admin_actions.SessionAdminUserAction.KICK,
            None,
        )

    @handle_network_errors
    async def switch_admin(self, new_admin_id: int):
        self.logger.info("Switching admin-ness of %d", new_admin_id)
        await self._session_admin_player(
            new_admin_id, admin_actions.SessionAdminUserAction.SWITCH_ADMIN,
            None,
        )

    async def request_session_update(self):
        self.logger.info("Requesting updated session data")
        await self.network_client.server_call(
            "multiplayer_request_session_update",
            self.current_session_id
        )
