import dataclasses

from PySide6 import QtCore

from randovania.games.prime2.layout.hint_configuration import SkyTempleKeyHintMode
from randovania.gui.generated.preset_echoes_hints_ui import Ui_PresetEchoesHints
from randovania.gui.lib.common_qt_lib import set_combo_with_value
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class PresetEchoesHints(PresetTab, Ui_PresetEchoesHints):

    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        self.setupUi(self)

        self.hint_layout.setAlignment(QtCore.Qt.AlignTop)

        for i, stk_hint_mode in enumerate(SkyTempleKeyHintMode):
            self.hint_sky_temple_key_combo.setItemData(i, stk_hint_mode)

        self.hint_sky_temple_key_combo.currentIndexChanged.connect(self._on_stk_combo_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Hints"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    def _on_stk_combo_changed(self, new_index: int):
        with self._editor as editor:
            editor.set_configuration_field(
                "hints",
                dataclasses.replace(editor.configuration.hints,
                                    sky_temple_keys=self.hint_sky_temple_key_combo.currentData()))

    def on_preset_changed(self, preset: Preset):
        set_combo_with_value(self.hint_sky_temple_key_combo, preset.configuration.hints.sky_temple_keys)
