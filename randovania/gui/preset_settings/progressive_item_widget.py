from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from randovania.layout.base.standard_pickup_state import StandardPickupState

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.pickup.standard_pickup import StandardPickupDefinition
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


def _state_has_item(state: StandardPickupState) -> bool:
    return (
        state.num_shuffled_pickups > 0
        or state.num_included_in_starting_pickups > 0
        or state.include_copy_in_original_location
    )


class ProgressiveItemWidget(QtWidgets.QCheckBox):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        editor: PresetEditor,
        progressive_item: StandardPickupDefinition,
        non_progressive_items: Iterable[StandardPickupDefinition],
    ):
        super().__init__(parent)
        self._editor = editor
        self.progressive_item = progressive_item
        self.non_progressive_items = list(non_progressive_items)
        self.setTristate(True)
        self.clicked.connect(self.change_progressive)

    def on_preset_changed(self, preset: Preset, elements: dict[StandardPickupDefinition, QtWidgets.QWidget]):
        major_configuration = preset.configuration.standard_pickup_configuration

        has_progressive = _state_has_item(major_configuration.pickups_state[self.progressive_item])
        has_non_progressive = any(
            _state_has_item(major_configuration.pickups_state[item]) for item in self.non_progressive_items
        )

        if not has_progressive and not has_non_progressive:
            has_progressive = self.isChecked()
            has_non_progressive = not has_progressive

        if has_non_progressive:
            new_state = Qt.CheckState.PartiallyChecked if has_progressive else Qt.CheckState.Unchecked
        else:
            new_state = Qt.CheckState.Checked
        self.setCheckState(new_state)

        for item in self.non_progressive_items:
            elements[item].setVisible(has_non_progressive)
        elements[self.progressive_item].setVisible(has_progressive)

    def change_progressive(self, is_progressive: bool):
        with self._editor as editor:
            if is_progressive:
                non_progressive_state = StandardPickupState()
                progressive_state = StandardPickupState(num_shuffled_pickups=len(self.non_progressive_items))
            else:
                non_progressive_state = StandardPickupState(num_shuffled_pickups=1)
                progressive_state = StandardPickupState()

            new_states = {self.progressive_item: progressive_state}
            for item in self.non_progressive_items:
                new_states[item] = non_progressive_state

            editor.standard_pickup_configuration = editor.standard_pickup_configuration.replace_states(new_states)
