from __future__ import annotations

import collections
import itertools
import json
import logging
import traceback
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from qasync import asyncSlot

from randovania.game_description import integrity_check
from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.hint_node import HintNode, HintNodeKind
from randovania.game_description.db.node import GenericNode, Node, NodeLocation
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.teleporter_network_node import TeleporterNetworkNode
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.gui.dialog.connections_editor import ConnectionsEditor
from randovania.gui.generated.node_details_popup_ui import Ui_NodeDetailsPopup
from randovania.gui.lib import async_dialog, common_qt_lib, signal_handling
from randovania.gui.lib.connections_visualizer import ConnectionsVisualizer
from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.widgets.combo_box_item_delegate import ComboBoxItemDelegate
from randovania.lib import enum_lib, frozen_lib

if TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.dock import DockType, DockWeakness, DockWeaknessDatabase
    from randovania.game_description.db.region import Region
    from randovania.game_description.game_description import GameDescription


def refresh_if_needed(combo: QtWidgets.QComboBox, func) -> None:
    if combo.currentIndex() == 0:
        func(0)


class DockWeaknessListModel(QtCore.QAbstractListModel):
    items: list[DockWeakness]
    delegate: ComboBoxItemDelegate
    type: DockType

    def __init__(self, db: DockWeaknessDatabase):
        super().__init__()
        self.db = db
        self.delegate = ComboBoxItemDelegate()
        self.change_type(db.dock_types[0])

    def change_type(self, new_type: DockType) -> None:
        self.type = new_type
        self.items = []
        self.delegate.items = list(self.db.weaknesses[self.type].keys())

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.items) + 1

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> str | None:
        if role not in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole}:
            return None

        if index.row() < len(self.items):
            return self.items[index.row()].name

        elif role == Qt.ItemDataRole.DisplayRole:
            return "New..."

        return ""

    def setData(self, index: QtCore.QModelIndex, value: str, role: int = ...) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            new_weak = self.db.weaknesses[self.type][value]
            if index.row() < len(self.items):
                self.items[index.row()] = new_weak
                self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.DisplayRole])
            else:
                row = self.rowCount()
                self.beginInsertRows(QtCore.QModelIndex(), row + 1, row + 1)
                self.items.append(new_weak)
                self.endInsertRows()
            return True
        return False

    def removeRows(self, row: int, count: int, parent: QtCore.QModelIndex = ...) -> bool:
        self.beginRemoveRows(QtCore.QModelIndex(), row, row + count - 1)
        del self.items[row : row + count]
        self.endRemoveRows()
        return True

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable


class NodeDetailsPopup(QtWidgets.QDialog, Ui_NodeDetailsPopup):
    _hint_requirement_to_collect = Requirement.trivial()
    _unlocked_by_requirement = Requirement.trivial()
    _activated_by_requirement = Requirement.trivial()
    _connections_visualizers: dict[QtWidgets.QWidget, ConnectionsVisualizer]

    def __init__(self, game: GameDescription, node: Node):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.game = game
        self.node = node

        self._connections_visualizers = {}
        self._type_to_tab = {
            GenericNode: self.tab_generic,
            DockNode: self.tab_dock,
            PickupNode: self.tab_pickup,
            EventNode: self.tab_event,
            ConfigurableNode: self.tab_configurable,
            HintNode: self.tab_hint,
            TeleporterNetworkNode: self.tab_teleporter_network,
        }
        tab_to_type = {tab: node_type for node_type, tab in self._type_to_tab.items()}

        # Dynamic Stuff
        for node_type in self._type_to_tab.keys():
            self.node_type_combo.addItem(node_type.__name__, node_type)

        self.layers_combo.clear()
        for layer in game.layers:
            self.layers_combo.addItem(layer)
        self.layers_combo.setCurrentIndex(self.layers_combo.findText(node.layers[0]))

        self.dock_incompatible_model = DockWeaknessListModel(self.game.dock_weakness_database)
        self.dock_incompatible_list.setItemDelegate(self.dock_incompatible_model.delegate)
        self.dock_incompatible_list.setModel(self.dock_incompatible_model)
        self.dock_type_combo.clear()
        for i, dock_type in enumerate(game.dock_weakness_database.dock_types):
            self.dock_type_combo.addItem(dock_type.long_name, userData=dock_type)
        refresh_if_needed(self.dock_type_combo, self.on_dock_type_combo)

        for region in sorted(game.region_list.regions, key=lambda x: x.name):
            self.dock_connection_region_combo.addItem(region.name, userData=region)
            self.teleporter_destination_region_combo.addItem(region.name, userData=region)
        refresh_if_needed(self.dock_connection_region_combo, self.on_dock_connection_region_combo)
        refresh_if_needed(self.dock_connection_area_combo, self.on_dock_connection_area_combo)
        refresh_if_needed(self.teleporter_destination_region_combo, self.on_teleporter_destination_region_combo)

        for event in sorted(game.resource_database.event, key=lambda it: it.long_name):
            self.event_resource_combo.addItem(event.long_name, event)
        if self.event_resource_combo.count() == 0:
            self.event_resource_combo.addItem("No events in database", None)
            self.event_resource_combo.setEnabled(False)

        for hint_node_kind in enum_lib.iterate_enum(HintNodeKind):
            self.hint_kind_combo.addItem(hint_node_kind.long_name, hint_node_kind)

        # Pickup
        for category in enum_lib.iterate_enum(LocationCategory):
            self.location_category_combo.addItem(category.long_name, category)

        # Teleporter
        self.set_teleporter_network_unlocked_by(Requirement.trivial())

        # Signals
        self.button_box.accepted.connect(self.try_accept)
        self.button_box.rejected.connect(self.reject)
        self.name_edit.textEdited.connect(self.on_name_edit)
        self.node_type_combo.currentIndexChanged.connect(self.on_node_type_combo)
        self.dock_connection_region_combo.currentIndexChanged.connect(self.on_dock_connection_region_combo)
        self.dock_connection_area_combo.currentIndexChanged.connect(self.on_dock_connection_area_combo)
        self.dock_type_combo.currentIndexChanged.connect(self.on_dock_type_combo)
        self.dock_update_name_button.clicked.connect(self.on_dock_update_name_button)
        self.dock_incompatible_button.clicked.connect(self.on_dock_incompatible_delete_selected)
        self.pickup_index_button.clicked.connect(self.on_pickup_index_button)
        self.teleporter_destination_region_combo.currentIndexChanged.connect(
            self.on_teleporter_destination_region_combo
        )
        self.hint_requirement_to_collect_button.clicked.connect(self.on_hint_requirement_to_collect_button)
        self.teleporter_network_unlocked_button.clicked.connect(self.on_teleporter_network_unlocked_button)
        self.teleporter_network_activate_button.clicked.connect(self.on_teleporter_network_activated_button)

        # Hide the tab bar
        tab_bar: QtWidgets.QTabBar = self.tab_widget.findChild(QtWidgets.QTabBar)
        tab_bar.hide()

        # Values
        self.name_edit.setText(node.name)
        self.heals_check.setChecked(node.heal)
        self.location_group.setChecked(node.location is not None)
        if node.location is not None:
            self.location_x_spin.setValue(node.location.x)
            self.location_y_spin.setValue(node.location.y)
            self.location_z_spin.setValue(node.location.z)
        self.description_edit.setMarkdown(node.description)
        self.extra_edit.setPlainText(json.dumps(frozen_lib.unwrap(node.extra), indent=4))

        try:
            visible_tab = self._fill_for_type(node)
            set_combo_with_value(self.node_type_combo, tab_to_type[visible_tab])
            refresh_if_needed(self.node_type_combo, self.on_node_type_combo)
        except Exception:
            pass

        self.on_name_edit(self.name_edit.text())

    def _fill_for_type(self, node: Node) -> QtWidgets.QWidget:
        if isinstance(node, GenericNode):
            return self.tab_generic

        elif isinstance(node, DockNode):
            self.fill_for_dock(node)
            return self.tab_dock

        elif isinstance(node, PickupNode):
            self.fill_for_pickup(node)
            return self.tab_pickup

        elif isinstance(node, EventNode):
            self.fill_for_event(node)
            return self.tab_event

        elif isinstance(node, ConfigurableNode):
            self.fill_for_configurable(node)
            return self.tab_configurable

        elif isinstance(node, HintNode):
            self.fill_for_hint(node)
            return self.tab_hint

        elif isinstance(node, TeleporterNetworkNode):
            self.fill_for_teleporter_network(node)
            return self.tab_teleporter_network

        else:
            raise ValueError(f"Unknown node type: {node}")

    def fill_for_dock(self, node: DockNode) -> None:
        # Connection
        other_node = self.game.region_list.node_by_identifier(node.default_connection)
        area = self.game.region_list.nodes_to_area(other_node)
        region = self.game.region_list.nodes_to_region(other_node)

        signal_handling.set_combo_with_value(self.dock_connection_region_combo, region)
        refresh_if_needed(self.dock_connection_region_combo, self.on_dock_connection_region_combo)
        signal_handling.set_combo_with_value(self.dock_connection_area_combo, area)
        refresh_if_needed(self.dock_connection_area_combo, self.on_dock_connection_area_combo)
        signal_handling.set_combo_with_value(self.dock_connection_node_combo, other_node)

        # Dock Weakness
        signal_handling.set_combo_with_value(self.dock_type_combo, node.dock_type)
        refresh_if_needed(self.dock_type_combo, self.on_dock_type_combo)
        signal_handling.set_combo_with_value(self.dock_weakness_combo, node.default_dock_weakness)
        self.dock_incompatible_model.items = list(node.incompatible_dock_weaknesses)
        self.dock_exclude_lock_rando_check.setChecked(node.exclude_from_dock_rando)

        # UI custom name
        self.ui_name_edit.setText(node.ui_custom_name)

    def fill_for_pickup(self, node: PickupNode) -> None:
        self.pickup_index_spin.setValue(node.pickup_index.index)
        signal_handling.set_combo_with_value(self.location_category_combo, node.location_category)

    def fill_for_event(self, node: EventNode) -> None:
        signal_handling.set_combo_with_value(self.event_resource_combo, node.event)

    def fill_for_configurable(self, node: ConfigurableNode) -> None:
        pass

    def fill_for_hint(self, node: HintNode) -> None:
        signal_handling.set_combo_with_value(self.hint_kind_combo, node.kind)
        self.set_hint_requirement_to_collect(node.lock_requirement)

    def set_hint_requirement_to_collect(self, requirement: Requirement) -> None:
        self._hint_requirement_to_collect = requirement
        self._create_connections_visualizer(
            self.hint_requirement_to_collect_group,
            self.hint_requirement_to_collect_layout,
            requirement,
        )

    def fill_for_teleporter_network(self, node: TeleporterNetworkNode) -> None:
        self.set_teleporter_network_unlocked_by(node.is_unlocked)
        self.set_teleporter_network_activated_by(node.requirement_to_activate)
        self.teleporter_network_edit.setText(node.network)

    def set_teleporter_network_unlocked_by(self, requirement: Requirement) -> None:
        self._unlocked_by_requirement = requirement
        self._create_connections_visualizer(
            self.teleporter_network_unlocked_group,
            self.teleporter_network_unlocked_layout,
            requirement,
        )

    def set_teleporter_network_activated_by(self, requirement: Requirement) -> None:
        self._activated_by_requirement = requirement
        self._create_connections_visualizer(
            self.teleporter_network_activate_group,
            self.teleporter_network_activate_layout,
            requirement,
        )

    # Connections Visualizer
    def _create_connections_visualizer(
        self, parent: QtWidgets.QWidget, layout: QtWidgets.QGridLayout, requirement: Requirement
    ) -> None:
        if parent in self._connections_visualizers:
            self._connections_visualizers.pop(parent).deleteLater()

        self._connections_visualizers[parent] = ConnectionsVisualizer(
            parent, layout, requirement, self.game.resource_database
        )

    # Signals
    def on_name_edit(self, value: str) -> None:
        has_error = False

        try:
            new_node = self.create_new_node()
        except ValueError:
            new_node = None

        if isinstance(new_node, DockNode):
            area = self.game.region_list.nodes_to_area(self.node)
            has_error = not integrity_check.dock_has_correct_name(area, new_node)

        common_qt_lib.set_error_border_stylesheet(self.name_edit, has_error)

    def on_node_type_combo(self, _: None) -> None:
        self.tab_widget.setCurrentWidget(self._type_to_tab[self.node_type_combo.currentData()])

    def on_dock_connection_region_combo(self, _: None) -> None:
        region: Region = self.dock_connection_region_combo.currentData()

        self.dock_connection_area_combo.clear()
        for area in sorted(region.areas, key=lambda x: x.name):
            self.dock_connection_area_combo.addItem(area.name, userData=area)

    def on_dock_connection_area_combo(self, _: None) -> None:
        area: Area | None = self.dock_connection_area_combo.currentData()

        self.dock_connection_node_combo.clear()
        empty = True
        if area is not None:
            for node in area.nodes:
                self.dock_connection_node_combo.addItem(node.name, userData=node)
                empty = False
        if empty:
            self.dock_connection_node_combo.addItem("Other", None)

    def on_dock_type_combo(self, _) -> None:
        self.dock_weakness_combo.clear()
        current_type: DockType = self.dock_type_combo.currentData()

        self.dock_incompatible_model.change_type(current_type)
        self.dock_incompatible_list.reset()

        for weakness in self.game.dock_weakness_database.get_by_type(current_type):
            self.dock_weakness_combo.addItem(weakness.name, weakness)

    def on_dock_update_name_button(self) -> None:
        new_node = self.create_new_node()
        assert isinstance(new_node, DockNode)
        expected_name = next(integrity_check.expected_dock_names(new_node))
        self.name_edit.setText(expected_name)
        self.on_name_edit(self.name_edit.text())

    def on_dock_incompatible_delete_selected(self) -> None:
        indices = [selection.row() for selection in self.dock_incompatible_list.selectedIndexes()]
        if indices:
            assert len(indices) == 1
            self.dock_incompatible_model.removeRow(indices[0])

    # Pickup

    def on_pickup_index_button(self) -> None:
        used_indices: dict[int, int] = collections.defaultdict(lambda: 0)
        for node in self.game.region_list.iterate_nodes():
            if isinstance(node, PickupNode):
                used_indices[node.pickup_index.index] += 1

        if isinstance(self.node, PickupNode):
            used_indices[self.node.pickup_index.index] -= 1

        for new_index in itertools.count(0):
            if used_indices[new_index] == 0:
                self.pickup_index_spin.setValue(new_index)
                return

    def on_teleporter_destination_region_combo(self, _) -> None:
        region: Region = self.teleporter_destination_region_combo.currentData()

        self.teleporter_destination_area_combo.clear()
        for area in sorted(region.areas, key=lambda x: x.name):
            self.teleporter_destination_area_combo.addItem(area.name, userData=area)

    @asyncSlot()
    async def on_hint_requirement_to_collect_button(self) -> None:
        requirement = await self._open_connections_editor(self._hint_requirement_to_collect)
        if requirement is not None:
            self.set_hint_requirement_to_collect(requirement)

    @asyncSlot()
    async def on_teleporter_network_unlocked_button(self) -> None:
        requirement = await self._open_connections_editor(self._unlocked_by_requirement)
        if requirement is not None:
            self.set_teleporter_network_unlocked_by(requirement)

    @asyncSlot()
    async def on_teleporter_network_activated_button(self) -> None:
        requirement = await self._open_connections_editor(self._activated_by_requirement)
        if requirement is not None:
            self.set_teleporter_network_activated_by(requirement)

    async def _open_connections_editor(self, requirement: Requirement) -> Requirement | None:
        self._edit_popup = ConnectionsEditor(self, self.game.resource_database, self.game.region_list, requirement)
        self._edit_popup.setModal(True)
        try:
            result = await async_dialog.execute_dialog(self._edit_popup)
            if result == QtWidgets.QDialog.DialogCode.Accepted:
                return self._edit_popup.final_requirement
            else:
                return None
        finally:
            self._edit_popup = None

    # Final
    def create_new_node(self) -> Node:
        node_type = self.node_type_combo.currentData()
        identifier = self.node.identifier.renamed(self.name_edit.text())
        node_index = self.node.node_index
        heal = self.heals_check.isChecked()
        valid_starting_location = self.node.valid_starting_location
        location = None
        if self.location_group.isChecked():
            location = NodeLocation(
                self.location_x_spin.value(), self.location_y_spin.value(), self.location_z_spin.value()
            )
        description = self.description_edit.toMarkdown().strip()
        extra = json.loads(self.extra_edit.toPlainText())
        layers = (self.layers_combo.currentText(),)

        if node_type == GenericNode:
            return GenericNode(
                identifier,
                node_index,
                heal,
                location,
                description,
                layers,
                extra,
                valid_starting_location,
            )

        elif node_type == DockNode:
            connection_node: Node = self.dock_connection_node_combo.currentData()

            return DockNode(
                identifier,
                node_index,
                heal,
                location,
                description,
                layers,
                extra,
                valid_starting_location,
                self.dock_type_combo.currentData(),
                connection_node.identifier,
                self.dock_weakness_combo.currentData(),
                None,
                None,
                self.dock_exclude_lock_rando_check.isChecked(),
                tuple(self.dock_incompatible_model.items),
                None if len(self.ui_name_edit.text()) == 0 else self.ui_name_edit.text(),
            )

        elif node_type == PickupNode:
            return PickupNode(
                identifier,
                node_index,
                heal,
                location,
                description,
                layers,
                extra,
                valid_starting_location,
                PickupIndex(self.pickup_index_spin.value()),
                location_category=self.location_category_combo.currentData(),
            )

        elif node_type == EventNode:
            event = self.event_resource_combo.currentData()
            if event is None:
                raise ValueError("There are no events in the database, unable to create EventNode.")
            return EventNode(
                identifier,
                node_index,
                heal,
                location,
                description,
                layers,
                extra,
                valid_starting_location,
                event,
            )

        elif node_type == ConfigurableNode:
            return ConfigurableNode(
                identifier,
                node_index,
                heal,
                location,
                description,
                layers,
                extra,
                valid_starting_location,
            )

        elif node_type == HintNode:
            return HintNode(
                identifier,
                node_index,
                heal,
                location,
                description,
                layers,
                extra,
                valid_starting_location,
                self.hint_kind_combo.currentData(),
                self._hint_requirement_to_collect,
            )

        elif node_type == TeleporterNetworkNode:
            return TeleporterNetworkNode(
                identifier,
                node_index,
                heal,
                location,
                description,
                layers,
                extra,
                valid_starting_location,
                self._unlocked_by_requirement,
                self.teleporter_network_edit.text(),
                self._activated_by_requirement,
            )

        else:
            raise RuntimeError(f"Unknown node type: {node_type}")

    def try_accept(self) -> None:
        try:
            self.create_new_node()
            self.accept()
        except Exception as e:
            logging.exception(f"Unable to save node: {e}")

            box = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Warning,
                "Invalid configuration",
                f"Unable to save node: {e}",
                QtWidgets.QMessageBox.StandardButton.Ok,
                None,
            )
            box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Ok)
            box.setDetailedText("".join(traceback.format_tb(e.__traceback__)))
            common_qt_lib.set_default_window_icon(box)
            box.exec_()
