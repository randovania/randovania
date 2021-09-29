from randovania.gui.generated.preset_logic_damage_ui import Ui_PresetLogicDamage
from randovania.gui.lib import common_qt_lib
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.damage_strictness import LayoutDamageStrictness
from randovania.layout.preset import Preset


class PresetLogicDamage(PresetTab, Ui_PresetLogicDamage):

    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        self.setupUi(self)

        self.damage_strictness_combo.setItemData(0, LayoutDamageStrictness.STRICT)
        self.damage_strictness_combo.setItemData(1, LayoutDamageStrictness.MEDIUM)
        self.damage_strictness_combo.setItemData(2, LayoutDamageStrictness.LENIENT)
        self.damage_strictness_combo.currentIndexChanged.connect(self._on_update_damage_strictness)

    @property
    def uses_patches_tab(self) -> bool:
        return False

    def on_preset_changed(self, preset: Preset):
        common_qt_lib.set_combo_with_value(self.damage_strictness_combo, preset.configuration.damage_strictness)

    def _on_update_damage_strictness(self, new_index: int):
        with self._editor as editor:
            editor.layout_configuration_damage_strictness = self.damage_strictness_combo.currentData()
