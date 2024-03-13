import dataclasses

from PySide6 import QtCore

from randovania.game_description.game_description import GameDescription
from randovania.games.samus_returns.layout.hint_configuration import ItemHintMode
from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
from randovania.gui.generated.preset_msr_hints_ui import Ui_PresetMSRHints
from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class PresetMSRHints(PresetTab, Ui_PresetMSRHints):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.hint_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        for i, item_hint_mode in enumerate(ItemHintMode):
            self.hint_artifact_combo.setItemData(i, item_hint_mode)

        self.hint_artifact_combo.currentIndexChanged.connect(self._on_art_combo_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Hints"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    def _on_art_combo_changed(self, new_index: int) -> None:
        with self._editor as editor:
            editor.set_configuration_field(
                "hints",
                dataclasses.replace(editor.configuration.hints, artifacts=self.hint_artifact_combo.currentData()),
            )

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, MSRConfiguration)
        set_combo_with_value(self.hint_artifact_combo, preset.configuration.hints.artifacts)
