import asyncio
import dataclasses
import functools
import random
from typing import List, Optional

from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QMainWindow, QMessageBox
from asyncqt import asyncSlot, asyncClose

from randovania.game_connection.connection_backend import ConnectionStatus
from randovania.game_description import data_reader
from randovania.gui.dialog.echoes_user_preferences_dialog import EchoesUserPreferencesDialog
from randovania.gui.dialog.game_input_dialog import GameInputDialog
from randovania.gui.dialog.logic_settings_window import LogicSettingsWindow
from randovania.gui.generated.game_session_ui import Ui_GameSessionWindow
from randovania.gui.lib import common_qt_lib, preset_describer, async_dialog
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.qt_network_client import handle_network_errors
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
    move_team_menu: QtWidgets.QMenu
    move_actions: List[QtWidgets.QAction]
    new_team_action: QtWidgets.QAction
    move_to_observer: QtWidgets.QAction
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
                action.setVisible(player.team is not None)
        else:
            self.set_visible(False)


@dataclasses.dataclass(frozen=True)
class Team:
    vertical_line: QtWidgets.QFrame
    title_line: QtWidgets.QFrame
    title_label: QtWidgets.QLabel
    players: List[PlayerWidget]

    def delete_widgets(self):
        for widget in [self.vertical_line, self.title_line, self.title_label]:
            widget.deleteLater()

        for player in self.players:
            player.delete_widgets()


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

    def set_is_admin(self, is_admin: bool):
        for widget in (self.customize, self.import_menu, self.delete):
            widget.setEnabled(is_admin)

    def set_preset(self, preset: Preset):
        self.name.setText(preset.name)


_PRESET_COLUMNS = 3


class GameSessionWindow(QMainWindow, Ui_GameSessionWindow, BackgroundTaskMixin):
    teams: List[Team]
    observers: List[PlayerWidget]
    rows: List[RowWidget]
    _game_session: GameSessionEntry
    has_closed = False
    _logic_settings_window: Optional[LogicSettingsWindow] = None

    on_generated_layout_signal = Signal(LayoutDescription)
    failed_to_generate_signal = Signal(GenerationFailure)

    def __init__(self, game_session: GameSessionEntry, preset_manager: PresetManager, options: Options):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.network_client = common_qt_lib.get_network_client()
        self.game_connection = common_qt_lib.get_game_connection()
        self.multiworld_client = MultiworldClient(self.network_client, self.game_connection)

        self._preset_manager = preset_manager
        self._options = options

        parent = self.central_widget

        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.progress_update_signal.connect(self.update_progress)
        self.stop_background_process_button.clicked.connect(self.stop_background_process)
        self.generate_game_button.clicked.connect(functools.partial(self.generate_game, True))
        self.generate_without_spoiler_button.clicked.connect(functools.partial(self.generate_game, False))
        self.customize_user_preferences_button.clicked.connect(self._open_user_preferences_dialog)
        self.session_status_tool.clicked.connect(self._session_status_button_clicked)
        self.save_iso_button.clicked.connect(self.save_iso)
        self.on_generated_layout_signal.connect(self._upload_layout_description)
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
        self.session_status_menu.addAction(self.start_session_action)
        self.finish_session_action = QtWidgets.QAction("Finish session", self.session_status_menu)
        self.finish_session_action.setEnabled(False)
        self.session_status_menu.addAction(self.finish_session_action)
        self.reset_session_action = QtWidgets.QAction("Reset session", self.session_status_menu)
        self.reset_session_action.setEnabled(False)
        self.session_status_menu.addAction(self.reset_session_action)
        self.session_status_tool.setMenu(self.session_status_menu)

        self.players_box = QtWidgets.QGroupBox(parent)
        self.players_box.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                                             QtWidgets.QSizePolicy.Minimum))
        self.players_layout = QtWidgets.QGridLayout(self.players_box)

        self.new_row_button = QtWidgets.QPushButton(self.players_box)
        self.new_row_button.clicked.connect(functools.partial(
            self._admin_global_action_slot, SessionAdminGlobalAction.CREATE_ROW,
            self._preset_manager.default_preset.as_json))
        self.new_row_button.setText("New Row")
        self.players_layout.addWidget(self.new_row_button, 0, 0, 1, 2)

        self.presets_line = QtWidgets.QFrame(self.players_box)
        self.presets_line.setFrameShape(QtWidgets.QFrame.HLine)
        self.presets_line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.players_layout.addWidget(self.presets_line, 1, 0, 1, 2)

        self.teams = []
        self.rows = []
        self.observers = []

        self.main_layout.insertWidget(1, self.players_box)

        spacer_item = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.main_layout.insertSpacerItem(2, spacer_item)

        self.network_client.GameSessionUpdated.connect(self.on_game_session_updated)
        self.on_game_session_updated(game_session)

        self.network_client.ConnectionStateUpdated.connect(self.on_server_connection_state_updated)
        self.on_server_connection_state_updated(self.network_client.connection_state)
        self.game_connection.StatusUpdated.connect(self.on_game_connection_status_updated)
        self.on_game_connection_status_updated(self.game_connection.current_status)
        asyncio.get_event_loop().create_task(self.multiworld_client.start())

    @asyncClose
    async def closeEvent(self, event: QtGui.QCloseEvent):
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
                await self.network_client.leave_session(user_response == QMessageBox.Yes)
        finally:
            super().closeEvent(event)
        self.has_closed = True

    def _show_failed_generation_exception(self, exception: GenerationFailure):
        QMessageBox.critical(self._window_manager,
                             "An error occurred while generating a seed",
                             "{}\n\nSome errors are expected to occur, please try again.".format(exception))

    # Row Functions
    @property
    def num_players(self) -> int:
        return len(self.rows)

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

        for team in self.teams:
            self.append_new_player_widget(team)

    def pop_row(self):
        self.rows.pop().delete_widgets()
        for team in self.teams:
            while len(team.players) > len(self.rows):
                team.players.pop().delete_widgets()

    def _row_show_preset_summary(self, row: RowWidget):
        row_index = self.rows.index(row)
        preset = self._game_session.presets[row_index]
        description = preset_describer.merge_categories(preset_describer.describe(preset))

        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowTitle(preset.name)
        message_box.setText(description)
        message_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
        message_box.exec_()

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
    def add_team(self) -> int:
        num_teams = len(self.teams)
        vertical_line = QtWidgets.QFrame(self.players_box)
        vertical_line.setFrameShape(QtWidgets.QFrame.VLine)
        vertical_line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.players_layout.addWidget(vertical_line, 0, (_PRESET_COLUMNS - 1) + num_teams * 3, -1, 1)

        title_line = QtWidgets.QFrame(self.players_box)
        title_line.setFrameShape(QtWidgets.QFrame.HLine)
        title_line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.players_layout.addWidget(title_line, 1, _PRESET_COLUMNS + num_teams * 3, 1, 2)

        team_name = QtWidgets.QLabel(self.players_box)
        team_name.setText(f"Team {num_teams + 1}")
        team_name.setMaximumHeight(30)
        self.players_layout.addWidget(team_name, 0, _PRESET_COLUMNS + num_teams * 3, 1, 2)

        self.history_team_combo.addItem(f"Team {num_teams + 1}")

        self.teams.append(Team(
            vertical_line=vertical_line,
            title_line=title_line,
            title_label=team_name,
            players=[],
        ))
        for _ in self.rows:
            self.append_new_player_widget(self.teams[-1])

        return len(self.teams) - 1

    def pop_team(self):
        self.history_team_combo.removeItem(self.history_team_combo.count() - 1)
        self.teams.pop().delete_widgets()

    def append_new_player_widget(self, team: Optional[Team]):
        if team is None:
            parent_layout = self.observer_layout
            observer_index = len(self.observers)
            team_id = observer_index % 3
            row_id = observer_index // 3
        else:
            parent_layout = self.players_layout
            team_id = self.teams.index(team)
            row_id = len(team.players)

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
        move_team_menu = QtWidgets.QMenu(tool_button_menu)

        widget = PlayerWidget(
            name=player_label,
            tool=tool_button,
            kick=QtWidgets.QAction(tool_button_menu),
            promote=QtWidgets.QAction(tool_button_menu),
            open_tracker=QtWidgets.QAction(tool_button_menu),
            abandon=QtWidgets.QAction(tool_button_menu),
            move_up=QtWidgets.QAction(tool_button_menu),
            move_down=QtWidgets.QAction(tool_button_menu),
            move_team_menu=move_team_menu,
            move_actions=[],
            new_team_action=QtWidgets.QAction(move_team_menu),
            move_to_observer=QtWidgets.QAction(move_team_menu),
        )

        widget.kick.setText("Kick Player")
        widget.kick.triggered.connect(functools.partial(
            self._admin_player_action_slot, widget, SessionAdminUserAction.KICK, None))
        tool_button_menu.addAction(widget.kick)

        widget.promote.setText("Promote to Admin")
        widget.promote.triggered.connect(functools.partial(
            self._admin_player_action_slot, widget, SessionAdminUserAction.SWITCH_ADMIN, None))
        tool_button_menu.addAction(widget.promote)

        widget.open_tracker.setText("Open Tracker")
        tool_button_menu.addAction(widget.open_tracker)

        widget.abandon.setText("Abandon")
        widget.abandon.triggered.connect(functools.partial(
            self._admin_player_action_slot, widget, SessionAdminUserAction.ABANDON, None))
        tool_button_menu.addAction(widget.abandon)

        widget.move_up.setText("Move up one slot")
        widget.move_up.triggered.connect(functools.partial(
            self._admin_player_action_slot, widget, SessionAdminUserAction.MOVE, -1))
        tool_button_menu.addAction(widget.move_up)

        widget.move_down.setText("Move down one slot")
        widget.move_down.triggered.connect(functools.partial(
            self._admin_player_action_slot, widget, SessionAdminUserAction.MOVE, 1))
        tool_button_menu.addAction(widget.move_down)

        move_team_menu.setTitle("Move to team")
        tool_button_menu.addMenu(move_team_menu)

        widget.new_team_action.setText("New Team")
        widget.new_team_action.triggered.connect(functools.partial(
            self._admin_player_action_slot, widget, SessionAdminUserAction.SWITCH_TO_NEW_TEAM, None))
        move_team_menu.addAction(widget.new_team_action)

        widget.move_to_observer.setText("Observer")
        widget.move_to_observer.triggered.connect(functools.partial(
            self._admin_player_action_slot, widget, SessionAdminUserAction.SWITCH_TEAM, None))
        move_team_menu.addAction(widget.move_to_observer)

        if team is None:
            self.observers.append(widget)
        else:
            team.players.append(widget)

    @property
    def num_teams(self) -> int:
        return len(self.teams)

    def update_session_actions(self):
        team_index = self.history_team_combo.currentIndex()
        team_actions = [action for action in self._game_session.actions if action.team == team_index]
        self.history_table_widget.horizontalHeader().setVisible(True)
        self.history_table_widget.setRowCount(len(team_actions))
        for i, action in enumerate(team_actions):
            self.history_table_widget.setItem(i, 0, QtWidgets.QTableWidgetItem(action.message))
            self.history_table_widget.setItem(i, 1, QtWidgets.QTableWidgetItem(action.time.strftime("%H:%M")))

    def on_game_session_updated(self, game_session: GameSessionEntry):
        self._game_session = game_session

        self_is_admin = game_session.players[self.network_client.current_user.id].admin

        self.session_name_edit.setText(game_session.name)

        while len(self.rows) > len(game_session.presets):
            self.pop_row()

        while self.num_teams < game_session.num_teams:
            self.add_team()

        while self.num_teams > game_session.num_teams:
            self.pop_team()

        while len(self.rows) < len(game_session.presets):
            self.add_row()

        for row, preset in zip(self.rows, game_session.presets):
            row.set_preset(preset)
            row.set_is_admin(self_is_admin)

        teams = [{} for _ in range(game_session.num_teams)]
        observers = []
        for player in game_session.players.values():
            if player.team is not None:
                teams[player.team][player.row] = player
            else:
                observers.append(player)

        team_has_slot = [
            len(team) < len(self.rows)
            for i, team in enumerate(teams)
        ]
        for team_id, team in enumerate(self.teams):
            for row_id, player in enumerate(team.players):
                player.set_player(teams[team_id].get(row_id))
                self._update_player_widget(player, game_session, self_is_admin, team_has_slot)

        while len(self.observers) > len(observers):
            self.observers.pop().delete_widgets()

        while len(self.observers) < len(observers):
            self.append_new_player_widget(None)

        for observer, observer_widget in zip(observers, self.observers):
            observer_widget.set_player(observer)
            self._update_player_widget(observer_widget, game_session, self_is_admin, team_has_slot)

        # Game Tab
        self.session_status_label.setText("Session: {}".format("In-Game" if game_session.in_game else "Not Started"))
        self.generate_game_button.setEnabled(self_is_admin)
        self.generate_without_spoiler_button.setEnabled(self_is_admin and False)
        self.session_status_tool.setEnabled(self_is_admin and game_session.seed_hash is not None)
        self.session_status_tool.setEnabled(self.session_status_tool.isEnabled())
        self.session_status_tool.setText("Finish" if game_session.in_game else "Start")

        self.save_iso_button.setEnabled(game_session.seed_hash is not None
                                        and self.current_player_membership.team is not None)
        if game_session.seed_hash is None:
            self.generate_game_label.setText("<Game not generated>")
            self.view_game_details_button.setEnabled(False)
        else:
            self.generate_game_label.setText(f"Seed hash: {game_session.word_hash} ({game_session.seed_hash})")
            self.view_game_details_button.setEnabled(game_session.spoiler and False)

        self.update_session_actions()

    @property
    def current_player_membership(self) -> PlayerSessionEntry:
        user = self.network_client.current_user
        return self._game_session.players[user.id]

    def _update_player_widget(self,
                              player_widget: PlayerWidget,
                              game_session: GameSessionEntry,
                              self_is_admin, team_has_slot):

        player = player_widget.player
        if player is None:
            return

        player_name = player.name
        if player.id == self.network_client.current_user.id:
            player_name += " (You)"
            admin_or_you = True
        else:
            admin_or_you = self_is_admin

        for i in range(len(player_widget.move_actions), self.num_teams):
            action = QtWidgets.QAction(player_widget.move_team_menu)
            action.setText(f"Team {i + 1}")
            action.triggered.connect(functools.partial(
                self._admin_player_action_slot, player_widget, SessionAdminUserAction.SWITCH_TEAM, i))
            player_widget.move_team_menu.insertAction(player_widget.new_team_action, action)
            player_widget.move_actions.append(action)

        player_is_admin = game_session.players[player_widget.player.id].admin
        if player_is_admin:
            promote_text = "Demote from Admin"
            num_required = 2
            player_name = "[Admin] " + player_name
        else:
            promote_text = "Promote to Admin"
            num_required = 1

        player_widget.name.setText(player_name)
        player_widget.promote.setText(promote_text)
        player_widget.promote.setEnabled(self_is_admin and game_session.num_admins >= num_required)
        player_widget.move_up.setEnabled(admin_or_you and player.row > 0)
        player_widget.move_down.setEnabled(admin_or_you and player.row + 1 < self.num_players)
        player_widget.abandon.setEnabled(admin_or_you)
        player_widget.move_to_observer.setEnabled(admin_or_you and player.team is not None)

        while len(player_widget.move_actions) > self.num_teams:
            player_widget.move_actions.pop().deleteLater()

        for i, action in enumerate(player_widget.move_actions):
            action.setEnabled(admin_or_you and team_has_slot[i] and (i != player.team))

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

    def generate_game(self, spoiler: bool):
        permalink = Permalink(
            seed_number=random.randint(0, 2 ** 31),
            spoiler=spoiler,
            presets={
                i: preset
                for i, preset in enumerate(self._game_session.presets)
            },
        )

        def work(progress_update: ProgressUpdateCallable):
            try:
                layout = simplified_patcher.generate_layout(progress_update=progress_update,
                                                            permalink=permalink,
                                                            options=self._options)
                progress_update(f"Success! Uploading...", 1)
                self.on_generated_layout_signal.emit(layout)

            except GenerationFailure as generate_exception:
                self.failed_to_generate_signal.emit(generate_exception)
                progress_update("Generation Failure: {}".format(generate_exception), -1)

        self.run_in_background_thread(work, "Creating a seed...")

    def _upload_layout_description(self, layout: LayoutDescription):
        self._upload_task = asyncio.create_task(
            self._admin_global_action(SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION, layout.as_json))

    @asyncSlot()
    @handle_network_errors
    async def start_session(self):
        if len(self._game_session.players) != self._game_session.num_teams * len(self._game_session.presets):
            await async_dialog.message_box(self,
                                           QMessageBox.Critical,
                                           "Missing players",
                                           "Unable to start the session: there are missing players.\n"
                                           "All slots of all teams must be filled before start.",
                                           QMessageBox.Ok)
            return

        await self._admin_global_action(SessionAdminGlobalAction.START_SESSION, None)

    @asyncSlot()
    async def _session_status_button_clicked(self):
        if self._game_session.in_game:
            await async_dialog.warning(self, "NYI", "Finish session not implemented.")
        else:
            await self.start_session()

    @asyncSlot()
    @handle_network_errors
    async def save_iso(self):
        membership = self.current_player_membership
        team = membership.team
        if team is None:
            return await async_dialog.message_box(self, QtWidgets.QMessageBox.Critical,
                                                  "Invalid action", "Observers can't generate an ISO.", QMessageBox.Ok)

        if any(player.player is None for player in self.teams[team].players):
            user_response = await async_dialog.warning(
                self,
                "Incomplete Team",
                ("Your team is currently missing a member.\n"
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

    def enable_buttons_with_background_tasks(self, value: bool):
        self.stop_background_process_button.setEnabled(not value)

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
