import asyncio
import dataclasses
import functools
import json
import logging
import random
from pathlib import Path
from typing import Optional

from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QMessageBox
from qasync import asyncSlot, asyncClose

from randovania.game_connection.game_connection import GameConnection
from randovania.game_description import default_database
from randovania.games.game import RandovaniaGame
from randovania.gui import game_specific_gui
from randovania.gui.dialog.login_prompt_dialog import LoginPromptDialog
from randovania.gui.dialog.permalink_dialog import PermalinkDialog
from randovania.gui.generated.game_session_ui import Ui_GameSessionWindow
from randovania.gui.lib import common_qt_lib, async_dialog, game_exporter, file_prompts
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.game_connection_setup import GameConnectionSetup
from randovania.gui.lib.generation_failure_handling import GenerationFailureHandler
from randovania.gui.lib.qt_network_client import handle_network_errors, QtNetworkClient
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.multiworld_client import MultiworldClient, BackendInUse
from randovania.gui.preset_settings.customize_preset_dialog import CustomizePresetDialog
from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options, InfoAlert
from randovania.interface_common.preset_editor import PresetEditor
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout import preset_describer
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink
from randovania.layout.versioned_preset import InvalidPreset, VersionedPreset
from randovania.lib.status_update_lib import ProgressUpdateCallable
from randovania.network_client.game_session import GameSessionEntry, PlayerSessionEntry, GameSessionActions, \
    GameSessionAuditLog
from randovania.network_client.network_client import ConnectionState, UnableToConnect
from randovania.network_common import error
from randovania.network_common.admin_actions import SessionAdminUserAction, SessionAdminGlobalAction
from randovania.network_common.session_state import GameSessionState
from randovania.resolver.exceptions import GenerationFailure

logger = logging.getLogger(__name__)


@dataclasses.dataclass()
class PlayerWidget:
    name: QtWidgets.QLabel
    connection_state: QtWidgets.QLabel | None
    tool: QtWidgets.QToolButton
    kick: QtGui.QAction
    promote: QtGui.QAction
    open_tracker: QtGui.QAction
    abandon: QtGui.QAction
    move_up: QtGui.QAction
    move_down: QtGui.QAction
    switch_observer_action: QtGui.QAction
    player: PlayerSessionEntry | None = None

    @property
    def widgets(self) -> list[QtWidgets.QWidget]:
        result = [self.name, self.tool]
        if self.connection_state is not None:
            result.append(self.connection_state)
        return result

    def delete_widgets(self):
        for widget in self.widgets:
            widget.deleteLater()

    def set_visible(self, value: bool):
        for widget in self.widgets:
            widget.setVisible(value)

    def set_player(self, player: PlayerSessionEntry | None):
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
            num_required = 0

        self.name.setText(player_name)
        if self.connection_state is not None:
            self.connection_state.setText(player.connection_state)
        self.kick.setEnabled(self_player.admin and player.id != self_player.id)
        self.promote.setText(promote_text)
        self.promote.setEnabled((self_player.admin or game_session.num_admins == 0)
                                and game_session.num_admins >= num_required)
        if not player.is_observer:
            self.move_up.setEnabled(admin_or_you and player.row > 0)
            self.move_down.setEnabled(admin_or_you and player.row + 1 < game_session.num_rows)
        self.abandon.setEnabled(admin_or_you)
        self.switch_observer_action.setText("Include in session" if player.is_observer else "Move to observers")
        self.switch_observer_action.setEnabled(admin_or_you)


@dataclasses.dataclass()
class RowWidget:
    name: QtWidgets.QLabel
    tool: QtWidgets.QToolButton
    view_summary: QtGui.QAction
    customize: QtGui.QAction
    import_menu: QtWidgets.QMenu
    import_actions: list[QtGui.QAction]
    export_menu: QtWidgets.QMenu
    export_actions: list[QtGui.QAction]
    delete: QtGui.QAction

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

    def set_preset(self, preset: VersionedPreset, include_game: bool):
        if include_game:
            self.name.setText(f"({preset.game.short_name}) {preset.name}")
        else:
            self.name.setText(preset.name)
        self.export_menu.setEnabled(preset.base_preset_uuid is not None)


_PRESET_COLUMNS = 3


class GameSessionWindow(QtWidgets.QMainWindow, Ui_GameSessionWindow, BackgroundTaskMixin):
    team_players: list[PlayerWidget]
    observers: list[PlayerWidget]
    rows: list[RowWidget]
    _game_session: GameSessionEntry
    has_closed = False
    _logic_settings_window: CustomizePresetDialog | None = None
    _window_manager: WindowManager
    _generating_game: bool = False
    _already_kicked = False
    _can_stop_background_process = True

    def __init__(self, network_client: QtNetworkClient, game_connection: GameConnection,
                 preset_manager: PresetManager, window_manager: WindowManager, options: Options):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.network_client = network_client
        self.game_connection = game_connection
        self.multiworld_client = MultiworldClient(self.network_client, self.game_connection)
        self.failure_handler = GenerationFailureHandler(self)

        self._preset_manager = preset_manager
        self._window_manager = window_manager
        self._options = options
        self._update_status_lock = asyncio.Lock()

        # Advanced Options
        self.advanced_options_menu = QtWidgets.QMenu(self.advanced_options_tool)
        self.rename_session_action = QtGui.QAction("Change title", self.advanced_options_menu)
        self.change_password_action = QtGui.QAction("Change password", self.advanced_options_menu)
        self.duplicate_session_action = QtGui.QAction("Duplicate session", self.advanced_options_menu)

        self.advanced_options_menu.addAction(self.rename_session_action)
        self.advanced_options_menu.addAction(self.change_password_action)
        self.advanced_options_menu.addAction(self.duplicate_session_action)
        self.advanced_options_tool.setMenu(self.advanced_options_menu)

        # Save ISO Button
        self.save_iso_menu = QtWidgets.QMenu(self.save_iso_button)
        self.copy_permalink_action = QtGui.QAction("Copy Permalink", self.save_iso_menu)

        self.save_iso_menu.addAction(self.copy_permalink_action)
        self.save_iso_button.setMenu(self.save_iso_menu)

        # Background process Button
        self.background_process_menu = QtWidgets.QMenu(self.background_process_button)
        self.generate_game_with_spoiler_action = QtGui.QAction("Generate game", self.background_process_menu)
        self.generate_game_with_spoiler_no_retry_action = QtGui.QAction("Generate game (no retries)",
                                                                        self.background_process_menu)
        self.generate_game_without_spoiler_action = QtGui.QAction("Generate without spoiler",
                                                                  self.background_process_menu)
        self.import_permalink_action = QtGui.QAction("Import permalink", self.background_process_menu)
        self.import_layout_action = QtGui.QAction("Import game/spoiler", self.background_process_menu)

        self.background_process_menu.addAction(self.generate_game_with_spoiler_action)
        self.background_process_menu.addAction(self.generate_game_with_spoiler_no_retry_action)
        self.background_process_menu.addAction(self.generate_game_without_spoiler_action)
        self.background_process_menu.addAction(self.import_permalink_action)
        self.background_process_menu.addAction(self.import_layout_action)
        self.background_process_button.setMenu(self.background_process_menu)

        # Game Connection
        self.game_connection_setup = GameConnectionSetup(self, self.game_connection_label,
                                                         self.game_connection, self._options)
        self.game_connection_setup.setup_tool_button_menu(self.game_connection_tool)

        # Session status
        self.session_status_menu = QtWidgets.QMenu(self.session_status_tool)
        self.start_session_action = QtGui.QAction("Start session", self.session_status_menu)
        self.finish_session_action = QtGui.QAction("Finish session", self.session_status_menu)
        self.reset_session_action = QtGui.QAction("Reset session", self.session_status_menu)

        self.session_status_menu.addAction(self.start_session_action)
        self.session_status_menu.addAction(self.finish_session_action)
        self.session_status_menu.addAction(self.reset_session_action)
        self.session_status_tool.setMenu(self.session_status_menu)

        self.players_layout.addWidget(self.players_vertical_line, 0, 2, -1, 1)

        self.rows = []
        self.observers = []
        self.team_players = []

        # tab stuff
        self.splitDockWidget(self.players_dock, self.game_dock, Qt.Vertical)
        self.splitDockWidget(self.game_dock, self.observers_dock, Qt.Horizontal)
        self.tabifyDockWidget(self.game_dock, self.history_dock)
        self.tabifyDockWidget(self.game_dock, self.audit_dock)
        self.game_dock.raise_()

        self.resizeDocks([self.players_dock, self.game_dock],
                         [self.height() - 200, 100],
                         Qt.Vertical)

    def connect_to_events(self):
        # Advanced Options
        self.rename_session_action.triggered.connect(self.rename_session)
        self.change_password_action.triggered.connect(self.change_password)
        self.duplicate_session_action.triggered.connect(self.duplicate_session)

        # Save ISO Button
        self.copy_permalink_action.triggered.connect(self.copy_permalink)

        self.generate_game_with_spoiler_action.triggered.connect(self.generate_game_with_spoiler)
        self.generate_game_with_spoiler_no_retry_action.triggered.connect(self.generate_game_with_spoiler_no_retry)
        self.generate_game_without_spoiler_action.triggered.connect(self.generate_game_without_spoiler)
        self.import_permalink_action.triggered.connect(self.import_permalink)
        self.import_layout_action.triggered.connect(self.import_layout)
        self.background_process_button.clicked.connect(self.background_process_button_clicked)

        # Signals
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.progress_update_signal.connect(self.update_progress)
        self.customize_user_preferences_button.clicked.connect(self._open_user_preferences_dialog)
        self.session_status_tool.clicked.connect(self._session_status_button_clicked)
        self.save_iso_button.clicked.connect(self.save_iso)
        self.view_game_details_button.clicked.connect(self.view_game_details)

        # Server Status
        self.server_connection_button.clicked.connect(self._connect_to_server)

        # Session status
        self.start_session_action.triggered.connect(self.start_session)
        self.finish_session_action.triggered.connect(self.finish_session)
        self.reset_session_action.triggered.connect(self.reset_session)
        self.new_row_button.clicked.connect(functools.partial(
            self._admin_global_action_slot, SessionAdminGlobalAction.CREATE_ROW,
            self._preset_manager.default_preset.as_json))

        self.multiworld_client.PendingUploadCount.connect(self.on_pending_upload_count_changed)
        self.network_client.GameSessionMetaUpdated.connect(self.on_game_session_meta_update)
        self.network_client.GameSessionActionsUpdated.connect(self.on_game_session_actions_update)
        self.network_client.GameSessionAuditLogUpdated.connect(self.on_game_session_audit_log_update)
        self.network_client.ConnectionStateUpdated.connect(self.on_server_connection_state_updated)
        self.game_connection.Updated.connect(self.on_game_connection_updated)

    @classmethod
    async def create_and_update(cls, network_client: QtNetworkClient, game_connection: GameConnection,
                                preset_manager: PresetManager, window_manager: WindowManager, options: Options,
                                ) -> Optional["GameSessionWindow"]:

        logger.debug("Creating GameSessionWindow")
        try:
            window = cls(network_client, game_connection, preset_manager, window_manager, options)
            await window.on_game_session_meta_update(network_client.current_game_session_meta)
            window.update_session_actions(network_client.current_game_session_actions)
            window.update_session_audit_log(network_client.current_game_session_audit_log)
            window.on_server_connection_state_updated(network_client.connection_state)
            window.connect_to_events()
            await window.on_game_connection_updated()

            logger.debug("Finished creating GameSessionWindow")

            return window

        except BackendInUse as e:
            await async_dialog.warning(
                window_manager, "Existing Connection",
                "Another instance of Randovania is already connected to an online session.\n"
                "Please close it before continuing.\n\n"
                f"If this error continues, please delete the following file:\n{e.lock_file}")

    @asyncClose
    async def closeEvent(self, event: QtGui.QCloseEvent):
        return await self._on_close_event(event)

    async def _on_close_event(self, event: QtGui.QCloseEvent):
        is_kicked = self.network_client.current_user.id not in self._game_session.players

        await self.multiworld_client.stop()
        try:
            self.multiworld_client.PendingUploadCount.disconnect(self.on_pending_upload_count_changed)
        except Exception as e:
            logging.exception(f"Unable to disconnect: {e}")
        try:
            self.network_client.GameSessionMetaUpdated.disconnect(self.on_game_session_meta_update)
        except Exception as e:
            logging.exception(f"Unable to disconnect: {e}")
        try:
            self.network_client.ConnectionStateUpdated.disconnect(self.on_server_connection_state_updated)
        except Exception as e:
            logging.exception(f"Unable to disconnect: {e}")
        try:
            self.game_connection.Updated.disconnect(self.on_game_connection_updated)
        except Exception as e:
            logging.exception(f"Unable to disconnect: {e}")

        try:
            if not is_kicked and not self.network_client.connection_state.is_disconnected:
                await self.network_client.leave_game_session(False)
        finally:
            for d in [self.players_dock, self.game_dock, self.observers_dock, self.history_dock]:
                d.close()
            super().closeEvent(event)
        self.has_closed = True

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
        export_menu = QtWidgets.QMenu(tool_button_menu)

        row = RowWidget(
            name=preset_name,
            tool=tool_button,
            view_summary=QtGui.QAction(tool_button_menu),
            customize=QtGui.QAction(tool_button_menu),
            import_menu=import_menu,
            import_actions=[],
            export_menu=export_menu,
            export_actions=[],
            delete=QtGui.QAction(tool_button_menu),
        )
        self.rows.append(row)

        row.view_summary.setText("View preset summary")
        row.view_summary.triggered.connect(functools.partial(self._row_show_preset_summary, row))
        tool_button_menu.addAction(row.view_summary)

        row.customize.setText("Customize preset")
        row.customize.triggered.connect(functools.partial(self._row_customize_preset, row))
        tool_button_menu.addAction(row.customize)

        row.import_menu.setTitle("Import preset")
        tool_button_menu.addMenu(row.import_menu)
        self._create_actions_for_import_menu(row)

        row.export_menu.setTitle("Export preset")
        tool_button_menu.addMenu(row.export_menu)

        save_copy = QtGui.QAction(tool_button_menu)
        save_copy.setText("Save copy of preset")
        save_copy.triggered.connect(functools.partial(self._row_save_preset_to_manager, row))
        row.export_actions.append(save_copy)
        export_menu.addAction(save_copy)

        save_to_file = QtGui.QAction(tool_button_menu)
        save_to_file.setText("Save to file")
        save_to_file.triggered.connect(functools.partial(self._row_save_preset_to_file, row))
        row.export_actions.append(save_to_file)
        export_menu.addAction(save_to_file)

        row.delete.setText("Delete session row")
        row.delete.triggered.connect(functools.partial(self._row_delete, row))
        tool_button_menu.addAction(row.delete)

        self.append_new_player_widget(False)

    def pop_row(self):
        self.rows.pop().delete_widgets()
        while len(self.team_players) > len(self.rows):
            self.team_players.pop().delete_widgets()

    def _create_actions_for_import_menu(self, row: RowWidget):
        def _add_single(preset: VersionedPreset, parent: QtWidgets.QMenu):
            action = QtGui.QAction(parent)
            action.setText(preset.name)
            action.triggered.connect(functools.partial(self._row_import_preset, row, preset))
            row.import_actions.append(action)
            parent.addAction(action)

        def _add(game: RandovaniaGame, parent: QtWidgets.QMenu):
            for preset in self._preset_manager.included_presets.values():
                if preset.game == game:
                    _add_single(preset, parent)

            parent.addSeparator()

            for preset in sorted(self._preset_manager.custom_presets.values(), key=lambda it: it.name):
                if preset.game == game:
                    _add_single(preset, parent)

        if len(self._game_session.allowed_games) > 1:
            for g in self._game_session.allowed_games:
                menu = QtWidgets.QMenu(row.import_menu)
                menu.setTitle(g.long_name)
                row.import_menu.addMenu(menu)
                _add(g, menu)
        else:
            _add(self._game_session.allowed_games[0], row.import_menu)

        from_file_action = QtGui.QAction(row.import_menu)
        from_file_action.setText("Import from file")
        from_file_action.triggered.connect(functools.partial(self._row_import_preset_from_file_prompt, row))
        row.import_actions.append(from_file_action)
        row.import_menu.addAction(from_file_action)

    def refresh_row_import_preset_actions(self):
        for row in self.rows:
            row.import_menu.clear()
            self._create_actions_for_import_menu(row)

    @asyncSlot()
    async def _row_show_preset_summary(self, row: RowWidget):
        row_index = self.rows.index(row)
        preset = self._game_session.presets[row_index].get_preset()
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
        old_preset = self._game_session.presets[row_index].get_preset()
        if old_preset.base_preset_uuid is None:
            old_preset = old_preset.fork()

        editor = PresetEditor(old_preset)
        self._logic_settings_window = CustomizePresetDialog(self._window_manager, editor)
        self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())
        editor.on_changed = lambda: self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())
        self._logic_settings_window._game_session_row = row

        result = await async_dialog.execute_dialog(self._logic_settings_window)
        self._logic_settings_window = None

        if result == QtWidgets.QDialog.Accepted:
            new_preset = VersionedPreset.with_preset(editor.create_custom_preset_with())

            if self._preset_manager.add_new_preset(new_preset):
                self.refresh_row_import_preset_actions()

            await self._do_import_preset(row_index, new_preset)

    @asyncSlot()
    @handle_network_errors
    async def _row_import_preset(self, row: RowWidget, preset: VersionedPreset):
        row_index = self.rows.index(row)
        await self._do_import_preset(row_index, preset)

    def _row_import_preset_from_file_prompt(self, row: RowWidget):
        path = common_qt_lib.prompt_user_for_preset_file(self._window_manager, new_file=False)
        if path is not None:
            self._row_import_preset_from_file(row, path)

    @asyncSlot()
    @handle_network_errors
    async def _row_import_preset_from_file(self, row: RowWidget, path: Path):
        preset = await VersionedPreset.from_file(path)
        try:
            preset.get_preset()
        except InvalidPreset:
            await async_dialog.message_box(
                self._window_manager,
                QtWidgets.QMessageBox.Critical,
                "Error loading preset",
                f"The file at '{path}' contains an invalid preset."
            )
            return

        row_index = self.rows.index(row)
        await self._do_import_preset(row_index, preset)

    async def _do_import_preset(self, row_index: int, preset: VersionedPreset):
        if incompatible := preset.get_preset().settings_incompatible_with_multiworld():
            return await async_dialog.warning(
                self, "Incompatible preset",
                "The following settings are incompatible with multiworld:\n" + "\n".join(incompatible),
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok
            )

        await self._admin_global_action(SessionAdminGlobalAction.CHANGE_ROW, (row_index, preset.as_json))

    def _row_save_preset_to_manager(self, row: RowWidget):
        row_index = self.rows.index(row)
        preset = self._game_session.presets[row_index]

        if self._preset_manager.add_new_preset(preset):
            self.refresh_row_import_preset_actions()

    def _row_save_preset_to_file(self, row: RowWidget):
        path = common_qt_lib.prompt_user_for_preset_file(self._window_manager, new_file=True)
        if path is None:
            return

        row_index = self.rows.index(row)
        preset = self._game_session.presets[row_index]
        preset.save_to_file(path)

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
        parent_layout.addWidget(player_label, 2 + row_id, _PRESET_COLUMNS + 0 + team_id * 3)

        connection_state = None
        if not is_observer:
            connection_state = QtWidgets.QLabel(self.players_box)
            connection_state.setText("")
            connection_state.setWordWrap(True)
            parent_layout.addWidget(connection_state, 2 + row_id, _PRESET_COLUMNS + 1 + team_id * 3)

        tool_button = QtWidgets.QToolButton(self.players_box)
        tool_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        tool_button.setText("...")
        parent_layout.addWidget(tool_button, 2 + row_id, _PRESET_COLUMNS + 2 + team_id * 3)

        tool_button_menu = QtWidgets.QMenu(tool_button)
        tool_button.setMenu(tool_button_menu)

        widget = PlayerWidget(
            name=player_label,
            connection_state=connection_state,
            tool=tool_button,
            kick=QtGui.QAction(tool_button_menu),
            promote=QtGui.QAction(tool_button_menu),
            open_tracker=QtGui.QAction(tool_button_menu),
            abandon=QtGui.QAction(tool_button_menu),
            move_up=QtGui.QAction(tool_button_menu),
            move_down=QtGui.QAction(tool_button_menu),
            switch_observer_action=QtGui.QAction(tool_button_menu),
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
    async def on_game_session_meta_update(self, game_session: GameSessionEntry):
        self._game_session = game_session

        if self.network_client.current_user.id not in game_session.players:
            return await self._on_kicked()

        self.players_dock.setWindowTitle(f"Session: {game_session.name}")
        self.advanced_options_tool.setEnabled(game_session.players[self.network_client.current_user.id].admin)
        self.customize_user_preferences_button.setEnabled(self.current_player_game is not None)

        self.sync_rows_to_game_session()
        self.sync_player_widgets_to_game_session()
        self.sync_background_process_to_game_session()
        self.update_game_tab()
        await self.update_multiworld_client_status()
        await self.update_logic_settings_window()

    @asyncSlot(GameSessionActions)
    async def on_game_session_actions_update(self, actions: GameSessionActions):
        self.update_session_actions(actions)

    @asyncSlot(GameSessionAuditLog)
    async def on_game_session_audit_log_update(self, audit_log: GameSessionAuditLog):
        self.update_session_audit_log(audit_log)

    async def _on_kicked(self):
        if self._already_kicked:
            return
        self._already_kicked = True
        leave_session = self.network_client.leave_game_session(False)
        if self._game_session.players:
            message = "Kicked", "You have been kicked out of the session."
        else:
            message = "Session deleted", "The session has been deleted."
        await asyncio.gather(async_dialog.warning(self, *message), leave_session)
        return QTimer.singleShot(0, self.close)

    def sync_rows_to_game_session(self):
        game_session = self._game_session
        self_player = game_session.players[self.network_client.current_user.id]

        while len(self.rows) > len(game_session.presets):
            self.pop_row()

        while len(self.rows) < len(game_session.presets):
            self.add_row()

        can_customize = game_session.generation_in_progress is None and game_session.game_details is None
        for i, (row, preset) in enumerate(zip(self.rows, game_session.presets)):
            row.set_preset(preset, len(game_session.allowed_games) > 1)
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
            if self._generating_game or game_session.game_details is None:
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
        _state_to_label = {
            GameSessionState.SETUP: "Start",
            GameSessionState.IN_PROGRESS: "Finish",
            GameSessionState.FINISHED: "Reset",
        }
        self.session_status_tool.setText(_state_to_label[game_session.state])

        self.save_iso_button.setEnabled(game_session.game_details is not None
                                        and not self.current_player_membership.is_observer)
        if game_session.game_details is None:
            self.generate_game_label.setText("<Game not generated>")
            self.view_game_details_button.setEnabled(False)
        else:
            game_details = game_session.game_details
            self.generate_game_label.setText(f"Seed hash: {game_details.word_hash} ({game_details.seed_hash})")
            self.view_game_details_button.setEnabled(game_details.spoiler)

        self.start_session_action.setEnabled(self_is_admin and game_session.state == GameSessionState.SETUP)
        self.finish_session_action.setEnabled(self_is_admin and game_session.state == GameSessionState.IN_PROGRESS)
        self.reset_session_action.setEnabled(self_is_admin and game_session.state != GameSessionState.SETUP)

    def update_session_actions(self, actions: GameSessionActions):
        scrollbar = self.history_table_widget.verticalScrollBar()
        autoscroll = scrollbar.value() == scrollbar.maximum()
        self.history_table_widget.horizontalHeader().setVisible(True)
        self.history_table_widget.setRowCount(len(actions.actions))
        for i, action in enumerate(actions.actions):
            try:
                preset = self._game_session.presets[action.provider_row]
                game = default_database.game_description_for(preset.game)
                try:
                    location_node = game.world_list.node_from_pickup_index(action.location)
                    location_name = game.world_list.node_name(location_node, with_world=True,
                                                              distinguish_dark_aether=True)
                except KeyError as e:
                    logger.warning("Action %d has invalid location %d for game %s", i, action.location.index,
                                   preset.game.long_name)
                    location_name = f"Invalid location: {e}"
            except IndexError:
                logger.warning("Action %d has invalid provider_row %d", i, action.provider_row)
                logger.info("All presets: %s", str([(p.game, p.name) for p in self._game_session.presets]))
                location_name = f"Invalid location: row {action.provider_row} has no preset"

            self.history_table_widget.setItem(i, 0, QtWidgets.QTableWidgetItem(action.provider))
            self.history_table_widget.setItem(i, 1, QtWidgets.QTableWidgetItem(action.receiver))
            self.history_table_widget.setItem(i, 2, QtWidgets.QTableWidgetItem(action.pickup))
            self.history_table_widget.setItem(i, 3, QtWidgets.QTableWidgetItem(location_name))
            self.history_table_widget.setItem(i, 4, QtWidgets.QTableWidgetItem(action.time.astimezone().strftime("%c")))

        if autoscroll:
            self.history_table_widget.scrollToBottom()

    def update_session_audit_log(self, audit_log: GameSessionAuditLog):
        scrollbar = self.audit_table_widget.verticalScrollBar()
        autoscroll = scrollbar.value() == scrollbar.maximum()
        self.audit_table_widget.horizontalHeader().setVisible(True)
        self.audit_table_widget.setRowCount(len(audit_log.entries))

        for i, entry in enumerate(audit_log.entries):
            self.audit_table_widget.setItem(i, 0, QtWidgets.QTableWidgetItem(entry.user))
            self.audit_table_widget.setItem(i, 1, QtWidgets.QTableWidgetItem(entry.message))
            self.audit_table_widget.setItem(i, 2, QtWidgets.QTableWidgetItem(entry.time.astimezone().strftime("%c")))

        if autoscroll:
            self.audit_table_widget.scrollToBottom()

    async def update_multiworld_client_status(self):
        game_session_in_progress = self._game_session.state == GameSessionState.IN_PROGRESS

        if game_session_in_progress:
            if not self.multiworld_client.is_active:
                you = self._game_session.players[self.network_client.current_user.id]
                session_id = f"{self._game_session.id}_{self._game_session.game_details.seed_hash}_{you.row}"
                persist_path = self.network_client.server_data_path.joinpath(f"game_session_{session_id}.json")
                await self.multiworld_client.start(persist_path)

        elif self.multiworld_client.is_active:
            await self.multiworld_client.stop()

    async def update_logic_settings_window(self):
        if self._logic_settings_window is not None:
            if self._game_session.game_details is not None:
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
            return await self.network_client.session_admin_global(action, arg)
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
            return await self.network_client.session_admin_player(player.id, action, arg)
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
        dialog = QtWidgets.QInputDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle("Enter new title")
        dialog.setLabelText("Enter the new title for the session:")
        if await async_dialog.execute_dialog(dialog) == QtWidgets.QDialog.Accepted:
            await self._admin_global_action(SessionAdminGlobalAction.CHANGE_TITLE, dialog.textValue())

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
    async def duplicate_session(self):
        dialog = QtWidgets.QInputDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle("Enter new title")
        dialog.setLabelText("Enter the title for the duplicated copy of the session:")
        if await async_dialog.execute_dialog(dialog) == QtWidgets.QDialog.Accepted:
            await self._admin_global_action(SessionAdminGlobalAction.DUPLICATE_SESSION, dialog.textValue())

    async def _check_dangerous_presets(self, permalink: Permalink) -> bool:
        all_dangerous_settings = {
            i: dangerous
            for i, preset in enumerate(permalink.parameters.presets)
            if (dangerous := preset.dangerous_settings())
        }
        if all_dangerous_settings:
            player_names = {
                i: widget.player.name
                for i, widget in enumerate(self.team_players)
                if widget.player is not None
            }

            def get_name(i):
                return player_names.get(i, f'Player {i + 1}')

            warnings = "\n".join(
                f"{get_name(i)} - {self._game_session.presets[i].name}: {', '.join(dangerous)}"
                for i, dangerous in all_dangerous_settings.items()
            )
            message = ("The following presets have settings that can cause an impossible game:\n"
                       f"\n{warnings}\n"
                       "\nDo you want to continue?")
            result = await async_dialog.warning(self, "Dangerous preset", message, QMessageBox.Yes | QMessageBox.No)
            if result != QMessageBox.Yes:
                return False

        return True

    async def generate_game(self, spoiler: bool, retries: int | None):
        await async_dialog.warning(
            self, "Multiworld Limitation",
            "Warning: Multiworld games doesn't have proper energy damage logic. "
            "You might be required to do Dark Aether or heated Magmoor Cavern checks with very low energy."
        )

        permalink = Permalink.from_parameters(GeneratorParameters(
            seed_number=random.randint(0, 2 ** 31),
            spoiler=spoiler,
            presets=[
                preset.get_preset()
                for preset in self._game_session.presets
            ],
        ))
        return await self.generate_game_with_permalink(permalink, retries=retries)

    async def generate_game_with_permalink(self, permalink: Permalink, retries: int | None):
        if not await self._check_dangerous_presets(permalink):
            return

        def generate_layout(progress_update: ProgressUpdateCallable):
            return simplified_patcher.generate_layout(progress_update=progress_update,
                                                      parameters=permalink.parameters,
                                                      options=self._options,
                                                      retries=retries)

        await self._admin_global_action(SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, True)
        self._generating_game = True
        try:
            layout = await self.run_in_background_async(generate_layout, "Creating a seed...")
            self.update_progress(f"Finished generating, uploading...", 100)
            await self._upload_layout_description(layout)
            self.update_progress("Uploaded!", 100)

        except Exception as e:
            await self._admin_global_action(SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, False)

            message = "Error"
            if isinstance(e, GenerationFailure):
                message = "Generation Failure"
                self.failure_handler.handle_failure(e)
            else:
                logger.exception("Unable to generate")

            self.update_progress(f"{message}: {e}", -1)

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
        await self.generate_game(True, retries=None)

    @asyncSlot()
    @handle_network_errors
    async def generate_game_with_spoiler_no_retry(self):
        await self.generate_game(True, retries=0)

    @asyncSlot()
    @handle_network_errors
    async def generate_game_without_spoiler(self):
        await self.generate_game(False, retries=None)

    async def _should_overwrite_presets(self, parameters: GeneratorParameters, permalink_source: bool) -> bool:
        if permalink_source:
            source_name = "permalink"
        else:
            source_name = "game file"

        if parameters.player_count != self._game_session.num_rows:
            await async_dialog.warning(
                self, "Incompatible permalink",
                f"Given {source_name} is for {parameters.player_count} players, but "
                f"this session only have {self._game_session.num_rows} rows.")
            return False

        if any(not preset_p.is_same_configuration(preset_s.get_preset())
               for preset_p, preset_s in zip(parameters.presets, self._game_session.presets)):
            response = await async_dialog.warning(
                self, "Different presets",
                f"Given {source_name} has different presets compared to the session.\n"
                f"Do you want to overwrite the session's presets?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if response != QMessageBox.Yes:
                return False

        return True

    @asyncSlot()
    @handle_network_errors
    async def import_permalink(self):
        dialog = PermalinkDialog()
        result = await async_dialog.execute_dialog(dialog)
        if result != QtWidgets.QDialog.Accepted:
            return

        permalink = dialog.get_permalink_from_field()
        if await self._should_overwrite_presets(permalink.parameters, permalink_source=True):
            await self.generate_game_with_permalink(permalink, retries=None)

    @asyncSlot()
    @handle_network_errors
    async def import_layout(self):
        json_path = await file_prompts.prompt_input_layout(self)
        if json_path is None:
            return

        layout = LayoutDescription.from_file(json_path)
        if await self._should_overwrite_presets(layout.generator_parameters, permalink_source=False):

            await self._admin_global_action(SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, True)
            try:
                await self._upload_layout_description(layout)
            finally:
                await self._admin_global_action(SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, False)

    async def _upload_layout_description(self, layout: LayoutDescription):
        await self._admin_global_action(SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION,
                                        layout.as_json(force_spoiler=True))

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
        result = await async_dialog.warning(
            self, "Finish session?",
            "It's no longer possible to collect items after the session is finished."
            "\nDo you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            await self._admin_global_action(SessionAdminGlobalAction.FINISH_SESSION, None)

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

    @property
    def current_player_game(self) -> RandovaniaGame | None:
        membership = self.current_player_membership
        if membership.is_observer:
            return None
        return self._game_session.presets[membership.row].game

    @asyncSlot()
    @handle_network_errors
    async def save_iso(self):
        membership = self.current_player_membership
        if membership.is_observer:
            return await async_dialog.message_box(self, QtWidgets.QMessageBox.Critical,
                                                  "Invalid action", "Observers can't export a game.", QMessageBox.Ok)

        if any(player.player is None for player in self.team_players):
            user_response = await async_dialog.warning(
                self,
                "Incomplete Session",
                ("This session is currently missing a player.\n"
                 "If you export your game right now, all references to that player will use a generic name instead.\n\n"
                 "Do you want to proceed?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if user_response == QMessageBox.No:
                return

        options = self._options

        if not options.is_alert_displayed(InfoAlert.MULTIWORLD_FAQ):
            await async_dialog.message_box(self, QMessageBox.Icon.Information, "Multiworld FAQ",
                                           "Have you read the Multiworld FAQ?\n"
                                           "It can be found in the main Randovania window → Help → Multiworld")
            options.mark_alert_as_displayed(InfoAlert.MULTIWORLD_FAQ)

        game = self.current_player_game
        patch_data = await self._admin_player_action(membership, SessionAdminUserAction.CREATE_PATCHER_FILE,
                                                     options.options_for_game(game).cosmetic_patches.as_json)

        other_worlds = [p.game for p in self._game_session.presets]
        dialog = game.gui.export_dialog(options, patch_data, self._game_session.game_details.word_hash, False,
                                        other_worlds)
        result = await async_dialog.execute_dialog(dialog)

        if result != QtWidgets.QDialog.Accepted:
            return

        dialog.save_options()
        self._can_stop_background_process = game.exporter.export_can_be_aborted
        await game_exporter.export_game(
            exporter=game.exporter,
            export_dialog=dialog,
            patch_data=patch_data,
            layout_for_spoiler=None,
            background=self,
            progress_update_signal=self.progress_update_signal,
        )

    @asyncSlot()
    @handle_network_errors
    async def view_game_details(self):
        if self._game_session.game_details is None:
            return await async_dialog.warning(self, "No Spoiler Available",
                                              "Unable to view game spoilers, no game available.")

        if not self._game_session.game_details.spoiler:
            return await async_dialog.warning(self, "No Spoiler Available",
                                              "Unable to view game spoilers, game was generated without spoiler.")

        description_json = await self._admin_global_action(SessionAdminGlobalAction.DOWNLOAD_LAYOUT_DESCRIPTION, None)
        description = LayoutDescription.from_json_dict(json.loads(description_json))
        self._window_manager.open_game_details(description)

    @asyncSlot()
    @handle_network_errors
    async def copy_permalink(self):
        permalink_str = await self._admin_global_action(SessionAdminGlobalAction.REQUEST_PERMALINK, None)
        dialog = QtWidgets.QInputDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle("Session permalink")
        dialog.setLabelText("Permalink:")
        dialog.setTextValue(permalink_str)
        common_qt_lib.set_clipboard(permalink_str)
        common_qt_lib.set_default_window_icon(dialog)
        await async_dialog.execute_dialog(dialog)

    @asyncSlot()
    @handle_network_errors
    async def background_process_button_clicked(self):
        if self.has_background_process:
            self.stop_background_process()
        elif self._game_session.generation_in_progress is not None:
            await self._admin_global_action(SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, False)
        elif self._game_session.game_details is not None:
            await self.clear_generated_game()
        else:
            await self.generate_game(True, retries=None)

    def update_background_process_button(self):
        is_admin = self.current_player_membership.admin
        if self.has_background_process:
            self.background_process_button.setEnabled(self.has_background_process and self._can_stop_background_process)
            self.background_process_button.setText("Stop")

        elif self._game_session.generation_in_progress is not None:
            self.background_process_button.setEnabled(is_admin)
            self.background_process_button.setText("Abort generation")
        else:
            self.background_process_button.setEnabled(self._game_session.state == GameSessionState.SETUP and is_admin)
            if self._game_session.game_details is not None:
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
        game = self.current_player_game
        if game is None:
            raise ValueError("_open_user_preferences_dialog called for observer")

        per_game_options = self._options.options_for_game(game)

        dialog = game_specific_gui.create_dialog_for_cosmetic_patches(self, per_game_options.cosmetic_patches)
        result = dialog.exec_()
        if result == QtWidgets.QDialog.Accepted:
            with self._options as options:
                options.set_options_for_game(game, dataclasses.replace(per_game_options,
                                                                       cosmetic_patches=dialog.cosmetic_patches))

    def on_server_connection_state_updated(self, state: ConnectionState):
        pending_upload = self.multiworld_client.num_locations_to_upload()

        self.server_connection_button.setEnabled(state in {ConnectionState.Disconnected,
                                                           ConnectionState.ConnectedNotLogged})
        self.server_connection_button.setText("Login" if state == ConnectionState.ConnectedNotLogged else "Connect")

        message = f"Server: {state.value}"
        if pending_upload > 0:
            message += f", with {pending_upload} unsent pickups"
        self.server_connection_label.setText(message)
        common_qt_lib.set_error_border_stylesheet(self.server_connection_label,
                                                  state == ConnectionState.ConnectedNotLogged)

    def on_pending_upload_count_changed(self, count: int):
        self.on_server_connection_state_updated(self.network_client.connection_state)

    @asyncSlot()
    @handle_network_errors
    async def _connect_to_server(self):
        if self.network_client.connection_state == ConnectionState.ConnectedNotLogged:
            await async_dialog.execute_dialog(LoginPromptDialog(self.network_client))
        else:
            await self.network_client.connect_to_server()

    @asyncSlot()
    async def on_game_connection_updated(self):
        try:
            async with self._update_status_lock:
                await self.network_client.session_self_update(self.game_connection.get_current_inventory(),
                                                              self.game_connection.current_status,
                                                              self.game_connection.backend_choice)
        except UnableToConnect:
            logger.info("Unable to connect to server to update status")
            await asyncio.sleep(1)

        except error.BaseNetworkError as e:
            logger.warning(f"Received a {e} when updating status for server")
            await asyncio.sleep(1)
