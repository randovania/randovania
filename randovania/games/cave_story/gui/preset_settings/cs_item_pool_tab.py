import dataclasses
from PySide2 import QtWidgets
from randovania.games.cave_story.layout.cs_configuration import CSObjective
from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.major_item_state import MajorItemState
from randovania.layout.preset import Preset


class CSPresetItemPool(PresetItemPool):
    _puppy_widget: QtWidgets.QCheckBox

    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        self._create_puppy_checkbox()
        self.previousObj = CSObjective.NORMAL_ENDING

        self._disable_starting()
    
    def on_preset_changed(self, preset: Preset):
        super().on_preset_changed(preset)

        self._puppy_widget.setChecked(preset.configuration.puppies_anywhere)
        
        if self.previousObj != preset.configuration.objective:
            if self.previousObj == CSObjective.BAD_ENDING or preset.configuration.objective == CSObjective.BAD_ENDING:
                self._update_explosive(preset.configuration.objective == CSObjective.BAD_ENDING)
            self.previousObj = preset.configuration.objective
    
    def _create_puppy_checkbox(self):
        parent, layout, _ = self._boxes_for_category["puppies"]

        puppy = QtWidgets.QCheckBox(parent)
        puppy.setText("Shuffle puppies anywhere")
        puppy.setToolTip("When disabled, puppies will only be shuffled within the Sand Zone. When enabled, puppies can be placed in any valid location.")
        puppy.stateChanged.connect(self._on_puppy_changed)

        line = QtWidgets.QFrame(parent)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line, layout.rowCount(), 0, 1, -1)

        layout.addWidget(puppy, layout.rowCount(), 0, 1, -1)
        self._puppy_widget = puppy
    
    def _on_puppy_changed(self):
        anywhere = self._puppy_widget.isChecked()
        with self._editor as editor:
            editor.set_configuration_field("puppies_anywhere", anywhere)
    
    def _update_explosive(self, bad_ending: bool):
        items = self._boxes_for_category["items"][2]
        explosive = next(item for item in items.keys() if item.name == "Explosive")
        explosive_box = items[explosive]

        if bad_ending:
            explosive_box.setVisible(False)
            explosive_box._update_for_state(MajorItemState(True, 0, 0))
        else:
            explosive_box.setVisible(True)
            explosive_box._update_for_state(MajorItemState(False, 1, 0))
    
    def _disable_starting(self):
        for _, _, widgets in self._boxes_for_category.values():
            for widget in widgets.values():
                widget.starting_radio.setEnabled(False)
                widget.starting_radio.setToolTip("Cave Story currently does not support starting items.")
        
        self.random_starting_box.setVisible(False)
