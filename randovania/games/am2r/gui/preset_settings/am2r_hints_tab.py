import dataclasses

from PySide6 import QtCore

from randovania.game_description.game_description import GameDescription
from randovania.games.am2r.gui.generated.preset_am2r_hints_ui import Ui_PresetAM2RHints
from randovania.games.am2r.layout.hint_configuration import ItemHintMode
from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class PresetAM2RHints(PresetTab, Ui_PresetAM2RHints):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.hint_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        for i, item_hint_mode in enumerate(ItemHintMode):
            self.hint_artifact_combo.setItemData(i, item_hint_mode)
            self.ice_beam_hint_combo.setItemData(i, item_hint_mode)

        self.hint_artifact_combo.currentIndexChanged.connect(self._on_art_combo_changed)
        self.ice_beam_hint_combo.currentIndexChanged.connect(self._on_ibeam_combo_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Hints"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    def _on_art_combo_changed(self, new_index: int):
        with self._editor as editor:
            editor.set_configuration_field(
                "hints",
                dataclasses.replace(editor.configuration.hints, artifacts=self.hint_artifact_combo.currentData()),
            )

    def _on_ibeam_combo_changed(self, new_index: int):
        with self._editor as editor:
            editor.set_configuration_field(
                "hints",
                dataclasses.replace(editor.configuration.hints, ice_beam=self.ice_beam_hint_combo.currentData()),
            )

    def on_preset_changed(self, preset: Preset):
        set_combo_with_value(self.hint_artifact_combo, preset.configuration.hints.artifacts)
        set_combo_with_value(self.ice_beam_hint_combo, preset.configuration.hints.ice_beam)
