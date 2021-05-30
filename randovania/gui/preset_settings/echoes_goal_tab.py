from PySide2 import QtCore

from randovania.gui.generated.preset_echoes_goal_ui import Ui_PresetEchoesGoal
from randovania.gui.lib.common_qt_lib import set_combo_with_value
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.prime2.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.layout.preset import Preset


class PresetEchoesGoal(PresetTab, Ui_PresetEchoesGoal):
    _editor: PresetEditor

    def __init__(self, editor: PresetEditor):
        super().__init__()
        self.setupUi(self)
        self._editor = editor

        self.goal_layout.setAlignment(QtCore.Qt.AlignTop)
        self.skytemple_combo.setItemData(0, LayoutSkyTempleKeyMode.ALL_BOSSES)
        self.skytemple_combo.setItemData(1, LayoutSkyTempleKeyMode.ALL_GUARDIANS)
        self.skytemple_combo.setItemData(2, int)

        self.skytemple_combo.options_field_name = "layout_configuration_sky_temple_keys"
        self.skytemple_combo.currentIndexChanged.connect(self._on_sky_temple_key_combo_changed)
        self.skytemple_slider.valueChanged.connect(self._on_sky_temple_key_combo_slider_changed)

    @property
    def uses_patches_tab(self) -> bool:
        return False

    def _on_sky_temple_key_combo_changed(self):
        combo_enum = self.skytemple_combo.currentData()
        with self._editor:
            if combo_enum is int:
                self.skytemple_slider.setEnabled(True)
                self._editor.layout_configuration_sky_temple_keys = LayoutSkyTempleKeyMode(
                    self.skytemple_slider.value())
            else:
                self.skytemple_slider.setEnabled(False)
                self._editor.layout_configuration_sky_temple_keys = combo_enum

    def _on_sky_temple_key_combo_slider_changed(self):
        self.skytemple_slider_label.setText(str(self.skytemple_slider.value()))
        self._on_sky_temple_key_combo_changed()

    def on_preset_changed(self, preset: Preset):
        keys = preset.configuration.sky_temple_keys
        if isinstance(keys.value, int):
            self.skytemple_slider.setValue(keys.value)
            data = int
        else:
            data = keys
        set_combo_with_value(self.skytemple_combo, data)
