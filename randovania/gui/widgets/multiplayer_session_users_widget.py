import dataclasses
import functools
import uuid

from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt, Signal
from qasync import asyncSlot

from randovania.gui import game_specific_gui
from randovania.gui.dialog.select_preset_dialog import SelectPresetDialog
from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog
from randovania.gui.lib import async_dialog, common_qt_lib
from randovania.gui.lib.multiplayer_session_api import MultiplayerSessionApi
from randovania.interface_common.options import Options, InfoAlert
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout import preset_describer
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common.multiplayer_session import MultiplayerSessionEntry, MultiplayerWorld, \
    MAX_WORLD_NAME_LENGTH, WORLD_NAME_RE
from randovania.network_common.session_state import MultiplayerSessionState


def make_tool(text: str):
    tool = QtWidgets.QToolButton()
    tool.setText(text)
    tool.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
    tool.setMinimumWidth(100)
    tool.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    return tool


def connect_to(action: QtGui.QAction, target, *args):
    if args:
        target = functools.partial(target, *args)
    action.triggered.connect(target)
    return action


class MultiplayerSessionUsersWidget(QtWidgets.QTreeWidget):
    GameExportRequested = Signal(uuid.UUID, dict)
    TrackWorldRequested = Signal(uuid.UUID, int)

    _session: MultiplayerSessionEntry

    def __init__(self, options: Options, preset_manager: PresetManager, session_api: MultiplayerSessionApi):
        super().__init__()
        self.header().setStretchLastSection(False)
        self.headerItem().setText(0, "Name")
        self.headerItem().setText(1, "")
        self.headerItem().setText(2, "")
        self.headerItem().setText(3, "")
        self.header().setVisible(False)

        self._options = options
        self._preset_manager = preset_manager
        self._session_api = session_api

    @property
    def your_id(self) -> int | None:
        user = self._session_api.network_client.current_user
        if user is not None:
            return user.id
        return None

    #

    def _create_select_preset_dialog(self, include_world_name_prompt: bool):
        return SelectPresetDialog(self._preset_manager, self._options,
                                  allowed_games=self._session.allowed_games,
                                  include_world_name_prompt=include_world_name_prompt)

    async def _prompt_for_preset(self):
        dialog = self._create_select_preset_dialog(False)
        result = await async_dialog.execute_dialog(dialog)
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            return dialog.selected_preset
        else:
            return None

    #

    @asyncSlot()
    async def _world_replace_preset(self, world_uid: uuid.UUID):
        preset = await self._prompt_for_preset()
        if preset is not None:
            await self._session_api.replace_preset_for(world_uid, preset)

    @asyncSlot()
    async def _world_claim_with(self, world_uid: uuid.UUID, owner: int):
        await self._session_api.claim_world_for(world_uid, owner)

    @asyncSlot()
    async def _world_unclaim(self, world_uid: uuid.UUID, owner: int):
        await self._session_api.unclaim_world(world_uid, owner)

    @asyncSlot()
    async def _kick_player(self, kick_id: int):
        await self._session_api.kick_player(kick_id)

    @asyncSlot()
    async def _switch_admin(self, new_admin_id: int):
        await self._session_api.switch_admin(new_admin_id)

    @asyncSlot()
    async def _world_rename(self, world_uid: uuid.UUID):
        new_name = await TextPromptDialog.prompt(
            parent=self,
            title="Enter world name",
            description="Select a new name for the world:",
            initial_value=self._session.get_world(world_uid).name,
            is_modal=True,
            max_length=MAX_WORLD_NAME_LENGTH,
            check_re=WORLD_NAME_RE,
        )
        if new_name is not None:
            await self._session_api.rename_world(world_uid, new_name)

    @asyncSlot()
    async def _world_delete(self, world_uid: uuid.UUID):
        await self._session_api.delete_world(world_uid)

    @asyncSlot()
    async def _preset_view_summary(self, world_uid: uuid.UUID):
        preset = self._get_preset(world_uid).get_preset()
        description = preset_describer.merge_categories(preset_describer.describe(preset))

        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowTitle(preset.name)
        message_box.setText(description)
        message_box.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        await async_dialog.execute_dialog(message_box)

    @asyncSlot()
    async def _preset_customize(self, world_uid: uuid.UUID):
        print("customize preset", world_uid)
        # if self._logic_settings_window is not None:
        #     if self._logic_settings_window._game_session_row == row:
        #         self._logic_settings_window.raise_()
        #         self._logic_settings_window.activateWindow()
        #     else:
        #         # show warning that a dialog is already in progress?
        #         await async_dialog.warning(self, "Customize in progress",
        #                                    "A window for customizing a preset is already open. "
        #                                    "Please close it before continuing.",
        #                                    async_dialog.StandardButton.Ok, async_dialog.StandardButton.Ok)
        #     return
        #
        # row_index = self.rows.index(row)
        # old_preset = self._game_session.presets[row_index].get_preset()
        # if self._preset_manager.is_included_preset_uuid(old_preset.uuid):
        #     old_preset = old_preset.fork()
        #
        # editor = PresetEditor(old_preset, self._options)
        # self._logic_settings_window = CustomizePresetDialog(self._window_manager, editor)
        # self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())
        # editor.on_changed = lambda: self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())
        # self._logic_settings_window._game_session_row = row
        #
        # result = await async_dialog.execute_dialog(self._logic_settings_window)
        # self._logic_settings_window = None
        #
        # if result == QtWidgets.QDialog.DialogCode.Accepted:
        #     new_preset = VersionedPreset.with_preset(editor.create_custom_preset_with())
        #
        #     if self._preset_manager.add_new_preset(new_preset):
        #         self.refresh_row_import_preset_actions()
        #
        #     await self._do_import_preset(row_index, new_preset)

    def _get_preset(self, world_uid: uuid.UUID) -> VersionedPreset:
        return VersionedPreset.from_str(self._session.get_world(world_uid).preset_raw)

    @asyncSlot()
    async def _world_save_preset_copy(self, world_uid: uuid.UUID):
        preset = self._get_preset(world_uid)

        if preset.is_included_preset:
            # Nothing to do, this is an included preset
            return

        self._preset_manager.add_new_preset(preset)

    @asyncSlot()
    async def _world_save_preset_to_file(self, world_uid: uuid.UUID):
        path = common_qt_lib.prompt_user_for_preset_file(self, new_file=True)
        if path is None:
            return

        preset = self._get_preset(world_uid)
        preset.save_to_file(path)

    @asyncSlot()
    async def _world_export(self, world_uid: uuid.UUID):
        options = self._options

        if not options.is_alert_displayed(InfoAlert.MULTIWORLD_FAQ):
            await async_dialog.message_box(self, QtWidgets.QMessageBox.Icon.Information, "Multiworld FAQ",
                                           "Have you read the Multiworld FAQ?\n"
                                           "It can be found in the main Randovania window → Help → Multiworld")
            options.mark_alert_as_displayed(InfoAlert.MULTIWORLD_FAQ)

        game_enum = self._get_preset(world_uid).game
        patch_data = await self._session_api.create_patcher_file(
            world_uid, options.options_for_game(game_enum).cosmetic_patches.as_json
        )
        self.GameExportRequested.emit(world_uid, patch_data)

    #

    @asyncSlot()
    async def _new_world(self, user_id: int):
        dialog = self._create_select_preset_dialog(True)

        result = await async_dialog.execute_dialog(dialog)
        if result != QtWidgets.QDialog.DialogCode.Accepted:
            return

        preset = dialog.selected_preset
        new_name = dialog.world_name_edit.text()

        # Temp
        await self._session_api.create_new_world(new_name, preset, user_id)

    @asyncSlot()
    async def _customize_cosmetic(self, world_uid: uuid.UUID):
        preset = self._get_preset(world_uid)
        per_game_options = self._options.options_for_game(preset.game)

        dialog = game_specific_gui.create_dialog_for_cosmetic_patches(self, per_game_options.cosmetic_patches)
        result = await async_dialog.execute_dialog(dialog)
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            with self._options as options:
                options.set_options_for_game(preset.game, dataclasses.replace(per_game_options,
                                                                              cosmetic_patches=dialog.cosmetic_patches))

    #

    def _watch_inventory(self, world_uid: uuid.UUID, user_id: int):
        self.TrackWorldRequested.emit(world_uid, user_id)

    #

    def is_admin(self) -> bool:
        return self._session.users[self.your_id].admin

    def update_state(self, game_session: MultiplayerSessionEntry):
        self.clear()

        self._session = game_session
        in_setup = self._session.state == MultiplayerSessionState.SETUP
        has_layout = self._session.game_details is not None

        world_by_id: dict[uuid.UUID, MultiplayerWorld] = {
            game.id: game
            for game in game_session.worlds
        }
        used_worlds = set()

        def _add_world(world_details: MultiplayerWorld, parent: QtWidgets.QTreeWidgetItem,
                       owner: int | None, user_world_state: str):

            preset = VersionedPreset.from_str(world_details.preset_raw)
            world_item = QtWidgets.QTreeWidgetItem(parent)
            # game_item.setFlags(game_item.flags() | Qt.ItemFlag.ItemIsEditable)
            world_item.setText(0, world_details.name)
            world_item.setText(1, preset.game.long_name)
            world_item.setText(2, user_world_state)

            world_tool = make_tool("Actions")

            world_menu = QtWidgets.QMenu(world_tool)
            preset_menu = world_menu.addMenu(f"Preset: {preset.name}")
            connect_to(preset_menu.addAction("View summary"),
                       self._preset_view_summary, world_details.id)

            if owner == self.your_id or self.is_admin():
                # TODO: Customize preset button
                # customize_action = preset_menu.addAction("Customize")
                # customize_action.setEnabled(not has_layout)
                # connect_to(customize_action,
                #            self._preset_customize, world_details.id)

                connect_to(
                    preset_menu.addAction("Replace with"),
                    self._world_replace_preset, world_details.id,
                ).setEnabled(not has_layout)

            export_menu = preset_menu.addMenu("Export preset")
            connect_to(export_menu.addAction("Save copy of preset"), self._world_save_preset_copy, world_details.id)
            connect_to(export_menu.addAction("Save to file"), self._world_save_preset_to_file, world_details.id)

            if owner == self.your_id:
                export_action = world_menu.addAction("Export game")
                export_action.setEnabled(has_layout)
                connect_to(export_action, self._world_export, world_details.id)

                connect_to(world_menu.addAction("Customize cosmetic options"), self._customize_cosmetic,
                           world_details.id)

            if owner is None:
                world_menu.addSeparator()
                connect_to(world_menu.addAction("Claim for yourself"),
                           self._world_claim_with, world_details.id,
                           self.your_id)

                if self.is_admin():
                    claim_menu = world_menu.addMenu("Claim for")
                    for p in self._session.users.values():
                        connect_to(claim_menu.addAction(p.name),
                                   self._world_claim_with, world_details.id,
                                   p.id)

            elif self.is_admin():
                world_menu.addSeparator()
                connect_to(world_menu.addAction("Unclaim"), self._world_unclaim, world_details.id, owner)

            if owner == self.your_id or self.is_admin():
                world_menu.addSeparator()
                connect_to(world_menu.addAction("Rename"), self._world_rename, world_details.id)
                delete_action = world_menu.addAction("Delete")
                delete_action.setEnabled(not has_layout)
                connect_to(delete_action, self._world_delete, world_details.id)

            if owner is not None:
                world_menu.addSeparator()
                connect_to(world_menu.addAction("Watch inventory"), self._watch_inventory, world_details.id, owner)

            world_tool.setMenu(world_menu)

            self.setItemWidget(world_item, 3, world_tool)

        for player in game_session.users.values():
            item = QtWidgets.QTreeWidgetItem(self)
            item.setExpanded(True)
            item.setText(0, player.name)
            if player.admin:
                item.setText(1, "(Admin)")

            for world_uid, state in player.worlds.items():
                used_worlds.add(world_uid)
                _add_world(world_by_id[world_uid], item, player.id, state.connection_state.pretty_text)

            if player.id != self.your_id and self.is_admin():
                tool = make_tool("Administrate")
                menu = QtWidgets.QMenu(tool)
                kick_action = menu.addAction("Kick player")
                connect_to(kick_action, self._kick_player, player.id)
                switch_admin = menu.addAction("Demote from Admin" if player.admin else "Promote to Admin")
                connect_to(switch_admin, self._switch_admin, player.id)
                tool.setMenu(menu)
                self.setItemWidget(item, 3, tool)

            if in_setup and not has_layout and (player.id == self.your_id or self.is_admin()):
                new_game_item = QtWidgets.QTreeWidgetItem(item)
                tool = make_tool("New world")
                tool.clicked.connect(functools.partial(self._new_world, player.id))
                self.setItemWidget(new_game_item, 0, tool)

        missing_games = set(world_by_id.keys()) - used_worlds
        if missing_games:
            missing_game_item = QtWidgets.QTreeWidgetItem(self)
            missing_game_item.setExpanded(True)
            missing_game_item.setText(0, "Unclaimed Games")

            for world_uid in missing_games:
                _add_world(world_by_id[world_uid], missing_game_item, None, "Abandoned")

        self.resizeColumnToContents(0)
        self.resizeColumnToContents(1)
