from __future__ import annotations

import dataclasses
import logging
from enum import Enum
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

from randovania import get_data_path
from randovania.game_description import default_database
from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.game_description.resources.inventory import Inventory
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.games.game import RandovaniaGame
from randovania.gui.lib.pixmap_lib import paint_with_opacity
from randovania.gui.lib.tracker_item_image import TrackerItemImage

if TYPE_CHECKING:
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo


class FieldToCheck(Enum):
    AMOUNT = "amount"
    CAPACITY = "capacity"
    MAX_CAPACITY = "max_capacity"


@dataclasses.dataclass(frozen=True)
class Element:
    labels: list[QtWidgets.QLabel | TrackerItemImage]
    resources: list[ItemResourceInfo]
    text_template: str
    minimum_to_check: int
    maximum_to_check: int
    field_to_check: FieldToCheck
    disabled_image: TrackerItemImage | None

    def __post_init__(self):
        if len(self.labels) > 1 and len(self.labels) != len(self.resources):
            raise ValueError(
                f"Label has {len(self.labels)} progressive icons, "
                f"but has {len(self.resources)} resources ({str([r.long_name for r in self.resources])})."
            )


class ItemTrackerWidget(QtWidgets.QGroupBox):
    give_item_signal = QtCore.Signal(PickupEntry)
    current_state: Inventory

    def __init__(self, tracker_config: dict):
        super().__init__()
        self._layout = QtWidgets.QGridLayout(self)
        self.tracker_config = tracker_config
        self.current_state = Inventory.empty()

        self.tracker_elements: list[Element] = []
        game_enum = RandovaniaGame(tracker_config["game"])
        resource_database = default_database.resource_database_for(game_enum)
        self.resource_database = resource_database

        for element in tracker_config["elements"]:
            text_template = ""
            col_span = element.get("col_span", 1)
            row_span = element.get("row_span", 1)
            minimum_to_check = element.get("minimum_to_check", 1)
            maximum_to_check = element.get("maximum_to_check", -1)
            field_to_check = FieldToCheck(element.get("field_to_check", FieldToCheck.CAPACITY.value))

            labels = []
            disabled_image = None
            if "image_path" in element:
                paths = element["image_path"]
                if not isinstance(paths, list):
                    paths = [paths]

                visible = True

                def get_label(path: str, invert_opacity: bool = False):
                    nonlocal visible
                    image_path = get_data_path().joinpath(path)
                    if not image_path.exists():
                        logging.error("Tracker asset not found: %s", image_path)
                    pixmap = QtGui.QPixmap(str(image_path))

                    not_checked_img = paint_with_opacity(pixmap, 0.3)
                    checked_img = paint_with_opacity(pixmap, 1.0)
                    if invert_opacity:
                        not_checked_img, checked_img = checked_img, not_checked_img

                    label = TrackerItemImage(self, not_checked_img, checked_img)
                    label.set_checked(False)
                    label.set_ignore_mouse_events(True)
                    label.setVisible(visible)
                    visible = False
                    return label

                for p in paths:
                    labels.append(get_label(p))

                if "disabled_image_path" in element:
                    disabled_image = get_label(element["disabled_image_path"])
                else:
                    disabled_image = get_label(paths[0], True)

            elif "label" in element:
                label = QtWidgets.QLabel(self)
                label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                if "style" in element:
                    label.setStyleSheet(element["style"])
                text_template = element["label"]
                labels.append(label)

            elif "progress_bar" in element:
                label = QtWidgets.QProgressBar(self)
                labels.append(label)

            else:
                raise ValueError(f"Invalid element: {element}")

            resources = [
                find_resource_info_with_long_name(resource_database.item, resource_name)
                for resource_name in element["resources"]
            ]
            for resource, label in zip(resources, labels):
                label.setToolTip(resource.long_name)

            self.tracker_elements.append(
                Element(
                    list(labels),
                    resources,
                    text_template,
                    minimum_to_check,
                    maximum_to_check,
                    field_to_check,
                    disabled_image,
                )
            )
            if disabled_image is not None:
                # this is lazy for progressives, but would require editing all json & adding a field I think
                if resources:
                    disabled_image.setToolTip(resources[0].long_name)
                labels.append(disabled_image)

            for label in labels:
                self._layout.addWidget(
                    label, element["row"], element["column"], row_span, col_span, QtCore.Qt.AlignmentFlag.AlignCenter
                )

        self.inventory_spacer = QtWidgets.QSpacerItem(
            5, 5, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )
        self._layout.addItem(self.inventory_spacer, self._layout.rowCount(), self._layout.columnCount())

    def update_state(self, inventory: Inventory):
        self.current_state = inventory

        for element in self.tracker_elements:
            if len(element.labels) > 1:
                satisfied = False
                for i, resource in reversed(list(enumerate(element.resources))):
                    current = inventory.get(resource)
                    fields = {
                        "amount": current.amount,
                        "capacity": current.capacity,
                        "max_capacity": resource.max_capacity,
                    }

                    if satisfied:
                        element.labels[i].setVisible(False)

                    elif fields[element.field_to_check.value] >= element.minimum_to_check:
                        # This tier is satisfied
                        satisfied = True
                        element.labels[i].setVisible(True)
                        element.labels[i].set_checked(True)
                    else:
                        element.labels[i].setVisible(False)

                element.disabled_image.setVisible(not satisfied)
                element.disabled_image.set_checked(satisfied)

            else:
                label = element.labels[0]

                amount = 0
                capacity = 0
                max_capacity = 0
                for resource in element.resources:
                    current = inventory.get(resource)
                    amount += current.amount
                    capacity += current.capacity
                    max_capacity += resource.max_capacity

                if isinstance(label, TrackerItemImage):
                    fields = {"amount": amount, "capacity": capacity, "max_capacity": max_capacity}
                    value = fields[element.field_to_check.value]
                    satisfied = max_capacity == 0 or (
                        value >= element.minimum_to_check
                        and (element.maximum_to_check == -1 or value <= element.maximum_to_check)
                    )
                    label.set_checked(satisfied)
                    label.setVisible(satisfied)
                    element.disabled_image.set_checked(not satisfied)
                    element.disabled_image.setVisible(not satisfied)

                elif isinstance(label, QtWidgets.QProgressBar):
                    label.setMaximum(max(capacity, 1))
                    label.setValue(amount)

                else:
                    label.setText(
                        element.text_template.format(
                            amount=amount,
                            capacity=capacity,
                            max_capacity=max_capacity,
                        )
                    )
