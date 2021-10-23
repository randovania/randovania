from randovania.gui.generated.preset_echoes_patches_ui import Ui_PresetEchoesPatches
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class PresetEchoesPatches(PresetTab, Ui_PresetEchoesPatches):

    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        self.setupUi(self)

        self.include_menu_mod_label.setText(self.include_menu_mod_label.text().replace("color:#0000ff;", ""))

        # Signals
        self.warp_to_start_check.stateChanged.connect(self._persist_option_then_notify("warp_to_start"))
        self.include_menu_mod_check.stateChanged.connect(self._persist_option_then_notify("include_menu_mod"))

    @property
    def uses_patches_tab(self) -> bool:
        return True

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        self.warp_to_start_check.setChecked(config.warp_to_start)
        self.include_menu_mod_check.setChecked(config.menu_mod)
