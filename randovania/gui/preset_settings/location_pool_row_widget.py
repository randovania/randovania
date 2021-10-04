import functools
from PySide2.QtCore import Signal
from PySide2.QtWidgets import QDialog, QRadioButton
from randovania.game_description.world.node import PickupNode

from randovania.gui.generated.widget_location_pool_row_ui import Ui_LocationPoolRowWidget

class LocationPoolRowWidget(QDialog, Ui_LocationPoolRowWidget):
    changed = Signal()
    node: PickupNode
    
    def __init__(self, node: PickupNode, location_name: str):
        super().__init__()
        self.setupUi(self)

        self.node = node
        self.label_location_name.setText(location_name)

        self.radio_vanilla.setVisible(False)
        self.radio_vanilla.setToolTip("Not yet implemented, coming soon")
        self.radio_fixed.setVisible(False)
        self.radio_fixed.setToolTip("Not yet implemented, coming soon")
        self.combo_fixed_item.setVisible(False)
        self.combo_fixed_item.setToolTip("Not yet implemented, coming soon")

        self.radio_vanilla.toggled.connect(self._on_radio_changed)
        self.radio_shuffled.toggled.connect(self._on_radio_changed)
        self.radio_shuffled_no_progression.toggled.connect(self._on_radio_changed)
        self.radio_fixed.toggled.connect(self._on_radio_changed)

    def set_can_have_progression(self, progression: bool):
        if progression:
            self.radio_shuffled.setChecked(True)
        else:
            self.radio_shuffled_no_progression.setChecked(True)
        self.changed.emit()

    def _on_radio_changed(self, checked: bool):
        if checked:
            self.changed.emit()

    @property
    def can_have_progression(self):
        return self.radio_shuffled.isChecked()