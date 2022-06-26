import dataclasses
import uuid

from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt

from randovania.games.game import RandovaniaGame
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.options import Options
from randovania.layout.versioned_preset import InvalidPreset, VersionedPreset


class PresetTreeWidget(QtWidgets.QTreeWidget):
    window_manager: WindowManager
    options: Options
    preset_to_item: dict[uuid.UUID, QtWidgets.QTreeWidgetItem]
    show_experimental: bool = False
    expanded_connected: bool = False
    root_tree_items: dict[RandovaniaGame, QtWidgets.QTreeWidgetItem]

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        item: QtWidgets.QTreeWidgetItem = self.itemAt(event.pos())
        if not item:
            return event.setDropAction(Qt.IgnoreAction)

        source = self.preset_for_item(self.currentItem())
        target = self.preset_for_item(item)

        if source is None or target is None:
            return event.setDropAction(Qt.IgnoreAction)

        if source.game != target.game or source.base_preset_uuid is None:
            return event.setDropAction(Qt.IgnoreAction)

        try:
            source_preset = source.get_preset()
        except InvalidPreset:
            return event.setDropAction(Qt.IgnoreAction)

        self.window_manager.preset_manager.add_new_preset(VersionedPreset.with_preset(
            dataclasses.replace(source_preset, base_preset_uuid=target.uuid)
        ))

        return super().dropEvent(event)

    def preset_for_item(self, item: QtWidgets.QTreeWidgetItem) -> VersionedPreset | None:
        return self.window_manager.preset_manager.preset_for_uuid(item.data(0, Qt.UserRole))

    @property
    def current_preset_data(self) -> VersionedPreset | None:
        for item in self.selectedItems():
            return self.preset_for_item(item)

    def set_show_experimental(self, show_experimental: bool):
        old = self.show_experimental
        self.show_experimental = show_experimental
        if old != show_experimental:
            self.update_items()

    def update_items(self):
        if self.expanded_connected:
            self.itemExpanded.disconnect(self.on_item_expanded)
            self.itemCollapsed.disconnect(self.on_item_collapsed)
            self.expanded_connected = False

        self.clear()

        self.root_tree_items = {}

        for game in RandovaniaGame.sorted_all_games():
            if not game.data.development_state.can_view(self.show_experimental):
                continue

            root = QtWidgets.QTreeWidgetItem(self)
            root.setText(0, game.long_name)
            root.setExpanded(self.options.is_game_expanded(game))
            self.root_tree_items[game] = root

        self.preset_to_item = {}

        # Included presets
        for preset in self.window_manager.preset_manager.included_presets.values():
            if not preset.game.data.development_state.can_view(self.show_experimental):
                continue

            item = QtWidgets.QTreeWidgetItem(self.root_tree_items[preset.game])
            item.setText(0, preset.name)
            item.setData(0, Qt.UserRole, preset.uuid)
            self.preset_to_item[preset.uuid] = item

        # Custom Presets
        for preset in self.window_manager.preset_manager.custom_presets.values():
            if not preset.game.data.development_state.can_view(self.show_experimental):
                continue

            item = QtWidgets.QTreeWidgetItem(self.root_tree_items[preset.game])
            item.setText(0, preset.name)
            item.setData(0, Qt.UserRole, preset.uuid)
            self.preset_to_item[preset.uuid] = item

        # Set parents after, so don't have issues with order
        for preset in sorted(self.window_manager.preset_manager.custom_presets.values(), key=lambda it: it.name):
            if preset.base_preset_uuid in self.preset_to_item:
                root_item = self.root_tree_items[preset.game]
                self_item = self.preset_to_item[preset.uuid]
                target_parent = parent_item = self.preset_to_item[preset.base_preset_uuid]

                while parent_item != root_item:
                    if parent_item == self_item:
                        # LOOP DETECTED!
                        target_parent = root_item
                        break
                    parent_item = parent_item.parent()

                root_item.removeChild(self_item)
                target_parent.addChild(self_item)

        for preset_uuid, item in self.preset_to_item.items():
            item.setExpanded(not self.options.is_preset_uuid_hidden(preset_uuid))

        self.itemExpanded.connect(self.on_item_expanded)
        self.itemCollapsed.connect(self.on_item_collapsed)
        self.expanded_connected = True

    def select_preset(self, preset: VersionedPreset):
        if preset.uuid in self.preset_to_item:
            self.setCurrentItem(self.preset_to_item[preset.uuid])

    def _find_game_for_root_item(self, item):
        for game, root_item in self.root_tree_items.items():
            if root_item is item:
                return game
        raise ValueError(f"Unknown item: {item}")

    def _on_item_new_state(self, item: QtWidgets.QTreeWidgetItem, new_state: bool):
        uid = item.data(0, Qt.UserRole)
        if uid is None:
            game = self._find_game_for_root_item(item)
            with self.options as options:
                options.set_is_game_expanded(game, new_state)
        else:
            with self.options as options:
                options.set_preset_uuid_hidden(uid, not new_state)

    def on_item_expanded(self, item):
        self._on_item_new_state(item, True)

    def on_item_collapsed(self, item):
        self._on_item_new_state(item, False)
