from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from randovania.game_description.world.pickup_node import PickupNode
from randovania.gui.generated.widget_location_pool_row_ui import Ui_LocationPoolRowWidget
from randovania.layout.base.available_locations import LocationPickupMode


class LocationPoolRowWidget(QWidget, Ui_LocationPoolRowWidget):
    changed = Signal(PickupNode)
    node: PickupNode

    def __init__(self, node: PickupNode, location_name: str):
        super().__init__()
        self.setupUi(self)

        self.node = node
        self.label_location_name.setText(location_name)

        self.radio_shuffled.toggled.connect(self._on_radio_changed)
        self.radio_shuffled_no_progression.toggled.connect(self._on_radio_changed)
        self.radio_shuffled_no_majors.toggled.connect(self._on_radio_changed)

    def set_location_pickup_mode(self, mode: LocationPickupMode):
        if mode == LocationPickupMode.SHUFFLED_NO_PROGRESSION:
            self.radio_shuffled_no_progression.setChecked(True)
        elif mode == LocationPickupMode.SHUFFLED_NO_MAJORS:
            self.radio_shuffled_no_majors.setChecked(True)
        else:
            self.radio_shuffled.setChecked(True)
        self.changed.emit(self.node)

    def set_is_major_only_location(self, major_only: bool):
        self.radio_shuffled_no_majors.setEnabled(not major_only)

    def _on_radio_changed(self, checked: bool):
        if checked:
            self.changed.emit(self.node)

    @property
    def location_pickup_mode(self) -> LocationPickupMode:
        if self.radio_shuffled_no_progression.isChecked():
            return LocationPickupMode.SHUFFLED_NO_PROGRESSION
        elif self.radio_shuffled_no_majors.isChecked():
            return LocationPickupMode.SHUFFLED_NO_MAJORS
        return LocationPickupMode.SHUFFLED
