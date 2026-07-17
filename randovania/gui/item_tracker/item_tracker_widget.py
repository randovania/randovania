from __future__ import annotations

import dataclasses
import logging
import typing
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

from randovania import get_data_path
from randovania.game_description import default_database
from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.game_description.resources.inventory import Inventory
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.gui.item_tracker.tracker_layout import (
    FieldToCheck,
    ImageTrackerElement,
    LabelTrackerElement,
    ProgressBarTrackerElement,
    TrackerLayout,
)
from randovania.gui.lib.pixmap_lib import paint_with_opacity
from randovania.gui.widgets.tracker_item_image import TrackerItemImage

if TYPE_CHECKING:
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo


type ElementWidget = QtWidgets.QLabel | TrackerItemImage | QtWidgets.QProgressBar


@dataclasses.dataclass(frozen=True)
class Element:
    widgets: list[ElementWidget]
    resources: list[ItemResourceInfo]
    text_template: str
    minimum_to_check: int
    maximum_to_check: int
    field_to_check: FieldToCheck
    disabled_image: TrackerItemImage | None

    def __post_init__(self) -> None:
        if len(self.widgets) > 1 and len(self.widgets) != len(self.resources):
            raise ValueError(
                f"Label has {len(self.widgets)} progressive icons, "
                f"but has {len(self.resources)} resources ({[r.long_name for r in self.resources]!s})."
            )


class ItemTrackerWidget(QtWidgets.QGroupBox):
    give_item_signal = QtCore.Signal(PickupEntry)
    current_state: Inventory

    def __init__(self, tracker_config: TrackerLayout) -> None:
        super().__init__()
        self._layout = QtWidgets.QGridLayout(self)
        self.tracker_config = tracker_config
        self.current_state = Inventory.empty()

        self.tracker_elements: list[Element] = []
        game_enum = tracker_config.game
        resource_database = default_database.resource_database_for(game_enum)
        self.resource_database = resource_database

        for element in tracker_config.elements:
            text_template = ""

            widgets: list[ElementWidget] = []
            disabled_image = None
            if isinstance(element, ImageTrackerElement):
                visible = True

                def get_image(path: str, invert_opacity: bool = False) -> TrackerItemImage:
                    nonlocal visible
                    image_path = get_data_path().joinpath(path)
                    if not image_path.exists():
                        logging.error("Tracker asset not found: %s", image_path)
                    pixmap = QtGui.QPixmap(str(image_path))

                    not_checked_img = paint_with_opacity(pixmap, 0.3)
                    checked_img = paint_with_opacity(pixmap, 1.0)
                    if invert_opacity:
                        not_checked_img, checked_img = checked_img, not_checked_img

                    image = TrackerItemImage(self, not_checked_img, checked_img)
                    image.set_checked(False)
                    image.set_ignore_mouse_events(True)
                    image.setVisible(visible)
                    visible = False
                    return image

                for p in element.image_paths:
                    widgets.append(get_image(p))

                if element.disabled_image_path is not None:
                    disabled_image = get_image(element.disabled_image_path)
                else:
                    disabled_image = get_image(element.image_paths[0], True)

            elif isinstance(element, LabelTrackerElement):
                label = QtWidgets.QLabel(self)
                label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                if element.style is not None:
                    label.setStyleSheet(element.style)
                text_template = element.label
                widgets.append(label)

            elif isinstance(element, ProgressBarTrackerElement):
                pbar = QtWidgets.QProgressBar(self)
                widgets.append(pbar)

            else:
                typing.assert_never(element)

            resources = [
                find_resource_info_with_long_name(resource_database.item, resource_name)
                for resource_name in element.resources
            ]
            for resource, widget in zip(resources, widgets):
                widget.setToolTip(resource.long_name)

            self.tracker_elements.append(
                Element(
                    list(widgets),
                    resources,
                    text_template,
                    element.minimum_to_check,
                    element.maximum_to_check,
                    element.field_to_check,
                    disabled_image,
                )
            )
            if disabled_image is not None:
                # this is lazy for progressives, but would require editing all json & adding a field I think
                if resources:
                    disabled_image.setToolTip(resources[0].long_name)
                widgets.append(disabled_image)

            for widget in widgets:
                self._layout.addWidget(
                    widget,
                    element.row,
                    element.column,
                    element.row_span,
                    element.col_span,
                    QtCore.Qt.AlignmentFlag.AlignCenter,
                )

        self.inventory_spacer = QtWidgets.QSpacerItem(
            5, 5, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )
        self._layout.addItem(self.inventory_spacer, self._layout.rowCount(), self._layout.columnCount())

    def update_state(self, inventory: Inventory) -> None:
        self.current_state = inventory

        for element in self.tracker_elements:
            if len(element.widgets) > 1:
                satisfied = False
                for widget, resource in reversed(list(zip(element.widgets, element.resources, strict=True))):
                    assert isinstance(widget, TrackerItemImage)

                    current = inventory.get(resource)
                    fields = {
                        "amount": current.amount,
                        "capacity": current.capacity,
                        "max_capacity": resource.max_capacity,
                    }

                    if satisfied:
                        widget.setVisible(False)

                    elif fields[element.field_to_check.value] >= element.minimum_to_check:
                        # This tier is satisfied
                        satisfied = True
                        widget.setVisible(True)
                        widget.set_checked(True)
                    else:
                        widget.setVisible(False)

                assert isinstance(element.disabled_image, TrackerItemImage)

                element.disabled_image.setVisible(not satisfied)
                element.disabled_image.set_checked(satisfied)

            else:
                label = element.widgets[0]

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

                    assert isinstance(element.disabled_image, TrackerItemImage)

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
