from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from PySide6 import QtWidgets
from qasync import asyncSlot

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


class OnlineInteractions(QtWidgets.QWidget):
    network_client: QtNetworkClient
    _login_window: QtWidgets.QDialog | None = None

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

        # Menu Bar
        main_window.menu_action_login_window.triggered.connect(self._action_login_window)

    @asyncSlot()
    @handle_network_errors
    async def _browse_for_session(self):
        if not await self.network_client.ensure_logged_in(self):
            return

        network_client = self.network_client
        browser = MultiplayerSessionBrowserDialog(network_client)

        try:
            result = await wait_dialog.cancellable_wait(
                self,
                asyncio.ensure_future(browser.refresh()),
                "Communicating",
                "Requesting the session list...",
            )
        except asyncio.CancelledError:
            return

        if not result:
            return

        if await async_dialog.execute_dialog(browser) == QtWidgets.QDialog.DialogCode.Accepted:
            await self.window_manager.ensure_multiplayer_session_window(
                network_client, browser.joined_session.id, self.options
            )

    @asyncSlot()
    @handle_network_errors
    async def _action_login_window(self):
        if self._login_window is not None:
            return self._login_window.show()

        self._login_window = LoginPromptDialog(self.network_client)
        try:
            await async_dialog.execute_dialog(self._login_window)
        finally:
            self._login_window = None

    @asyncSlot()
    @handle_network_errors
    async def _host_game_session(self):
        if not await self.network_client.ensure_logged_in(self):
            return

        session_name = await TextPromptDialog.prompt(
            parent=self,
            title="Enter session name",
            description="Select a name for the session:",
            is_modal=True,
            max_length=MAX_SESSION_NAME_LENGTH,
        )
        if session_name is None:
            return

        new_session = await self.network_client.create_new_session(session_name)
        await self.window_manager.ensure_multiplayer_session_window(
            self.network_client,
            new_session.id,
            self.options,
        )
