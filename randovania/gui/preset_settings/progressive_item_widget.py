from typing import Iterable, Dict

from PySide2 import QtWidgets
from PySide2.QtCore import Qt

from randovania.game_description.item.major_item import MajorItem
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.major_item_state import MajorItemState
from randovania.layout.preset import Preset


def _state_has_item(state: MajorItemState) -> bool:
    return (state.num_shuffled_pickups > 0
            or state.num_included_in_starting_items > 0
            or state.include_copy_in_original_location)


class ProgressiveItemWidget(QtWidgets.QCheckBox):
    def __init__(self, parent: QtWidgets.QWidget, editor: PresetEditor,
                 progressive_item: MajorItem, non_progressive_items: Iterable[MajorItem]):
        super().__init__(parent)
        self._editor = editor
        self.progressive_item = progressive_item
        self.non_progressive_items = list(non_progressive_items)
        self.setTristate(True)
        self.clicked.connect(self.change_progressive)

    def on_preset_changed(self, preset: Preset, elements: Dict[MajorItem, QtWidgets.QWidget]):
        major_configuration = preset.configuration.major_items_configuration

        has_progressive = _state_has_item(major_configuration.items_state[self.progressive_item])
        has_non_progressive = any(_state_has_item(major_configuration.items_state[item])
                                  for item in self.non_progressive_items)

        if has_non_progressive:
            new_state = Qt.PartiallyChecked if has_progressive else Qt.Unchecked
        else:
            new_state = Qt.Checked
        self.setCheckState(new_state)

        for item in self.non_progressive_items:
            elements[item].setVisible(has_non_progressive)
        elements[self.progressive_item].setVisible(has_progressive)

    def change_progressive(self, is_progressive: bool):
        with self._editor as editor:
            if is_progressive:
                non_progressive_state = MajorItemState()
                progressive_state = MajorItemState(num_shuffled_pickups=len(self.non_progressive_items))
            else:
                non_progressive_state = MajorItemState(num_shuffled_pickups=1)
                progressive_state = MajorItemState()

            new_states = {self.progressive_item: progressive_state}
            for item in self.non_progressive_items:
                new_states[item] = non_progressive_state

            editor.major_items_configuration = editor.major_items_configuration.replace_states(new_states)
