from typing import Optional

from PySide2 import QtWidgets
from qasync import asyncSlot

from randovania.gui.dialog.login_prompt_dialog import LoginPromptDialog
from randovania.gui.game_session_window import GameSessionWindow
from randovania.gui.generated.main_window_ui import Ui_MainWindow
from randovania.gui.lib import common_qt_lib, async_dialog
from randovania.gui.lib.qt_network_client import handle_network_errors, QtNetworkClient
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.online_game_list_window import GameSessionBrowserDialog
from randovania.interface_common.options import Options
from randovania.interface_common.preset_manager import PresetManager
from randovania.network_client.network_client import ConnectionState


class OnlineInteractions(QtWidgets.QWidget):
    network_client: QtNetworkClient
    game_session_window: Optional[GameSessionWindow] = None
    _login_window: Optional[QtWidgets.QDialog] = None

    def __init__(self, window_manager: WindowManager, preset_manager: PresetManager, network_client: QtNetworkClient,
                 main_window: Ui_MainWindow, options: Options):
        super().__init__(window_manager)

        self.window_manager = window_manager
        self.preset_manager = preset_manager
        self.network_client = network_client
        self.main_window = main_window
        self.options = options

        # Signals
        main_window.browse_sessions_button.clicked.connect(self._browse_for_game_session)
        main_window.host_new_game_button.clicked.connect(self._host_game_session)

        # Menu Bar
        main_window.action_login_window.triggered.connect(self._action_login_window)

    async def _game_session_active(self) -> bool:
        if self.game_session_window is None or self.game_session_window.has_closed:
            return False
        else:
            await async_dialog.message_box(
                self,
                QtWidgets.QMessageBox.Critical,
                "Game Session in progress",
                "There's already a game session window open. Please close it first.",
                QtWidgets.QMessageBox.Ok
            )
            self.game_session_window.activateWindow()
            return True

    async def _ensure_logged_in(self) -> bool:
        network_client = self.network_client
        if network_client.connection_state == ConnectionState.Connected:
            return True

        if network_client.connection_state.is_disconnected:
            message_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, "Connecting",
                                                "Connecting to server...", QtWidgets.QMessageBox.Cancel,
                                                self)

            connecting = network_client.connect_to_server()
            message_box.rejected.connect(connecting.cancel)
            message_box.show()
            try:
                await connecting
            finally:
                message_box.close()

        if network_client.current_user is None:
            await async_dialog.execute_dialog(LoginPromptDialog(network_client))

        return network_client.current_user is not None

    @asyncSlot()
    @handle_network_errors
    async def _browse_for_game_session(self):
        if await self._game_session_active():
            return

        if not await self._ensure_logged_in():
            return

        network_client = self.network_client
        browser = GameSessionBrowserDialog(network_client)
        await browser.refresh()
        if await async_dialog.execute_dialog(browser) == browser.Accepted:
            self.game_session_window = await GameSessionWindow.create_and_update(
                network_client, common_qt_lib.get_game_connection(), self.preset_manager,
                self.window_manager, self.options)
            if self.game_session_window is not None:
                self.game_session_window.show()

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
        if await self._game_session_active():
            return

        if not await self._ensure_logged_in():
            return

        dialog = QtWidgets.QInputDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle("Enter session name")
        dialog.setLabelText("Select a name for the session:")
        if await async_dialog.execute_dialog(dialog) != dialog.Accepted:
            return

        await self.network_client.create_new_session(dialog.textValue())
        self.game_session_window = await GameSessionWindow.create_and_update(self.network_client,
                                                                             common_qt_lib.get_game_connection(),
                                                                             self.preset_manager,
                                                                             self.window_manager,
                                                                             self.options)
        if self.game_session_window is not None:
            self.game_session_window.show()
