import dataclasses
import uuid
from typing import Optional, Dict

from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import Qt

from randovania.games.game import RandovaniaGame
from randovania.gui.lib.window_manager import WindowManager
from randovania.lib import enum_lib
from randovania.layout.preset_migration import VersionedPreset, InvalidPreset


class PresetTreeWidget(QtWidgets.QTreeWidget):
    window_manager: WindowManager
    preset_to_item: Dict[uuid.UUID, QtWidgets.QTreeWidgetItem]
    show_experimental: bool = False

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

    def preset_for_item(self, item: QtWidgets.QTreeWidgetItem) -> Optional[VersionedPreset]:
        return self.window_manager.preset_manager.preset_for_uuid(item.data(0, Qt.UserRole))

    @property
    def current_preset_data(self) -> Optional[VersionedPreset]:
        for item in self.selectedItems():
            return self.preset_for_item(item)

    def set_show_experimental(self, show_experimental: bool):
        old = self.show_experimental
        self.show_experimental = show_experimental
        if old != show_experimental:
            self.update_items()

    def update_items(self):
        self.clear()

        tree_item = {}
        for game in enum_lib.iterate_enum(RandovaniaGame):
            if game.is_experimental and not self.show_experimental:
                continue

            root = QtWidgets.QTreeWidgetItem(self)
            root.setText(0, game.long_name)
            root.setExpanded(True)
            tree_item[game] = root

        self.preset_to_item = {}

        # Included presets
        for preset in self.window_manager.preset_manager.included_presets.values():
            if preset.game.is_experimental and not self.show_experimental:
                continue

            item = QtWidgets.QTreeWidgetItem(tree_item[preset.game])
            item.setText(0, preset.name)
            item.setExpanded(True)
            item.setData(0, Qt.UserRole, preset.uuid)
            self.preset_to_item[preset.uuid] = item

        # Custom Presets
        for preset in self.window_manager.preset_manager.custom_presets.values():
            if preset.game.is_experimental and not self.show_experimental:
                continue

            item = QtWidgets.QTreeWidgetItem(tree_item[preset.game])
            item.setText(0, preset.name)
            item.setData(0, Qt.UserRole, preset.uuid)
            self.preset_to_item[preset.uuid] = item

        # Set parents after, so don't have issues with order
        for preset in sorted(self.window_manager.preset_manager.custom_presets.values(), key=lambda it: it.name):
            if preset.base_preset_uuid in self.preset_to_item:
                tree_item[preset.game].removeChild(self.preset_to_item[preset.uuid])
                self.preset_to_item[preset.base_preset_uuid].addChild(self.preset_to_item[preset.uuid])

    def select_preset(self, preset: VersionedPreset):
        if preset.uuid in self.preset_to_item:
            self.setCurrentItem(self.preset_to_item[preset.uuid])
