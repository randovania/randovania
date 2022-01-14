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

        

    @property
    def uses_patches_tab(self) -> bool:
        return False


    
