from randovania.gui.generated.preset_cs_hp_ui import Ui_PresetCSHP
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class PresetCSHP(PresetTab, Ui_PresetCSHP):
    def __init__(self, editor: PresetEditor) -> None:
        super().__init__(editor)
        self.setupUi(self)

        self.starting_hp_spin_box.valueChanged.connect(self._on_starting_hp_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "HP"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def _on_starting_hp_changed(self):
        with self._editor as editor:
            editor.set_configuration_field("starting_hp", int(self.starting_hp_spin_box.value()))

    def on_preset_changed(self, preset: Preset):
        self.starting_hp_spin_box.setValue(preset.configuration.starting_hp)
