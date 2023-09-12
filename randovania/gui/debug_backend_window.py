from __future__ import annotations

import random
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QMainWindow
from qasync import asyncSlot

from randovania.game_connection.connector.remote_connector import PlayerLocationEvent
from randovania.game_description import default_database
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.gui.generated.debug_connector_window_ui import Ui_DebugConnectorWindow
from randovania.gui.lib import common_qt_lib, signal_handling

if TYPE_CHECKING:
    from randovania.game_connection.connector.debug_remote_connector import DebugRemoteConnector
    from randovania.game_description.resources.resource_info import ResourceInfo


class RangeSpinBoxItemEditorCreator(QtWidgets.QItemEditorCreatorBase):
    def __init__(self, minimum: int, maximum: int):
        super().__init__()
        self.minimum = minimum
        self.maximum = maximum

    def createWidget(self, parent):
        spin = QtWidgets.QSpinBox(parent)
        spin.setMinimum(self.minimum)
        spin.setMaximum(self.maximum)
        return spin

    def valuePropertyName(self):
        return "value"


def _create_delegate_for(item: ItemResourceInfo):
    factory = QtWidgets.QItemEditorFactory()
    factory.registerEditor(QtCore.QMetaType.Int.value, RangeSpinBoxItemEditorCreator(0, item.max_capacity))

    delegate = QtWidgets.QStyledItemDelegate()
    delegate.setItemEditorFactory(factory)
    return delegate


class DebugConnectorWindow(Ui_DebugConnectorWindow):
    _connected: bool = False
    _timer: QtCore.QTimer
    _resource_to_item: dict[ResourceInfo, QtGui.QStandardItem]

    def __init__(self, connector: DebugRemoteConnector):
        super().__init__()
        self.window = QMainWindow()
        self.setupUi(self.window)
        common_qt_lib.set_default_window_icon(self.window)

        self.connector = connector
        connector.InventoryUpdated.connect(self.update_inventory_table)
        connector.MessagesUpdated.connect(self.update_message_list)

        self.messages_item_model = QtGui.QStandardItemModel(0, 1, self.window)
        self.messages_list.setModel(self.messages_item_model)
        self.inventory_item_model = QtGui.QStandardItemModel(0, 2, self.window)
        self.inventory_item_model.setHorizontalHeaderLabels(["Name", "Amount"])
        self.inventory_table_view.setModel(self.inventory_item_model)

        db = default_database.resource_database_for(connector.game_enum)
        self._resource_to_item = {}
        self._item_delegates = {}
        self.inventory_item_model.setRowCount(len(db.item))
        for item in db.item:
            name_item = QtGui.QStandardItem(item.long_name)
            name_item.setEditable(False)
            self.inventory_item_model.setItem(item.resource_index, 0, name_item)
            self._resource_to_item[item] = QtGui.QStandardItem()
            self._resource_to_item[item].setData(item, QtCore.Qt.ItemDataRole.UserRole)
            self.inventory_item_model.setItem(item.resource_index, 1, self._resource_to_item[item])
            if item.max_capacity > 1:
                self._item_delegates[item] = _create_delegate_for(item)
                self.inventory_table_view.setItemDelegateForRow(item.resource_index, self._item_delegates[item])

            self._update_item_amount(item, 0)

        self.inventory_item_model.itemChanged.connect(self._on_item_changed)
        self.reset_button.clicked.connect(self.finish)

        self.collect_location_combo.setVisible(False)
        self.collect_location_button.clicked.connect(self._emit_collection)
        self.collect_location_button.setEnabled(False)
        self.collect_randomly_check.stateChanged.connect(self._on_collect_randomly_toggle)
        signal_handling.on_combo(self.current_region_combo, self._on_current_region_changed)

        self._timer = QtCore.QTimer(self.window)
        self._timer.timeout.connect(self._collect_randomly)
        self._timer.setInterval(10000)

        self._setup_locations_combo()
        self.update_inventory_table()
        self.update_message_list()

    def _on_collect_randomly_toggle(self, value: int):
        if bool(value):
            self._timer.start()
        else:
            self._timer.stop()

    def _on_current_region_changed(self, _):
        self.connector.PlayerLocationChanged.emit(
            PlayerLocationEvent(
                self.current_region_combo.currentData(),
                None,
            )
        )

    def _collect_randomly(self):
        row = random.randint(0, self.collect_location_combo.count())
        self._collect_location(self.collect_location_combo.itemData(row))

    def show(self):
        self.window.show()

    def _emit_collection(self):
        self._collect_location(self.collect_location_combo.currentData())

    def _collect_location(self, location: int):
        self.connector.PickupIndexCollected.emit(PickupIndex(location))

    def _setup_locations_combo(self):
        game = default_database.game_description_for(self.connector.game_enum)
        index_to_name = {
            node.pickup_index.index: game.region_list.area_name(area)
            for region, area, node in game.region_list.all_regions_areas_nodes
            if isinstance(node, PickupNode)
        }

        names = index_to_name

        self.collect_location_combo.clear()
        for index, name in sorted(names.items(), key=lambda t: t[1]):
            self.collect_location_combo.addItem(name, index)

        self.current_region_combo.addItem("Title Screen", None)
        for region in game.region_list.regions:
            self.current_region_combo.addItem(region.name, region)

        self.collect_location_button.setEnabled(True)
        self.collect_location_combo.setVisible(True)

    @asyncSlot()
    async def finish(self):
        await self.connector.force_finish()
        self.window.close()

    def update_message_list(self):
        self.messages_item_model.setRowCount(len(self.connector.messages))
        for i, message in enumerate(self.connector.messages):
            self.messages_item_model.setItem(i, QtGui.QStandardItem(message))

    def update_inventory_table(self):
        for resource, quantity in self.connector.item_collection.as_resource_gain():
            if resource in self._resource_to_item:
                self._update_item_amount(resource, quantity)

    def _update_item_amount(self, item: ItemResourceInfo, amount: int):
        if item.max_capacity > 1:
            self._resource_to_item[item].setData(amount, QtCore.Qt.ItemDataRole.DisplayRole)
        else:
            self._resource_to_item[item].setData(amount > 0, QtCore.Qt.ItemDataRole.DisplayRole)

    def _on_item_changed(self, widget: QtGui.QStandardItem):
        item = widget.data(QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(item, ItemResourceInfo):
            return

        value: int | bool = widget.data(QtCore.Qt.ItemDataRole.DisplayRole)
        value = int(value)

        self.connector.item_collection.set_resource(item, value)
        self.connector.emit_inventory()
