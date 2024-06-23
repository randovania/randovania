from __future__ import annotations

import collections
import functools
from typing import TYPE_CHECKING

import wiiload
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from qasync import asyncSlot

import randovania
from randovania.game_connection.builder.connector_builder_option import ConnectorBuilderOption
from randovania.game_connection.builder.debug_connector_builder import DebugConnectorBuilder
from randovania.game_connection.builder.nintendont_connector_builder import NintendontConnectorBuilder
from randovania.game_connection.connector.debug_remote_connector import DebugRemoteConnector
from randovania.game_connection.connector.remote_connector import ImportantStatusMessage, RemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.games.dread.gui.dialog.dread_connector_prompt_dialog import (
    CSConnectorPromptDialog,
    DreadConnectorPromptDialog,
)
from randovania.games.game import RandovaniaGame
from randovania.gui.debug_backend_window import DebugConnectorWindow
from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog
from randovania.gui.generated.game_connection_window_ui import Ui_GameConnectionWindow
from randovania.gui.lib import async_dialog, common_qt_lib
from randovania.gui.lib.qt_network_client import QtNetworkClient, handle_network_errors
from randovania.interface_common.players_configuration import INVALID_UUID
from randovania.network_common import error

if TYPE_CHECKING:
    import uuid

    from randovania.game_connection.builder.connector_builder import ConnectorBuilder
    from randovania.game_connection.game_connection import GameConnection
    from randovania.gui.main_window import MainWindow
    from randovania.gui.multiworld_client import MultiworldClient
    from randovania.interface_common.options import Options


class BuilderUi:
    group: QtWidgets.QGroupBox
    layout: QtWidgets.QGridLayout
    button: QtWidgets.QToolButton
    remove: QtGui.QAction
    description: QtWidgets.QLabel
    status: QtWidgets.QLabel
    open_session_action: QtGui.QAction
    important_message_menu: QtWidgets.QMenu | None = None
    send_arbitrary_message_action: QtGui.QAction | None = None
    connector: RemoteConnector | None = None

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
        self.status.setTextFormat(Qt.MarkdownText)

        self.layout.addWidget(self.button)
        self.layout.addWidget(self.description, 0, 1)
        self.layout.addWidget(self.status, 1, 0, 1, 2)

    def update_for_disconnected_builder(self, builder: ConnectorBuilder):
        message = "Not Connected."
        if (status := builder.get_status_message()) is not None:
            message += f" {status}"

        self.status.setText(message)
        self.open_session_action.setEnabled(False)

    def update_for_remote_connector(self, connector: RemoteConnector, multiworld_client: MultiworldClient):
        self.connector = connector
        world_uid = connector.layout_uuid
        has_session = False

        lines = [f"Connected to {connector.description()}.", ""]
        if world_uid == INVALID_UUID:
            lines.append("Solo game.")
        else:
            data = multiworld_client.database.get_data_for(world_uid)
            if data.server_data is not None:
                has_session = True
                name = f"World '{data.server_data.world_name}' for session '{data.server_data.session_name}'."
            else:
                name = "Unknown Multiworld game."

            msg = (
                f"{name} {len(data.collected_locations)} collected locations, "
                f"with {len(set(data.collected_locations) - set(data.uploaded_locations))} "
                f"pending delivery to other players."
            )

            err = multiworld_client.get_world_sync_error(world_uid)
            if err is not None:
                msg += f"\n\n**\\*\\*Received {err} on last delivery.\\*\\***"

            lines.append(msg)

        self.open_session_action.setEnabled(has_session)
        self.status.setText("\n".join(lines))

    @asyncSlot()
    async def _send_important_message(self, status_message: ImportantStatusMessage):
        if self.connector is not None:
            await self.connector.display_important_message(status_message)

    @asyncSlot()
    async def _send_arbitrary_message(self):
        if self.connector is None:
            return

        message = await TextPromptDialog.prompt(
            parent=self.group,
            title="What message to send?",
            description="What message to send?",
            is_modal=True,
            max_length=50,
        )
        await self.connector.display_arbitrary_message(message)

    def add_send_message_actions(self):
        self.menu.addSeparator()

        self.important_message_menu = self.menu.addMenu("Display important message")
        for status_message in ImportantStatusMessage:
            self.important_message_menu.addAction(status_message.name).triggered.connect(
                functools.partial(self._send_important_message, status_message)
            )

        self.send_arbitrary_message_action = self.menu.addAction("Display arbitrary message")
        self.send_arbitrary_message_action.triggered.connect(self._send_arbitrary_message)

    def update_send_message_actions(self):
        if self.important_message_menu is None:
            return

        self.important_message_menu.setEnabled(self.connector is not None)
        can_arbitrary_send = self.connector is not None and self.connector.can_display_arbitrary_messages()
        self.send_arbitrary_message_action.setEnabled(can_arbitrary_send)


class GameConnectionWindow(QtWidgets.QMainWindow, Ui_GameConnectionWindow):
    ui_for_builder: dict[ConnectorBuilder, BuilderUi]
    layout_uuid_for_builder: dict[ConnectorBuilder, uuid.UUID]

    def __init__(
        self,
        window_manager: MainWindow,
        network_client: QtNetworkClient,
        options: Options,
        game_connection: GameConnection,
    ):
        super().__init__()
        common_qt_lib.set_default_window_icon(self)
        self.setupUi(self)
        self.window_manager = window_manager
        self.network_client = network_client
        self.options = options
        self.game_connection = game_connection
        self.world_database = game_connection.world_database

        self.builders_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self.add_builder_menu = QtWidgets.QMenu(self.add_builder_button)
        self._builder_actions = {}
        for choice in ConnectorBuilderChoice.all_usable_choices():
            action = QtGui.QAction(choice.pretty_text, self.add_builder_menu)
            self._builder_actions[choice] = action
            action.triggered.connect(functools.partial(self._add_connector_builder, choice))
            self.add_builder_menu.addAction(action)
        self.add_builder_button.setMenu(self.add_builder_menu)

        self.help_label.linkActivated.connect(self.window_manager.open_app_navigation_link)
        self.game_connection.BuildersChanged.connect(self.setup_builder_ui)
        self.game_connection.BuildersUpdated.connect(self.update_builder_ui)
        self.game_connection.GameStateUpdated.connect(self.update_builder_ui)
        self.world_database.WorldDataUpdate.connect(self.update_builder_ui)
        self.window_manager.multiworld_client.SyncFailure.connect(self.update_builder_ui)
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
            game.long_name: game for game in sorted(RandovaniaGame.all_games(), key=lambda it: it.long_name)
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
                "You can check the IP address on the pause screen of Homebrew Channel.",
            )
            if new_ip is None:
                return
            args["ip"] = new_ip

        if choice == ConnectorBuilderChoice.DREAD:
            new_ip = await DreadConnectorPromptDialog.prompt(
                parent=self,
                is_modal=True,
                title="Select Ryujinx or Switch to connect to",
                description="Enter the IP address of your Switch. It can be found in the system settings.",
            )
            if new_ip is None:
                return
            args["ip"] = new_ip

        if choice == ConnectorBuilderChoice.CS:
            new_ip = await CSConnectorPromptDialog.prompt(
                parent=self,
                is_modal=True,
                title="Select Cave Story to connect to",
                description="Enter the IP address of the machine running Cave Story.",
            )
            if new_ip is None:
                return
            args["ip"] = new_ip

        if choice == ConnectorBuilderChoice.AM2R:
            # TODO: in the future, for maybe Android, add a nice GUI that allows one to have a user provided ip.
            args["ip"] = "localhost"

        if choice == ConnectorBuilderChoice.MSR:
            # TODO: Add a GUI for the IP whenever we support Luma
            args["ip"] = "localhost"

        if choice == ConnectorBuilderChoice.DEBUG:
            new_game = await self._prompt_for_game("Choose Game", "Select the game to use for the debug connection.")
            if new_game is None:
                return
            args["game"] = new_game.value

        self.game_connection.add_connection_builder(ConnectorBuilderOption(choice, args).create_builder())

    def setup_builder_ui(self):
        for child in self.builders_content.findChildren(QtWidgets.QWidget):
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
    async def _attempt_join(self, builder: ConnectorBuilder):
        connector = self.game_connection.get_connector_for_builder(builder)
        if connector is None:
            return

        layout_uuid = connector.layout_uuid
        if layout_uuid == INVALID_UUID:
            return

        if not await self.network_client.ensure_logged_in(self):
            return

        session_id = self._check_session_data(layout_uuid)
        try:
            await self.network_client.listen_to_session(session_id, True)
            await self.window_manager.ensure_multiplayer_session_window(self.network_client, session_id, self.options)
        except error.NotAuthorizedForActionError:
            await async_dialog.warning(self, "Unauthorized", "You're not a member of this session.")

    def _check_session_data(self, layout_uuid: uuid.UUID) -> int | None:
        world_data = self.world_database.get_data_for(layout_uuid)
        server_data = world_data.server_data
        if server_data is not None:
            return server_data.session_id
        return None

    def update_builder_ui(self):
        for builder, ui in self.ui_for_builder.items():
            connector = self.game_connection.get_connector_for_builder(builder)
            if connector is None:
                ui.update_for_disconnected_builder(builder)
            else:
                ui.update_for_remote_connector(connector, self.window_manager.multiworld_client)
            ui.update_send_message_actions()

    def add_ui_for_builder(self, builder: ConnectorBuilder):
        ui = BuilderUi(self.builders_content)
        ui.menu.addAction("Remove").triggered.connect(
            functools.partial(self.game_connection.remove_connection_builder, builder)
        )

        ui.menu.addSeparator()
        ui.open_session_action = ui.menu.addAction("Open Session Window")
        ui.open_session_action.triggered.connect(functools.partial(self._attempt_join, builder))

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

        if not randovania.is_frozen():
            ui.add_send_message_actions()

        ui.description.setText(builder.pretty_text)
        self.ui_for_builder[builder] = ui

        self.builders_layout.addWidget(ui.group)

    @asyncSlot()
    async def on_upload_nintendont_action(self, builder: NintendontConnectorBuilder):
        nintendont_file = randovania.get_data_path().joinpath("nintendont", "boot.dol")
        if not nintendont_file.is_file():
            return await async_dialog.warning(self, "Missing Nintendont", "Unable to find a Nintendont executable.")

        text = f"Uploading Nintendont to the Wii at {builder.ip}..."
        box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.NoIcon,
            "Uploading to Homebrew Channel",
            text,
            QtWidgets.QMessageBox.StandardButton.Ok,
            self,
        )
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
