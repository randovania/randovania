import functools

from PySide6 import QtWidgets

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

        self._constant_damage_widgets = [
            ("constant_heat_damage", self.constant_heat_damage_check, self.constant_heat_damage_spin_box),
            ("constant_cold_damage", self.constant_cold_damage_check, self.constant_cold_damage_spin_box),
            ("constant_lava_damage", self.constant_lava_damage_check, self.constant_lava_damage_spin_box),
        ]

        self.energy_tank_capacity_spin_box.valueChanged.connect(self._persist_tank_capacity)
        signal_handling.on_checked(self.immediate_energy_parts_check, self._persist_immediate_energy_parts)
        for field_name, check, spin in self._constant_damage_widgets:
            signal_handling.on_checked(
                check,
                functools.partial(
                    self._persist_constant_environment_damage_enabled,
                    field_name, spin,
                )
            )
            spin.valueChanged.connect(self._persist_argument(field_name))

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

        for config_name, check, spin in self._constant_damage_widgets:
            config_value = getattr(config, config_name)
            constant_enabled = config_value is not None
            check.setChecked(constant_enabled)
            spin.setEnabled(constant_enabled)
            if constant_enabled:
                spin.setValue(config_value)

    def _persist_tank_capacity(self):
        with self._editor as editor:
            editor.set_configuration_field("energy_per_tank", int(self.energy_tank_capacity_spin_box.value()))

    def _persist_immediate_energy_parts(self, checked: bool):
        with self._editor as editor:
            editor.set_configuration_field("immediate_energy_parts", checked)

    def _persist_constant_environment_damage_enabled(self, field_name: str, spin: QtWidgets.QSpinBox, checked: bool):
        with self._editor as editor:
            editor.set_configuration_field(field_name, spin.value() if checked else None)
