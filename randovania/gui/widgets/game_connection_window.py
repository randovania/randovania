import collections
import functools
import uuid

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
from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog
from randovania.gui.generated.game_connection_window_ui import Ui_GameConnectionWindow
from randovania.gui.lib import common_qt_lib, async_dialog
from randovania.gui.lib.qt_network_client import handle_network_errors, QtNetworkClient
from randovania.gui.main_window import MainWindow
from randovania.interface_common.players_configuration import INVALID_UUID
from randovania.interface_common.options import Options
from randovania.network_common import error

class BuilderUi:
    group: QtWidgets.QGroupBox
    layout: QtWidgets.QGridLayout
    button: QtWidgets.QToolButton
    remove: QtGui.QAction
    description: QtWidgets.QLabel
    status: QtWidgets.QLabel
    join_session: tuple[QtGui.QAction, QtGui.QAction] # seperator + button

    def __init__(self, parent: QtWidgets.QWidget):
        self.group = QtWidgets.QGroupBox(parent)
        self.layout = QtWidgets.QGridLayout(self.group)
        self.join_session = None

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
    
    def add_session_button(self) -> QtGui.QAction:
        if self.join_session:
            return self.join_session[1]
        seperator = self.menu.addSeparator()
        button = QtGui.QAction(self.menu)
        button.setText("Open Session Window")
        self.menu.addAction(button)
        self.join_session = (seperator, button)
        return button

    def remove_session_button(self):
        if self.join_session:
            seperator, button = self.join_session
            self.menu.removeAction(seperator)
            self.menu.removeAction(button)
            self.join_session = None

    def change_session_button(self, new_value: bool):
        if self.join_session:
            button = self.join_session[1]
            button.setDisabled(new_value)


class GameConnectionWindow(QtWidgets.QMainWindow, Ui_GameConnectionWindow):
    ui_for_builder: dict[ConnectorBuilder, BuilderUi]
    layout_uuid_for_builder: dict[ConnectorBuilder, uuid.UUID]

    def __init__(self, window_manager: MainWindow, network_client: QtNetworkClient,
                  options: Options, game_connection: GameConnection):
        super().__init__()
        common_qt_lib.set_default_window_icon(self)
        self.setupUi(self)
        self.window_manager = window_manager
        self.network_client = network_client
        self.options = options
        self.game_connection = game_connection
        self.world_database = game_connection.world_database

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
        self.game_connection.GameStateUpdated.connect(self.update_builder_ui)
        self.world_database.WorldDataUpdate.connect(self._update_join_actions)
        self.setup_builder_ui()

    async def _prompt_for_text(self, title: str, label: str) -> str | None:
        return await TextPromptDialog.prompt(
            parent=self,
            title=title,
            description=label,
            is_modal=True,
        )

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
        self.layout_uuid_for_builder = {}
        add_action_enabled: dict[ConnectorBuilderChoice, bool] = collections.defaultdict(lambda: True)

        for builder in self.game_connection.connection_builders:
            if not builder.connector_builder_choice.is_usable():
                continue

            self.add_ui_for_builder(builder)
            if not builder.connector_builder_choice.supports_multiple_instances():
                add_action_enabled[builder.connector_builder_choice] = False

        for choice, action in self._builder_actions.items():
            action.setEnabled(add_action_enabled[choice])

        self.update_builder_ui()

    @asyncSlot()
    @handle_network_errors
    async def _attempt_join(self, layout_uuid: uuid.UUID):
        if not await self.network_client.ensure_logged_in(self):
            return
        session_id = self._check_session_data(layout_uuid)
        try:
            await self.network_client.listen_to_session(session_id, True)
            await self.window_manager.ensure_multiplayer_session_window(
                self.network_client, session_id,
                self.options
            )
        except error.NotAuthorizedForAction:
            await async_dialog.warning(self, "Unauthorized",
                                       "You're not a member of this session.")

    def _update_join_actions(self):
        for builder, layout_uuid in self.layout_uuid_for_builder.items():
            new_value = self._check_session_data(layout_uuid) is None
            self.ui_for_builder[builder].change_session_button(new_value)

    def _check_session_data(self, layout_uuid: uuid.UUID) -> int | None:
        world_data = self.world_database.get_data_for(layout_uuid)
        server_data = world_data.server_data
        if server_data is not None:
            return server_data.session_id
        return None

    def _get_valid_uuid(self, builder: ConnectorBuilder) -> uuid.UUID | None:
        # check if there is a remote connector for the builder
        associated_rc = self.game_connection.remote_connectors.get(builder, None)
        if associated_rc is None:
            return None
        
        # check the uuid
        layout_uuid = associated_rc.layout_uuid
        if layout_uuid == INVALID_UUID:
            return None

        return layout_uuid

    def _add_session_action(self, builder: ConnectorBuilder, ui: BuilderUi):
        def new_button(layout_uuid: uuid.UUID):
            button = ui.add_session_button()
            button.triggered.connect(functools.partial(self._attempt_join, layout_uuid))
            self._update_join_actions()

        layout_uuid = self._get_valid_uuid(builder)
        layout_uuid_before = self.layout_uuid_for_builder.get(builder, None)
        # same uuid or both are None
        if layout_uuid_before == layout_uuid:
            return
        self.layout_uuid_for_builder[builder] = layout_uuid
        # layout_uuid was none but now there is a valid one
        if layout_uuid is not None and layout_uuid_before is None:
            new_button(layout_uuid)
        # fast switch of uuid (like possible with dolphin)
        elif layout_uuid is not None and layout_uuid_before is not None:
            ui.remove_session_button()
            new_button(layout_uuid)
        # uuid switched from valid to non valid
        elif layout_uuid is None:
            ui.remove_session_button()

    def update_builder_ui(self):
        for builder, ui in self.ui_for_builder.items():
            if (message := builder.get_status_message()) is not None:
                ui.status.setText(message)
                self._add_session_action(builder, ui)

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
