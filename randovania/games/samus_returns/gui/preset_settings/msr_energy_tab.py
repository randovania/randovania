from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
from randovania.gui.generated.preset_msr_energy_ui import Ui_PresetMSREnergy
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetMSREnergy(PresetTab, Ui_PresetMSREnergy):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.energy_tank_capacity_spin_box.valueChanged.connect(self._persist_tank_capacity)
        self.energy_capacity_spin_box.valueChanged.connect(self._persist_capacity)

    @classmethod
    def tab_title(cls) -> str:
        return "Energy"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, MSRConfiguration)
        self.energy_tank_capacity_spin_box.setValue(config.energy_per_tank)
        self.energy_capacity_spin_box.setValue(config.starting_energy)

    def _persist_tank_capacity(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("energy_per_tank", int(self.energy_tank_capacity_spin_box.value()))

    def _persist_capacity(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("starting_energy", int(self.energy_capacity_spin_box.value()))
