from PySide2 import QtCore

from randovania.gui.generated.preset_echoes_goal_ui import Ui_PresetEchoesGoal
from randovania.gui.lib.common_qt_lib import set_combo_with_value
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.prime2.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.layout.preset import Preset


class PresetEchoesGoal(PresetTab, Ui_PresetEchoesGoal):

    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignTop)
        self.skytemple_combo.setItemData(0, LayoutSkyTempleKeyMode.ALL_BOSSES)
        self.skytemple_combo.setItemData(1, LayoutSkyTempleKeyMode.ALL_GUARDIANS)
        self.skytemple_combo.setItemData(2, int)

        self.skytemple_combo.options_field_name = "layout_configuration_sky_temple_keys"
        self.skytemple_combo.currentIndexChanged.connect(self._on_sky_temple_key_combo_changed)
        self.skytemple_slider.valueChanged.connect(self._on_sky_temple_key_combo_slider_changed)

        # Default to False, since the slider defaults to a non-collect keys value.
        self._set_slider_visible(False)

    @property
    def uses_patches_tab(self) -> bool:
        return False

    def _set_slider_visible(self, visible: bool):
        for w in [self.skytemple_slider, self.skytemple_slider_label]:
            w.setVisible(visible)

    def _on_sky_temple_key_combo_changed(self):
        combo_enum = self.skytemple_combo.currentData()
        with self._editor as editor:
            if combo_enum is int:
                new_value = LayoutSkyTempleKeyMode(self.skytemple_slider.value())
                self._set_slider_visible(True)
            else:
                new_value = combo_enum
                self._set_slider_visible(False)

            editor.layout_configuration_sky_temple_keys = new_value

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
