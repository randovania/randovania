from __future__ import annotations

import abc
import logging
import typing
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

from randovania import get_data_path
from randovania.game_description import default_database
from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.game_description.resources.inventory import Inventory
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.gui.item_tracker.tracker_structure import (
    ImageTrackerElement,
    LabelTrackerElement,
    ProgressBarTrackerElement,
    TrackerElement,
    TrackerStructure,
)
from randovania.gui.item_tracker.tracker_theme import TrackerTheme
from randovania.gui.lib.pixmap_lib import paint_with_opacity
from randovania.gui.widgets.tracker_item_image import TrackerItemImage

if TYPE_CHECKING:
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo


type ElementWidget = QtWidgets.QLabel | TrackerItemImage | QtWidgets.QProgressBar


def _sum_over_resources(resources: list[ItemResourceInfo], inventory: Inventory) -> tuple[int, int, int]:
    amount = 0
    capacity = 0
    max_capacity = 0
    for resource in resources:
        current = inventory.get(resource)
        amount += current.amount
        capacity += current.capacity
        max_capacity += resource.max_capacity
    return amount, capacity, max_capacity


class TrackerElementView(abc.ABC):
    """
    Owns both the widgets for a single tracker element and how they react to a new
    Inventory. Each element kind (image/label/progress bar, and any added later) gets its
    own subclass, so adding a new kind never requires touching the others or the widget
    that hosts them.
    """

    widgets: list[ElementWidget]

    @abc.abstractmethod
    def update_state(self, inventory: Inventory) -> None:
        raise NotImplementedError


class ImageElementView(TrackerElementView):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        element: ImageTrackerElement,
        theme: TrackerTheme,
        resources: list[ItemResourceInfo],
    ) -> None:
        self.element = element
        self.resources = resources

        image_theme = theme.image_for(element.name)
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

            image = TrackerItemImage(parent, not_checked_img, checked_img)
            image.set_checked(False)
            image.set_ignore_mouse_events(True)
            image.setVisible(visible)
            visible = False
            return image

        images = [get_image(p) for p in image_theme.image_paths]

        if image_theme.disabled_image_path is not None:
            disabled_image = get_image(image_theme.disabled_image_path)
        else:
            disabled_image = get_image(image_theme.image_paths[0], True)

        for resource, widget in zip(resources, images):
            widget.setToolTip(resource.long_name)
        if resources:
            # this is lazy for progressives, but would require editing all json & adding a field I think
            disabled_image.setToolTip(resources[0].long_name)

        self.images = images
        self.disabled_image = disabled_image
        self.widgets = [*images, disabled_image]

    def update_state(self, inventory: Inventory) -> None:
        if len(self.images) > 1:
            satisfied = False
            for widget, resource in reversed(list(zip(self.images, self.resources, strict=True))):
                current = inventory.get(resource)
                fields = {
                    "amount": current.amount,
                    "capacity": current.capacity,
                    "max_capacity": resource.max_capacity,
                }

                if satisfied:
                    widget.setVisible(False)
                elif fields[self.element.field_to_check.value] >= self.element.minimum_to_check:
                    # This tier is satisfied
                    satisfied = True
                    widget.setVisible(True)
                    widget.set_checked(True)
                else:
                    widget.setVisible(False)

            self.disabled_image.setVisible(not satisfied)
            self.disabled_image.set_checked(satisfied)

        else:
            amount, capacity, max_capacity = _sum_over_resources(self.resources, inventory)
            fields = {"amount": amount, "capacity": capacity, "max_capacity": max_capacity}
            value = fields[self.element.field_to_check.value]
            satisfied = max_capacity == 0 or (
                value >= self.element.minimum_to_check
                and (self.element.maximum_to_check == -1 or value <= self.element.maximum_to_check)
            )

            image = self.images[0]
            image.set_checked(satisfied)
            image.setVisible(satisfied)

            self.disabled_image.set_checked(not satisfied)
            self.disabled_image.setVisible(not satisfied)


class LabelElementView(TrackerElementView):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        element: LabelTrackerElement,
        theme: TrackerTheme,
        resources: list[ItemResourceInfo],
    ) -> None:
        label_theme = theme.label_for(element.name)

        label = QtWidgets.QLabel(parent)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        if label_theme.style is not None:
            label.setStyleSheet(label_theme.style)
        if resources:
            label.setToolTip(resources[0].long_name)

        self.label = label
        self.text_template = label_theme.text
        self.resources = resources
        self.widgets = [label]

    def update_state(self, inventory: Inventory) -> None:
        amount, capacity, max_capacity = _sum_over_resources(self.resources, inventory)
        self.label.setText(
            self.text_template.format(
                amount=amount,
                capacity=capacity,
                max_capacity=max_capacity,
            )
        )


class ProgressBarElementView(TrackerElementView):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        resources: list[ItemResourceInfo],
    ) -> None:
        pbar = QtWidgets.QProgressBar(parent)
        if resources:
            pbar.setToolTip(resources[0].long_name)

        self.pbar = pbar
        self.resources = resources
        self.widgets = [pbar]

    def update_state(self, inventory: Inventory) -> None:
        amount, capacity, _max_capacity = _sum_over_resources(self.resources, inventory)
        self.pbar.setMaximum(max(capacity, 1))
        self.pbar.setValue(amount)


def _build_element_view(
    parent: QtWidgets.QWidget,
    element: TrackerElement,
    theme: TrackerTheme,
    resources: list[ItemResourceInfo],
) -> TrackerElementView:
    if isinstance(element, ImageTrackerElement):
        return ImageElementView(parent, element, theme, resources)
    elif isinstance(element, LabelTrackerElement):
        return LabelElementView(parent, element, theme, resources)
    elif isinstance(element, ProgressBarTrackerElement):
        return ProgressBarElementView(parent, resources)
    else:
        typing.assert_never(element)


class ItemTrackerWidget(QtWidgets.QGroupBox):
    give_item_signal = QtCore.Signal(PickupEntry)
    current_state: Inventory

    def __init__(self, structure: TrackerStructure, theme: TrackerTheme) -> None:
        super().__init__()
        self._layout = QtWidgets.QGridLayout(self)
        self.structure = structure
        self.theme = theme
        self.current_state = Inventory.empty()

        self.tracker_elements: list[TrackerElementView] = []
        resource_database = default_database.resource_database_for(structure.game)
        self.resource_database = resource_database

        for element in structure.elements:
            resources = [
                find_resource_info_with_long_name(resource_database.item, resource_name)
                for resource_name in element.resources
            ]

            view = _build_element_view(self, element, theme, resources)
            self.tracker_elements.append(view)

            for widget in view.widgets:
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

        for view in self.tracker_elements:
            view.update_state(inventory)
