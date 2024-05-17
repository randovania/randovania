from __future__ import annotations

import math
from typing import TYPE_CHECKING, NamedTuple

from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from randovania.layout.base.ammo_pickup_state import AmmoPickupState

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.pickup.ammo_pickup import AmmoPickupDefinition
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class AmmoPickupWidgets(NamedTuple):
    pickup_spinbox: QtWidgets.QSpinBox
    expected_count: QtWidgets.QLabel | None
    expected_template: str
    pickup_box: QtWidgets.QGroupBox
    require_main_item_check: QtWidgets.QCheckBox | None


class SplitAmmoWidget(QtWidgets.QCheckBox):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        editor: PresetEditor,
        unified_ammo: AmmoPickupDefinition,
        split_ammo: Iterable[AmmoPickupDefinition],
    ):
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

    def on_preset_changed(self, preset: Preset, ammo_pickup_widgets: dict[AmmoPickupDefinition, AmmoPickupWidgets]):
        ammo_configuration = preset.configuration.ammo_pickup_configuration

        has_unified = ammo_configuration.pickups_state[self.unified_ammo].pickup_count > 0
        has_split = any(ammo_configuration.pickups_state[item].pickup_count > 0 for item in self.split_ammo)

        if not has_split and not has_unified:
            has_split, has_unified = self._last_check_state
        else:
            self._last_check_state = has_split, has_unified

        if has_unified:
            new_state = Qt.CheckState.PartiallyChecked if has_split else Qt.CheckState.Unchecked
        else:
            new_state = Qt.CheckState.Checked
        self.setCheckState(new_state)

        ammo_pickup_widgets[self.unified_ammo].pickup_box.setVisible(has_unified)
        for item in self.split_ammo:
            ammo_pickup_widgets[item].pickup_box.setVisible(has_split)

    def change_split(self, has_split: bool):
        with self._editor as editor:
            ammo_configuration = editor.ammo_pickup_configuration

            current_total = sum(
                ammo_configuration.pickups_state[ammo].pickup_count for ammo in (self.unified_ammo, *self.split_ammo)
            )

            new_states = {}
            if has_split:
                ref = ammo_configuration.pickups_state[self.unified_ammo]
                for i, split in enumerate(self.split_ammo):
                    new_count = current_total // len(self.split_ammo)
                    new_states[split] = AmmoPickupState(
                        ammo_count=(
                            math.ceil(
                                ref.ammo_count[i] * (current_total / new_count),
                            ),
                        ),
                        pickup_count=new_count,
                    )
                new_states[self.unified_ammo] = AmmoPickupState(
                    ammo_count=tuple(0 for _ in self.unified_ammo.items),
                    pickup_count=0,
                )

            else:
                for split in self.split_ammo:
                    new_states[split] = AmmoPickupState(ammo_count=(0,), pickup_count=0)
                new_states[self.unified_ammo] = AmmoPickupState(
                    ammo_count=tuple(
                        math.ceil(
                            ammo_configuration.pickups_state[split].ammo_count[0]
                            * (ammo_configuration.pickups_state[split].pickup_count / current_total)
                        )
                        for split in self.split_ammo
                    ),
                    pickup_count=current_total,
                )

            editor.ammo_pickup_configuration = ammo_configuration.replace_states(new_states)
            self._last_check_state = (has_split, not has_split)
