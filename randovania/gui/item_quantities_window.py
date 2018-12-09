import functools
from typing import Dict

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QMainWindow, QLabel, QSpinBox

from randovania.game_description.default_database import default_prime2_pickup_database
from randovania.game_description.resources import PickupEntry
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.common_qt_lib import application_options
from randovania.gui.item_quantities_window_ui import Ui_ItemQuantitiesWindow
from randovania.gui.tab_service import TabService


class CustomSpinBox(QSpinBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)

    def focusInEvent(self, event: QEvent):
        self.setFocusPolicy(Qt.WheelFocus)

    def focusOutEvent(self, event: QEvent):
        self.setFocusPolicy(Qt.StrongFocus)

    def eventFilter(self, obj: QSpinBox, event: QEvent) -> bool:
        if event.type() == QEvent.Wheel and isinstance(obj, QSpinBox):
            if obj.focusPolicy() == Qt.WheelFocus:
                event.accept()
                return False
            else:
                event.ignore()
                return True
        return super().eventFilter(obj, event)


class ItemQuantitiesWindow(QMainWindow, Ui_ItemQuantitiesWindow):
    _spinbox_for_item: Dict[PickupEntry, QSpinBox] = {}
    _bulk_changing_quantity = False

    _total_item_count = 0
    _maximum_item_count = 0

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin):
        super().__init__()
        self.setupUi(self)

        # Connect to Events
        self.itemquantity_reset_button.clicked.connect(self._reset_item_quantities)
        self.itemquantity_total_label.keep_visible_with_help_disabled = True
        self._create_item_toggles()

    def _create_item_toggles(self):
        options = application_options()
        pickup_database = default_prime2_pickup_database()

        self._maximum_item_count = pickup_database.total_pickup_count
        pickups = set(pickup_database.pickups.values())

        # TODO: Very specific logic that should be provided by data
        pickups.remove(pickup_database.pickup_by_name("Energy Transfer Module"))

        num_rows = len(pickups) / 2
        for i, pickup in enumerate(sorted(pickups, key=lambda pickup: pickup.name)):
            row = 3 + i % num_rows
            column = (i // num_rows) * 2
            pickup_label = QLabel(self.scroll_area_widget_contents)
            pickup_label.setText(pickup.name)
            pickup_label.keep_visible_with_help_disabled = True
            self.gridLayout_3.addWidget(pickup_label, row, column, 1, 1)

            original_quantity = pickup_database.original_quantity_for(pickup)
            # FIXME: this needs the actual pickup now
            value = options.quantity_for_pickup(pickup)
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
        self._bulk_changing_quantity = True

        pickup_database = default_prime2_pickup_database()
        for pickup in pickup_database.pickups.values():
            if pickup in self._spinbox_for_item:
                self._spinbox_for_item[pickup].setValue(pickup_database.original_quantity_for(pickup))

        application_options().save_to_disk()
        self._bulk_changing_quantity = False

    def _change_item_quantity(self, spin_box: QSpinBox, new_quantity: int):
        self._total_item_count -= spin_box.previous_value
        self._total_item_count += new_quantity
        spin_box.previous_value = new_quantity
        self._update_item_quantity_total_label()

        options = application_options()
        options.set_quantity_for_pickup(spin_box.pickup, new_quantity)

        if not self._bulk_changing_quantity:
            options.save_to_disk()

    def _update_item_quantity_total_label(self):
        self.itemquantity_total_label.setText("Total Pickups: {}/{}".format(
            self._total_item_count, self._maximum_item_count))
