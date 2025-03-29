from __future__ import annotations

import asyncio
import typing
from typing import TYPE_CHECKING

from PySide6 import QtWidgets
from qasync import asyncSlot

from randovania import monitoring
from randovania.gui.async_race_room_window import AsyncRaceRoomWindow
from randovania.gui.dialog.async_race_creation_dialog import AsyncRaceCreationDialog
from randovania.gui.dialog.async_race_room_browser_dialog import AsyncRaceRoomBrowserDialog
from randovania.gui.dialog.login_prompt_dialog import LoginPromptDialog
from randovania.gui.dialog.multiplayer_session_browser_dialog import MultiplayerSessionBrowserDialog
from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog
from randovania.gui.lib import async_dialog, wait_dialog
from randovania.gui.lib.qt_network_client import QtNetworkClient, handle_network_errors
from randovania.network_common.multiplayer_session import MAX_SESSION_NAME_LENGTH

if TYPE_CHECKING:
    from randovania.gui.generated.main_window_ui import Ui_MainWindow
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.options import Options
    from randovania.interface_common.preset_manager import PresetManager

BaseSession = typing.TypeVar("BaseSession")


class BaseBrowser(async_dialog.DialogLike, typing.Protocol[BaseSession]):
    def __init__(self, network_client: QtNetworkClient): ...

    async def refresh(self, *, ignore_limit: bool = False) -> bool: ...

    joined_session: BaseSession | None


class OnlineInteractions(QtWidgets.QWidget):
    network_client: QtNetworkClient
    _login_window: QtWidgets.QDialog | None = None
    _async_race_creation: AsyncRaceCreationDialog | None = None

    def __init__(
        self,
        window_manager: WindowManager,
        preset_manager: PresetManager,
        network_client: QtNetworkClient,
        main_window: Ui_MainWindow,
        options: Options,
    ):
        super().__init__(window_manager)

        self.window_manager = window_manager
        self.preset_manager = preset_manager
        self.network_client = network_client
        self.main_window = main_window
        self.options = options

        # Signals
        main_window.browse_sessions_button.clicked.connect(self._browse_for_session)
        main_window.host_new_game_button.clicked.connect(self._host_game_session)
        main_window.browse_async_races_button.clicked.connect(self._browse_async_races)

        # Menu Bar
        main_window.menu_action_login_window.triggered.connect(self._action_login_window)
        main_window.menu_action_async_race.triggered.connect(self._action_create_async_race)

    async def _base_browse(
        self,
        type_: type[BaseBrowser[BaseSession]],
        wait_message: str,
    ) -> BaseSession | None:
        """
        Requests a list of sessions via the given widget, then returns the one the user selected.
        :param type_: The type of the widget to use to display sessions
        :param wait_message: Message to display to the user while the sessions are downloaded
        :return: The selected session, or None if none were selected or an error occurred.
        """
        if not await self.network_client.ensure_logged_in(self):
            return None

        browser = type_(self.network_client)

        try:
            result = await wait_dialog.cancellable_wait(
                self,
                asyncio.ensure_future(browser.refresh()),
                "Communicating",
                wait_message,
            )
        except asyncio.CancelledError:
            return None

        if not result:
            return None

        if await async_dialog.execute_dialog(browser) == QtWidgets.QDialog.DialogCode.Accepted:
            joined_session = browser.joined_session
            assert joined_session is not None
            return joined_session

        return None

    @asyncSlot()
    @handle_network_errors
    async def _browse_async_races(self) -> None:
        """
        Displays a selection widget for async races and then opens a widget for displaying the selected one.
        """
        room = await self._base_browse(
            AsyncRaceRoomBrowserDialog,
            "Requesting the room list...",
        )
        if room is not None:
            async_room = AsyncRaceRoomWindow(room, self.network_client, self.options, self.window_manager)
            async_room.show()
            self.window_manager.track_window(async_room)

    @asyncSlot()
    @handle_network_errors
    async def _browse_for_session(self) -> None:
        """
        Displays a selection widget for multiplayer sessions and then opens a widget for displaying the selected one.
        """
        session = await self._base_browse(
            MultiplayerSessionBrowserDialog,
            "Requesting the session list...",
        )
        if session is not None:
            await self.window_manager.ensure_multiplayer_session_window(self.network_client, session.id, self.options)

    @asyncSlot()
    @handle_network_errors
    async def _action_login_window(self) -> None:
        if self._login_window is not None:
            self._login_window.show()
            return

        self._login_window = LoginPromptDialog(self.network_client)
        try:
            await async_dialog.execute_dialog(self._login_window)
        finally:
            self._login_window = None

    @asyncSlot()
    @handle_network_errors
    async def _action_create_async_race(self) -> None:
        if not await self.network_client.ensure_logged_in(self):
            return

        if self._async_race_creation is not None:
            self._async_race_creation.raise_()
            return

        self._async_race_creation = AsyncRaceCreationDialog(
            self,
            self.window_manager,
            self.options,
        )
        try:
            result = await async_dialog.execute_dialog(self._async_race_creation)

            if result == QtWidgets.QDialog.DialogCode.Accepted:
                assert self._async_race_creation.layout_description is not None
                room = await self.network_client.create_async_race_room(
                    self._async_race_creation.layout_description,
                    self._async_race_creation.create_settings_object(),
                )
                async_room = AsyncRaceRoomWindow(room, self.network_client, self.options, self.window_manager)
                async_room.show()
                self.window_manager.track_window(async_room)
        finally:
            self._async_race_creation = None

    @asyncSlot()
    @handle_network_errors
    async def _host_game_session(self) -> None:
        if not await self.network_client.ensure_logged_in(self):
            return

        monitoring.metrics.incr("gui_multiworld_generate_clicked")

        session_name = await TextPromptDialog.prompt(
            parent=self,
            title="Enter session name",
            description="Select a name for the session:",
            is_modal=True,
            max_length=MAX_SESSION_NAME_LENGTH,
        )
        if session_name is None:
            return

        monitoring.metrics.incr("gui_multiworld_generate_accepted")

        new_session = await self.network_client.create_new_session(session_name)
        await self.window_manager.ensure_multiplayer_session_window(
            self.network_client,
            new_session.id,
            self.options,
        )
