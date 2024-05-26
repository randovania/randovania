from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.samus_returns.gui.generated.preset_msr_aeion_ui import Ui_PresetMSRAeion
from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetMSRAeion(PresetTab, Ui_PresetMSRAeion):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.aeion_capacity_spin_box.valueChanged.connect(self._persist_capacity)

    @classmethod
    def tab_title(cls) -> str:
        return "Aeion"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, MSRConfiguration)
        self.aeion_capacity_spin_box.setValue(config.starting_aeion)

    def _persist_capacity(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("starting_aeion", int(self.aeion_capacity_spin_box.value()))
