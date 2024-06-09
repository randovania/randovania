from __future__ import annotations

import asyncio
import collections
import itertools
import logging
import random
from typing import TYPE_CHECKING, Self

from PySide6 import QtCore, QtGui, QtWidgets
from qasync import asyncClose, asyncSlot

from randovania.game_description import default_database
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.gui.auto_tracker_window import load_trackers_configuration
from randovania.gui.dialog.login_prompt_dialog import LoginPromptDialog
from randovania.gui.dialog.permalink_dialog import PermalinkDialog
from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog
from randovania.gui.generated.multiplayer_session_ui import Ui_MultiplayerSessionWindow
from randovania.gui.lib import async_dialog, common_qt_lib, game_exporter, layout_loader, model_lib
from randovania.gui.lib.background_task_mixin import BackgroundTaskInProgressError, BackgroundTaskMixin
from randovania.gui.lib.generation_failure_handling import GenerationFailureHandler
from randovania.gui.lib.multiplayer_session_api import MultiplayerSessionApi
from randovania.gui.lib.qt_network_client import AnyNetworkError, QtNetworkClient, handle_network_errors
from randovania.gui.widgets.item_tracker_popup_window import ItemTrackerPopupWindow
from randovania.gui.widgets.multiplayer_session_users_widget import MultiplayerSessionUsersWidget, connect_to
from randovania.interface_common import generator_frontend
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink
from randovania.layout.versioned_preset import VersionedPreset
from randovania.lib import string_lib
from randovania.lib.container_lib import zip2
from randovania.network_client.network_client import ConnectionState
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.multiplayer_session import (
    MAX_SESSION_NAME_LENGTH,
    MultiplayerSessionAction,
    MultiplayerSessionActions,
    MultiplayerSessionAuditLog,
    MultiplayerSessionEntry,
    MultiplayerUser,
    WorldUserInventory,
)
from randovania.network_common.session_visibility import MultiplayerSessionVisibility

if TYPE_CHECKING:
    import uuid

    from randovania.games.game import RandovaniaGame
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.customize_preset_dialog import CustomizePresetDialog
    from randovania.interface_common.options import Options
    from randovania.layout.preset import Preset
    from randovania.lib.status_update_lib import ProgressUpdateCallable

logger = logging.getLogger(__name__)


class HistoryItemModel(QtCore.QAbstractTableModel):
    actions: MultiplayerSessionActions

    def __init__(self, parent: MultiplayerSessionWindow, actions: MultiplayerSessionActions):
        super().__init__(parent)
        self.session_window = parent
        self.actions = actions

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...):
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == QtCore.Qt.Orientation.Horizontal:
            return ["Provider", "Receiver", "Pickup", "Location", "Time"][section]
        else:
            return section

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.actions.actions)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return 5

    def data(self, index: QtCore.QModelIndex, role: int = ...):
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None

        action = self.actions.actions[index.row()]

        column = index.column()

        if column == 2:
            return action.pickup
        elif column == 4:
            return QtCore.QDateTime.fromSecsSinceEpoch(int(action.time.timestamp()))

        provider_name, receiver_name, location_name = self.session_window._describe_action(action)
        if column == 0:
            return provider_name
        elif column == 1:
            return receiver_name
        else:
            return location_name

    def set_actions(self, actions: MultiplayerSessionActions):
        self.beginResetModel()
        self.actions = actions
        self.endResetModel()


class HistoryFilterModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent: MultiplayerSessionWindow):
        super().__init__(parent)
        self.provider_filter = None
        self.receiver_filter = None
        self.generic_filter = ""

    def filterAcceptsRow(self, source_row: int, source_parent: QtCore.QModelIndex) -> bool:
        model = self.sourceModel()

        def get_column(i):
            return model.itemData(model.index(source_row, i)).get(0, "")

        if self.provider_filter is not None:
            if self.provider_filter != get_column(0):
                return False

        if self.receiver_filter is not None:
            if self.receiver_filter != get_column(1):
                return False

        if not self.generic_filter:
            return True

        return any(self.generic_filter in col.lower() for col in (get_column(2), get_column(3)))

    def set_provider_filter(self, name: str | None):
        self.provider_filter = name
        self.invalidateRowsFilter()

    def set_receiver_filter(self, name: str | None):
        self.receiver_filter = name
        self.invalidateRowsFilter()

    def set_generic_filter(self, text: str):
        self.generic_filter = text.lower()
        self.invalidateRowsFilter()


class MultiplayerSessionWindow(QtWidgets.QMainWindow, Ui_MultiplayerSessionWindow, BackgroundTaskMixin):
    tracker_windows: dict[tuple[uuid.UUID, int], ItemTrackerPopupWindow]
    _old_session: MultiplayerSessionEntry | None = None
    _session: MultiplayerSessionEntry
    _last_actions: MultiplayerSessionActions
    _pending_actions: MultiplayerSessionActions | None = None
    has_closed = False
    _logic_settings_window: CustomizePresetDialog | None = None
    _generating_game: bool = False
    _already_kicked = False
    _can_stop_background_process = True
    _window_manager: WindowManager | None
    _all_locations: set[str]
    _all_pickups: set[str]

    def __init__(self, game_session_api: MultiplayerSessionApi, window_manager: WindowManager, options: Options):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.game_session_api = game_session_api
        self.network_client = game_session_api.network_client
        self.failure_handler = GenerationFailureHandler(self)

        self._window_manager = window_manager
        self._multiworld_client = window_manager.multiworld_client

        self._options = options
        self._trackers = load_trackers_configuration(for_solo=False)
        self._update_status_lock = asyncio.Lock()

        game_session_api.widget_root = self
        game_session_api.setParent(self)
        self.users_widget = MultiplayerSessionUsersWidget(options, self._window_manager, game_session_api)
        self.users_widget.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        )
        self.worlds_layout.insertWidget(0, self.users_widget)
        self.tab_widget.setCurrentIndex(0)
        self._all_locations = set()
        self._all_pickups = set()
        self._last_actions = MultiplayerSessionActions(game_session_api.current_session_id, [])

        self.audit_item_model = QtGui.QStandardItemModel(0, 3, self)
        self.audit_item_model.setHorizontalHeaderLabels(["User", "Message", "Time"])
        self.tab_audit.setModel(self.audit_item_model)
        self.tab_audit.sortByColumn(2, QtCore.Qt.SortOrder.AscendingOrder)

        self.history_item_model = HistoryItemModel(self, self._last_actions)
        # self.history_item_model.setHorizontalHeaderLabels(["Provider", "Receiver", "Pickup", "Location", "Time"])
        self.history_item_proxy = HistoryFilterModel(self)
        self.history_item_proxy.setSourceModel(self.history_item_model)
        self.history_view.setModel(self.history_item_proxy)
        self.history_view.sortByColumn(4, QtCore.Qt.SortOrder.AscendingOrder)

        # Advanced Options
        self.advanced_options_menu = QtWidgets.QMenu(self.advanced_options_tool)
        self.rename_session_action = QtGui.QAction("Change title", self.advanced_options_menu)
        self.change_password_action = QtGui.QAction("Change password", self.advanced_options_menu)
        self.duplicate_session_action = QtGui.QAction("Duplicate session", self.advanced_options_menu)
        self.export_all_presets_action = QtGui.QAction("Export all presets", self.advanced_options_menu)

        self.advanced_options_menu.addAction(self.rename_session_action)
        self.advanced_options_menu.addAction(self.change_password_action)
        self.advanced_options_menu.addAction(self.duplicate_session_action)
        self.advanced_options_menu.addAction(self.export_all_presets_action)
        self.advanced_options_tool.setMenu(self.advanced_options_menu)

        # Generate Game Menu
        self.generate_game_menu = QtWidgets.QMenu(self.generate_game_button)
        self.generate_game_with_spoiler_action = QtGui.QAction("Generate game", self.generate_game_menu)
        self.generate_game_with_spoiler_no_retry_action = QtGui.QAction(
            "Generate game (no retries)", self.generate_game_menu
        )
        self.generate_game_without_spoiler_action = QtGui.QAction("Generate without spoiler", self.generate_game_menu)
        self.import_permalink_action = QtGui.QAction("Import permalink", self.generate_game_menu)
        self.import_layout_action = QtGui.QAction("Import game/spoiler", self.generate_game_menu)

        self.generate_game_menu.addAction(self.generate_game_with_spoiler_action)
        self.generate_game_menu.addAction(self.generate_game_with_spoiler_no_retry_action)
        self.generate_game_menu.addAction(self.generate_game_without_spoiler_action)
        self.generate_game_menu.addAction(self.import_permalink_action)
        self.generate_game_menu.addAction(self.import_layout_action)
        self.generate_game_button.setMenu(self.generate_game_menu)

        self.export_game_menu = QtWidgets.QMenu(self.export_game_button)

        self.tracker_windows = {}

    def connect_to_events(self):
        # Game Generation
        self.generate_game_with_spoiler_action.triggered.connect(self.generate_game_with_spoiler)
        self.generate_game_with_spoiler_no_retry_action.triggered.connect(self.generate_game_with_spoiler_no_retry)
        self.generate_game_without_spoiler_action.triggered.connect(self.generate_game_without_spoiler)
        self.import_permalink_action.triggered.connect(self.import_permalink)
        self.import_layout_action.triggered.connect(self.import_layout)
        self.generate_game_button.clicked.connect(self.generate_game_button_clicked)
        self.session_visibility_button.clicked.connect(self._session_visibility_button_clicked)
        self.export_game_button.clicked.connect(self.export_game_button_clicked)

        # History
        self.history_filter_provider_combo.currentIndexChanged.connect(self.on_history_filter_provider_combo)
        self.history_filter_receiver_combo.currentIndexChanged.connect(self.on_history_filter_receiver_combo)
        self.history_filter_edit.textChanged.connect(self.on_history_filter_edit)

        # Session Admin
        self.rename_session_action.triggered.connect(self.rename_session)
        self.change_password_action.triggered.connect(self.change_password)
        self.duplicate_session_action.triggered.connect(self.duplicate_session)
        self.export_all_presets_action.triggered.connect(self.export_all_presets)
        self.copy_permalink_button.clicked.connect(self.copy_permalink)
        self.view_game_details_button.clicked.connect(self.view_game_details)
        self.everyone_can_claim_check.clicked.connect(self._on_everyone_can_claim_check)

        # Background Tasks
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.progress_update_signal.connect(self.update_progress)
        self.background_process_button.clicked.connect(self.background_process_button_clicked)

        # Connectivity
        self.server_connection_button.clicked.connect(self._connect_to_server)
        self.edit_game_connections_button.clicked.connect(self._window_manager.open_game_connection_window)

        # Signals
        self.users_widget.GameExportRequested.connect(self.game_export_listener)
        self.users_widget.TrackWorldRequested.connect(self.track_world_listener)
        self.network_client.MultiplayerSessionMetaUpdated.connect(self.on_meta_update)
        self.network_client.MultiplayerSessionActionsUpdated.connect(self.on_actions_update)
        self.network_client.MultiplayerAuditLogUpdated.connect(self.on_audit_log_update)
        self.network_client.WorldUserInventoryUpdated.connect(self.on_user_inventory_update)
        self.network_client.ConnectionStateUpdated.connect(self.on_server_connection_state_updated)
        self._multiworld_client.SyncFailure.connect(self.update_multiworld_client_status)
        self._multiworld_client.database.WorldDataUpdate.connect(self.update_multiworld_client_status)
        self._multiworld_client.game_connection.GameStateUpdated.connect(self.update_multiworld_client_status)
        self.not_connected_warning_label.linkActivated.connect(self._window_manager.open_game_connection_window)

    def _get_world_order(self) -> list[uuid.UUID]:
        return [world.id for world in self._session.worlds]

    def _get_world_names(self) -> list[str]:
        return [world.name for world in self._session.worlds]

    @classmethod
    async def create_and_update(
        cls, network_client: QtNetworkClient, session_id: int, window_manager: WindowManager, options: Options
    ) -> Self:
        logger.debug("Creating MultiplayerSessionWindow")

        game_session_api = MultiplayerSessionApi(network_client, session_id)
        window = cls(game_session_api, window_manager, options)
        window.on_server_connection_state_updated(network_client.connection_state)
        window.connect_to_events()
        await game_session_api.request_session_update()
        # await window.on_game_state_updated()

        logger.debug("Finished creating MultiplayerSessionWindow")

        return window

    @asyncClose
    async def closeEvent(self, event: QtGui.QCloseEvent):
        return await self._on_close_event(event)

    async def _on_close_event(self, event: QtGui.QCloseEvent):
        is_kicked = self.network_client.current_user.id not in self._session.users

        try:
            self.network_client.MultiplayerSessionMetaUpdated.disconnect(self.on_meta_update)
        except Exception as e:
            logging.exception(f"Unable to disconnect: {e}")
        try:
            self.network_client.ConnectionStateUpdated.disconnect(self.on_server_connection_state_updated)
        except Exception as e:
            logging.exception(f"Unable to disconnect: {e}")

        try:
            if not is_kicked and not self.network_client.connection_state.is_disconnected:
                await self.network_client.listen_to_session(self._session.id, False)
        finally:
            for d in list(self.tracker_windows.values()):
                d.close()
            super().closeEvent(event)
        self.has_closed = True

    @asyncSlot(MultiplayerSessionEntry)
    async def on_meta_update(self, session: MultiplayerSessionEntry):
        if session.id != self.game_session_api.current_session_id:
            return

        if hasattr(self, "_session"):
            self._old_session = self._session
        self._session = session

        if self.network_client.current_user.id not in session.users:
            return await self._on_kicked()

        self.advanced_options_tool.setEnabled(session.users[self.network_client.current_user.id].admin)
        # self.customize_user_preferences_button.setEnabled(self.current_player_game is not None)

        self.setWindowTitle(f"Multiworld Session: {self._session.name}")
        self.users_widget.update_state(self._session)
        self.sync_background_process_to_session()
        self.update_history_filter_world_combo()
        self.update_game_tab()
        await self.update_logic_settings_window()
        self.update_multiworld_client_status()
        self.everyone_can_claim_check.setChecked(session.allow_everyone_claim_world)
        self.everyone_can_claim_check.setEnabled(self.users_widget.is_admin())

    @asyncSlot(MultiplayerSessionActions)
    async def on_actions_update(self, actions: MultiplayerSessionActions):
        if actions.session_id == self._session.id:
            self.update_session_actions(actions)

    @asyncSlot(MultiplayerSessionAuditLog)
    async def on_audit_log_update(self, audit_log: MultiplayerSessionAuditLog):
        if audit_log.session_id == self._session.id:
            self.update_session_audit_log(audit_log)

    @asyncSlot(WorldUserInventory)
    async def on_user_inventory_update(self, inventory: WorldUserInventory):
        dock = self.tracker_windows.get((inventory.world_id, inventory.user_id))
        if dock is not None:
            tracker = dock.item_tracker
            tracker.update_state(
                Inventory(
                    {
                        tracker.resource_database.get_item(name): InventoryItem(0, capacity)
                        for name, capacity in inventory.inventory.items()
                    }
                )
            )

    async def _on_kicked(self):
        if self._already_kicked:
            return
        self._already_kicked = True
        leave_session = self.network_client.listen_to_session(self._session.id, False)
        if self._session.users:
            message = "Kicked", "You have been kicked out of the session."
        else:
            message = "Session deleted", "The session has been deleted."
        await asyncio.gather(async_dialog.warning(self, *message), leave_session)
        return QtCore.QTimer.singleShot(0, self.close)

    def sync_background_process_to_session(self):
        session = self._session
        if session.generation_in_progress is not None:
            if not self._generating_game:
                other_user = session.users[session.generation_in_progress]
                self.progress_label.setText(f"Game being generated by {other_user.name}")

        elif self.has_background_process:
            if self._generating_game or session.game_details is None:
                self.stop_background_process()
        else:
            self.progress_label.setText("")

    def update_game_tab(self):
        session = self._session
        own_entry = session.users[self.network_client.current_user.id]
        self_is_admin = own_entry.admin

        self.update_background_process_button()
        self.update_generate_game_button()
        self.generate_game_with_spoiler_action.setEnabled(self_is_admin)
        self.generate_game_without_spoiler_action.setEnabled(self_is_admin)
        self.import_permalink_action.setEnabled(self_is_admin)
        self.session_visibility_button.setEnabled(self_is_admin)
        _state_to_label = {
            MultiplayerSessionVisibility.VISIBLE: "Hide session",
            MultiplayerSessionVisibility.HIDDEN: "Unhide session",
        }
        self.session_visibility_button.setText(_state_to_label[session.visibility])

        self.copy_permalink_button.setEnabled(session.game_details is not None)
        if session.game_details is None:
            self.generate_game_label.setText("<Game not generated>")
            self.view_game_details_button.setEnabled(False)
            self.export_game_button.setEnabled(False)
        else:
            game_details = session.game_details
            self.generate_game_label.setText(f"Seed hash: {game_details.word_hash} ({game_details.seed_hash})")
            self.view_game_details_button.setEnabled(game_details.spoiler)
            if len(own_entry.worlds) > 1:
                self.export_game_button.setEnabled(True)
                self.export_game_menu.clear()
                self.export_game_button.setMenu(self.export_game_menu)

                for world_uid in own_entry.worlds.keys():
                    connect_to(
                        self.export_game_menu.addAction(session.get_world(world_uid).name),
                        self.users_widget.world_export,
                        world_uid,
                    )

            elif len(own_entry.worlds) == 1:
                self.export_game_button.setEnabled(True)
                self.export_game_button.setMenu(None)
            else:
                self.export_game_button.setEnabled(False)

    def _describe_action(self, action: MultiplayerSessionAction):
        # get_world can fail if the session meta is not up-to-date
        try:
            provider_world = self._session.get_world(action.provider)
            provider_name = provider_world.name
            receiver_name = self._session.get_world(action.receiver).name
        except KeyError as e:
            return "Unknown", "Unknown", f"Unknown worlds {e}"

        game = default_database.game_description_for(provider_world.preset.game)
        try:
            location_node = game.region_list.node_from_pickup_index(action.location_index)
            location_name = game.region_list.node_name(location_node, with_region=True, distinguish_dark_aether=True)

            return provider_name, receiver_name, location_name

        except KeyError as e:
            return "Unknown", "Unknown", f"Invalid location: {e}"

    def update_session_actions(self, actions: MultiplayerSessionActions):
        if actions == self._last_actions:
            return

        self._pending_actions = actions

        scrollbar = self.history_view.verticalScrollBar()
        autoscroll = scrollbar.value() == scrollbar.maximum()

        self.history_item_model.set_actions(actions)

        self._last_actions = actions
        if autoscroll:
            self.history_view.scrollToBottom()

    def update_history_filter_world_combo(self):
        if self._old_session is not None:
            old_world_names = self._old_session.get_world_names()
        else:
            old_world_names = []

        new_world_names = self._session.get_world_names()

        if new_world_names == old_world_names:
            return

        for prefix, combo in [
            ("Provider: ", self.history_filter_provider_combo),
            ("Receiver: ", self.history_filter_receiver_combo),
        ]:
            combo.addItems([""] * (len(new_world_names) + 1 - combo.count()))
            for i, world_name in enumerate(sorted(new_world_names)):
                combo.setItemText(i + 1, prefix + world_name)
                combo.setItemData(i + 1, world_name)

        self.on_history_filter_provider_combo()
        self.on_history_filter_receiver_combo()

    def on_history_filter_provider_combo(self):
        self.history_item_proxy.set_provider_filter(self.history_filter_provider_combo.currentData())

    def on_history_filter_receiver_combo(self):
        self.history_item_proxy.set_receiver_filter(self.history_filter_receiver_combo.currentData())

    def on_history_filter_edit(self):
        self.history_item_proxy.set_generic_filter(self.history_filter_edit.text())

    def update_session_audit_log(self, audit_log: MultiplayerSessionAuditLog):
        scrollbar = self.tab_audit.verticalScrollBar()
        autoscroll = scrollbar.value() == scrollbar.maximum()
        # self.tab_audit.horizontalHeader().setVisible(True)
        self.audit_item_model.setRowCount(len(audit_log.entries))

        for i, entry in enumerate(audit_log.entries):
            self.audit_item_model.setItem(i, 0, QtGui.QStandardItem(entry.user))
            self.audit_item_model.setItem(i, 1, QtGui.QStandardItem(entry.message))
            self.audit_item_model.setItem(i, 2, model_lib.create_date_item(entry.time))

        if autoscroll:
            self.tab_audit.scrollToBottom()
            self.tab_audit.resizeColumnToContents(1)

    async def update_logic_settings_window(self):
        if self._logic_settings_window is not None:
            if self._session.game_details is not None:
                self._logic_settings_window.reject()
                await async_dialog.warning(
                    self, "Game was generated", "A game was generated, so changing presets is no longer possible."
                )
            else:
                self._logic_settings_window.setEnabled(self._session.generation_in_progress is None)

    @property
    def current_player_membership(self) -> MultiplayerUser:
        user = self.network_client.current_user
        return self._session.users[user.id]

    @asyncSlot()
    @handle_network_errors
    async def rename_session(self):
        new_name = await TextPromptDialog.prompt(
            parent=self,
            title="Enter new title",
            description="Enter the new title for the session:",
            initial_value=self._session.name,
            is_modal=True,
            max_length=MAX_SESSION_NAME_LENGTH,
        )
        if new_name is not None:
            await self.game_session_api.rename_session(new_name)

    @asyncSlot()
    async def change_password(self):
        password = await TextPromptDialog.prompt(
            parent=self,
            title="Enter password",
            description="Enter the new password for the session:",
            is_password=True,
            is_modal=True,
        )
        if password is not None:
            await self.game_session_api.change_password(password)

    @asyncSlot()
    async def duplicate_session(self):
        new_name = await TextPromptDialog.prompt(
            parent=self,
            title="Enter new title",
            description="Enter the title for the duplicated copy of the session:",
            is_modal=True,
            max_length=MAX_SESSION_NAME_LENGTH,
        )
        if new_name is not None:
            await self.game_session_api.duplicate_session(new_name)

    def export_all_presets(self):
        path = common_qt_lib.prompt_user_for_preset_folder(self)

        if path is None:
            return

        world_owners = {world_uid: user for user in self._session.users.values() for world_uid in user.worlds.keys()}
        world_count = len(self._session.worlds)
        extension = VersionedPreset.file_extension()

        for i, world in enumerate(self._session.worlds):
            world_num = i + 1
            owner_name = world_owners[world.id].name if world.id in world_owners else "Unclaimed"
            owner_name = owner_name.replace("-", "_")
            world_name = world.name.replace("-", "_")
            preset = world.preset
            filename = (
                string_lib.sanitize_for_path(f"World{world_num}-{preset.game.short_name}-{owner_name}-{world_name}")
                + f".{extension}"
            )
            filepath = path / filename
            preset.save_to_file(filepath)

            self.update_progress(f"Completed: {world_num} of {world_count} presets", world_num * 100 / world_count)

        self.update_progress(f"Successfully exported {world_count} presets", 100)

    async def clear_generated_game(self):
        if self._last_actions.actions:
            warning = (
                "<b>all progress in this session is permanently lost</b>."
                "<br /><br />Are you sure you wish to continue?"
            )
            icon = QtWidgets.QMessageBox.Icon.Critical
        else:
            warning = "all players must export the ISOs again."
            icon = QtWidgets.QMessageBox.Icon.Warning

        if await async_dialog.yes_no_prompt(
            self,
            "Clear generated game?",
            f"Clearing the generated game will allow presets to be customized again, but {warning}",
            icon=icon,
        ):
            await self.game_session_api.clear_generated_game()

    async def _check_dangerous_presets(self, permalink: Permalink) -> bool:
        def _combine(arr: list[list[str]]):
            return "\n".join(
                f"{world.name}: {', '.join(dangerous)}"
                for world, dangerous in zip2(self._session.worlds, arr)
                if dangerous
            )

        all_incompatible_settings = [
            preset.settings_incompatible_with_multiworld() for preset in permalink.parameters.presets
        ]
        if any(all_incompatible_settings):
            message = (
                "The following worlds have settings that are incompatible with Multiworld:\n"
                f"\n{_combine(all_incompatible_settings)}\n"
                "\nDo you want to continue?"
            )
            await async_dialog.warning(self, "Incompatible preset", message)
            return False

        all_dangerous_settings = [preset.dangerous_settings() for preset in permalink.parameters.presets]
        if any(all_dangerous_settings):
            message = (
                "The following worlds have settings that can cause an impossible game:\n"
                f"\n{_combine(all_dangerous_settings)}\n"
                "\nDo you want to continue?"
            )
            result = await async_dialog.warning(
                self, "Dangerous preset", message, async_dialog.StandardButton.Yes | async_dialog.StandardButton.No
            )
            if result != async_dialog.StandardButton.Yes:
                return False

        return True

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

    async def generate_game(self, spoiler: bool, retries: int | None):
        not_ready_users = [user for user in self._session.users.values() if not user.ready]
        if not_ready_users:
            if not await async_dialog.yes_no_prompt(
                self,
                "User not Ready",
                "The following users are not ready. Do you want to continue generating a game?\n\n"
                + ", ".join(user.name for user in not_ready_users),
            ):
                return

        await async_dialog.warning(
            self,
            "Multiworld Limitation",
            "Warning: Multiworld games doesn't have proper energy damage logic. "
            "You might be required to do Dark Aether or heated Magmoor Cavern checks with very low energy.",
        )

        permalink = Permalink.from_parameters(
            GeneratorParameters(
                seed_number=random.randint(0, 2**31),
                spoiler=spoiler,
                presets=[VersionedPreset.from_str(world.preset_raw).get_preset() for world in self._session.worlds],
            )
        )
        return await self.generate_game_with_permalink(permalink, retries=retries)

    async def generate_game_with_permalink(self, permalink: Permalink, retries: int | None):
        if not await self._check_dangerous_presets(permalink):
            return

        if self.has_background_process:
            return async_dialog.warning(
                self,
                "Busy",
                "Unable to generate a game right now, another background process is already in progress.",
            )

        def generate_layout(progress_update: ProgressUpdateCallable):
            return generator_frontend.generate_layout(
                progress_update=progress_update,
                parameters=permalink.parameters,
                options=self._options,
                retries=retries,
                world_names=self._get_world_names(),
            )

        async with self.game_session_api.prepare_to_upload_layout(self._get_world_order()) as uploader:
            self._generating_game = True
            try:
                layout = await self.run_in_background_async(generate_layout, "Creating a game...")

                last_multiplayer = self._options.data_dir.joinpath(f"last_multiplayer_{self._session.id}.rdvgame")
                if layout.has_spoiler:
                    layout.save_to_file(last_multiplayer)

                self.update_progress("Finished generating, uploading...", 100)
                await uploader(layout)
                self.update_progress("Uploaded!", 100)

                if layout.has_spoiler:
                    last_multiplayer.unlink()

            except (asyncio.exceptions.CancelledError, BackgroundTaskInProgressError):
                pass

            except AnyNetworkError:
                # We're interested in catching generation failures.
                # Let network errors be handled by who called us, which will be captured by handle_network_errors
                raise

            except Exception as e:
                await self.failure_handler.handle_exception(
                    e,
                    self.update_progress,
                )

            finally:
                self._generating_game = False

    async def _should_overwrite_presets(self, parameters: GeneratorParameters, permalink_source: bool) -> bool:
        if permalink_source:
            source_name = "permalink"
        else:
            source_name = "game file"

        if parameters.world_count < len(self._session.worlds):
            await async_dialog.warning(
                self,
                f"Incompatible {source_name}",
                f"Given {source_name} is for {parameters.world_count} worlds, but "
                f"this session has {len(self._session.worlds)} worlds.",
            )
            return False

        if any(
            not preset_p.is_same_configuration(world.preset.get_preset())
            for preset_p, world in zip2(parameters.presets, self._session.worlds, strict=False)
        ):
            response = await async_dialog.warning(
                self,
                "Different presets",
                f"Given {source_name} has different presets compared to the session.\n"
                f"Do you want to overwrite the session's presets?",
                async_dialog.StandardButton.Yes | async_dialog.StandardButton.No,
                async_dialog.StandardButton.No,
            )
            if response != async_dialog.StandardButton.Yes:
                return False

        all_names = {world.name for world in self._session.worlds}
        for i in range(len(self._session.worlds), parameters.world_count):
            name = f"World {i + 1}"
            for suffix in itertools.count():
                if name not in all_names:
                    break
                name = f"World {i + 1} ({suffix + 1})"

            await self.game_session_api.create_unclaimed_world(
                name, VersionedPreset.with_preset(parameters.get_preset(i))
            )

        if parameters.world_count != len(self._session.worlds):
            await async_dialog.warning(
                self,
                "Temporary error",
                f"New worlds created to fit the imported {source_name}. Please import it again.",
            )
            return False
        else:
            for preset, world in zip2(parameters.presets, self._session.worlds):
                if preset != world.preset.get_preset():
                    await self.game_session_api.replace_preset_for(world.id, VersionedPreset.with_preset(preset))

        return True

    def _check_for_unsupported_games(self, presets: list[Preset]) -> list[str]:
        unsupported_games = sorted(
            {preset.game.data.long_name for preset in presets if preset.game not in self._session.allowed_games}
        )
        return unsupported_games

    async def _show_dialog_for_unsupported_games(self, unsupported_games: list[str]) -> None:
        unsupported_games_str = ", ".join(unsupported_games)
        await async_dialog.warning(self, "Invalid layout", f"Unsupported games: {unsupported_games_str}")

    @asyncSlot()
    @handle_network_errors
    async def import_permalink(self):
        dialog = PermalinkDialog()
        result = await async_dialog.execute_dialog(dialog)
        if result != QtWidgets.QDialog.DialogCode.Accepted:
            return

        permalink = dialog.get_permalink_from_field()
        unsupported_games = self._check_for_unsupported_games(permalink.parameters.presets)
        if unsupported_games:
            await self._show_dialog_for_unsupported_games(unsupported_games)
            return

        if await self._should_overwrite_presets(permalink.parameters, permalink_source=True):
            await self.generate_game_with_permalink(permalink, retries=None)

    @asyncSlot()
    @handle_network_errors
    async def import_layout(self):
        layout = await layout_loader.prompt_and_load_layout_description(self)
        if layout is None:
            return

        unsupported_games = self._check_for_unsupported_games(list(layout.all_presets))
        if unsupported_games:
            await self._show_dialog_for_unsupported_games(unsupported_games)
            return

        if await self._should_overwrite_presets(layout.generator_parameters, permalink_source=False):
            async with self.game_session_api.prepare_to_upload_layout(self._get_world_order()) as uploader:
                await uploader(layout)

    @asyncSlot()
    @handle_network_errors
    async def _session_visibility_button_clicked(self):
        await self._session_visibility_button_clicked_raw()

    async def _session_visibility_button_clicked_raw(self):
        state = self._session.visibility
        if state == MultiplayerSessionVisibility.VISIBLE:
            await self.game_session_api.change_visibility(MultiplayerSessionVisibility.HIDDEN)
        elif state == MultiplayerSessionVisibility.HIDDEN:
            await self.game_session_api.change_visibility(MultiplayerSessionVisibility.VISIBLE)
        else:
            raise RuntimeError(f"Unknown session state: {state}")

    @asyncSlot()
    async def export_game_button_clicked(self):
        own_entry = self._session.users[self.network_client.current_user.id]
        if len(own_entry.worlds) != 1:
            raise RuntimeError("Can only click this button when there's exactly one world")

        world_uid = next(iter(own_entry.worlds.keys()))
        await self.users_widget.world_export(world_uid)

    @asyncSlot()
    async def _on_everyone_can_claim_check(self):
        await self.game_session_api.set_everyone_can_claim(self.everyone_can_claim_check.isChecked())

    @asyncSlot()
    async def game_export_listener(self, world_id: uuid.UUID, patch_data: dict):
        world = self._session.get_world(world_id)
        games_by_world: dict[uuid.UUID, RandovaniaGame] = {
            w.id: VersionedPreset.from_str(w.preset_raw).game for w in self._session.worlds
        }
        game = games_by_world[world_id]

        export_suffix = string_lib.sanitize_for_path(f"{self._session.name} - {world.name}")
        dialog = game.gui.export_dialog(self._options, patch_data, export_suffix, False, list(games_by_world.values()))
        result = await async_dialog.execute_dialog(dialog)

        if result != QtWidgets.QDialog.DialogCode.Accepted:
            return

        dialog.save_options()
        self._can_stop_background_process = game.exporter.export_can_be_aborted
        self.tab_widget.setCurrentWidget(self.tab_session)
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
        if self._session.game_details is None:
            return await async_dialog.warning(
                self, "No Spoiler Available", "Unable to view game spoilers, no game available."
            )

        if not self._session.game_details.spoiler:
            return await async_dialog.warning(
                self, "No Spoiler Available", "Unable to view game spoilers, game was generated without spoiler."
            )

        description = await self.game_session_api.request_layout_description(self._session.worlds)
        if description is not None:
            self._window_manager.open_game_details(description, self._get_world_names())

    @asyncSlot()
    async def copy_permalink(self):
        permalink_str = await self.game_session_api.request_permalink()
        if permalink_str is None:
            return

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
    async def generate_game_button_clicked(self):
        if self._session.game_details is not None:
            await self.clear_generated_game()
        elif self._session.generation_in_progress is not None:
            await self.game_session_api.abort_generation()
        else:
            await self.generate_game(True, retries=None)

    def update_generate_game_button(self):
        is_enabled = self.current_player_membership.admin
        has_menu = False

        if self._session.game_details is not None:
            text = "Clear generated game"
        elif self._session.generation_in_progress is not None:
            text = "Abort generation"
        else:
            text = "Generate game"
            has_menu = True

        self.generate_game_button.setEnabled(is_enabled)
        self.generate_game_button.setText(text)
        self.generate_game_button.setMenu(self.generate_game_menu if has_menu else None)

    def background_process_button_clicked(self):
        self.stop_background_process()

    def update_background_process_button(self):
        self.background_process_button.setEnabled(self.has_background_process and self._can_stop_background_process)
        self.background_process_button.setText("Stop")

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

    @asyncSlot()
    async def _display_disconnected_warning(self):
        self.activateWindow()
        error_msg = self.network_client.last_connection_error or "Unknown Error"
        error_msg = error_msg.replace("\n", "<br />")
        await async_dialog.warning(
            self,
            "Disconnected from Server",
            "You have been disconnected from the server and attempts to reconnect have failed with:<br /><br />"
            f"{error_msg}",
        )

    _disconnected_warning_timer: QtCore.QTimer | None = None

    def _ensure_disconnected_warning_timer(self):
        if self._disconnected_warning_timer is None:
            logger.debug("Starting timer to display a warning about being disconnected.")
            self._disconnected_warning_timer = QtCore.QTimer(self)
            self._disconnected_warning_timer.setSingleShot(True)
            self._disconnected_warning_timer.timeout.connect(self._display_disconnected_warning)
            self._disconnected_warning_timer.start(60_000)  # 60s

    def _cancel_disconnected_warning_timer(self):
        if self._disconnected_warning_timer is not None:
            logger.debug("Cancelling timer for disconnection warning.")
            self._disconnected_warning_timer.stop()
            self._disconnected_warning_timer = None

    def on_server_connection_state_updated(self, state: ConnectionState):
        if state != ConnectionState.Connected:
            self._ensure_disconnected_warning_timer()
        else:
            self._cancel_disconnected_warning_timer()

        self.server_connection_button.setEnabled(
            state in {ConnectionState.Disconnected, ConnectionState.ConnectedNotLogged}
        )
        self.server_connection_button.setText("Login" if state == ConnectionState.ConnectedNotLogged else "Connect")

        message = f"Server: {state.value}"
        self.server_connection_label.setText(message)
        common_qt_lib.set_error_border_stylesheet(
            self.server_connection_label, state == ConnectionState.ConnectedNotLogged
        )

    def update_multiworld_client_status(self):
        lines = []

        err = self._multiworld_client.last_sync_exception
        if err is not None:
            lines.append(f"Error when syncing worlds: {err}")

        try:
            user_worlds = self._session.users[self.network_client.current_user.id].worlds
        except (AttributeError, KeyError):
            # _session hasn't been set yet or user isn't in session
            user_worlds = {}

        game_connection = self._multiworld_client.game_connection
        connected_worlds: dict[uuid.UUID, list[str]] = collections.defaultdict(list)
        for connector, connected_state in game_connection.connected_states.items():
            if connected_state.status != GameConnectionStatus.Disconnected:
                connected_worlds[connected_state.id].append(
                    f"{connected_state.status.pretty_text} via "
                    f"{game_connection.get_builder_for_connector(connector).pretty_text}"
                )

        connected_worlds = {k: v for k, v in connected_worlds.items() if v}

        world_status = []
        for uid in user_worlds.keys():
            data = self._multiworld_client.database.get_data_for(uid)

            msg = (
                f"- {self._session.get_world(uid).name}: {len(data.collected_locations)} collected locations, "
                f"{len(set(data.collected_locations) - set(data.uploaded_locations))} pending uploads."
            )

            if uid in connected_worlds:
                msg += f" {', '.join(connected_worlds[uid])}."

            err = self._multiworld_client.get_world_sync_error(uid)
            if err is not None:
                msg += f" Received {err} when syncing."

            world_status.append(msg)

        if world_status:
            lines.append("Status of your worlds, in this client:")
            lines.extend(world_status)

        self.multiworld_client_status_label.setText("\n".join(lines))

        warning_message = ""

        if user_worlds and self._session.game_details:
            if connected_worlds:
                if not (connected_worlds.keys() & user_worlds.keys()):
                    plural = "game" if len(connected_worlds) == 1 else "games"
                    warning_message = (
                        f"You are connected to {len(connected_worlds)} {plural}, but none for this session. "
                        "<a href='open://game-connections'>View details?</a>"
                    )
            else:
                warning_message = (
                    "You are currently connected to no games right now. "
                    "<a href='open://game-connections'>View details?</a>"
                )

        self.not_connected_warning_label.setText(warning_message)
        self.not_connected_warning_label.setVisible(bool(warning_message))

    @asyncSlot()
    @handle_network_errors
    async def _connect_to_server(self):
        if self.network_client.connection_state == ConnectionState.ConnectedNotLogged:
            await async_dialog.execute_dialog(LoginPromptDialog(self.network_client))
        else:
            await self.network_client.connect_to_server()

    def _on_close_item_tracker(self, world_uid: uuid.UUID, user_id: int):
        self.tracker_windows.pop((world_uid, user_id))
        asyncio.run_coroutine_threadsafe(
            self.network_client.world_track_inventory(world_uid, user_id, False), asyncio.get_event_loop()
        )

    @asyncSlot()
    @handle_network_errors
    async def track_world_listener(self, world_uid: uuid.UUID, user_id: int):
        existing_tracker = self.tracker_windows.get((world_uid, user_id))
        if existing_tracker is not None:
            return existing_tracker.raise_()

        world = self._session.get_world(world_uid)
        preset = VersionedPreset.from_str(world.preset_raw)

        if preset.game not in self._trackers:
            return await async_dialog.message_box(
                self,
                QtWidgets.QMessageBox.Icon.Information,
                "Unsupported Game",
                f"No tracker available for {preset.game.long_name}",
            )

        tracker_window = ItemTrackerPopupWindow(
            f"{self._session.name} Tracker: {world.name}",
            self._trackers[preset.game],
            lambda: self._on_close_item_tracker(world_uid, user_id),
        )
        tracker_window.show()

        self.tracker_windows[(world_uid, user_id)] = tracker_window
        await self.network_client.world_track_inventory(world_uid, user_id, True)
