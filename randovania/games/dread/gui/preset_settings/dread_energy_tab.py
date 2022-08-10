from randovania.game_description.game_description import GameDescription
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.gui.generated.preset_dread_energy_ui import Ui_PresetDreadEnergy
from randovania.gui.lib import signal_handling
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class PresetDreadEnergy(PresetTab, Ui_PresetDreadEnergy):

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.energy_tank_capacity_spin_box.valueChanged.connect(self._persist_tank_capacity)
        signal_handling.on_checked(self.immediate_energy_parts_check, self._persist_immediate_energy_parts)
        signal_handling.on_checked(self.linear_damage_runs_check, self._persist_linear_damage_runs)
        self.linear_dps_spin_box.valueChanged.connect(self._persist_linear_dps)

    @classmethod
    def tab_title(cls) -> str:
        return "Energy"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        assert isinstance(config, DreadConfiguration)
        self.energy_tank_capacity_spin_box.setEnabled(config.immediate_energy_parts)
        self.energy_tank_capacity_spin_box.setValue(config.energy_per_tank)
        self.immediate_energy_parts_check.setChecked(config.immediate_energy_parts)
        self.linear_damage_runs_check.setChecked(config.linear_damage_runs)
        self.linear_dps_spin_box.setEnabled(config.linear_damage_runs)
        self.linear_dps_spin_box.setValue(config.linear_dps)

    def _persist_tank_capacity(self):
        with self._editor as editor:
            editor.set_configuration_field("energy_per_tank", int(self.energy_tank_capacity_spin_box.value()))

    def _persist_immediate_energy_parts(self, checked: bool):
        with self._editor as editor:
            editor.set_configuration_field("immediate_energy_parts", checked)

    def _persist_linear_dps(self):
        with self._editor as editor:
            editor.set_configuration_field("linear_dps", int(self.linear_dps_spin_box.value()))
    
    def _persist_linear_damage_runs(self, checked:bool):
        with self._editor as editor:
            editor.set_configuration_field("linear_damage_runs", checked)
