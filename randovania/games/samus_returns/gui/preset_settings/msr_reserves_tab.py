from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.samus_returns.gui.generated.preset_msr_reserves_ui import Ui_PresetMSRReserves
from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetMSRReserves(PresetTab, Ui_PresetMSRReserves):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.energy_capacity_spin_box.valueChanged.connect(self._persist_capacity)
        self.aeion_capacity_spin_box.valueChanged.connect(self._persist_capacity)
        self.missile_capacity_spin_box.valueChanged.connect(self._persist_capacity)
        self.super_missile_capacity_spin_box.valueChanged.connect(self._persist_capacity)

    @classmethod
    def tab_title(cls) -> str:
        return "Reserve Tanks"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, MSRConfiguration)
        self.energy_capacity_spin_box.setValue(config.life_tank_size)
        self.aeion_capacity_spin_box.setValue(config.aeion_tank_size)
        self.missile_capacity_spin_box.setValue(config.missile_tank_size)
        self.super_missile_capacity_spin_box.setValue(config.super_missile_tank_size)

    def _persist_capacity(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("life_tank_size", int(self.energy_capacity_spin_box.value()))
            editor.set_configuration_field("aeion_tank_size", int(self.aeion_capacity_spin_box.value()))
            editor.set_configuration_field("missile_tank_size", int(self.missile_capacity_spin_box.value()))
            editor.set_configuration_field("super_missile_tank_size", int(self.super_missile_capacity_spin_box.value()))
