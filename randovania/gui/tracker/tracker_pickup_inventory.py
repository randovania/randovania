from __future__ import annotations

import collections
import functools
import math
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.gui.lib.scroll_protected import ScrollProtectedSpinBox
from randovania.gui.tracker.tracker_component import TrackerComponent
from randovania.resolver.state import State, add_pickup_to_state

if TYPE_CHECKING:
    from randovania.game_description.pickup.pickup_category import PickupCategory
    from randovania.game_description.resources.pickup_entry import PickupEntry
    from randovania.generator.filler.runner import PlayerPool
    from randovania.layout.base.base_configuration import BaseConfiguration


class TrackerPickupInventory(TrackerComponent):
    _collected_pickups: dict[PickupEntry, int]
    _widget_for_pickup: dict[PickupEntry, QtWidgets.QCheckBox | ScrollProtectedSpinBox]
    _during_setup: bool = False

    @classmethod
    def create_for(cls, player_pool: PlayerPool, configuration: BaseConfiguration,
                   ) -> TrackerPickupInventory | None:
        return cls(player_pool.pickups)

    def __init__(self, item_pool: list[PickupEntry]):
        super().__init__()
        self._collected_pickups = {}
        self._widget_for_pickup = {}

        self.setWindowTitle("Inventory (Pickups)")

        self.root_widget = QtWidgets.QScrollArea()
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)
        self.root_widget.setWidgetResizable(True)
        self.setWidget(self.root_widget)

        self.scroll_contents = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_contents)
        self.root_widget.setWidget(self.scroll_contents)

        parent_widgets: dict[PickupCategory, tuple[QtWidgets.QGroupBox, QtWidgets.QGridLayout]] = {}
        categories: set[PickupCategory] = {pickup.pickup_category for pickup in item_pool}
        row_for_parent: dict[QtWidgets.QGroupBox, int] = {}
        column_for_parent: dict[QtWidgets.QGroupBox, int] = {}

        for category in sorted(categories, key=lambda it: it.long_name):
            box = QtWidgets.QGroupBox(self.scroll_contents)
            box.setTitle(category.long_name)
            box.setObjectName(f"{category.long_name}_box")
            self.scroll_layout.addWidget(box)

            layout = QtWidgets.QGridLayout(box)
            layout.setSpacing(6)
            layout.setContentsMargins(11, 11, 11, 11)

            parent_widgets[category] = (box, layout)
            row_for_parent[box] = column_for_parent[box] = 0

        k_column_count = 2

        pickup_by_name = {}
        pickup_with_quantity = {}

        for pickup in item_pool:
            if pickup.name in pickup_by_name:
                pickup_with_quantity[pickup_by_name[pickup.name]] += 1
            else:
                pickup_by_name[pickup.name] = pickup
                pickup_with_quantity[pickup] = 1

        non_expansions_with_quantity = []
        without_quantity_by_parent: dict[
            QtWidgets.QGroupBox,
            list[tuple[QtWidgets.QGridLayout, PickupEntry]]
        ] = collections.defaultdict(list)

        for pickup, quantity in pickup_with_quantity.items():
            self._collected_pickups[pickup] = 0
            parent_widget, parent_layout = parent_widgets[pickup.pickup_category]

            if quantity > 1:
                non_expansions_with_quantity.append((parent_widget, parent_layout, pickup, quantity))
            else:
                without_quantity_by_parent[parent_widget].append((parent_layout, pickup))

        for parent_widget, entries in without_quantity_by_parent.items():
            num_rows = math.ceil(len(entries) / k_column_count)
            for parent_layout, pickup in entries:
                check_box = QtWidgets.QCheckBox(parent_widget)
                check_box.setText(pickup.name)
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

        for parent_widget, parent_layout, pickup, quantity in non_expansions_with_quantity:
            self._create_widgets_with_quantity(pickup, parent_widget, parent_layout,
                                               row_for_parent[parent_widget],
                                               quantity)
            row_for_parent[parent_widget] += 1

        for parent_widget, _ in parent_widgets.values():
            # Nothing was added to this box
            if row_for_parent[parent_widget] == column_for_parent.get(parent_widget) == 0:
                parent_widget.setVisible(False)

    # Usability

    def _notify_changes(self):
        # TODO
        pass

    def _change_item_quantity(self, pickup: PickupEntry, use_quantity_as_bool: bool, quantity: int):
        if use_quantity_as_bool:
            if bool(quantity):
                quantity = 1
            else:
                quantity = 0

        self._collected_pickups[pickup] = quantity
        if not self._during_setup:
            self._notify_changes()

    def bulk_change_quantity(self, new_quantity: dict[PickupEntry, int]):
        self._during_setup = True
        for pickup, quantity in new_quantity.items():
            widget = self._widget_for_pickup[pickup]
            if isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(quantity > 0)
            else:
                widget.setValue(quantity)
        self._during_setup = False

    def _create_widgets_with_quantity(self,
                                      pickup: PickupEntry,
                                      parent_widget: QtWidgets.QWidget,
                                      parent_layout: QtWidgets.QGridLayout,
                                      row: int,
                                      quantity: int,
                                      ):
        label = QtWidgets.QLabel(parent_widget)
        label.setText(pickup.name)
        parent_layout.addWidget(label, row, 0)

        spin_box = ScrollProtectedSpinBox(parent_widget)
        spin_box.setMaximumWidth(50)
        spin_box.setMaximum(quantity)
        spin_box.valueChanged.connect(functools.partial(self._change_item_quantity, pickup, False))
        self._widget_for_pickup[pickup] = spin_box
        parent_layout.addWidget(spin_box, row, 1)

    def reset(self):
        self.bulk_change_quantity({
            pickup: 0
            for pickup in self._collected_pickups.keys()
        })

    # Restoring State

    def decode_persisted_state(self, previous_state: dict) -> dict[PickupEntry, int] | None:
        try:
            pickup_name_to_pickup: dict[str, PickupEntry] = {
                pickup.name: pickup
                for pickup in self._collected_pickups.keys()
            }
            return {
                pickup_name_to_pickup[pickup_name]: quantity
                for pickup_name, quantity in previous_state["collected_pickups"].items()
            }
        except (KeyError, AttributeError):
            return None

    def apply_previous_state(self, previous_state: dict[PickupEntry, int]) -> None:
        self.bulk_change_quantity(previous_state)

    # Persisting State

    def persist_current_state(self):
        return {
            "collected_pickups": {
                pickup.name: quantity
                for pickup, quantity in self._collected_pickups.items()
            },
        }

    # As State

    def fill_into_state(self, state: State) -> State | None:
        for pickup, quantity in self._collected_pickups.items():
            for _ in range(quantity):
                add_pickup_to_state(state, pickup)

        return state
