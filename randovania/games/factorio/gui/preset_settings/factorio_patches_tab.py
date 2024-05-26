from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.factorio.gui.generated.preset_factorio_patches_ui import Ui_PresetFactorioPatches
from randovania.games.factorio.layout import FactorioConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetFactorioPatches(PresetTab, Ui_PresetFactorioPatches):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        # Signals
        self.full_tech_tree_check.stateChanged.connect(self._persist_option_then_notify("full_tech_tree"))

    @classmethod
    def tab_title(cls) -> str:
        return "Changes"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, FactorioConfiguration)
        self.full_tech_tree_check.setChecked(config.full_tech_tree)
