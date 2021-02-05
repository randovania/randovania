from typing import Optional

import wiiload
from PySide2 import QtWidgets
from asyncqt import asyncSlot

from randovania import get_data_path
from randovania.game_connection.backend_choice import GameBackendChoice
from randovania.game_connection.dolphin_backend import DolphinBackend
from randovania.game_connection.game_connection import GameConnection
from randovania.game_connection.nintendont_backend import NintendontBackend
from randovania.gui.lib import async_dialog
from randovania.interface_common.options import Options, InfoAlert


class GameConnectionSetup:
    def __init__(self, parent: QtWidgets.QWidget, tool_button: QtWidgets.QToolButton,
                 label: QtWidgets.QLabel, connection: GameConnection, options: Options):
        self.parent = parent
        self.tool = tool_button
        self.label = label
        self.game_connection = connection
        self.options = options

        self.game_connection.Updated.connect(self.on_game_connection_updated)
        self.tool.setText("Configure backend")

        def _create_check(text: str, on_triggered, default: Optional[bool] = None):
            action = QtWidgets.QAction(self.tool)
            action.setText(text)
            action.setCheckable(True)
            if default is not None:
                action.setChecked(default)
            action.triggered.connect(on_triggered)
            return action

        self.game_connection_menu = QtWidgets.QMenu(self.tool)

        self.use_dolphin_backend = _create_check("Dolphin", self.on_use_dolphin_backend)
        self.use_nintendont_backend = _create_check("", self.on_use_nintendont_backend)
        self.upload_nintendont_action = QtWidgets.QAction(self.tool)
        self.upload_nintendont_action.setText("Upload Nintendont to Homebrew Channel")
        self.upload_nintendont_action.triggered.connect(self.on_upload_nintendont_action)
        self.connect_to_game = _create_check("Connect to the game", self.on_connect_to_game, True)

        self.game_connection_menu.addAction(self.use_dolphin_backend)
        self.game_connection_menu.addAction(self.use_nintendont_backend)
        self.game_connection_menu.addAction(self.upload_nintendont_action)
        self.game_connection_menu.addSeparator()
        self.game_connection_menu.addAction(self.connect_to_game)

        self.tool.setMenu(self.game_connection_menu)

        self.refresh_backend()
        self.on_game_connection_updated()

    def on_game_connection_updated(self):
        self.label.setText(self.game_connection.pretty_current_status)

    def refresh_backend(self):
        backend = self.game_connection.backend

        self.use_dolphin_backend.setChecked(isinstance(backend, DolphinBackend))
        if isinstance(backend, NintendontBackend):
            self.use_nintendont_backend.setChecked(True)
            self.use_nintendont_backend.setText(f"Nintendont: {backend.ip}")
            self.upload_nintendont_action.setEnabled(True)
        else:
            self.use_nintendont_backend.setChecked(False)
            self.use_nintendont_backend.setText(f"Nintendont")
            self.upload_nintendont_action.setEnabled(False)

    def on_use_dolphin_backend(self):
        self.game_connection.set_backend(DolphinBackend())
        with self.options as options:
            options.game_backend = GameBackendChoice.DOLPHIN
        self.refresh_backend()

    @asyncSlot()
    async def on_use_nintendont_backend(self):
        dialog = QtWidgets.QInputDialog(self.parent)
        dialog.setModal(True)
        dialog.setWindowTitle("Enter Wii's IP")
        dialog.setLabelText("Enter the IP address of your Wii. "
                            "You can check the IP address on the pause screen of Homebrew Channel.")
        if self.options.nintendont_ip is not None:
            dialog.setTextValue(self.options.nintendont_ip)

        if await async_dialog.execute_dialog(dialog) == dialog.Accepted:
            new_ip = dialog.textValue()
            if new_ip != "":
                if not self.options.is_alert_displayed(InfoAlert.NINTENDONT_UNSTABLE):
                    await async_dialog.warning(self.parent, "Nintendont Limitation",
                                               "Warning: The Nintendont integration isn't perfect and is known to "
                                               "crash.")
                    self.options.mark_alert_as_displayed(InfoAlert.NINTENDONT_UNSTABLE)

                with self.options as options:
                    options.nintendont_ip = new_ip
                    options.game_backend = GameBackendChoice.NINTENDONT
                self.game_connection.set_backend(NintendontBackend(new_ip))
        self.refresh_backend()

    @asyncSlot()
    async def on_upload_nintendont_action(self):
        nintendont_file = get_data_path().joinpath("nintendont", "boot.dol")
        if not nintendont_file.is_file():
            return await async_dialog.warning(self.parent, "Missing Nintendont",
                                              "Unable to find a Nintendont executable.")

        text = f"Uploading Nintendont to the Wii at {self.options.nintendont_ip}..."
        box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, "Uploading to Homebrew Channel",
                                    text, QtWidgets.QMessageBox.Ok, self.parent)
        box.button(QtWidgets.QMessageBox.Ok).setEnabled(False)
        box.show()

        try:
            await wiiload.upload_file(nintendont_file, [], self.options.nintendont_ip)
            box.setText(f"Upload finished successfully. Check your Wii for more.")
        except Exception as e:
            box.setText(f"Error uploading to Wii: {e}")
        finally:
            box.button(QtWidgets.QMessageBox.Ok).setEnabled(True)

    def on_connect_to_game(self):
        connect_to_game = self.connect_to_game.isChecked()
        self.game_connection.backend.set_connection_enabled(connect_to_game)
