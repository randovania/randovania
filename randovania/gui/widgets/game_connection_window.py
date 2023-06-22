import collections
import functools

import wiiload
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt
from qasync import asyncSlot

import randovania
from randovania.game_connection.builder.connector_builder import ConnectorBuilder
from randovania.game_connection.builder.connector_builder_option import ConnectorBuilderOption
from randovania.game_connection.builder.debug_connector_builder import DebugConnectorBuilder
from randovania.game_connection.builder.nintendont_connector_builder import NintendontConnectorBuilder
from randovania.game_connection.connector.debug_remote_connector import DebugRemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.game_connection import GameConnection
from randovania.games.game import RandovaniaGame
from randovania.gui.debug_backend_window import DebugConnectorWindow
from randovania.gui.generated.game_connection_window_ui import Ui_GameConnectionWindow
from randovania.gui.lib import common_qt_lib, async_dialog


class BuilderUi:
    group: QtWidgets.QGroupBox
    layout: QtWidgets.QGridLayout
    button: QtWidgets.QToolButton
    remove: QtGui.QAction
    description: QtWidgets.QLabel
    status: QtWidgets.QLabel

    def __init__(self, parent: QtWidgets.QWidget):
        self.group = QtWidgets.QGroupBox(parent)
        self.layout = QtWidgets.QGridLayout(self.group)

        self.button = QtWidgets.QToolButton(self.group)
        self.button.setText("...")
        self.button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        # self.button.setMaximumWidth(75)

        self.menu = QtWidgets.QMenu(self.button)
        self.button.setMenu(self.menu)

        self.description = QtWidgets.QLabel(self.group)
        self.description.setWordWrap(True)

        self.status = QtWidgets.QLabel(self.group)
        self.status.setWordWrap(True)

        self.layout.addWidget(self.button)
        self.layout.addWidget(self.description, 0, 1)
        self.layout.addWidget(self.status, 1, 0, 1, 2)


class GameConnectionWindow(QtWidgets.QMainWindow, Ui_GameConnectionWindow):
    ui_for_builder: dict[ConnectorBuilder, BuilderUi]

    def __init__(self, game_connection: GameConnection):
        super().__init__()
        common_qt_lib.set_default_window_icon(self)
        self.setupUi(self)
        self.game_connection = game_connection

        self.add_builder_menu = QtWidgets.QMenu(self.add_builder_button)
        self._builder_actions = {}
        for choice in ConnectorBuilderChoice.all_usable_choices():
            action = QtGui.QAction(choice.pretty_text, self.add_builder_menu)
            self._builder_actions[choice] = action
            action.triggered.connect(functools.partial(self._add_connector_builder, choice))
            self.add_builder_menu.addAction(action)
        self.add_builder_button.setMenu(self.add_builder_menu)

        self.game_connection.BuildersChanged.connect(self.setup_builder_ui)
        self.game_connection.BuildersUpdated.connect(self.update_builder_ui)
        self.setup_builder_ui()

    async def _prompt_for_text(self, title: str, label: str) -> str | None:
        dialog = QtWidgets.QInputDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        new_text = ""
        if await async_dialog.execute_dialog(dialog) == QtWidgets.QDialog.DialogCode.Accepted:
            new_text = dialog.textValue()

        if new_text == "":
            return None
        return new_text

    async def _prompt_for_game(self, title: str, label: str) -> RandovaniaGame | None:
        games_by_name = {
            game.long_name: game
            for game in sorted(RandovaniaGame.all_games(), key=lambda it: it.long_name)
        }

        dialog = QtWidgets.QInputDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setComboBoxItems(list(games_by_name.keys()))
        new_text = ""
        if await async_dialog.execute_dialog(dialog) == QtWidgets.QDialog.DialogCode.Accepted:
            new_text = dialog.textValue()

        if new_text == "":
            return None

        return games_by_name[new_text]

    @asyncSlot()
    async def _add_connector_builder(self, choice: ConnectorBuilderChoice):
        args = {}

        if choice == ConnectorBuilderChoice.NINTENDONT:
            new_ip = await self._prompt_for_text(
                "Enter Wii's IP",
                "Enter the IP address of your Wii. "
                "You can check the IP address on the pause screen of Homebrew Channel."
            )
            if new_ip is None:
                return
            args["ip"] = new_ip

        if choice == ConnectorBuilderChoice.DREAD:
            new_ip = await self._prompt_for_text(
                "Enter Ryujinx's/Switch's IP",
                "Enter the IP address of your Switch or use \"localhost\" for Ryujinx."
                "You can check the IP address in the system settings."
            )
            if new_ip is None:
                return
            args["ip"] = new_ip

        if choice == ConnectorBuilderChoice.DEBUG:
            new_game = await self._prompt_for_game(
                "Choose Game",
                "Select the game to use for the debug connection."
            )
            if new_game is None:
                return
            args["game"] = new_game.value

        self.game_connection.add_connection_builder(
            ConnectorBuilderOption(choice, args).create_builder()
        )

    def setup_builder_ui(self):
        for child in self.builders_group.findChildren(QtWidgets.QWidget):
            child.deleteLater()

        self.ui_for_builder = {}
        add_action_enabled: dict[ConnectorBuilderChoice, bool] = collections.defaultdict(lambda: True)

        for builder in self.game_connection.connection_builders:
            if not builder.connector_builder_choice.is_usable():
                continue

            self.add_ui_for_builder(builder)
            if not builder.connector_builder_choice.supports_multiple_instances():
                add_action_enabled[builder.connector_builder_choice] = False

        for choice, action in self._builder_actions.items():
            action.setEnabled(add_action_enabled[choice])

        # TODO: multiworld can't handle multiple builders, so disable it for now
        self.add_builder_button.setEnabled(not self.game_connection.connection_builders)

        self.update_builder_ui()

    def update_builder_ui(self):
        for builder, ui in self.ui_for_builder.items():
            if (message := builder.get_status_message()) is not None:
                ui.status.setText(message)

    def add_ui_for_builder(self, builder: ConnectorBuilder):
        ui = BuilderUi(self.builders_group)
        ui.menu.addAction("Remove").triggered.connect(
            functools.partial(self.game_connection.remove_connection_builder, builder)
        )
        # TODO: add the auto tracker action
        # ui.menu.addAction("Open Auto-Tracker").triggered.connect(
        #     functools.partial(self.open_auto_tracker, builder)
        # )
        if isinstance(builder, NintendontConnectorBuilder):
            ui.menu.addSeparator()
            action = QtGui.QAction(ui.menu)
            action.setText("Upload Nintendont to Homebrew Channel")
            action.triggered.connect(functools.partial(self.on_upload_nintendont_action, builder))
            ui.menu.addAction(action)

        if isinstance(builder, DebugConnectorBuilder):
            ui.menu.addSeparator()
            action = QtGui.QAction(ui.menu)
            action.setText("Open debug interface")
            action.triggered.connect(functools.partial(self.open_debug_connector_window, builder))
            ui.menu.addAction(action)

        ui.description.setText(builder.pretty_text)
        self.ui_for_builder[builder] = ui

        self.builders_layout.addWidget(ui.group)

    @asyncSlot()
    async def on_upload_nintendont_action(self, builder: NintendontConnectorBuilder):
        nintendont_file = randovania.get_data_path().joinpath("nintendont", "boot.dol")
        if not nintendont_file.is_file():
            return await async_dialog.warning(self, "Missing Nintendont",
                                              "Unable to find a Nintendont executable.")

        text = f"Uploading Nintendont to the Wii at {builder.ip}..."
        box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.NoIcon, "Uploading to Homebrew Channel",
                                    text, QtWidgets.QMessageBox.StandardButton.Ok, self)
        common_qt_lib.set_default_window_icon(box)
        box.button(QtWidgets.QMessageBox.StandardButton.Ok).setEnabled(False)
        box.show()

        try:
            await wiiload.upload_file(nintendont_file, [], builder.ip)
            box.setText("Upload finished successfully. Check your Wii for more.")
        except Exception as e:
            box.setText(f"Error uploading to Wii: {e}")
        finally:
            box.button(QtWidgets.QMessageBox.StandardButton.Ok).setEnabled(True)

    def open_debug_connector_window(self, builder: DebugConnectorBuilder):
        connector = self.game_connection.get_connector_for_builder(builder)
        if connector is not None:
            assert isinstance(connector, DebugRemoteConnector)
            builder.connector_window = DebugConnectorWindow(connector)
            builder.connector_window.show()
