from typing import Iterable, Dict, NamedTuple, Optional

from PySide2 import QtWidgets
from PySide2.QtCore import Qt

from randovania.game_description.item.ammo import Ammo
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.ammo_state import AmmoState
from randovania.layout.preset import Preset


class AmmoPickupWidgets(NamedTuple):
    pickup_spinbox: QtWidgets.QSpinBox
    expected_count: QtWidgets.QLabel
    pickup_box: QtWidgets.QGroupBox
    require_major_item_check: Optional[QtWidgets.QCheckBox]


class SplitAmmoWidget(QtWidgets.QCheckBox):
    def __init__(self, parent: QtWidgets.QWidget, editor: PresetEditor,
                 unified_ammo: Ammo, split_ammo: Iterable[Ammo]):
        super().__init__(parent)
        self._editor = editor
        self.unified_ammo = unified_ammo
        self.split_ammo = list(split_ammo)
        self.setTristate(True)
        self._last_check_state = (True, False)
        self.clicked.connect(self.change_split)

    def on_preset_changed(self, preset: Preset, ammo_pickup_widgets: Dict[Ammo, AmmoPickupWidgets]):
        ammo_configuration = preset.configuration.ammo_configuration

        has_unified = ammo_configuration.items_state[self.unified_ammo].pickup_count > 0
        has_split = any(ammo_configuration.items_state[item].pickup_count > 0
                        for item in self.split_ammo)

        if not has_split and not has_unified:
            has_split, has_unified = self._last_check_state
        else:
            self._last_check_state = has_split, has_unified

        if has_unified:
            new_state = Qt.PartiallyChecked if has_split else Qt.Unchecked
        else:
            new_state = Qt.Checked
        self.setCheckState(new_state)

        ammo_pickup_widgets[self.unified_ammo].pickup_box.setVisible(has_unified)
        for item in self.split_ammo:
            ammo_pickup_widgets[item].pickup_box.setVisible(has_split)

    def change_split(self, has_split: bool):
        with self._editor as editor:
            ammo_configuration = editor.ammo_configuration

            current_total = sum(
                ammo_configuration.items_state[ammo].pickup_count
                for ammo in (self.unified_ammo, *self.split_ammo)
            )
            if has_split:
                split_state = AmmoState(pickup_count=current_total // len(self.split_ammo))
                unified_state = AmmoState()
            else:
                split_state = AmmoState()
                unified_state = AmmoState(pickup_count=current_total)

            new_states = {self.unified_ammo: unified_state}
            for ammo in self.split_ammo:
                new_states[ammo] = split_state

            editor.ammo_configuration = ammo_configuration.replace_states(new_states)
            self._last_check_state = (has_split, not has_split)
