from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.prime1.gui.generated.preset_prime_hints_ui import Ui_PresetPrimeHints
from randovania.games.prime1.layout.hint_configuration import ArtifactHintMode, PhazonSuitHintMode
from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetPrimeHints(PresetTab, Ui_PresetPrimeHints):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.hint_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        for i, art_hint_mode in enumerate(ArtifactHintMode):
            self.hint_artifact_combo.setItemData(i, art_hint_mode)
        self.hint_artifact_combo.currentIndexChanged.connect(self._on_art_combo_changed)

        for i, psuit_hint_mode in enumerate(PhazonSuitHintMode):
            self.phazon_suit_hint_combo.setItemData(i, psuit_hint_mode)
        self.phazon_suit_hint_combo.currentIndexChanged.connect(self._on_psuit_combo_changed)

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

    def _on_psuit_combo_changed(self, new_index: int):
        with self._editor as editor:
            editor.set_configuration_field(
                "hints",
                dataclasses.replace(editor.configuration.hints, phazon_suit=self.phazon_suit_hint_combo.currentData()),
            )

    def on_preset_changed(self, preset: Preset):
        set_combo_with_value(self.hint_artifact_combo, preset.configuration.hints.artifacts)
        set_combo_with_value(self.phazon_suit_hint_combo, preset.configuration.hints.phazon_suit)
