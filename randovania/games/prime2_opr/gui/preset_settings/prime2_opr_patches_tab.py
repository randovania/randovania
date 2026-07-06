from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime2_opr.gui.generated.preset_prime2_opr_patches_ui import Ui_PresetEchoesOPRPatches
from randovania.games.prime2_opr.layout.prime2_opr_configuration import EchoesOPRConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetEchoesOPRPatches(PresetTab[EchoesOPRConfiguration], Ui_PresetEchoesOPRPatches):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.include_practice_mod_label.setText(self.include_practice_mod_label.text().replace("color:#0000ff;", ""))

        for widget in [
            self.inverted_check,
            self.inverted_label,
            self.inverted_line,
        ]:
            widget.setVisible(self._editor._options.experimental_settings)

        # Signals
        self.include_practice_mod_check.stateChanged.connect(self._persist_bool("practice_mod"))
        self.inverted_check.stateChanged.connect(self._persist_bool("inverted_mode"))
        self.save_doors_check.stateChanged.connect(self._persist_bool("blue_save_doors"))
        self.portal_rando_check.stateChanged.connect(self._persist_bool("portal_rando"))

    @classmethod
    def tab_title(cls) -> str:
        return "Other"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def on_preset_changed(self, preset: Preset[EchoesOPRConfiguration]) -> None:
        config = preset.configuration

        self.include_practice_mod_check.setChecked(config.practice_mod)
        self.inverted_check.setChecked(config.inverted_mode)
        self.save_doors_check.setChecked(config.blue_save_doors)
        self.portal_rando_check.setChecked(config.portal_rando)
