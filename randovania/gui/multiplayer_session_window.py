import asyncio
import json
import logging
import random
import uuid
from typing import Self

from PySide6 import QtWidgets, QtGui, QtCore
from qasync import asyncSlot, asyncClose

from randovania.game_description import default_database
from randovania.games.game import RandovaniaGame
from randovania.gui.auto_tracker_window import load_trackers_configuration
from randovania.gui.dialog.login_prompt_dialog import LoginPromptDialog
from randovania.gui.dialog.permalink_dialog import PermalinkDialog
from randovania.gui.generated.multiplayer_session_ui import Ui_MultiplayerSessionWindow
from randovania.gui.lib import common_qt_lib, async_dialog, game_exporter, layout_loader
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.generation_failure_handling import GenerationFailureHandler
from randovania.gui.lib.multiplayer_session_api import MultiplayerSessionApi
from randovania.gui.lib.qt_network_client import handle_network_errors, QtNetworkClient
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.customize_preset_dialog import CustomizePresetDialog
from randovania.gui.widgets.multiplayer_session_users_widget import MultiplayerSessionUsersWidget
from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink
from randovania.layout.versioned_preset import VersionedPreset
from randovania.lib.status_update_lib import ProgressUpdateCallable
from randovania.network_client.network_client import ConnectionState
from randovania.network_common.admin_actions import SessionAdminGlobalAction
from randovania.network_common.multiplayer_session import (
    MultiplayerSessionEntry, MultiplayerUser, MultiplayerSessionActions, MultiplayerSessionAuditLog,
    MultiplayerSessionAction
)
from randovania.network_common.session_state import MultiplayerSessionState

logger = logging.getLogger(__name__)


# class ItemTrackerDock(QtWidgets.QDockWidget):
#     def __init__(self, parent: QtWidgets.QWidget, title: str, tracker_layout: dict,
#                  on_close):
#         super().__init__(parent)
#         self.on_close = on_close
#
#         self.setWindowTitle(title)
#         self.item_tracker = ItemTrackerWidget(tracker_layout)
#         self.item_tracker.update_state({})
#         self.setWidget(self.item_tracker)
#
#     def change_tracker_layout(self, tracker_layout: dict):
#         self.widget().deleteLater()
#         current_state = self.item_tracker.current_state
#         self.item_tracker = ItemTrackerWidget(tracker_layout)
#         self.item_tracker.update_state(current_state)
#         self.setWidget(self.item_tracker)
#
#     def closeEvent(self, event: QtGui.QCloseEvent) -> None:
#         self.on_close()
#         return super().closeEvent(event)


class MultiplayerSessionWindow(QtWidgets.QMainWindow, Ui_MultiplayerSessionWindow, BackgroundTaskMixin):
    # tracker_docks: dict[tuple[uuid.UUID, int], ItemTrackerDock]
    _session: MultiplayerSessionEntry
    has_closed = False
    _logic_settings_window: CustomizePresetDialog | None = None
    _window_manager: WindowManager
    _generating_game: bool = False
    _already_kicked = False
    _can_stop_background_process = True

    def __init__(self, game_session_api: MultiplayerSessionApi, window_manager: WindowManager, options: Options):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.game_session_api = game_session_api
        self.network_client = game_session_api.network_client
        self.failure_handler = GenerationFailureHandler(self)

        self._preset_manager = window_manager.preset_manager
        self._window_manager = window_manager
        self._options = options
        self._trackers = load_trackers_configuration()
        self._update_status_lock = asyncio.Lock()

        game_session_api.widget_root = self
        game_session_api.setParent(self)
        self.game_session_users_widget = MultiplayerSessionUsersWidget(options, self._preset_manager, game_session_api)
        self.tabWidget.removeTab(0)
        self.tabWidget.insertTab(0, self.game_session_users_widget, "Players")
        self.tabWidget.setCurrentIndex(0)

        # Advanced Options
        self.advanced_options_menu = QtWidgets.QMenu(self.advanced_options_tool)
        self.rename_session_action = QtGui.QAction("Change title", self.advanced_options_menu)
        self.change_password_action = QtGui.QAction("Change password", self.advanced_options_menu)
        self.duplicate_session_action = QtGui.QAction("Duplicate session", self.advanced_options_menu)

        self.advanced_options_menu.addAction(self.rename_session_action)
        self.advanced_options_menu.addAction(self.change_password_action)
        self.advanced_options_menu.addAction(self.duplicate_session_action)
        self.advanced_options_tool.setMenu(self.advanced_options_menu)

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

        # Session status
        self.session_status_menu = QtWidgets.QMenu(self.session_status_tool)
        self.start_session_action = QtGui.QAction("Start session", self.session_status_menu)
        self.finish_session_action = QtGui.QAction("Finish session", self.session_status_menu)
        self.reset_session_action = QtGui.QAction("Reset session", self.session_status_menu)

        self.session_status_menu.addAction(self.start_session_action)
        self.session_status_menu.addAction(self.finish_session_action)
        self.session_status_menu.addAction(self.reset_session_action)
        self.session_status_tool.setMenu(self.session_status_menu)

        self.tracker_docks = {}

    def connect_to_events(self):
        # Advanced Options
        self.rename_session_action.triggered.connect(self.rename_session)
        self.change_password_action.triggered.connect(self.change_password)
        self.duplicate_session_action.triggered.connect(self.duplicate_session)

        # Save ISO Button
        self.copy_permalink_button.clicked.connect(self.copy_permalink)

        self.generate_game_with_spoiler_action.triggered.connect(self.generate_game_with_spoiler)
        self.generate_game_with_spoiler_no_retry_action.triggered.connect(self.generate_game_with_spoiler_no_retry)
        self.generate_game_without_spoiler_action.triggered.connect(self.generate_game_without_spoiler)
        self.import_permalink_action.triggered.connect(self.import_permalink)
        self.import_layout_action.triggered.connect(self.import_layout)
        self.background_process_button.clicked.connect(self.background_process_button_clicked)

        # Signals
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.progress_update_signal.connect(self.update_progress)
        self.session_status_tool.clicked.connect(self._session_status_button_clicked)
        self.view_game_details_button.clicked.connect(self.view_game_details)
        self.game_session_users_widget.GameExportRequested.connect(self.game_export_listener)

        # Server Status
        self.server_connection_button.clicked.connect(self._connect_to_server)

        # Session status
        self.start_session_action.triggered.connect(self.start_session)
        self.finish_session_action.triggered.connect(self.finish_session)
        self.reset_session_action.triggered.connect(self.reset_session)

        self.network_client.MultiplayerSessionMetaUpdated.connect(self.on_meta_update)
        self.network_client.MultiplayerSessionActionsUpdated.connect(self.on_actions_update)
        self.network_client.MultiplayerAuditLogUpdated.connect(self.on_audit_log_update)
        # self.network_client.GameSessionInventoryUpdated.connect(self.on_user_inventory_update)
        self.network_client.ConnectionStateUpdated.connect(self.on_server_connection_state_updated)

    def _get_world_order(self) -> list[str]:
        return [
            str(world.id)
            for world in self._session.worlds
        ]

    @classmethod
    async def create_and_update(cls, network_client: QtNetworkClient, session_entry: MultiplayerSessionEntry,
                                window_manager: WindowManager, options: Options,
                                ) -> Self:

        logger.debug("Creating MultiplayerSessionWindow")

        game_session_api = MultiplayerSessionApi(network_client, session_entry)
        window = cls(game_session_api, window_manager, options)
        await window.on_meta_update(session_entry)
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
                await self.network_client.listen_to_session(self._session, False)
        finally:
            # for d in list(self.tracker_docks.values()):
            #     d.close()
            super().closeEvent(event)
        self.has_closed = True

    @asyncSlot(MultiplayerSessionEntry)
    async def on_meta_update(self, session: MultiplayerSessionEntry):
        if session.id != self.game_session_api.current_entry.id:
            return

        self._session = session

        if self.network_client.current_user.id not in session.users:
            return await self._on_kicked()

        self.advanced_options_tool.setEnabled(session.users[self.network_client.current_user.id].admin)
        # self.customize_user_preferences_button.setEnabled(self.current_player_game is not None)

        self.game_session_users_widget.update_state(self._session)
        self.sync_background_process_to_session()
        self.update_game_tab()
        await self.update_logic_settings_window()

    @asyncSlot(MultiplayerSessionActions)
    async def on_actions_update(self, actions: MultiplayerSessionActions):
        if actions.session_id == self._session.id:
            self.update_session_actions(actions)

    @asyncSlot(MultiplayerSessionAuditLog)
    async def on_audit_log_update(self, audit_log: MultiplayerSessionAuditLog):
        if audit_log.session_id == self._session.id:
            self.update_session_audit_log(audit_log)

    # @asyncSlot(WorldUserInventory)
    # async def on_user_inventory_update(self, inventory: WorldUserInventory):
    #     dock = self.tracker_docks.get((inventory.world_id, inventory.user_id))
    #     if dock is not None:
    #         tracker = dock.item_tracker
    #         tracker.update_state({
    #             tracker.resource_database.get_item(name): item
    #             for name, item in inventory.inventory.items()
    #         })

    async def _on_kicked(self):
        if self._already_kicked:
            return
        self._already_kicked = True
        leave_session = self.network_client.listen_to_session(self._session, False)
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
        self_is_admin = session.users[self.network_client.current_user.id].admin

        self.session_status_label.setText(f"Session: {session.state.user_friendly_name}")
        self.update_background_process_button()
        self.generate_game_with_spoiler_action.setEnabled(self_is_admin)
        self.generate_game_without_spoiler_action.setEnabled(self_is_admin)
        self.import_permalink_action.setEnabled(self_is_admin)
        self.session_status_tool.setEnabled(self_is_admin)
        _state_to_label = {
            MultiplayerSessionState.SETUP: "Start",
            MultiplayerSessionState.IN_PROGRESS: "Finish",
            MultiplayerSessionState.FINISHED: "Reset",
        }
        self.session_status_tool.setText(_state_to_label[session.state])

        if session.game_details is None:
            self.generate_game_label.setText("<Game not generated>")
            self.view_game_details_button.setEnabled(False)
        else:
            game_details = session.game_details
            self.generate_game_label.setText(f"Seed hash: {game_details.word_hash} ({game_details.seed_hash})")
            self.view_game_details_button.setEnabled(game_details.spoiler)

        self.start_session_action.setEnabled(self_is_admin and session.state == MultiplayerSessionState.SETUP)
        self.finish_session_action.setEnabled(
            self_is_admin and session.state == MultiplayerSessionState.IN_PROGRESS)
        self.reset_session_action.setEnabled(self_is_admin and session.state != MultiplayerSessionState.SETUP)

    def _describe_action(self, action: MultiplayerSessionAction):
        # get_world can fail if the session meta is not up-to-date
        try:
            provider_world = self._session.get_world(action.provider)
            provider_name = provider_world.name
            receiver_name = self._session.get_world(action.receiver).name
        except KeyError as e:
            return "Unknown", "Unknown", f"Unknown worlds {e}"

        preset = VersionedPreset.from_str(provider_world.preset_raw)
        game = default_database.game_description_for(preset.game)
        try:
            location_node = game.region_list.node_from_pickup_index(action.location_index)
            location_name = game.region_list.node_name(location_node, with_region=True,
                                                       distinguish_dark_aether=True)

            return provider_name, receiver_name, location_name

        except KeyError as e:
            return "Unknown", "Unknown", f"Invalid location: {e}"

    def update_session_actions(self, actions: MultiplayerSessionActions):
        scrollbar = self.tab_history.verticalScrollBar()
        autoscroll = scrollbar.value() == scrollbar.maximum()
        self.tab_history.horizontalHeader().setVisible(True)
        self.tab_history.setRowCount(len(actions.actions))

        for i, action in enumerate(actions.actions):
            provider_name, receiver_name, location_name = self._describe_action(action)
            self.tab_history.setItem(i, 0, QtWidgets.QTableWidgetItem(provider_name))
            self.tab_history.setItem(i, 1, QtWidgets.QTableWidgetItem(receiver_name))
            self.tab_history.setItem(i, 2, QtWidgets.QTableWidgetItem(action.pickup))
            self.tab_history.setItem(i, 3, QtWidgets.QTableWidgetItem(location_name))
            self.tab_history.setItem(i, 4, QtWidgets.QTableWidgetItem(action.time.astimezone().strftime("%c")))

        if autoscroll:
            self.tab_history.scrollToBottom()

    def update_session_audit_log(self, audit_log: MultiplayerSessionAuditLog):
        scrollbar = self.tab_audit.verticalScrollBar()
        autoscroll = scrollbar.value() == scrollbar.maximum()
        self.tab_audit.horizontalHeader().setVisible(True)
        self.tab_audit.setRowCount(len(audit_log.entries))

        for i, entry in enumerate(audit_log.entries):
            self.tab_audit.setItem(i, 0, QtWidgets.QTableWidgetItem(entry.user))
            self.tab_audit.setItem(i, 1, QtWidgets.QTableWidgetItem(entry.message))
            self.tab_audit.setItem(i, 2, QtWidgets.QTableWidgetItem(entry.time.astimezone().strftime("%c")))

        if autoscroll:
            self.tab_audit.scrollToBottom()

    async def update_logic_settings_window(self):
        if self._logic_settings_window is not None:
            if self._session.game_details is not None:
                self._logic_settings_window.reject()
                await async_dialog.warning(self, "Game was generated",
                                           "A game was generated, so changing presets is no longer possible.")
            else:
                self._logic_settings_window.setEnabled(self._session.generation_in_progress is None)

    @property
    def current_player_membership(self) -> MultiplayerUser:
        user = self.network_client.current_user
        return self._session.users[user.id]

    async def _admin_global_action(self, action: SessionAdminGlobalAction, arg):
        self.setEnabled(False)
        try:
            return await self.network_client.session_admin_global(self._session, action, arg)
        finally:
            self.setEnabled(True)

    @asyncSlot()
    @handle_network_errors
    async def rename_session(self):
        dialog = QtWidgets.QInputDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle("Enter new title")
        dialog.setLabelText("Enter the new title for the session:")
        if await async_dialog.execute_dialog(dialog) == QtWidgets.QDialog.DialogCode.Accepted:
            await self._admin_global_action(SessionAdminGlobalAction.CHANGE_TITLE, dialog.textValue())

    @asyncSlot()
    @handle_network_errors
    async def change_password(self):
        dialog = QtWidgets.QInputDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle("Enter password")
        dialog.setLabelText("Enter the new password for the session:")
        dialog.setTextEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        if await async_dialog.execute_dialog(dialog) == QtWidgets.QDialog.DialogCode.Accepted:
            await self._admin_global_action(SessionAdminGlobalAction.CHANGE_PASSWORD, dialog.textValue())

    @asyncSlot()
    @handle_network_errors
    async def duplicate_session(self):
        dialog = QtWidgets.QInputDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle("Enter new title")
        dialog.setLabelText("Enter the title for the duplicated copy of the session:")
        if await async_dialog.execute_dialog(dialog) == QtWidgets.QDialog.DialogCode.Accepted:
            await self._admin_global_action(SessionAdminGlobalAction.DUPLICATE_SESSION, dialog.textValue())

    async def _check_dangerous_presets(self, permalink: Permalink) -> bool:
        all_dangerous_settings = [
            preset.dangerous_settings()
            for preset in permalink.parameters.presets
        ]
        if any(all_dangerous_settings):
            warnings = "\n".join(
                f"{world.name}: {', '.join(dangerous)}"
                for world, dangerous in zip(self._session.worlds, all_dangerous_settings)
                if dangerous
            )
            message = ("The following presets have settings that can cause an impossible game:\n"
                       f"\n{warnings}\n"
                       "\nDo you want to continue?")
            result = await async_dialog.warning(self, "Dangerous preset", message,
                                                async_dialog.StandardButton.Yes | async_dialog.StandardButton.No)
            if result != async_dialog.StandardButton.Yes:
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
                VersionedPreset.from_str(world.preset_raw).get_preset()
                for world in self._session.worlds
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

        await self._admin_global_action(SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, self._get_world_order())
        self._generating_game = True
        try:
            layout = await self.run_in_background_async(generate_layout, "Creating a game...")
            self.update_progress("Finished generating, uploading...", 100)
            await self._upload_layout_description(layout)
            self.update_progress("Uploaded!", 100)

        except asyncio.exceptions.CancelledError:
            pass

        except Exception as e:
            await self.failure_handler.handle_exception(
                e, self.update_progress,
            )

        finally:
            await self._admin_global_action(SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, [])
            self._generating_game = False

    async def clear_generated_game(self):
        result = await async_dialog.warning(
            self, "Clear generated game?",
            "Clearing the generated game will allow presets to be customized again, but all "
            "players must export the ISOs again.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )
        if result == QtWidgets.QMessageBox.StandardButton.Yes:
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

        if parameters.player_count != len(self._session.worlds):
            await async_dialog.warning(
                self, "Incompatible permalink",
                f"Given {source_name} is for {parameters.player_count} players, but "
                f"this session only have {len(self._session.worlds)} rows.")
            return False

        if any(not preset_p.is_same_configuration(preset_s.get_preset())
               for preset_p, preset_s in zip(parameters.presets, self._session.worlds)):
            response = await async_dialog.warning(
                self, "Different presets",
                f"Given {source_name} has different presets compared to the session.\n"
                f"Do you want to overwrite the session's presets?",
                async_dialog.StandardButton.Yes | async_dialog.StandardButton.No,
                async_dialog.StandardButton.No
            )
            if response != async_dialog.StandardButton.Yes:
                return False

        return True

    @asyncSlot()
    @handle_network_errors
    async def import_permalink(self):
        dialog = PermalinkDialog()
        result = await async_dialog.execute_dialog(dialog)
        if result != QtWidgets.QDialog.DialogCode.Accepted:
            return

        permalink = dialog.get_permalink_from_field()
        if await self._should_overwrite_presets(permalink.parameters, permalink_source=True):
            await self.generate_game_with_permalink(permalink, retries=None)

    @asyncSlot()
    @handle_network_errors
    async def import_layout(self):
        layout = await layout_loader.prompt_and_load_layout_description(self)
        if layout is None:
            return

        if await self._should_overwrite_presets(layout.generator_parameters, permalink_source=False):
            await self._admin_global_action(SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, self._get_world_order())
            try:
                await self._upload_layout_description(layout)
            finally:
                await self._admin_global_action(SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, [])

    async def _upload_layout_description(self, layout: LayoutDescription):
        await self._admin_global_action(SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION,
                                        layout.as_json(force_spoiler=True))

    @asyncSlot()
    @handle_network_errors
    async def start_session(self):
        await self._admin_global_action(SessionAdminGlobalAction.START_SESSION, None)

    @asyncSlot()
    @handle_network_errors
    async def finish_session(self):
        result = await async_dialog.warning(
            self, "Finish session?",
            "It's no longer possible to collect items after the session is finished."
            "\nDo you want to continue?",
            async_dialog.StandardButton.Yes | async_dialog.StandardButton.No,
            async_dialog.StandardButton.No,
        )
        if result == async_dialog.StandardButton.Yes:
            await self._admin_global_action(SessionAdminGlobalAction.FINISH_SESSION, None)

    @asyncSlot()
    @handle_network_errors
    async def reset_session(self):
        await async_dialog.warning(self, "NYI", "Reset session is not implemented.")

    @asyncSlot()
    async def _session_status_button_clicked(self):
        state = self._session.state
        if state == MultiplayerSessionState.SETUP:
            await self.start_session()
        elif state == MultiplayerSessionState.IN_PROGRESS:
            await self.finish_session()
        elif state == MultiplayerSessionState.FINISHED:
            await self.reset_session()
        else:
            raise RuntimeError(f"Unknown session state: {state}")

    @asyncSlot()
    async def game_export_listener(self, world_id: uuid.UUID, patch_data: dict):
        world = self._session.get_world(world_id)
        games_by_world: dict[uuid.UUID, RandovaniaGame] = {
            w.id: VersionedPreset.from_str(w.preset_raw).game for w in self._session.worlds
        }
        game = games_by_world[world_id]

        dialog = game.gui.export_dialog(self._options, patch_data, f"{self._session.name} - {world.name}",
                                        False, list(games_by_world.values()))
        result = await async_dialog.execute_dialog(dialog)

        if result != QtWidgets.QDialog.DialogCode.Accepted:
            return

        dialog.save_options()
        self._can_stop_background_process = game.exporter.export_can_be_aborted
        self.tabWidget.setCurrentWidget(self.tab_session)
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
            return await async_dialog.warning(self, "No Spoiler Available",
                                              "Unable to view game spoilers, no game available.")

        if not self._session.game_details.spoiler:
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
        elif self._session.generation_in_progress is not None:
            await self._admin_global_action(SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION, [])
        elif self._session.game_details is not None:
            await self.clear_generated_game()
        else:
            await self.generate_game(True, retries=None)

    def update_background_process_button(self):
        is_admin = self.current_player_membership.admin
        if self.has_background_process:
            self.background_process_button.setEnabled(self.has_background_process and self._can_stop_background_process)
            self.background_process_button.setText("Stop")

        elif self._session.generation_in_progress is not None:
            self.background_process_button.setEnabled(is_admin)
            self.background_process_button.setText("Abort generation")
        else:
            self.background_process_button.setEnabled(
                self._session.state == MultiplayerSessionState.SETUP and is_admin)
            if self._session.game_details is not None:
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

    def on_server_connection_state_updated(self, state: ConnectionState):
        self.server_connection_button.setEnabled(state in {ConnectionState.Disconnected,
                                                           ConnectionState.ConnectedNotLogged})
        self.server_connection_button.setText("Login" if state == ConnectionState.ConnectedNotLogged else "Connect")

        message = f"Server: {state.value}"
        self.server_connection_label.setText(message)
        common_qt_lib.set_error_border_stylesheet(self.server_connection_label,
                                                  state == ConnectionState.ConnectedNotLogged)

    @asyncSlot()
    @handle_network_errors
    async def _connect_to_server(self):
        if self.network_client.connection_state == ConnectionState.ConnectedNotLogged:
            await async_dialog.execute_dialog(LoginPromptDialog(self.network_client))
        else:
            await self.network_client.connect_to_server()
    #
    # def _on_close_item_tracker(self, row_id: int):
    #     self.removeDockWidget(self.tracker_docks.pop(row_id))
    #     asyncio.run_coroutine_threadsafe(
    #         self.network_client.session_track_inventory(row_id, False),
    #         asyncio.get_event_loop()
    #     )
    #
    # def _item_tracker_menu_requested(self, pos: QtCore.QPoint, row_id: int):
    #     preset = self._session.worlds[row_id]
    #
    #     menu = QtWidgets.QMenu(self.tracker_docks[row_id])
    #
    #     for name in sorted(self._trackers[preset.game].keys()):
    #         menu.addAction(name).setData(self._trackers[preset.game][name])
    #
    #     action = menu.exec(QtGui.QCursor.pos())
    #     if action is None:
    #         return
    #     self.tracker_docks[row_id].change_tracker_layout(json_lib.read_path(action.data()))
    #
    # @asyncSlot(int)
    # async def _selected_item_tracker_menu(self, row_id: int):
    #     preset = self._session.worlds[row_id]
    #
    #     if row_id in self.tracker_docks:
    #         return async_dialog.message_box(self, QtWidgets.QMessageBox.Icon.Information,
    #                                         "Tracker Open", "Tracker already open for this row.")
    #     elif preset.game not in self._trackers:
    #         return async_dialog.message_box(self, QtWidgets.QMessageBox.Icon.Information,
    #                                         "Unsupported Game", f"No tracker available for {preset.game.long_name}")
    #
    #     tracker_path: Path | None = None
    #     for tracker_path in self._trackers[preset.game].values():
    #         break
    #     assert tracker_path is not None
    #
    #     item_tracker = ItemTrackerDock(
    #         self, f"Tracker: {self.team_players[row_id].player.name}", json_lib.read_path(tracker_path),
    #         lambda: self._on_close_item_tracker(row_id)
    #     )
    #     item_tracker.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
    #     item_tracker.customContextMenuRequested.connect(functools.partial(
    #         self._item_tracker_menu_requested,
    #         row_id=row_id,
    #     ))
    #     self.addDockWidget(QtCore.Qt.DockWidgetArea.TopDockWidgetArea, item_tracker)
    #     item_tracker.setFloating(True)
    #
    #     self.tracker_docks[row_id] = item_tracker
    #     asyncio.run_coroutine_threadsafe(
    #         self.network_client.session_track_inventory(row_id, True),
    #         asyncio.get_event_loop()
    #     )
