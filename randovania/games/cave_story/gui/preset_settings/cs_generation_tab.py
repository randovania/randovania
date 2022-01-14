from typing import Iterable, Optional
from PySide2.QtWidgets import *
from randovania.games.cave_story.layout.cs_configuration import CSObjective
from randovania.gui.preset_settings.generation_tab import PresetGeneration
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset

class PresetCSGeneration(PresetGeneration):
    def __init__(self, editor: PresetEditor) -> None:
        self._create_puppy_checkbox()
        super().__init__(editor)

    @property
    def game_specific_widgets(self) -> Optional[Iterable[QWidget]]:
        yield self._puppy_widget
    
    def on_preset_changed(self, preset: Preset):
        super().on_preset_changed(preset)
        self._puppy_widget.setChecked(preset.configuration.puppies_anywhere)
        for w in [self.check_full_clear, self.full_clear_label, self.full_clear_line]:
            w.setVisible(preset.configuration.objective != CSObjective.HUNDRED_PERCENT)

    def _create_puppy_checkbox(self):
        puppy = QCheckBox("Shuffle puppies anywhere")
        puppy.setToolTip("When disabled, puppies will only be shuffled within the Sand Zone. When enabled, puppies can be placed in any valid location.")
        puppy.stateChanged.connect(self._on_puppy_changed)
        self._puppy_widget = puppy
    
    def _on_puppy_changed(self):
        anywhere = self._puppy_widget.isChecked()
        with self._editor as editor:
            editor.set_configuration_field("puppies_anywhere", anywhere)
    