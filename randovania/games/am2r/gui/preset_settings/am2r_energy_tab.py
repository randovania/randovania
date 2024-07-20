from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.am2r.gui.generated.preset_am2r_energy_ui import Ui_PresetAM2REnergy
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetAM2REnergy(PresetTab, Ui_PresetAM2REnergy):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.energy_tank_capacity_spin_box.valueChanged.connect(self._persist_tank_capacity)
        self.first_suit_spin_box.valueChanged.connect(self._persist_first_suit_dr)
        self.second_suit_spin_box.valueChanged.connect(self._persist_second_suit_dr)

    @classmethod
    def tab_title(cls) -> str:
        return "Energy"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        assert isinstance(config, AM2RConfiguration)
        self.energy_tank_capacity_spin_box.setValue(config.energy_per_tank)
        self.first_suit_spin_box.setValue(config.first_suit_dr)
        self.second_suit_spin_box.setValue(config.second_suit_dr)

    def _persist_tank_capacity(self):
        with self._editor as editor:
            editor.set_configuration_field("energy_per_tank", int(self.energy_tank_capacity_spin_box.value()))

    def _persist_first_suit_dr(self):
        with self._editor as editor:
            editor.set_configuration_field("first_suit_dr", int(self.first_suit_spin_box.value()))
        self.second_suit_spin_box.setMinimum(self.first_suit_spin_box.value())

    def _persist_second_suit_dr(self):
        with self._editor as editor:
            editor.set_configuration_field("second_suit_dr", int(self.second_suit_spin_box.value()))
        self.first_suit_spin_box.setMaximum(self.second_suit_spin_box.value())
