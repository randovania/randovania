from __future__ import annotations

import dataclasses
import functools
import logging
import uuid
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal
from qasync import asyncSlot

from randovania.game_connection.builder.debug_connector_builder import DebugConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.gui import game_specific_gui
from randovania.gui.dialog.multiplayer_select_preset_dialog import MultiplayerSelectPresetDialog
from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog
from randovania.gui.lib import async_dialog, common_qt_lib
from randovania.interface_common.options import InfoAlert, Options
from randovania.layout import preset_describer
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common.multiplayer_session import (
    MAX_WORLD_NAME_LENGTH,
    WORLD_NAME_RE,
    MultiplayerSessionEntry,
    MultiplayerUser,
    MultiplayerWorld,
    UserWorldDetail,
)

if TYPE_CHECKING:
    from randovania.games.game import RandovaniaGame
    from randovania.gui.lib.multiplayer_session_api import MultiplayerSessionApi
    from randovania.gui.lib.window_manager import WindowManager

logger = logging.getLogger(__name__)


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


@dataclasses.dataclass()
class UserWidgetEntry:
    item: QtWidgets.QTreeWidgetItem
    ready_check: QtWidgets.QCheckBox
    switch_admin: QtGui.QAction | None

    def update(self, user: MultiplayerUser):
        self.item.setText(0, user.name)
        self.item.setText(1, "(Admin)" if user.admin else "")
        self.ready_check.setChecked(user.ready)
        if self.switch_admin is not None:
            self.switch_admin.setText("Demote from Admin" if user.admin else "Promote to Admin")


@dataclasses.dataclass()
class WorldWidgetEntry:
    item: QtWidgets.QTreeWidgetItem
    preset_menu: QtWidgets.QMenu

    def update(self, world_details: MultiplayerWorld, detail: UserWorldDetail | None):
        self.item.setText(0, world_details.name)
        self.item.setText(1, world_details.preset.game.long_name)
        self.item.setText(2, detail.connection_state.pretty_text if detail is not None else "Abandoned")
        self.preset_menu.setTitle(f"Preset: {world_details.preset.name}")

        if detail is not None:
            self.item.setText(4, "Last Activity:")
            self.item.setTextAlignment(4, QtCore.Qt.AlignmentFlag.AlignRight)
            self.item.setData(
                5,
                QtCore.Qt.ItemDataRole.DisplayRole,
                QtCore.QDateTime.fromSecsSinceEpoch(int(detail.last_activity.timestamp())),
            )


class MultiplayerSessionUsersWidget(QtWidgets.QTreeWidget):
    GameExportRequested = Signal(uuid.UUID, dict)
    TrackWorldRequested = Signal(uuid.UUID, int)

    _last_session: MultiplayerSessionEntry | None = None
    _session: MultiplayerSessionEntry
    _user_widgets: dict[int, UserWidgetEntry]
    _world_widgets: dict[uuid.UUID, WorldWidgetEntry]

    def __init__(self, options: Options, window_manager: WindowManager, session_api: MultiplayerSessionApi):
        super().__init__()
        self.header().setStretchLastSection(False)
        self.headerItem().setText(0, "Name")
        self.headerItem().setText(1, "")
        self.headerItem().setText(2, "")
        self.headerItem().setText(3, "")
        self.headerItem().setText(4, "")
        self.headerItem().setText(5, "")
        self.header().setVisible(False)
        self.header().setSectionsMovable(False)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel)

        self._options = options
        self._window_manager = window_manager
        self._session_api = session_api
        self._world_widgets = {}
        self._user_widgets = {}

    @property
    def your_id(self) -> int | None:
        user = self._session_api.network_client.current_user
        if user is not None:
            return user.id
        return None

    def _widget_state_for(self, session: MultiplayerSessionEntry | None):
        if session is None:
            return []

        you = session.users.get(self.your_id)
        return [
            you is not None and you.admin,
            [(user.id, user.name, list(user.worlds.keys())) for user in session.users_list],
            [w.id for w in session.worlds],
            session.generation_in_progress,
            session.game_details,
        ]

    #

    def _create_select_preset_dialog(self, include_world_name_prompt: bool, default_game: RandovaniaGame | None):
        return MultiplayerSelectPresetDialog(
            self._window_manager,
            self._options,
            allowed_games=self._session.allowed_games,
            default_game=default_game,
            include_world_name_prompt=include_world_name_prompt,
        )

    async def _prompt_for_preset(self, default_game: RandovaniaGame | None):
        dialog = self._create_select_preset_dialog(False, default_game)
        result = await async_dialog.execute_dialog(dialog)
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            return dialog.selected_preset
        else:
            return None

    #

    @asyncSlot()
    async def _world_replace_preset(self, world_uid: uuid.UUID):
        game = self._session.get_world(world_uid).preset.game
        preset = await self._prompt_for_preset(game)
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
    async def _switch_readiness(self, user_id: int):
        await self._session_api.switch_readiness(user_id)

    @asyncSlot()
    async def _world_rename(self, world_uid: uuid.UUID):
        old_name = self._session.get_world(world_uid).name
        new_name = await TextPromptDialog.prompt(
            parent=self,
            title="Enter world name",
            description="Select a new name for the world:",
            initial_value=old_name,
            is_modal=True,
            max_length=MAX_WORLD_NAME_LENGTH,
            check_re=WORLD_NAME_RE,
        )
        if new_name == old_name:
            return

        if new_name is not None:
            if any(new_name == world.name for world in self._session.worlds):
                return await async_dialog.warning(
                    self, "Name already exists", f"A world named '{new_name}' already exists."
                )

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

    def _get_preset(self, world_uid: uuid.UUID) -> VersionedPreset:
        return VersionedPreset.from_str(self._session.get_world(world_uid).preset_raw)

    @asyncSlot()
    async def _world_save_preset_copy(self, world_uid: uuid.UUID):
        preset = self._get_preset(world_uid)

        if preset.is_included_preset:
            # Nothing to do, this is an included preset
            return

        self._window_manager.preset_manager.add_new_preset(preset)

    @asyncSlot()
    async def _world_save_preset_to_file(self, world_uid: uuid.UUID):
        path = common_qt_lib.prompt_user_for_preset_file(self, new_file=True)
        if path is None:
            return

        preset = self._get_preset(world_uid)
        preset.save_to_file(path)

    @asyncSlot()
    async def world_export(self, world_uid: uuid.UUID):
        options = self._options

        if not options.is_alert_displayed(InfoAlert.MULTIWORLD_FAQ):
            await async_dialog.message_box(
                self,
                QtWidgets.QMessageBox.Icon.Information,
                "Multiworld FAQ",
                "Have you read the Multiworld FAQ?\n"
                "It can be found in the main Randovania window → Help → Multiworld",
            )
            options.mark_alert_as_displayed(InfoAlert.MULTIWORLD_FAQ)

        game_enum = self._get_preset(world_uid).game
        patch_data = await self._session_api.create_patcher_file(
            world_uid, options.options_for_game(game_enum).cosmetic_patches.as_json
        )
        self.GameExportRequested.emit(world_uid, patch_data)

    #

    @asyncSlot()
    async def _new_world(self, user_id: int):
        dialog = self._create_select_preset_dialog(True, None)

        result = await async_dialog.execute_dialog(dialog)
        if result != QtWidgets.QDialog.DialogCode.Accepted:
            return

        preset = dialog.selected_preset
        new_name = dialog.world_name_edit.text().strip()

        if any(new_name == world.name for world in self._session.worlds):
            return await async_dialog.warning(
                self, "Name already exists", f"A world named '{new_name}' already exists."
            )

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
                options.set_options_for_game(
                    preset.game, dataclasses.replace(per_game_options, cosmetic_patches=dialog.cosmetic_patches)
                )

    def _register_debug_connector(self, world_uid: uuid.UUID):
        common_qt_lib.get_game_connection().add_connection_builder(
            DebugConnectorBuilder.create(
                self._get_preset(world_uid).game,
                world_uid,
            )
        )

    #

    def _watch_inventory(self, world_uid: uuid.UUID, user_id: int):
        self.TrackWorldRequested.emit(world_uid, user_id)

    #
    def is_admin(self) -> bool:
        return self._session.users[self.your_id].admin

    def _create_world_item(
        self, world_id: uuid.UUID, parent: QtWidgets.QTreeWidgetItem, owner: int | None
    ) -> WorldWidgetEntry:
        in_generation = self._session.generation_in_progress is not None
        has_layout = self._session.game_details is not None
        can_change_preset = not has_layout and not in_generation

        world_item = QtWidgets.QTreeWidgetItem(parent)
        world_item.setText(0, "<the name>")
        world_item.setText(1, "<game>")
        world_item.setText(2, "<state>")

        world_tool = make_tool("Actions")

        world_menu = QtWidgets.QMenu(world_tool)
        preset_menu = world_menu.addMenu("Preset: <preset name>")
        connect_to(preset_menu.addAction("View summary"), self._preset_view_summary, world_id)

        if owner == self.your_id or self.is_admin():
            connect_to(
                preset_menu.addAction("Replace with"),
                self._world_replace_preset,
                world_id,
            ).setEnabled(can_change_preset)

        export_menu = preset_menu.addMenu("Export preset")
        connect_to(export_menu.addAction("Save copy of preset"), self._world_save_preset_copy, world_id)
        connect_to(export_menu.addAction("Save to file"), self._world_save_preset_to_file, world_id)

        if owner == self.your_id:
            export_action = world_menu.addAction("Export game")
            export_action.setEnabled(has_layout)
            connect_to(export_action, self.world_export, world_id)

            connect_to(world_menu.addAction("Customize cosmetic options"), self._customize_cosmetic, world_id)
            if ConnectorBuilderChoice.DEBUG.is_usable():
                connect_to(
                    world_menu.addAction("Connect via debug connector"), self._register_debug_connector, world_id
                )

        if self.is_admin() or self._session.allow_everyone_claim_world:
            if owner is None:
                world_menu.addSeparator()
                connect_to(world_menu.addAction("Claim for yourself"), self._world_claim_with, world_id, self.your_id)

                if self.is_admin():
                    claim_menu = world_menu.addMenu("Claim for")
                    for p in self._session.users.values():
                        connect_to(claim_menu.addAction(p.name), self._world_claim_with, world_id, p.id)

            else:
                world_menu.addSeparator()
                connect_to(world_menu.addAction("Unclaim"), self._world_unclaim, world_id, owner)

        if owner == self.your_id or self.is_admin():
            world_menu.addSeparator()
            connect_to(world_menu.addAction("Rename"), self._world_rename, world_id)
            delete_action = world_menu.addAction("Delete")
            delete_action.setEnabled(can_change_preset)
            connect_to(delete_action, self._world_delete, world_id)

        if owner is not None:
            world_menu.addSeparator()
            connect_to(world_menu.addAction("Watch inventory"), self._watch_inventory, world_id, owner)

        world_tool.setMenu(world_menu)

        self.setItemWidget(world_item, 3, world_tool)

        self._world_widgets[world_id] = WorldWidgetEntry(
            item=world_item,
            preset_menu=preset_menu,
        )
        return self._world_widgets[world_id]

    def _create_all_widgets_from_scratch(self):
        self.clear()
        self._world_widgets.clear()
        self._user_widgets.clear()

        in_generation = self._session.generation_in_progress is not None
        has_layout = self._session.game_details is not None

        world_by_id: dict[uuid.UUID, MultiplayerWorld] = {world.id: world for world in self._session.worlds}
        used_worlds = set()

        for user in self._session.users.values():
            item = QtWidgets.QTreeWidgetItem(self)
            item.setExpanded(True)

            ready_check = QtWidgets.QCheckBox("Ready?")
            ready_check.setEnabled(user.id == self.your_id or self.is_admin())
            ready_check.clicked.connect(functools.partial(self._switch_readiness, user.id))
            self.setItemWidget(item, 2, ready_check)

            for world_uid, state in user.worlds.items():
                used_worlds.add(world_uid)
                the_item = self._create_world_item(world_uid, item, user.id)
                the_item.update(world_by_id[world_uid], state)

            if user.id != self.your_id and self.is_admin():
                tool = make_tool("Administrate")
                menu = QtWidgets.QMenu(tool)
                kick_action = menu.addAction("Kick player")
                connect_to(kick_action, self._kick_player, user.id)
                switch_admin = menu.addAction("Switch Admin")
                connect_to(switch_admin, self._switch_admin, user.id)
                tool.setMenu(menu)
                self.setItemWidget(item, 3, tool)
            else:
                switch_admin = None

            if not has_layout and (user.id == self.your_id or self.is_admin()):
                new_game_item = QtWidgets.QTreeWidgetItem(item)
                tool = QtWidgets.QPushButton("Add new world")
                tool.clicked.connect(functools.partial(self._new_world, user.id))
                tool.setMinimumWidth(100)
                tool.setEnabled(not in_generation)
                self.setItemWidget(new_game_item, 0, tool)

            self._user_widgets[user.id] = UserWidgetEntry(
                item=item,
                ready_check=ready_check,
                switch_admin=switch_admin,
            )
            self._user_widgets[user.id].update(user)

        unclaimed_worlds = set(world_by_id.keys()) - used_worlds
        if unclaimed_worlds:
            unclaimed_world_item = QtWidgets.QTreeWidgetItem(self)
            unclaimed_world_item.setExpanded(True)
            unclaimed_world_item.setText(0, "Unclaimed Games")

            for world_uid, world in world_by_id.items():
                if world_uid in unclaimed_worlds:
                    self._create_world_item(world_uid, unclaimed_world_item, None).update(
                        world_by_id[world_uid],
                        None,
                    )

        self.resizeColumnToContents(0)
        self.resizeColumnToContents(1)

    def update_state(self, session: MultiplayerSessionEntry):
        self._last_session = getattr(self, "_session", None)
        self._session = session

        if self._widget_state_for(self._last_session) != self._widget_state_for(session):
            if self._last_session is not None:
                logger.info("Recreating all widgets as can't update only strings")
            return self._create_all_widgets_from_scratch()

        logger.info("Lightweight widget update")
        world_states = {}

        for user in session.users_list:
            self._user_widgets[user.id].update(user)
            for world_id, state in user.worlds.items():
                world_states[world_id] = state

        for world in session.worlds:
            self._world_widgets[world.id].update(world, world_states.get(world.id))
