from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import Qt

from randovania import monitoring

if TYPE_CHECKING:
    import uuid

    from randovania.games.game import RandovaniaGame
    from randovania.interface_common.options import Options
    from randovania.interface_common.preset_manager import PresetManager
    from randovania.layout.versioned_preset import VersionedPreset


class PresetTreeWidget(QtWidgets.QTreeWidget):
    game: RandovaniaGame
    preset_manager: PresetManager
    options: Options
    preset_to_item: dict[uuid.UUID, QtWidgets.QTreeWidgetItem]
    expanded_connected: bool = False

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        source = self.preset_for_item(self.currentItem())
        if source is None:
            return event.setDropAction(Qt.IgnoreAction)

        if source.is_included_preset:
            return event.setDropAction(Qt.IgnoreAction)

        new_order = self.options.get_preset_order_for(self.game)
        try:
            new_order.remove(source.uuid)
        except ValueError:
            # No order present, that's fine
            pass

        item: QtWidgets.QTreeWidgetItem | None = self.itemAt(event.pos())
        if item is None:
            target_uuid = None
            new_order.append(source.uuid)
        else:
            target = self.preset_for_item(item)

            if self.dropIndicatorPosition() != QtWidgets.QAbstractItemView.DropIndicatorPosition.OnItem:
                target_uuid = self.options.get_parent_for_preset(target.uuid)

                new_index = new_order.index(target.uuid)
                if self.dropIndicatorPosition() != QtWidgets.QAbstractItemView.DropIndicatorPosition.AboveItem:
                    new_index += 1
                new_order.insert(new_index, source.uuid)

            else:
                target_uuid = target.uuid

        with self.options as options:
            options.set_parent_for_preset(source.uuid, target_uuid)
            options.set_preset_order_for(self.game, new_order)

        self.update_items()
        return event.setDropAction(Qt.IgnoreAction)

    def preset_for_item(self, item: QtWidgets.QTreeWidgetItem) -> VersionedPreset | None:
        return self.preset_manager.preset_for_uuid(item.data(0, Qt.UserRole))

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

        def create_item(
            parent: QtWidgets.QTreeWidgetItem | QtWidgets.QTreeWidget,
            the_preset: VersionedPreset,
        ) -> QtWidgets.QTreeWidgetItem:
            it = QtWidgets.QTreeWidgetItem(parent)
            it.setText(0, the_preset.name)
            it.setData(0, Qt.UserRole, the_preset.uuid)
            self.preset_to_item[the_preset.uuid] = it
            return it

        # Included presets
        for preset in self.preset_manager.included_presets.values():
            if preset.game != self.game:
                continue

            item = create_item(self, preset)
            root_parents.add(item)

            if default_parent is None:
                # The first included preset will be the parent of all presets with missing parents
                default_parent = item

        # Custom Presets
        order_by_key = {pid: i for i, pid in enumerate(self.options.get_preset_order_for(self.game))}
        ordered_custom_presets = [
            preset for preset in self.preset_manager.custom_presets.values() if preset.game == self.game
        ]
        ordered_custom_presets.sort(key=lambda p: (order_by_key.get(p.uuid, math.inf), p.name.lower()))

        for preset in ordered_custom_presets:
            preset_parent = self.options.get_parent_for_preset(preset.uuid)
            item = create_item(self if preset_parent is None else default_parent, preset)
            if preset_parent is None:
                root_parents.add(item)

        monitoring.metrics.gauge(
            "amount_of_presets", value=len(self.preset_to_item), tags={"game": self.game.short_name}
        )

        # Set parents after, so don't have issues with order
        for preset in ordered_custom_presets:
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

        final_order = [
            item.data(0, Qt.UserRole)
            for item in self.findItems("", Qt.MatchFlag.MatchRecursive | Qt.MatchFlag.MatchStartsWith)
        ]

        with self.options as options:
            options.set_preset_order_for(self.game, final_order)

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
