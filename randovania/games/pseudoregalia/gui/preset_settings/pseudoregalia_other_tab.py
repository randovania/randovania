from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.pseudoregalia.gui.generated.preset_pseudoregalia_other_ui import Ui_PresetPseudoregaliaOther
from randovania.games.pseudoregalia.layout import PseudoregaliaConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetPseudoregaliaOther(PresetTab[PseudoregaliaConfiguration], Ui_PresetPseudoregaliaOther):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        # Signals
        self.goatling_shuffle_check.stateChanged.connect(self._persist_option_then_notify("goatling_shuffle"))
        self.chair_shuffle_check.stateChanged.connect(self._persist_option_then_notify("chair_shuffle"))
        self.note_shuffle_check.stateChanged.connect(self._persist_option_then_notify("note_shuffle"))

    @classmethod
    def tab_title(cls) -> str:
        return "Other"

    @classmethod
    def header_name(cls) -> str | None:
        return cls.GAME_MODIFICATIONS_HEADER

    def on_preset_changed(self, preset: Preset[PseudoregaliaConfiguration]) -> None:
        config = preset.configuration
        self.goatling_shuffle_check.setChecked(config.goatling_shuffle)
        self.chair_shuffle_check.setChecked(config.chair_shuffle)
        self.note_shuffle_check.setChecked(config.note_shuffle)
