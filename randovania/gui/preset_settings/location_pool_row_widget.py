from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from randovania.game_description.db.pickup_node import PickupNode
from randovania.gui.generated.widget_location_pool_row_ui import Ui_LocationPoolRowWidget


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

    def set_can_have_progression(self, progression: bool):
        if progression:
            self.radio_shuffled.setChecked(True)
        else:
            self.radio_shuffled_no_progression.setChecked(True)
        self.changed.emit(self.node)

    def _on_radio_changed(self, checked: bool):
        if checked:
            self.changed.emit(self.node)

    @property
    def can_have_progression(self):
        return self.radio_shuffled.isChecked()
