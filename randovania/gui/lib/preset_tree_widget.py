import dataclasses
import uuid

from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt

from randovania.games.game import RandovaniaGame
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.options import Options
from randovania.layout.versioned_preset import InvalidPreset, VersionedPreset


class PresetTreeWidget(QtWidgets.QTreeWidget):
    game: RandovaniaGame
    window_manager: WindowManager
    options: Options
    preset_to_item: dict[uuid.UUID, QtWidgets.QTreeWidgetItem]
    expanded_connected: bool = False

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        item: QtWidgets.QTreeWidgetItem = self.itemAt(event.pos())
        if not item:
            return event.setDropAction(Qt.IgnoreAction)

        source = self.preset_for_item(self.currentItem())
        target = self.preset_for_item(item)

        if source is None or target is None:
            return event.setDropAction(Qt.IgnoreAction)

        if source.game != target.game or source.is_included_preset:
            return event.setDropAction(Qt.IgnoreAction)

        with self.options as options:
            options.set_parent_for_preset(source.uuid, target.uuid)

        return super().dropEvent(event)

    def preset_for_item(self, item: QtWidgets.QTreeWidgetItem) -> VersionedPreset | None:
        return self.window_manager.preset_manager.preset_for_uuid(item.data(0, Qt.UserRole))

    @property
    def current_preset_data(self) -> VersionedPreset | None:
        for item in self.selectedItems():
            return self.preset_for_item(item)

    def update_items(self):
        if self.expanded_connected:
            self.itemExpanded.disconnect(self.on_item_expanded)
            self.itemCollapsed.disconnect(self.on_item_collapsed)
            self.expanded_connected = False

        self.clear()
        self.setRootIsDecorated(True)

        self.preset_to_item = {}
        default_parent = None
        root_parents = set()

        # Included presets
        for preset in self.window_manager.preset_manager.included_presets.values():
            if preset.game != self.game:
                continue

            item = QtWidgets.QTreeWidgetItem(self)
            item.setText(0, preset.name)
            item.setData(0, Qt.UserRole, preset.uuid)
            item.setExpanded(True)
            self.preset_to_item[preset.uuid] = item
            root_parents.add(item)

            if default_parent is None:
                # The first included preset will be the parent of all presets with missing parents
                default_parent = item

        # Custom Presets
        for preset in self.window_manager.preset_manager.custom_presets.values():
            if preset.game != self.game:
                continue

            item = QtWidgets.QTreeWidgetItem(default_parent)
            item.setText(0, preset.name)
            item.setData(0, Qt.UserRole, preset.uuid)
            self.preset_to_item[preset.uuid] = item

        # Set parents after, so don't have issues with order
        for preset in sorted(self.window_manager.preset_manager.custom_presets.values(), key=lambda it: it.name):
            preset_parent = self.options.get_parent_for_preset(preset.uuid)
            if preset_parent in self.preset_to_item:
                self_item = self.preset_to_item[preset.uuid]
                target_parent = parent_item = self.preset_to_item[preset_parent]

                while parent_item not in root_parents:
                    if parent_item == self_item:
                        # LOOP DETECTED!
                        target_parent = default_parent
                        break
                    parent_item = parent_item.parent()

                if default_parent != target_parent:
                    default_parent.removeChild(self_item)
                    target_parent.addChild(self_item)

        for preset_uuid, item in self.preset_to_item.items():
            item.setExpanded(not self.options.is_preset_uuid_hidden(preset_uuid))

        self.itemExpanded.connect(self.on_item_expanded)
        self.itemCollapsed.connect(self.on_item_collapsed)
        self.expanded_connected = True

    def select_preset(self, preset: VersionedPreset):
        if preset.uuid in self.preset_to_item:
            self.setCurrentItem(self.preset_to_item[preset.uuid])

    def _on_item_new_state(self, item: QtWidgets.QTreeWidgetItem, new_state: bool):
        uid = item.data(0, Qt.UserRole)
        if uid is not None:
            with self.options as options:
                options.set_preset_uuid_hidden(uid, not new_state)

    def on_item_expanded(self, item):
        self._on_item_new_state(item, True)

    def on_item_collapsed(self, item):
        self._on_item_new_state(item, False)
