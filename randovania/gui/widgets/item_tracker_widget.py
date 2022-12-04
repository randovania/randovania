import dataclasses
import logging
from enum import Enum

from PySide6 import QtWidgets, QtGui, QtCore

from randovania import get_data_path
from randovania.game_connection.connection_base import InventoryItem
from randovania.game_description import default_database
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.games.game import RandovaniaGame
from randovania.gui.lib.pixmap_lib import paint_with_opacity
from randovania.gui.lib.tracker_item_image import TrackerItemImage


class FieldToCheck(Enum):
    AMOUNT = "amount"
    CAPACITY = "capacity"
    MAX_CAPACITY = "max_capacity"


@dataclasses.dataclass(frozen=True)
class Element:
    labels: list[QtWidgets.QLabel | TrackerItemImage | TrackerItemImage]
    resources: list[ItemResourceInfo]
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


class ItemTrackerWidget(QtWidgets.QGroupBox):
    give_item_signal = QtCore.Signal(PickupEntry)
    current_state: dict[ItemResourceInfo, InventoryItem]

    def __init__(self, tracker_config: dict):
        super().__init__()
        self._layout = QtWidgets.QGridLayout(self)
        self.tracker_config = tracker_config

        self.tracker_elements: list[Element] = []
        game_enum = RandovaniaGame(tracker_config["game"])
        resource_database = default_database.resource_database_for(game_enum)
        self.resource_database = resource_database

        for element in tracker_config["elements"]:
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
                    pixmap = QtGui.QPixmap(str(image_path))

                    label = TrackerItemImage(self, paint_with_opacity(pixmap, 0.3),
                                             paint_with_opacity(pixmap, 1.0))
                    label.set_checked(False)
                    label.set_ignore_mouse_events(True)
                    label.setVisible(visible)
                    visible = False
                    labels.append(label)

            elif "label" in element:
                label = QtWidgets.QLabel(self)
                label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                text_template = element["label"]
                labels.append(label)

            else:
                raise ValueError(f"Invalid element: {element}")

            resources = [
                find_resource_info_with_long_name(resource_database.item, resource_name)
                for resource_name in element["resources"]
            ]
            for resource, label in zip(resources, labels):
                label.setToolTip(resource.long_name)

            self.tracker_elements.append(Element(labels, resources, text_template, minimum_to_check, field_to_check))
            for label in labels:
                self._layout.addWidget(label, element["row"], element["column"])

        self.inventory_spacer = QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Policy.Expanding,
                                                      QtWidgets.QSizePolicy.Policy.Expanding)
        self._layout.addItem(self.inventory_spacer, self._layout.rowCount(), self._layout.columnCount())

    def update_state(self, inventory: dict[ItemResourceInfo, InventoryItem]):
        self.current_state = inventory
        for element in self.tracker_elements:
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

                if isinstance(label, TrackerItemImage):
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
