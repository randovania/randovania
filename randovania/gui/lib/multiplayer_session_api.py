from __future__ import annotations

import contextlib
import functools
import logging
import typing

from PySide6 import QtCore, QtWidgets

from randovania.gui.lib import async_dialog
from randovania.layout.layout_description import LayoutDescription
from randovania.network_client.network_client import UnableToConnect
from randovania.network_common import admin_actions, error

if typing.TYPE_CHECKING:
    import uuid

    from randovania.gui.lib.qt_network_client import QtNetworkClient
    from randovania.layout.versioned_preset import VersionedPreset
    from randovania.lib.json_lib import JsonType
    from randovania.network_common.multiplayer_session import MultiplayerWorld
    from randovania.network_common.session_visibility import MultiplayerSessionVisibility

Param = typing.ParamSpec("Param")
RetType = typing.TypeVar("RetType")
OriginalFunc = typing.Callable[Param, RetType]


def handle_network_errors(
    fn: typing.Callable[typing.Concatenate[MultiplayerSessionApi, Param], RetType],
) -> typing.Callable[Param, RetType]:
    @functools.wraps(fn)
    async def wrapper(self: MultiplayerSessionApi, *args: typing.Any, **kwargs: typing.Any) -> RetType | None:
        parent = self.widget_root
        try:
            return await fn(self, *args, **kwargs)

        except error.InvalidActionError as e:
            await async_dialog.warning(parent, "Invalid action", f"{e}")

        except error.ServerError:
            await async_dialog.warning(
                parent, "Server error", "An error occurred on the server while processing your request."
            )

        except error.NotLoggedInError:
            await async_dialog.warning(parent, "Unauthenticated", "You must be logged in.")

        except error.NotAuthorizedForActionError:
            await async_dialog.warning(parent, "Unauthorized", "You're not authorized to perform that action.")

        except error.UserNotAuthorizedToUseServerError:
            await async_dialog.warning(
                parent,
                "Unauthorized",
                "You're not authorized to use this build.\nPlease check #dev-builds for more details.",
            )

        except error.UnsupportedClientError as e:
            s = e.detail.replace("\n", "<br />")
            await async_dialog.warning(
                parent,
                "Unsupported client",
                s,
            )

        except UnableToConnect as e:
            s = e.reason.replace("\n", "<br />")
            await async_dialog.warning(
                parent, "Connection Error", f"<b>Unable to connect to the server:</b><br /><br />{s}"
            )

        except error.RequestTimeoutError as e:
            await async_dialog.warning(
                parent,
                "Connection Error",
                f"<b>Timeout while communicating with the server:</b><br /><br />{e}"
                f"<br />Further attempts will wait for longer.",
            )

        except error.WorldDoesNotExistError:
            await async_dialog.warning(
                parent,
                "World does not exist",
                "The world you tried to change does not exist. "
                "If this error keeps happening, please reopen the Window and/or Randovania.",
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

    def process(
        self, msg: str, kwargs: typing.MutableMapping[str, typing.Any]
    ) -> tuple[str, typing.MutableMapping[str, typing.Any]]:
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

    async def _session_admin_global(
        self, action: admin_actions.SessionAdminGlobalAction, *args: JsonType | bytes
    ) -> JsonType | None:
        assert self.widget_root is not None
        try:
            self.widget_root.setEnabled(False)
            return await self.network_client.server_call(
                "multiplayer_admin_session",
                [self.current_session_id, action.value, *args],
            )
        finally:
            self.widget_root.setEnabled(True)

    async def _session_admin_player(
        self, user_id: int, action: admin_actions.SessionAdminUserAction, *args: JsonType | bytes
    ) -> JsonType | None:
        assert self.widget_root is not None
        try:
            self.widget_root.setEnabled(False)
            return await self.network_client.server_call(
                "multiplayer_admin_player",
                [self.current_session_id, user_id, action.value, *args],
            )
        finally:
            self.widget_root.setEnabled(True)

    @handle_network_errors
    async def rename_session(self, new_name: str) -> None:
        self.logger.info("Renaming session to %s", new_name)
        await self._session_admin_global(admin_actions.SessionAdminGlobalAction.CHANGE_TITLE, new_name)

    @handle_network_errors
    async def change_password(self, password: str) -> None:
        self.logger.info("Changing password")
        await self._session_admin_global(admin_actions.SessionAdminGlobalAction.CHANGE_PASSWORD, password)

    @handle_network_errors
    async def duplicate_session(self, new_name: str) -> None:
        self.logger.info("Duplicating session as %s", new_name)
        await self._session_admin_global(admin_actions.SessionAdminGlobalAction.DUPLICATE_SESSION, new_name)

    @handle_network_errors
    async def change_visibility(self, new_visibility: MultiplayerSessionVisibility) -> None:
        self.logger.info("Setting visibility to %s", new_visibility)
        await self._session_admin_global(admin_actions.SessionAdminGlobalAction.CHANGE_VISIBILITY, new_visibility.value)

    @handle_network_errors
    async def abort_generation(self) -> None:
        self.logger.info("Aborting generation")
        await self._session_admin_global(admin_actions.SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, [])

    async def _upload_layout(self, layout: LayoutDescription) -> None:
        self.logger.info("Uploading a layout description")
        await self._session_admin_global(
            admin_actions.SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION,
            layout.as_binary(include_presets=False, force_spoiler=True),
        )

    @contextlib.asynccontextmanager
    async def prepare_to_upload_layout(self, world_order: list[uuid.UUID]) -> typing.AsyncIterator[int]:
        ordered_ids = [str(world_id) for world_id in world_order]
        self.logger.info("Marking session with generation in progress")
        await self._session_admin_global(admin_actions.SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, ordered_ids)
        yield self._upload_layout
        self.logger.info("Clearing generation in progress")
        await self._session_admin_global(admin_actions.SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, [])

    @handle_network_errors
    async def clear_generated_game(self) -> None:
        self.logger.info("Clearing current layout description")
        await self._session_admin_global(admin_actions.SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION, None)

    @handle_network_errors
    async def request_permalink(self) -> str | None:
        self.logger.info("Requesting permalink")
        return typing.cast(
            "str | None", await self._session_admin_global(admin_actions.SessionAdminGlobalAction.REQUEST_PERMALINK)
        )

    @handle_network_errors
    async def request_layout_description(self, worlds: list[MultiplayerWorld]) -> LayoutDescription | None:
        self.logger.info("Requesting layout description")
        description_binary = typing.cast(
            "bytes | None",
            await self._session_admin_global(admin_actions.SessionAdminGlobalAction.DOWNLOAD_LAYOUT_DESCRIPTION),
        )
        if description_binary is None:
            return None

        return LayoutDescription.from_bytes(description_binary, presets=[world.preset for world in worlds])

    #

    @handle_network_errors
    async def replace_preset_for(self, world_uid: uuid.UUID, preset: VersionedPreset) -> None:
        self.logger.info("Replacing preset for %s with %s", world_uid, preset.name)
        await self._session_admin_global(
            admin_actions.SessionAdminGlobalAction.CHANGE_WORLD,
            str(world_uid),
            preset.as_bytes(),
        )

    @handle_network_errors
    async def claim_world_for(self, world_uid: uuid.UUID, owner: int) -> None:
        self.logger.info("Claiming %s for %d", world_uid, owner)
        await self._session_admin_player(owner, admin_actions.SessionAdminUserAction.CLAIM, str(world_uid))

    @handle_network_errors
    async def unclaim_world(self, world_uid: uuid.UUID, owner: int) -> None:
        self.logger.info("Unclaiming %s from %d", world_uid, owner)
        await self._session_admin_player(owner, admin_actions.SessionAdminUserAction.UNCLAIM, str(world_uid))

    @handle_network_errors
    async def rename_world(self, world_uid: uuid.UUID, new_name: str) -> None:
        self.logger.info("Renaming world %s to %s", world_uid, new_name)
        await self._session_admin_global(
            admin_actions.SessionAdminGlobalAction.RENAME_WORLD,
            str(world_uid),
            new_name,
        )

    @handle_network_errors
    async def delete_world(self, world_uid: uuid.UUID) -> None:
        self.logger.info("Deleting world %s", world_uid)
        await self._session_admin_global(
            admin_actions.SessionAdminGlobalAction.DELETE_WORLD,
            str(world_uid),
        )

    @handle_network_errors
    async def create_new_world(self, name: str, preset: VersionedPreset, owner: int) -> None:
        self.logger.info("Creating world named '%s' with %s for %d", name, preset.name, owner)
        await self._session_admin_player(
            owner,
            admin_actions.SessionAdminUserAction.CREATE_WORLD_FOR,
            name,
            preset.as_bytes(),
        )

    @handle_network_errors
    async def create_unclaimed_world(self, name: str, preset: VersionedPreset) -> None:
        self.logger.info("Creating unclaimed world named '%s' with %s", name, preset.name)
        await self._session_admin_global(
            admin_actions.SessionAdminGlobalAction.CREATE_WORLD,
            name,
            preset.as_bytes(),
        )

    @handle_network_errors
    async def create_patcher_file(self, world_uid: uuid.UUID, cosmetic_patches: dict) -> dict:
        self.logger.info("Requesting patcher file for %s", world_uid)
        return typing.cast(
            "dict",
            await self._session_admin_global(
                admin_actions.SessionAdminGlobalAction.CREATE_PATCHER_FILE,
                str(world_uid),
                cosmetic_patches,
            ),
        )

    @handle_network_errors
    async def kick_player(self, kick_id: int) -> None:
        self.logger.info("Kicking player %d", kick_id)
        await self._session_admin_player(
            kick_id,
            admin_actions.SessionAdminUserAction.KICK,
        )

    @handle_network_errors
    async def switch_admin(self, new_admin_id: int) -> None:
        self.logger.info("Switching admin-ness of %d", new_admin_id)
        await self._session_admin_player(
            new_admin_id,
            admin_actions.SessionAdminUserAction.SWITCH_ADMIN,
        )

    @handle_network_errors
    async def set_allow_coop(self, flag: bool) -> None:
        self.logger.info("Setting whether to allow coop to %s", flag)
        await self._session_admin_global(
            admin_actions.SessionAdminGlobalAction.SET_ALLOW_COOP,
            flag,
        )

    @handle_network_errors
    async def set_everyone_can_claim(self, flag: bool) -> None:
        self.logger.info("Setting whether everyone can claim to %s", flag)
        await self._session_admin_global(
            admin_actions.SessionAdminGlobalAction.SET_ALLOW_EVERYONE_CLAIM,
            flag,
        )

    @handle_network_errors
    async def switch_readiness(self, user_id: int) -> None:
        self.logger.info("Switching ready-ness of %d", user_id)
        await self._session_admin_player(
            user_id,
            admin_actions.SessionAdminUserAction.SWITCH_READY,
        )

    async def request_session_update(self) -> None:
        self.logger.info("Requesting updated session data")
        await self.network_client.server_call("multiplayer_request_session_update", self.current_session_id)
