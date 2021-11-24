import dataclasses
from PySide2 import QtWidgets
from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class CSPresetItemPool(PresetItemPool):
    _puppy_widget: QtWidgets.QCheckBox

    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        self._create_puppy_checkbox()
    
    def on_preset_changed(self, preset: Preset):
        super().on_preset_changed(preset)

        self._puppy_widget.setChecked(preset.configuration.puppies_anywhere)
    
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
    
