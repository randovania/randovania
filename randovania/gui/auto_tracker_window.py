import dataclasses
import json
import logging
from enum import Enum
from typing import Dict, List, Union, Optional

import PySide2
from PySide2 import QtWidgets
from PySide2.QtCore import QTimer, Signal, Qt
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QMainWindow, QLabel, QSpacerItem, QSizePolicy, QActionGroup
from qasync import asyncSlot

from randovania import get_data_path
from randovania.game_connection.connection_base import GameConnectionStatus, InventoryItem
from randovania.game_connection.game_connection import GameConnection
from randovania.game_description import default_database
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.games.game import RandovaniaGame
from randovania.gui.generated.auto_tracker_window_ui import Ui_AutoTrackerWindow
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.clickable_label import ClickableLabel
from randovania.gui.lib.game_connection_setup import GameConnectionSetup
from randovania.gui.lib.pixmap_lib import paint_with_opacity
from randovania.interface_common.options import Options


def path_for(name: str):
    return get_data_path().joinpath(f"gui_assets/tracker", name)


class FieldToCheck(Enum):
    AMOUNT = "amount"
    CAPACITY = "capacity"
    MAX_CAPACITY = "max_capacity"


@dataclasses.dataclass(frozen=True)
class Element:
    labels: List[Union[QLabel, ClickableLabel, ClickableLabel]]
    resources: List[ItemResourceInfo]
    text_template: str
    minimum_to_check: int
    field_to_check: FieldToCheck

    def __post_init__(self):
        if len(self.labels) > 1 and len(self.labels) != len(self.resources):
            raise ValueError("Label has {} progressive icons, but has {} resources ({}).".format(
                len(self.labels),
                len(self.resources),
                str([r.long_name for r in self.resources])
            ))


class AutoTrackerWindow(QMainWindow, Ui_AutoTrackerWindow):
    _hooked = False
    _base_address: int
    trackers: Dict[str, str]
    _current_tracker_game: RandovaniaGame = None
    _current_tracker_name: str = None
    give_item_signal = Signal(PickupEntry)

    def __init__(self, game_connection: GameConnection, options: Options):
        super().__init__()
        self.setupUi(self)
        self.game_connection = game_connection
        self.options = options
        common_qt_lib.set_default_window_icon(self)

        with get_data_path().joinpath(f"gui_assets/tracker/trackers.json").open("r") as trackers_file:
            self.trackers = json.load(trackers_file)["trackers"]

        self._action_to_name = {}
        theme_group = QActionGroup(self)
        for name in self.trackers.keys():
            action = QtWidgets.QAction(self.menu_tracker)
            action.setText(name)
            action.setCheckable(True)
            action.setChecked(name == options.selected_tracker)
            action.triggered.connect(self._on_action_select_tracker)
            self.menu_tracker.addAction(action)
            self._action_to_name[action] = name
            theme_group.addAction(action)

        self._tracker_elements: List[Element] = []
        self.create_tracker()

        self.game_connection_setup = GameConnectionSetup(self, self.connection_status_label,
                                                         self.game_connection, options)
        self.game_connection_setup.create_backend_entries(self.menu_backend)
        self.game_connection_setup.create_upload_nintendont_action(self.menu_options)
        self.game_connection_setup.refresh_backend()

        self.action_force_update.triggered.connect(self.on_force_update_button)

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

    @property
    def selected_tracker(self) -> Optional[str]:
        for action, name in self._action_to_name.items():
            if action.isChecked():
                return name

    def _update_tracker_from_hook(self, inventory: Dict[ItemResourceInfo, InventoryItem]):
        for element in self._tracker_elements:
            if len(element.labels) > 1:
                satisfied = False
                for i, resource in reversed(list(enumerate(element.resources))):
                    current = inventory.get(resource, InventoryItem(0, 0))
                    fields = {"amount": current.amount, "capacity": current.capacity,
                              "max_capacity": resource.max_capacity}

                    if satisfied:
                        element.labels[i].setVisible(False)

                    elif fields[element.field_to_check.value] >= element.minimum_to_check:
                        # This tier is satisfied
                        satisfied = True
                        element.labels[i].setVisible(True)
                        element.labels[i].set_checked(True)
                    else:
                        element.labels[i].setVisible(False)

                if not satisfied:
                    element.labels[0].setVisible(True)
                    element.labels[0].set_checked(False)

            else:
                label = element.labels[0]

                amount = 0
                capacity = 0
                max_capacity = 0
                for resource in element.resources:
                    current = inventory.get(resource, InventoryItem(0, 0))
                    amount += current.amount
                    capacity += current.capacity
                    max_capacity += resource.max_capacity

                if isinstance(label, ClickableLabel):
                    fields = {"amount": amount, "capacity": capacity, "max_capacity": max_capacity}
                    value_target = element.minimum_to_check
                    value = fields[element.field_to_check.value]
                    label.set_checked(max_capacity == 0 or value >= value_target)
                else:
                    label.setText(element.text_template.format(
                        amount=amount,
                        capacity=capacity,
                        max_capacity=max_capacity,
                    ))

    def _on_action_select_tracker(self):
        with self.options as options:
            options.selected_tracker = self.selected_tracker
        self.create_tracker()

    @asyncSlot()
    async def _on_timer_update(self):
        try:
            current_status = self.game_connection.current_status
            if current_status not in {GameConnectionStatus.Disconnected, GameConnectionStatus.UnknownGame,
                                      GameConnectionStatus.WrongGame}:
                self.action_force_update.setEnabled(True)
            else:
                self.action_force_update.setEnabled(False)

            if current_status == GameConnectionStatus.InGame or current_status == GameConnectionStatus.TrackerOnly:
                if self.game_connection.connector.game_enum == self._current_tracker_game:
                    inventory = self.game_connection.get_current_inventory()
                    self._update_tracker_from_hook(inventory)
                    self.game_connection_setup.on_game_connection_updated()
                else:
                    self.connection_status_label.setText("{}: Wrong Game ({})".format(
                        self.game_connection.backend_choice.pretty_text,
                        self.game_connection.current_game_name,
                    ))
        finally:
            self._update_timer.start()

    def delete_tracker(self):
        for element in self._tracker_elements:
            for l in element.labels:
                l.deleteLater()

        self._tracker_elements.clear()

    def create_tracker(self):
        tracker_name = self.selected_tracker
        if tracker_name == self._current_tracker_name or tracker_name is None:
            return

        self.delete_tracker()

        with path_for(self.trackers[tracker_name]).open("r") as tracker_details_file:
            tracker_details = json.load(tracker_details_file)

        game_enum = RandovaniaGame(tracker_details["game"])
        resource_database = default_database.resource_database_for(game_enum)

        for element in tracker_details["elements"]:
            text_template = ""
            minimum_to_check = element.get("minimum_to_check", 1)
            field_to_check = FieldToCheck(element.get("field_to_check", FieldToCheck.CAPACITY.value))

            labels = []
            if "image_path" in element:
                paths = element["image_path"]
                if not isinstance(paths, list):
                    paths = [paths]

                visible = True
                for path in paths:
                    image_path = get_data_path().joinpath(path)
                    if not image_path.exists():
                        logging.error("Tracker asset not found: %s", image_path)
                    pixmap = QPixmap(str(image_path))

                    label = ClickableLabel(self.inventory_group, paint_with_opacity(pixmap, 0.3),
                                           paint_with_opacity(pixmap, 1.0))
                    label.set_checked(False)
                    label.set_ignore_mouse_events(True)
                    label.setVisible(visible)
                    visible = False
                    labels.append(label)

            elif "label" in element:
                label = QLabel(self.inventory_group)
                label.setAlignment(Qt.AlignCenter)
                text_template = element["label"]
                labels.append(label)

            else:
                raise ValueError(f"Invalid element: {element}")

            resources = [
                find_resource_info_with_long_name(resource_database.item, resource_name)
                for resource_name in element["resources"]
            ]
            self._tracker_elements.append(Element(labels, resources, text_template, minimum_to_check, field_to_check))
            for l in labels:
                self.inventory_layout.addWidget(l, element["row"], element["column"])

        self.inventory_spacer = QSpacerItem(5, 5, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.inventory_layout.addItem(self.inventory_spacer, self.inventory_layout.rowCount(),
                                      self.inventory_layout.columnCount())

        self._current_tracker_game = game_enum
        self._update_tracker_from_hook({})

        self._current_tracker_name = tracker_name

    @asyncSlot()
    async def on_force_update_button(self):
        await self.game_connection.update_current_inventory()
        inventory = self.game_connection.get_current_inventory()
        logging.info("Inventory:" + "\n".join(
            f"{item.long_name}: {inv_item.amount}/{inv_item.capacity}"
            for item, inv_item in sorted(inventory.items(), key=lambda it: it[0].long_name)
        ))
