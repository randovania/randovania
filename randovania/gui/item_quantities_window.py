import functools
from typing import Dict

from PySide2.QtWidgets import QMainWindow, QLabel, QSpinBox

from randovania.game_description.default_database import default_prime2_pickup_database
from randovania.game_description.resources import PickupEntry
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.custom_spin_box import CustomSpinBox
from randovania.gui.item_quantities_window_ui import Ui_ItemQuantitiesWindow
from randovania.gui.tab_service import TabService
from randovania.interface_common.options import Options


class ItemQuantitiesWindow(QMainWindow, Ui_ItemQuantitiesWindow):
    _options: Options
    _spinbox_for_item: Dict[PickupEntry, QSpinBox] = {}

    _total_item_count = 0
    _maximum_item_count = 0

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin, options: Options):
        super().__init__()
        self.setupUi(self)
        self._options = options

        # Connect to Events
        self.itemquantity_reset_button.clicked.connect(self._reset_item_quantities)
        self.itemquantity_total_label.keep_visible_with_help_disabled = True
        self._create_item_toggles()

    def _create_item_toggles(self):
        pickup_database = default_prime2_pickup_database()

        self._maximum_item_count = pickup_database.total_pickup_count
        pickups = set(pickup_database.pickups.values())
        pickups.remove(pickup_database.useless_pickup)

        num_rows = len(pickups) / 2
        for i, pickup in enumerate(sorted(pickups, key=lambda pickup: pickup.name)):
            row = 3 + i % num_rows
            column = (i // num_rows) * 2
            pickup_label = QLabel(self.scroll_area_widget_contents)
            pickup_label.setText(pickup.name)
            pickup_label.keep_visible_with_help_disabled = True
            self.gridLayout_3.addWidget(pickup_label, row, column, 1, 1)

            original_quantity = pickup_database.original_quantity_for(pickup)
            value = self._options.quantity_for_pickup(pickup)
            if value is None:
                value = original_quantity
            self._total_item_count += value

            spin_box = CustomSpinBox(self.scroll_area_widget_contents)
            spin_box.pickup = pickup
            spin_box.original_quantity = original_quantity
            spin_box.previous_value = value
            spin_box.setValue(value)
            spin_box.setFixedWidth(75)
            spin_box.setMaximum(self._maximum_item_count)
            spin_box.valueChanged.connect(functools.partial(self._change_item_quantity, spin_box))
            self._spinbox_for_item[pickup] = spin_box
            self.gridLayout_3.addWidget(spin_box, row, column + 1, 1, 1)

        self._update_item_quantity_total_label()

    def _reset_item_quantities(self):
        with self._options as options:
            options.set_pickup_quantities({})

    def _change_item_quantity(self, spin_box: QSpinBox, new_quantity: int):
        """Changes the value for a specific spin box"""
        self._total_item_count -= spin_box.previous_value
        self._total_item_count += new_quantity
        spin_box.previous_value = new_quantity
        self._update_item_quantity_total_label()

        with self._options as options:
            options.set_quantity_for_pickup(spin_box.pickup, new_quantity)

    def _update_item_quantity_total_label(self):
        self.itemquantity_total_label.setText("Total Pickups: {}/{}".format(
            self._total_item_count, self._maximum_item_count))

    # Options
    def on_options_changed(self):
        for pickup, quantity in self._options.layout_configuration.pickup_quantities.items():
            if pickup in self._spinbox_for_item:
                self._spinbox_for_item[pickup].setValue(quantity)
