import dataclasses
import json
import logging
from typing import Dict, List, Union

import PySide2
from PySide2.QtCore import QTimer, Signal, Qt
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QMainWindow, QLabel
from asyncqt import asyncSlot

from randovania import get_data_path
from randovania.game_connection.connection_base import GameConnectionStatus, InventoryItem
from randovania.game_connection.game_connection import GameConnection
from randovania.game_description import default_database
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_database import find_resource_info_with_long_name
from randovania.games.game import RandovaniaGame
from randovania.gui.generated.auto_tracker_window_ui import Ui_AutoTrackerWindow
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.clickable_label import ClickableLabel
from randovania.gui.lib.game_connection_setup import GameConnectionSetup
from randovania.gui.lib.pixmap_lib import paint_with_opacity
from randovania.interface_common.options import Options


@dataclasses.dataclass(frozen=True)
class Element:
    label: Union[QLabel, ClickableLabel]
    resources: List[ItemResourceInfo]
    text_template: str


class AutoTrackerWindow(QMainWindow, Ui_AutoTrackerWindow):
    _hooked = False
    _base_address: int
    give_item_signal = Signal(PickupEntry)

    def __init__(self, game_connection: GameConnection, options: Options):
        super().__init__()
        self.setupUi(self)
        self.game_connection = game_connection
        common_qt_lib.set_default_window_icon(self)

        self._tracker_elements: List[Element] = []
        self.create_tracker()

        self.game_connection_setup = GameConnectionSetup(self, self.game_connection_tool, self.connection_status_label,
                                                         self.game_connection, options)
        self.force_update_button.clicked.connect(self.on_force_update_button)

        self._update_timer = QTimer(self)
        self._update_timer.setInterval(100)
        self._update_timer.timeout.connect(self._on_timer_update)
        self._update_timer.setSingleShot(True)

    def showEvent(self, event: PySide2.QtGui.QShowEvent):
        self._update_timer.start()
        super().showEvent(event)

    def hideEvent(self, event: PySide2.QtGui.QHideEvent):
        self._update_timer.stop()
        super().hideEvent(event)

    def _update_tracker_from_hook(self, inventory: Dict[ItemResourceInfo, InventoryItem]):
        for element in self._tracker_elements:
            amount = 0
            capacity = 0
            max_capacity = 0
            for resource in element.resources:
                current = inventory.get(resource, InventoryItem(0, 0))
                amount += current.amount
                capacity += current.capacity
                max_capacity += resource.max_capacity

            if isinstance(element.label, ClickableLabel):
                element.label.set_checked(max_capacity == 0 or capacity > 0)
            else:
                element.label.setText(element.text_template.format(
                    amount=amount,
                    capacity=capacity,
                    max_capacity=max_capacity,
                ))

    @asyncSlot()
    async def _on_timer_update(self):
        try:
            current_status = self.game_connection.current_status
            if current_status == GameConnectionStatus.InGame or current_status == GameConnectionStatus.TrackerOnly:
                inventory = self.game_connection.get_current_inventory()
                self._update_tracker_from_hook(inventory)
        finally:
            self._update_timer.start()

    def delete_tracker(self):
        for element in self._tracker_elements:
            element.label.deleteLater()

        self._tracker_elements.clear()

    def create_tracker(self):
        self.delete_tracker()
        game_enum = RandovaniaGame.PRIME2

        resource_database = default_database.resource_database_for(game_enum)
        with get_data_path().joinpath(f"gui_assets/tracker/{game_enum.value}.json").open("r") as tracker_details_file:
            tracker_details = json.load(tracker_details_file)

        for element in tracker_details["elements"]:
            text_template = ""

            if "image_path" in element:
                image_path = get_data_path().joinpath(element["image_path"])
                pixmap = QPixmap(str(image_path))

                label = ClickableLabel(self.inventory_group, paint_with_opacity(pixmap, 0.3),
                                       paint_with_opacity(pixmap, 1.0))
                label.set_checked(False)
                label.set_ignore_mouse_events(True)

            elif "label" in element:
                label = QLabel(self.inventory_group)
                label.setAlignment(Qt.AlignCenter)
                text_template = element["label"]

            else:
                raise ValueError(f"Invalid element: {element}")

            resources = [
                find_resource_info_with_long_name(resource_database.item, resource_name)
                for resource_name in element["resources"]
            ]
            self._tracker_elements.append(Element(label, resources, text_template))
            self.inventory_layout.addWidget(label, element["row"], element["column"])

    @asyncSlot()
    async def on_force_update_button(self):
        await self.game_connection.backend.update_current_inventory()
        inventory = self.game_connection.get_current_inventory()
        print("Inventory:" + "\n".join(
            f"{item.long_name}: {inv_item.amount}/{inv_item.capacity}"
            for item, inv_item in sorted(inventory.items(), key=lambda it: it[0].long_name)
        ))
