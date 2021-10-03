import math
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

        invalid_split = [split for split in self.split_ammo if len(split.items) != 1]
        if invalid_split:
            raise ValueError(f"The following split ammo have more than one item associated: {invalid_split}")

        if len(unified_ammo.items) != len(self.split_ammo):
            raise ValueError("The unified ammo should have as many items as there are split ammo items.")

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

            new_states = {}
            if has_split:
                ref = ammo_configuration.items_state[self.unified_ammo]
                for i, split in enumerate(self.split_ammo):
                    new_count = current_total // len(self.split_ammo)
                    new_states[split] = AmmoState(
                        ammo_count=(math.ceil(
                            ref.ammo_count[i] * (current_total / new_count),
                        ),),
                        pickup_count=new_count,
                    )
                new_states[self.unified_ammo] = AmmoState(
                    ammo_count=tuple(0 for _ in self.unified_ammo.items),
                    pickup_count=0,
                )

            else:
                for split in self.split_ammo:
                    new_states[split] = AmmoState(
                        ammo_count=(0,),
                        pickup_count=0
                    )
                new_states[self.unified_ammo] = AmmoState(
                    ammo_count=tuple(
                        math.ceil(
                            ammo_configuration.items_state[split].ammo_count[0] * (
                                    ammo_configuration.items_state[split].pickup_count / current_total
                            )
                        )
                        for split in self.split_ammo
                    ),
                    pickup_count=current_total,
                )

            editor.ammo_configuration = ammo_configuration.replace_states(new_states)
            self._last_check_state = (has_split, not has_split)
