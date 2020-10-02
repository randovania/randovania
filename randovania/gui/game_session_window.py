import asyncio
import dataclasses
import functools
import json
import random
from typing import List, Optional

from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import Qt, Signal, QTimer
from PySide2.QtWidgets import QMainWindow, QMessageBox
from asyncqt import asyncSlot, asyncClose

from randovania.game_connection.connection_backend import ConnectionStatus
from randovania.game_connection.game_connection import GameConnection
from randovania.game_description import data_reader
from randovania.gui.dialog.echoes_user_preferences_dialog import EchoesUserPreferencesDialog
from randovania.gui.dialog.game_input_dialog import GameInputDialog
from randovania.gui.dialog.logic_settings_window import LogicSettingsWindow
from randovania.gui.generated.game_session_ui import Ui_GameSessionWindow
from randovania.gui.lib import common_qt_lib, preset_describer, async_dialog
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.qt_network_client import handle_network_errors, QtNetworkClient
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.multiworld_client import MultiworldClient
from randovania.interface_common import simplified_patcher, status_update_lib
from randovania.interface_common.options import Options
from randovania.interface_common.preset_editor import PresetEditor
from randovania.interface_common.preset_manager import PresetManager
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink
from randovania.layout.preset import Preset
from randovania.network_client.game_session import GameSessionEntry, PlayerSessionEntry
from randovania.network_client.network_client import ConnectionState
from randovania.network_common.admin_actions import SessionAdminUserAction, SessionAdminGlobalAction
from randovania.network_common.session_state import GameSessionState
from randovania.resolver.exceptions import GenerationFailure


@dataclasses.dataclass()
class PlayerWidget:
    name: QtWidgets.QLabel
    tool: QtWidgets.QToolButton
    kick: QtWidgets.QAction
    promote: QtWidgets.QAction
    open_tracker: QtWidgets.QAction
    abandon: QtWidgets.QAction
    move_up: QtWidgets.QAction
    move_down: QtWidgets.QAction
    switch_observer_action: QtWidgets.QAction
    player: Optional[PlayerSessionEntry] = None

    @property
    def widgets(self):
        return [self.name, self.tool]

    def delete_widgets(self):
        for widget in self.widgets:
            widget.deleteLater()

    def set_visible(self, value: bool):
        for widget in self.widgets:
            widget.setVisible(value)

    def set_player(self, player: Optional[PlayerSessionEntry]):
        self.player = player
        if player is not None:
            self.set_visible(True)
            for action in (self.move_up, self.move_down, self.abandon, self.open_tracker):
                action.setVisible(not player.is_observer)
        else:
            self.set_visible(False)

    def update_player_widget(self,
                             game_session: GameSessionEntry,
                             self_player: PlayerSessionEntry,
                             ):

        player = self.player
        if player is None:
            return

        player_name = player.name
        if player.id == self_player.id:
            player_name += " (You)"
            admin_or_you = True
        else:
            admin_or_you = self_player.admin

        player_is_admin = game_session.players[self.player.id].admin
        if player_is_admin:
            promote_text = "Demote from Admin"
            num_required = 2
            player_name = "[Admin] " + player_name
        else:
            promote_text = "Promote to Admin"
            num_required = 1

        self.name.setText(player_name)
        self.kick.setEnabled(self_player.admin and player.id != self_player.id)
        self.promote.setText(promote_text)
        self.promote.setEnabled(self_player.admin and game_session.num_admins >= num_required)
        self.move_up.setEnabled(admin_or_you and player.row > 0)
        self.move_down.setEnabled(admin_or_you and player.row + 1 < game_session.num_rows)
        self.abandon.setEnabled(admin_or_you)
        self.switch_observer_action.setText("Include in session" if player.is_observer else "Move to observers")
        self.switch_observer_action.setEnabled(admin_or_you)


@dataclasses.dataclass()
class RowWidget:
    name: QtWidgets.QLabel
    tool: QtWidgets.QToolButton
    view_summary: QtWidgets.QAction
    customize: QtWidgets.QAction
    import_menu: QtWidgets.QMenu
    import_actions: List[QtWidgets.QAction]
    save_copy: QtWidgets.QAction
    delete: QtWidgets.QAction

    @property
    def widgets(self):
        return [self.name, self.tool]

    def delete_widgets(self):
        for widget in self.widgets:
            widget.deleteLater()

    def set_is_admin(self, is_admin: bool, is_your_row: bool, can_customize: bool):
        for widget in (self.customize, self.import_menu):
            widget.setEnabled(can_customize and (is_admin or is_your_row))
        self.delete.setEnabled(can_customize and is_admin)

    def set_preset(self, preset: Preset):
        self.name.setText(preset.name)


_PRESET_COLUMNS = 3


class GameSessionWindow(QMainWindow, Ui_GameSessionWindow, BackgroundTaskMixin):
    team_players: List[PlayerWidget]
    observers: List[PlayerWidget]
    rows: List[RowWidget]
    _game_session: GameSessionEntry
    has_closed = False
    _logic_settings_window: Optional[LogicSettingsWindow] = None
    _window_manager: WindowManager
    _generating_game: bool = False

    failed_to_generate_signal = Signal(GenerationFailure)

    def __init__(self, network_client: QtNetworkClient, game_connection: GameConnection,
                 preset_manager: PresetManager, window_manager: WindowManager, options: Options):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.network_client = network_client
        self.game_connection = game_connection
        self.multiworld_client = MultiworldClient(self.network_client, self.game_connection)

        self._preset_manager = preset_manager
        self._window_manager = window_manager
        self._options = options

        # Advanced Options
        self.advanced_options_menu = QtWidgets.QMenu(self.advanced_options_tool)
        self.rename_session_action = QtWidgets.QAction("Change title", self.advanced_options_menu)
        self.change_password_action = QtWidgets.QAction("Change password", self.advanced_options_menu)
        self.delete_session_action = QtWidgets.QAction("Delete session", self.advanced_options_menu)

        self.advanced_options_menu.addAction(self.rename_session_action)
        self.advanced_options_menu.addAction(self.change_password_action)
        self.advanced_options_menu.addAction(self.delete_session_action)
        self.advanced_options_tool.setMenu(self.advanced_options_menu)

        self.rename_session_action.triggered.connect(self.rename_session)
        self.change_password_action.triggered.connect(self.change_password)
        self.delete_session_action.triggered.connect(self.delete_session)

        # Background process Button
        self.background_process_menu = QtWidgets.QMenu(self.background_process_button)
        self.generate_game_with_spoiler_action = QtWidgets.QAction("Generate game", self.background_process_menu)
        self.generate_game_without_spoiler_action = QtWidgets.QAction("Generate without spoiler",
                                                                      self.background_process_menu)
        self.import_permalink_action = QtWidgets.QAction("Import permalink", self.background_process_menu)
        self.background_process_menu.addAction(self.generate_game_with_spoiler_action)
        self.background_process_menu.addAction(self.generate_game_without_spoiler_action)
        self.background_process_menu.addAction(self.import_permalink_action)
        self.background_process_button.setMenu(self.background_process_menu)

        self.generate_game_with_spoiler_action.triggered.connect(self.generate_game_with_spoiler)
        self.generate_game_without_spoiler_action.triggered.connect(self.generate_game_without_spoiler)
        self.import_permalink_action.triggered.connect(self.import_permalink)
        self.background_process_button.clicked.connect(self.background_process_button_clicked)

        # Signals
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.progress_update_signal.connect(self.update_progress)
        self.customize_user_preferences_button.clicked.connect(self._open_user_preferences_dialog)
        self.session_status_tool.clicked.connect(self._session_status_button_clicked)
        self.save_iso_button.clicked.connect(self.save_iso)
        self.view_game_details_button.clicked.connect(self.view_game_details)
        self.failed_to_generate_signal.connect(self._show_failed_generation_exception)

        # Game Connection
        self.game_connection_menu = QtWidgets.QMenu(self.game_connection_tool)
        setup_connection_action = QtWidgets.QAction("Setup game connection", self.game_connection_menu)
        self.game_connection_menu.addAction(setup_connection_action)
        self.game_connection_tool.setMenu(self.game_connection_menu)
        self.game_connection_tool.setVisible(False)

        # Server Status
        self.server_connection_button.clicked.connect(self._connect_to_server)

        # Session status
        self.session_status_menu = QtWidgets.QMenu(self.session_status_tool)
        self.start_session_action = QtWidgets.QAction("Start session", self.session_status_menu)
        self.start_session_action.triggered.connect(self.start_session)

        self.finish_session_action = QtWidgets.QAction("Finish session", self.session_status_menu)
        self.finish_session_action.triggered.connect(self.finish_session)
        self.finish_session_action.setEnabled(False)

        self.reset_session_action = QtWidgets.QAction("Reset session", self.session_status_menu)
        self.reset_session_action.triggered.connect(self.reset_session)
        self.reset_session_action.setEnabled(False)

        self.session_status_menu.addAction(self.start_session_action)
        self.session_status_menu.addAction(self.finish_session_action)
        self.session_status_menu.addAction(self.reset_session_action)
        self.session_status_tool.setMenu(self.session_status_menu)

        self.players_layout.addWidget(self.players_vertical_line, 0, 2, -1, 1)
        self.new_row_button.clicked.connect(functools.partial(
            self._admin_global_action_slot, SessionAdminGlobalAction.CREATE_ROW,
            self._preset_manager.default_preset.as_json))

        self.rows = []
        self.observers = []
        self.team_players = []

        self.main_layout.insertWidget(1, self.players_box)

        spacer_item = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.main_layout.insertSpacerItem(2, spacer_item)

        self.network_client.GameSessionUpdated.connect(self.on_game_session_updated)
        self.network_client.ConnectionStateUpdated.connect(self.on_server_connection_state_updated)
        self.game_connection.StatusUpdated.connect(self.on_game_connection_status_updated)

    @classmethod
    async def create_and_update(cls, network_client: QtNetworkClient, game_connection: GameConnection,
                                preset_manager: PresetManager, window_manager: WindowManager, options: Options,
                                ) -> "GameSessionWindow":
        window = cls(network_client, game_connection, preset_manager, window_manager, options)
        await window.on_game_session_updated(network_client.current_game_session)
        window.on_server_connection_state_updated(network_client.connection_state)
        window.on_game_connection_status_updated(game_connection.current_status)
        return window

    @asyncClose
    async def closeEvent(self, event: QtGui.QCloseEvent):
        if self.network_client.current_user.id not in self._game_session.players:
            super().closeEvent(event)
            self.has_closed = True
            return

        user_response = await async_dialog.warning(
            self,
            "Leaving Game Session",
            ("Do you want to also leave the session?\n\n"
             "Yes: Leave permanently, freeing a spot for others.\n"
             "No: Close the window, but stay in the session. You can rejoin later.\n"
             "Cancel: Do nothing\n"),
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.No
        )
        if user_response == QMessageBox.Cancel:
            event.ignore()
            return

        await self.multiworld_client.stop()
        self.network_client.GameSessionUpdated.disconnect(self.on_game_session_updated)

        try:
            if user_response == QMessageBox.Yes or not self.network_client.connection_state.is_disconnected:
                await self.network_client.leave_game_session(user_response == QMessageBox.Yes)
        finally:
            super().closeEvent(event)
        self.has_closed = True

    def _show_failed_generation_exception(self, exception: GenerationFailure):
        QMessageBox.critical(self._window_manager,
                             "An error occurred while generating a seed",
                             "{}\n\nSome errors are expected to occur, please try again.".format(exception))

    # Row Functions

    def add_row(self):
        preset_name = QtWidgets.QLabel(self.players_box)
        preset_name.setText("")
        preset_name.setMaximumWidth(180)
        self.players_layout.addWidget(preset_name, len(self.rows) + 2, 0)

        tool_button = QtWidgets.QToolButton(self.players_box)
        tool_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        tool_button.setText("...")
        self.players_layout.addWidget(tool_button, len(self.rows) + 2, 1)

        tool_button_menu = QtWidgets.QMenu(tool_button)
        tool_button.setMenu(tool_button_menu)
        import_menu = QtWidgets.QMenu(tool_button_menu)

        row = RowWidget(
            name=preset_name,
            tool=tool_button,
            view_summary=QtWidgets.QAction(tool_button_menu),
            customize=QtWidgets.QAction(tool_button_menu),
            import_menu=import_menu,
            import_actions=[],
            save_copy=QtWidgets.QAction(tool_button_menu),
            delete=QtWidgets.QAction(tool_button_menu),
        )
        self.rows.append(row)

        row.view_summary.setText("View preset summary")
        row.view_summary.triggered.connect(functools.partial(self._row_show_preset_summary, row))
        tool_button_menu.addAction(row.view_summary)

        row.customize.setText("Customize preset")
        row.customize.triggered.connect(functools.partial(self._row_customize_preset, row))
        tool_button_menu.addAction(row.customize)

        row.import_menu.setTitle("Import preset")
        for included_preset in self._preset_manager.all_presets:
            action = QtWidgets.QAction(row.import_menu)
            action.setText(included_preset.name)
            action.triggered.connect(functools.partial(self._row_import_preset, row, included_preset))
            row.import_actions.append(action)
            row.import_menu.addAction(action)

        tool_button_menu.addMenu(row.import_menu)

        row.save_copy.setText("Save copy of preset")
        row.save_copy.triggered.connect(functools.partial(self._row_save_preset, row))
        tool_button_menu.addAction(row.save_copy)

        row.delete.setText("Delete session row")
        row.delete.triggered.connect(functools.partial(self._row_delete, row))
        tool_button_menu.addAction(row.delete)

        self.append_new_player_widget(False)

    def pop_row(self):
        self.rows.pop().delete_widgets()
        while len(self.team_players) > len(self.rows):
            self.team_players.pop().delete_widgets()

    @asyncSlot()
    async def _row_show_preset_summary(self, row: RowWidget):
        row_index = self.rows.index(row)
        preset = self._game_session.presets[row_index]
        description = preset_describer.merge_categories(preset_describer.describe(preset))

        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowTitle(preset.name)
        message_box.setText(description)
        message_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
        await async_dialog.execute_dialog(message_box)

    @asyncSlot()
    @handle_network_errors
    async def _row_customize_preset(self, row: RowWidget):
        if self._logic_settings_window is not None:
            if self._logic_settings_window._game_session_row == row:
                self._logic_settings_window.raise_()
                self._logic_settings_window.activateWindow()
            else:
                # show warning that a dialog is already in progress?
                await async_dialog.warning(self, "Customize in progress",
                                           "A window for customizing a preset is already open. "
                                           "Please close it before continuing.",
                                           QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        row_index = self.rows.index(row)
        preset = self._game_session.presets[row_index]

        editor = PresetEditor(preset)
        self._logic_settings_window = LogicSettingsWindow(None, editor)
        self._logic_settings_window._game_session_row = row

        self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())
        editor.on_changed = lambda: self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())

        result = await async_dialog.execute_dialog(self._logic_settings_window)
        self._logic_settings_window = None

        if result == QtWidgets.QDialog.Accepted:
            await self._admin_global_action(
                SessionAdminGlobalAction.CHANGE_ROW,
                (row_index, editor.create_custom_preset_with().as_json))

    @asyncSlot()
    @handle_network_errors
    async def _row_import_preset(self, row: RowWidget, preset: Preset):
        row_index = self.rows.index(row)
        await self._admin_global_action(SessionAdminGlobalAction.CHANGE_ROW, (row_index, preset.as_json))

    def _row_save_preset(self, row: RowWidget):
        row_index = self.rows.index(row)
        preset = self._game_session.presets[row_index]

        existing_preset = self._preset_manager.preset_for_name(preset.name)
        if existing_preset is not None:
            if existing_preset == preset:
                return

            user_response = QMessageBox.warning(
                self,
                "Preset name conflict",
                "A preset named '{}' already exists. Do you want to overwrite it?".format(preset.name),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if user_response == QMessageBox.No:
                return

        self._preset_manager.add_new_preset(preset)

    @asyncSlot()
    @handle_network_errors
    async def _row_delete(self, row: RowWidget):
        row_index = self.rows.index(row)
        if row != self.rows[-1]:
            await async_dialog.message_box(self, QMessageBox.Critical,
                                           "Unable to delete row", "Can only delete the last row.")
        elif len(self.rows) <= 1:
            await async_dialog.message_box(self, QMessageBox.Critical,
                                           "Unable to delete row", "At least one row must remain.")
        else:
            await self._admin_global_action(SessionAdminGlobalAction.DELETE_ROW, row_index)

    # Team Functions
    def append_new_player_widget(self, is_observer: bool):
        if is_observer:
            parent_layout = self.observer_layout
            observer_index = len(self.observers)
            team_id = observer_index % 3
            row_id = observer_index // 3
        else:
            parent_layout = self.players_layout
            team_id = 0
            row_id = len(self.team_players)

        player_label = QtWidgets.QLabel(self.players_box)
        player_label.setText("")
        player_label.setWordWrap(True)
        parent_layout.addWidget(player_label, 2 + row_id, _PRESET_COLUMNS + team_id * 3)

        tool_button = QtWidgets.QToolButton(self.players_box)
        tool_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        tool_button.setText("...")
        parent_layout.addWidget(tool_button, 2 + row_id, _PRESET_COLUMNS + 1 + team_id * 3)

        tool_button_menu = QtWidgets.QMenu(tool_button)
        tool_button.setMenu(tool_button_menu)

        widget = PlayerWidget(
            name=player_label,
            tool=tool_button,
            kick=QtWidgets.QAction(tool_button_menu),
            promote=QtWidgets.QAction(tool_button_menu),
            open_tracker=QtWidgets.QAction(tool_button_menu),
            abandon=QtWidgets.QAction(tool_button_menu),
            move_up=QtWidgets.QAction(tool_button_menu),
            move_down=QtWidgets.QAction(tool_button_menu),
            switch_observer_action=QtWidgets.QAction(tool_button_menu),
        )

        def player_action(action: SessionAdminUserAction, arg):
            return functools.partial(self._admin_player_action_slot, widget, action, arg)

        widget.kick.setText("Kick Player")
        widget.kick.triggered.connect(player_action(SessionAdminUserAction.KICK, None))
        tool_button_menu.addAction(widget.kick)

        widget.promote.setText("Promote to Admin")
        widget.promote.triggered.connect(player_action(SessionAdminUserAction.SWITCH_ADMIN, None))
        tool_button_menu.addAction(widget.promote)

        widget.open_tracker.setText("Open Tracker (NYI)")
        tool_button_menu.addAction(widget.open_tracker)

        widget.abandon.setText("Abandon (NYI)")
        widget.abandon.triggered.connect(player_action(SessionAdminUserAction.ABANDON, None))
        tool_button_menu.addAction(widget.abandon)

        widget.move_up.setText("Move up one slot")
        widget.move_up.triggered.connect(player_action(SessionAdminUserAction.MOVE, -1))
        tool_button_menu.addAction(widget.move_up)

        widget.move_down.setText("Move down one slot")
        widget.move_down.triggered.connect(player_action(SessionAdminUserAction.MOVE, 1))
        tool_button_menu.addAction(widget.move_down)

        widget.switch_observer_action.setText("Move to Observer")
        widget.switch_observer_action.triggered.connect(functools.partial(self._switch_observer_action, widget))
        tool_button_menu.addAction(widget.switch_observer_action)

        if is_observer:
            self.observers.append(widget)
        else:
            self.team_players.append(widget)

    @asyncSlot(GameSessionEntry)
    async def on_game_session_updated(self, game_session: GameSessionEntry):
        self._game_session = game_session

        if self.network_client.current_user.id not in game_session.players:
            return await self._on_kicked()

        self.session_name_label.setText(game_session.name)
        self.advanced_options_tool.setEnabled(game_session.players[self.network_client.current_user.id].admin)

        self.sync_rows_to_game_session()
        self.sync_player_widgets_to_game_session()
        self.sync_background_process_to_game_session()
        self.update_game_tab()
        self.update_session_actions()
        await self.update_multiworld_client_status()
        await self.update_logic_settings_window()

    async def _on_kicked(self):
        await asyncio.gather(
            async_dialog.warning(self, "Kicked", "You have been kicked out of the session."),
            self.network_client.leave_game_session(False),
        )
        return QTimer.singleShot(0, self.close)

    def sync_rows_to_game_session(self):
        game_session = self._game_session
        self_player = game_session.players[self.network_client.current_user.id]

        while len(self.rows) > len(game_session.presets):
            self.pop_row()

        while len(self.rows) < len(game_session.presets):
            self.add_row()

        can_customize = game_session.generation_in_progress is None and game_session.seed_hash is None
        for i, (row, preset) in enumerate(zip(self.rows, game_session.presets)):
            row.set_preset(preset)
            row.set_is_admin(self_player.admin, is_your_row=self_player.row == i, can_customize=can_customize)

    def sync_player_widgets_to_game_session(self):
        game_session = self._game_session
        self_player = game_session.players[self.network_client.current_user.id]

        session_team = {}
        observers = []
        for player in game_session.players.values():
            if player.is_observer:
                observers.append(player)
            else:
                session_team[player.row] = player

        for row_id, player_widget in enumerate(self.team_players):
            player_widget.set_player(session_team.get(row_id))
            player_widget.update_player_widget(game_session, self_player)

        while len(self.observers) > len(observers):
            self.observers.pop().delete_widgets()

        while len(self.observers) < len(observers):
            self.append_new_player_widget(True)

        for observer, observer_widget in zip(observers, self.observers):
            observer_widget.set_player(observer)
            observer_widget.update_player_widget(game_session, self_player)

    def sync_background_process_to_game_session(self):
        game_session = self._game_session
        if game_session.generation_in_progress is not None:
            if not self._generating_game:
                other_player = game_session.players[game_session.generation_in_progress]
                self.progress_label.setText(f"Game being generated by {other_player.name}")

        elif self.has_background_process:
            if self._generating_game or game_session.seed_hash is None:
                self.stop_background_process()
        else:
            self.progress_label.setText("")

    def update_game_tab(self):
        game_session = self._game_session
        self_is_admin = game_session.players[self.network_client.current_user.id].admin

        self.session_status_label.setText(f"Session: {game_session.state.user_friendly_name}")
        self.update_background_process_button()
        self.generate_game_with_spoiler_action.setEnabled(self_is_admin)
        self.generate_game_without_spoiler_action.setEnabled(self_is_admin)
        self.import_permalink_action.setEnabled(self_is_admin)
        self.session_status_tool.setEnabled(self_is_admin)
        self.session_status_tool.setText("Start" if game_session.state == GameSessionState.SETUP else "Finish")

        self.save_iso_button.setEnabled(game_session.seed_hash is not None
                                        and not self.current_player_membership.is_observer)
        if game_session.seed_hash is None:
            self.generate_game_label.setText("<Game not generated>")
            self.view_game_details_button.setEnabled(False)
        else:
            self.generate_game_label.setText(f"Seed hash: {game_session.word_hash} ({game_session.seed_hash})")
            self.view_game_details_button.setEnabled(game_session.spoiler)

    def update_session_actions(self):
        self.history_table_widget.horizontalHeader().setVisible(True)
        self.history_table_widget.setRowCount(len(self._game_session.actions))
        for i, action in enumerate(self._game_session.actions):
            self.history_table_widget.setItem(i, 0, QtWidgets.QTableWidgetItem(action.message))
            self.history_table_widget.setItem(i, 1, QtWidgets.QTableWidgetItem(action.time.strftime("%H:%M")))

    async def update_multiworld_client_status(self):
        game_session_in_progress = self._game_session.state == GameSessionState.IN_PROGRESS

        if game_session_in_progress:
            if not self.multiworld_client.is_active:
                you = self._game_session.players[self.network_client.current_user.id]
                persist_path = self.network_client.server_data_path.joinpath(
                    f"game_session_{self._game_session.id}_{you.row}.json")
                await self.multiworld_client.start(persist_path)
        elif self.multiworld_client.is_active:
            await self.multiworld_client.stop()

    async def update_logic_settings_window(self):
        if self._logic_settings_window is not None:
            if self._game_session.seed_hash is not None:
                self._logic_settings_window.reject()
                await async_dialog.warning(self, "Game was generated",
                                           "A game was generated, so changing presets is no longer possible.")
            else:
                self._logic_settings_window.setEnabled(self._game_session.generation_in_progress is None)

    @property
    def current_player_membership(self) -> PlayerSessionEntry:
        user = self.network_client.current_user
        return self._game_session.players[user.id]

    @asyncSlot()
    @handle_network_errors
    async def _admin_global_action_slot(self, action: SessionAdminGlobalAction, arg):
        return await self._admin_global_action(action, arg)

    async def _admin_global_action(self, action: SessionAdminGlobalAction, arg):
        self.setEnabled(False)
        try:
            return await self.network_client.session_admin_global(self._game_session.id, action, arg)
        finally:
            self.setEnabled(True)

    @asyncSlot()
    @handle_network_errors
    async def _admin_player_action_slot(self, player: PlayerWidget, action: SessionAdminUserAction, arg):
        if player.player is None:
            raise RuntimeError("Admin action attempted on empty slot")
        return await self._admin_player_action(player.player, action, arg)

    async def _admin_player_action(self, player: PlayerSessionEntry, action: SessionAdminUserAction, arg):
        self.setEnabled(False)
        try:
            return await self.network_client.session_admin_player(self._game_session.id, player.id, action, arg)
        finally:
            self.setEnabled(True)

    @asyncSlot()
    @handle_network_errors
    async def _switch_observer_action(self, widget: PlayerWidget):
        if widget.player.is_observer:
            if any(row.player is None for row in self.team_players):
                return await self._admin_player_action(widget.player, SessionAdminUserAction.SWITCH_IS_OBSERVER, 0)
            else:
                return await async_dialog.warning(self, "No free slot",
                                                  "There are no free slots for players in this session.\n\n"
                                                  "Press 'New Row' to add more if needed.")
        else:
            return await self._admin_player_action(widget.player, SessionAdminUserAction.SWITCH_IS_OBSERVER, None)

    @asyncSlot()
    @handle_network_errors
    async def rename_session(self):
        await async_dialog.warning(self, "Not yet implemented",
                                   "Renaming session isn't implemented yet.")

    @asyncSlot()
    @handle_network_errors
    async def change_password(self):
        dialog = QtWidgets.QInputDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle("Enter password")
        dialog.setLabelText("Enter the new password for the session:")
        dialog.setTextEchoMode(QtWidgets.QLineEdit.Password)
        if await async_dialog.execute_dialog(dialog) == QtWidgets.QDialog.Accepted:
            await self._admin_global_action(SessionAdminGlobalAction.CHANGE_PASSWORD, dialog.textValue())

    @asyncSlot()
    @handle_network_errors
    async def delete_session(self):
        await async_dialog.warning(self, "Not yet implemented",
                                   "Deleting session isn't implemented yet.")

    async def generate_game(self, spoiler: bool):
        permalink = Permalink(
            seed_number=random.randint(0, 2 ** 31),
            spoiler=spoiler,
            presets={
                i: preset
                for i, preset in enumerate(self._game_session.presets)
            },
        )

        def generate_layout(progress_update: ProgressUpdateCallable):
            return simplified_patcher.generate_layout(progress_update=progress_update,
                                                      permalink=permalink,
                                                      options=self._options)

        await self._admin_global_action(SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, True)
        self._generating_game = True
        try:
            layout = await self.run_in_background_async(generate_layout, "Creating a seed...")
            self.update_progress(f"Finished generating, uploading...", 100)
            await self._upload_layout_description(layout)
            self.update_progress("Uploaded!", 100)

        except GenerationFailure as e:
            await self._admin_global_action(SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, False)

            message = "Error"
            if isinstance(e, GenerationFailure):
                message = "Generation Failure"
                self.failed_to_generate_signal.emit(e)

            self.update_progress(f"{message}: {e} - {type(e)}", -1)

        finally:
            self._generating_game = False

    async def clear_generated_game(self):
        result = await async_dialog.warning(
            self, "Clear generated game?",
            "Clearing the generated game will allow presets to be customized again, but all "
            "players must export the ISOs again.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if result == QMessageBox.Yes:
            await self._admin_global_action(SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION, None)

    @asyncSlot()
    @handle_network_errors
    async def generate_game_with_spoiler(self):
        await self.generate_game(True)

    @asyncSlot()
    @handle_network_errors
    async def generate_game_without_spoiler(self):
        await async_dialog.warning(self, "Not yet implemented",
                                   "Online game sessions without spoilers aren't available right now.")

    @asyncSlot()
    @handle_network_errors
    async def import_permalink(self):
        await async_dialog.warning(self, "Not yet implemented",
                                   "Importing permalinks aren't available right now.")

    async def _upload_layout_description(self, layout: LayoutDescription):
        await self._admin_global_action(SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION,
                                        layout.as_json)

    @asyncSlot()
    @handle_network_errors
    async def start_session(self):
        num_players = sum(1 for player in self._game_session.players.values() if not player.is_observer)
        if num_players != self._game_session.num_rows:
            await async_dialog.message_box(self,
                                           QMessageBox.Critical,
                                           "Missing players",
                                           "Unable to start the session: there are missing players.\n"
                                           "All slots of all teams must be filled before start.",
                                           QMessageBox.Ok)
            return

        await self._admin_global_action(SessionAdminGlobalAction.START_SESSION, None)

    @asyncSlot()
    @handle_network_errors
    async def finish_session(self):
        await async_dialog.warning(self, "NYI", "Finish session is not implemented.")

    @asyncSlot()
    @handle_network_errors
    async def reset_session(self):
        await async_dialog.warning(self, "NYI", "Reset session is not implemented.")

    @asyncSlot()
    async def _session_status_button_clicked(self):
        state = self._game_session.state
        if state == GameSessionState.SETUP:
            await self.start_session()
        elif state == GameSessionState.IN_PROGRESS:
            await self.finish_session()
        elif state == GameSessionState.FINISHED:
            await self.reset_session()
        else:
            raise RuntimeError(f"Unknown session state: {state}")

    @asyncSlot()
    @handle_network_errors
    async def save_iso(self):
        membership = self.current_player_membership
        if membership.is_observer:
            return await async_dialog.message_box(self, QtWidgets.QMessageBox.Critical,
                                                  "Invalid action", "Observers can't generate an ISO.", QMessageBox.Ok)

        if any(player.player is None for player in self.team_players):
            user_response = await async_dialog.warning(
                self,
                "Incomplete Session",
                ("This session is currently missing a player.\n"
                 "If you create an ISO right now, all references to that player will use a generic name instead.\n\n"
                 "Do you want to proceed?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if user_response == QMessageBox.No:
                return

        options = self._options
        dialog = GameInputDialog(options, "Echoes Randomizer - {}.iso".format(self._game_session.word_hash), False)
        result = await async_dialog.execute_dialog(dialog)

        if result != QtWidgets.QDialog.Accepted:
            return

        patcher_data = await self._admin_player_action(membership, SessionAdminUserAction.CREATE_PATCHER_FILE,
                                                       options.cosmetic_patches.as_json)
        shareable_hash = self._game_session.seed_hash

        configuration = self._game_session.presets[membership.row].layout_configuration
        game = data_reader.decode_data(configuration.game_data)
        game_specific = dataclasses.replace(
            game.game_specific,
            energy_per_tank=configuration.energy_per_tank,
            beam_configurations=configuration.beam_configuration.create_game_specific(game.resource_database))

        input_file = dialog.input_file
        output_file = dialog.output_file

        with options:
            options.output_directory = output_file.parent

        def work(progress_update: ProgressUpdateCallable):
            num_updaters = 2
            if input_file is not None:
                num_updaters += 1

            updaters = status_update_lib.split_progress_update(progress_update, num_updaters)
            if input_file is not None:
                simplified_patcher.unpack_iso(input_iso=input_file,
                                              options=options,
                                              progress_update=updaters[0])

            # Apply Layout
            simplified_patcher.apply_patcher_file(patcher_file=patcher_data,
                                                  game_specific=game_specific,
                                                  shareable_hash=shareable_hash,
                                                  options=options,
                                                  progress_update=updaters[-2])

            # Pack ISO
            simplified_patcher.pack_iso(output_iso=output_file,
                                        options=options,
                                        progress_update=updaters[-1])
            progress_update(f"Finished!", 1)

        self.run_in_background_thread(work, "Exporting...")

    @asyncSlot()
    @handle_network_errors
    async def view_game_details(self):
        if self._game_session.seed_hash is None:
            return await async_dialog.warning(self, "No Spoiler Available",
                                              "Unable to view game spoilers, no game available.")

        if not self._game_session.spoiler:
            return await async_dialog.warning(self, "No Spoiler Available",
                                              "Unable to view game spoilers, game was generated without spoiler.")

        description_json = await self._admin_global_action(SessionAdminGlobalAction.DOWNLOAD_LAYOUT_DESCRIPTION, None)
        description = LayoutDescription.from_json_dict(json.loads(description_json))
        self._window_manager.open_game_details(description)

    @asyncSlot()
    @handle_network_errors
    async def background_process_button_clicked(self):
        if self.has_background_process:
            self.stop_background_process()
        elif self._game_session.generation_in_progress is not None:
            await self._admin_global_action(SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, False)
        elif self._game_session.seed_hash is not None:
            await self.clear_generated_game()
        else:
            await self.generate_game(True)

    def update_background_process_button(self):
        is_admin = self.current_player_membership.admin
        if self.has_background_process:
            self.background_process_button.setEnabled(self.has_background_process or is_admin)
            self.background_process_button.setText("Stop")

        elif self._game_session.generation_in_progress is not None:
            self.background_process_button.setEnabled(is_admin)
            self.background_process_button.setText("Abort generation")
        else:
            self.background_process_button.setEnabled(self._game_session.state == GameSessionState.SETUP and is_admin)
            if self._game_session.seed_hash is not None:
                self.background_process_button.setText("Clear generated game")
            else:
                self.background_process_button.setText("Generate game")

    def enable_buttons_with_background_tasks(self, value: bool):
        self.update_background_process_button()

    def update_progress(self, message: str, percentage: int):
        self.progress_label.setText(message)
        if "Aborted" in message:
            percentage = 0
        if percentage >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percentage)
        else:
            self.progress_bar.setRange(0, 0)

    def _open_user_preferences_dialog(self):
        dialog = EchoesUserPreferencesDialog(self, self._options.cosmetic_patches)
        result = dialog.exec_()
        if result == QtWidgets.QDialog.Accepted:
            with self._options as options:
                options.cosmetic_patches = dialog.cosmetic_patches

    def on_server_connection_state_updated(self, state: ConnectionState):
        self.server_connection_button.setEnabled(state == ConnectionState.Disconnected)
        self.server_connection_label.setText(f"Server: {state.value}")

    def on_game_connection_status_updated(self, status: ConnectionStatus):
        self.game_connection_label.setText(self.game_connection.pretty_current_status)

    @asyncSlot()
    @handle_network_errors
    async def _connect_to_server(self):
        await self.network_client.connect_to_server()
