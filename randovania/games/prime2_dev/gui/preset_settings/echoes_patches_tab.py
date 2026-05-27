from __future__ import annotations

from typing import TYPE_CHECKING

import randovania
from randovania.games.prime2_dev.gui.generated.preset_echoes_patches_ui import Ui_PresetEchoesPatches
from randovania.games.prime2_dev.layout.echoes_configuration import EchoesConfiguration, PracticeModMode
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetEchoesPatches(PresetTab, Ui_PresetEchoesPatches):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.practice_mod_description_label.setText(self.include_menu_mod_label.text().replace("color:#0000ff;", ""))
        for mode in PracticeModMode:
            self.practice_mod_mode_combo.addItem(mode.long_name, mode)

        for widget in [
            self.inverted_check,
            self.inverted_label,
            self.inverted_line,
        ]:
            widget.setVisible(randovania.is_dev_version())

        # Signals
        signal_handling.on_combo(self.practice_mod_mode_combo, self._on_practice_mod_mode_changed)
        self.inverted_check.stateChanged.connect(self._persist_option_then_notify("inverted_mode"))
        self.save_doors_check.stateChanged.connect(self._persist_option_then_notify("blue_save_doors"))

    @classmethod
    def tab_title(cls) -> str:
        return "Other"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, EchoesConfiguration)

        signal_handling.set_combo_with_value(self.practice_mod_mode_combo, config.practice_mod)
        self.inverted_check.setChecked(config.inverted_mode)
        self.save_doors_check.setChecked(config.blue_save_doors)

    def _on_practice_mod_mode_changed(self, value: PracticeModMode) -> None:
        with self._editor as editor:
            editor.set_configuration_field("practice_mod", value)
