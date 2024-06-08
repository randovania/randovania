from __future__ import annotations

from typing import TYPE_CHECKING

import randovania
from randovania.games.prime2.gui.generated.preset_echoes_patches_ui import Ui_PresetEchoesPatches
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.layout.base.dock_rando_configuration import DockRandoMode

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetEchoesPatches(PresetTab, Ui_PresetEchoesPatches):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.include_menu_mod_label.setText(self.include_menu_mod_label.text().replace("color:#0000ff;", ""))
        for widget in [
            self.inverted_check,
            self.inverted_label,
            self.inverted_line,
            self.portal_rando_check,
            self.portal_rando_label,
            self.portal_rando_line,
        ]:
            widget.setVisible(randovania.is_dev_version())

        # Signals
        self.warp_to_start_check.stateChanged.connect(self._persist_option_then_notify("warp_to_start"))
        self.include_menu_mod_check.stateChanged.connect(self._persist_option_then_notify("menu_mod"))
        self.new_patcher_check.stateChanged.connect(self._persist_option_then_notify("use_new_patcher"))
        self.portal_rando_check.stateChanged.connect(self._persist_option_then_notify("portal_rando"))
        self.inverted_check.stateChanged.connect(self._persist_option_then_notify("inverted_mode"))
        self.save_doors_check.stateChanged.connect(self._persist_option_then_notify("blue_save_doors"))

    @classmethod
    def tab_title(cls) -> str:
        return "Other"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        assert isinstance(config, EchoesConfiguration)
        self.warp_to_start_check.setChecked(config.warp_to_start)
        self.include_menu_mod_check.setChecked(config.menu_mod)
        self.new_patcher_check.setChecked(config.use_new_patcher)
        self.new_patcher_check.setEnabled(config.dock_rando.mode == DockRandoMode.VANILLA)
        self.portal_rando_check.setEnabled(config.use_new_patcher)
        self.portal_rando_check.setChecked(config.portal_rando)
        self.inverted_check.setEnabled(config.use_new_patcher)
        self.inverted_check.setChecked(config.inverted_mode)
        self.save_doors_check.setChecked(config.blue_save_doors)
