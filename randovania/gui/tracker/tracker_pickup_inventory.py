from __future__ import annotations

import collections
import functools
import itertools
import math
from typing import TYPE_CHECKING, Self, override

from PySide6 import QtCore, QtWidgets

from randovania.graph.state import add_pickup_to_state
from randovania.gui.tracker.tracker_component import TrackerComponent
from randovania.gui.widgets.scroll_protected import ScrollProtectedSpinBox

if TYPE_CHECKING:
    from randovania.game_description.hint_features import HintFeature
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.generator.pickup_pool import PoolResults
    from randovania.graph.state import State
    from randovania.gui.tracker.tracker_component import TrackerComponentSetup


class TrackerPickupInventory(TrackerComponent):
    """Lets the user say which pickups they've collected so far."""

    dock_area = QtCore.Qt.DockWidgetArea.LeftDockWidgetArea

    _collected_pickups: dict[PickupEntry, int]
    _starting_quantity: dict[PickupEntry, int]
    _widget_for_pickup: dict[PickupEntry, QtWidgets.QCheckBox | ScrollProtectedSpinBox]
    _during_setup: bool = False

    @classmethod
    @override
    def create_for(cls, setup: TrackerComponentSetup) -> Self | None:
        return cls(setup.pickup_pool)

    def __init__(self, pickup_pool: PoolResults) -> None:
        super().__init__()
        self._collected_pickups = {}
        self._widget_for_pickup = {}

        self.setWindowTitle("Inventory")

        self.root_widget = QtWidgets.QScrollArea()
        self.root_widget.setWidgetResizable(True)
        self.root_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.root_widget)

        self.scroll_contents = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_contents)
        self.root_widget.setWidget(self.scroll_contents)

        pickup_by_name: dict[str, PickupEntry] = {}
        pickup_with_quantity: dict[PickupEntry, int] = {}
        self._starting_quantity: dict[PickupEntry, int] = {}

        for pickup, is_starting in itertools.chain(
            zip(pickup_pool.pickups_in_world(), itertools.repeat(False)),
            zip(pickup_pool.starting, itertools.repeat(True)),
        ):
            if pickup.name in pickup_by_name:
                pickup_with_quantity[pickup_by_name[pickup.name]] += 1
            else:
                pickup_by_name[pickup.name] = pickup
                pickup_with_quantity[pickup] = 1

            if is_starting:
                p = pickup_by_name[pickup.name]
                self._starting_quantity[p] = self._starting_quantity.get(p, 0) + 1

        # One box per gui category, in a stable order.
        parent_widgets: dict[HintFeature, tuple[QtWidgets.QGroupBox, QtWidgets.QGridLayout]] = {}
        categories = {pickup.gui_category for pickup in pickup_with_quantity}
        row_for_parent: dict[QtWidgets.QGroupBox, int] = {}
        column_for_parent: dict[QtWidgets.QGroupBox, int] = {}

        for category in sorted(categories, key=lambda it: it.long_name):
            box = QtWidgets.QGroupBox(self.scroll_contents)
            box.setTitle(category.long_name)
            box.setObjectName(f"{category.name}_box")
            self.scroll_layout.addWidget(box)

            layout = QtWidgets.QGridLayout(box)
            parent_widgets[category] = (box, layout)
            row_for_parent[box] = column_for_parent[box] = 0

        k_column_count = 2

        with_quantity = []
        without_quantity_by_parent: dict[QtWidgets.QGroupBox, list[tuple[QtWidgets.QGridLayout, PickupEntry]]] = (
            collections.defaultdict(list)
        )

        for pickup, quantity in pickup_with_quantity.items():
            self._collected_pickups[pickup] = 0
            parent_widget, parent_layout = parent_widgets[pickup.gui_category]

            if quantity > 1:
                with_quantity.append((parent_widget, parent_layout, pickup, quantity))
            else:
                without_quantity_by_parent[parent_widget].append((parent_layout, pickup))

        for parent_widget, entries in without_quantity_by_parent.items():
            num_rows = math.ceil(len(entries) / k_column_count)
            for parent_layout, pickup in entries:
                check_box = QtWidgets.QCheckBox(parent_widget)
                check_box.setText(pickup.name)

                if self._starting_quantity.get(pickup, 0) > 0:
                    check_box.setChecked(True)
                    check_box.setEnabled(False)
                    check_box.setToolTip("Starting pickup")

                check_box.stateChanged.connect(functools.partial(self._change_item_quantity, pickup, True))
                self._widget_for_pickup[pickup] = check_box

                row = row_for_parent[parent_widget]
                column = column_for_parent[parent_widget]
                parent_layout.addWidget(check_box, row, column)
                row += 1

                if row >= num_rows:
                    row = 0
                    column += 1

                row_for_parent[parent_widget] = row
                column_for_parent[parent_widget] = column

            # Prepare the rows for the spin boxes below
            row_for_parent[parent_widget] = num_rows
            column_for_parent[parent_widget] = 0

        for parent_widget, parent_layout, pickup, quantity in with_quantity:
            self._create_widgets_with_quantity(
                pickup,
                parent_widget,
                parent_layout,
                row_for_parent[parent_widget],
                quantity,
                self._starting_quantity.get(pickup, 0),
            )
            row_for_parent[parent_widget] += 1

        self.scroll_layout.addStretch()

    def _create_widgets_with_quantity(
        self,
        pickup: PickupEntry,
        parent_widget: QtWidgets.QWidget,
        parent_layout: QtWidgets.QGridLayout,
        row: int,
        quantity: int,
        starting_quantity: int,
    ) -> None:
        label = QtWidgets.QLabel(parent_widget)
        label.setText(pickup.name)
        parent_layout.addWidget(label, row, 0)

        spin_box = ScrollProtectedSpinBox(parent_widget)
        spin_box.setMaximumWidth(50)
        spin_box.setMinimum(starting_quantity)
        spin_box.setMaximum(quantity)
        if starting_quantity == quantity:
            spin_box.setEnabled(False)
        spin_box.valueChanged.connect(functools.partial(self._change_item_quantity, pickup, False))
        self._widget_for_pickup[pickup] = spin_box
        parent_layout.addWidget(spin_box, row, 1)

    def _change_item_quantity(self, pickup: PickupEntry, use_quantity_as_bool: bool, quantity: int) -> None:
        if use_quantity_as_bool:
            quantity = 1 if bool(quantity) else 0

        self._collected_pickups[pickup] = quantity - self._starting_quantity.get(pickup, 0)
        if not self._during_setup:
            self.StateChanged.emit()

    def bulk_change_quantity(self, new_quantity: dict[PickupEntry, int]) -> None:
        """Sets all pickup widgets at once. new_quantity ignores the starting quantity."""
        self._during_setup = True
        for pickup, quantity in new_quantity.items():
            widget = self._widget_for_pickup[pickup]
            quantity += self._starting_quantity.get(pickup, 0)

            if isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(quantity > 0)
            else:
                widget.setValue(quantity)
        self._during_setup = False

    # Tracker Component

    @override
    def reset(self) -> None:
        self.bulk_change_quantity(dict.fromkeys(self._collected_pickups.keys(), 0))

    @override
    def decode_persisted_state(self, previous_state: dict) -> dict[PickupEntry, int] | None:
        try:
            pickup_name_to_pickup = {pickup.name: pickup for pickup in self._collected_pickups.keys()}
            return {
                pickup_name_to_pickup[pickup_name]: quantity
                for pickup_name, quantity in previous_state["collected_pickups"].items()
            }
        except (KeyError, AttributeError):
            return None

    @override
    def apply_previous_state(self, previous_state: dict[PickupEntry, int]) -> None:
        self.bulk_change_quantity(previous_state)

    @override
    def persist_current_state(self) -> dict:
        return {
            "collected_pickups": {pickup.name: quantity for pickup, quantity in self._collected_pickups.items()},
        }

    @override
    def fill_into_state(self, state: State) -> None:
        for pickup, quantity in self._collected_pickups.items():
            for _ in range(quantity):
                add_pickup_to_state(state, pickup)
