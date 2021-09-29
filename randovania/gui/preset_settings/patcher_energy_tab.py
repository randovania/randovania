import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.gui.generated.preset_patcher_energy_ui import Ui_PresetPatcherEnergy
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset
from randovania.layout.prime1.prime_configuration import PrimeConfiguration
from randovania.layout.prime2.echoes_configuration import EchoesConfiguration


class PresetPatcherEnergy(PresetTab, Ui_PresetPatcherEnergy):

    def __init__(self, editor: PresetEditor, game_enum: RandovaniaGame):
        super().__init__(editor)
        self.setupUi(self)
        self.game_enum = game_enum

        self.energy_tank_capacity_spin_box.valueChanged.connect(self._persist_tank_capacity)
        signal_handling.on_checked(self.dangerous_tank_check, self._persist_dangerous_tank)

        if self.game_enum == RandovaniaGame.METROID_PRIME_ECHOES:
            config_fields = {
                field.name: field
                for field in dataclasses.fields(EchoesConfiguration)
            }
            self.varia_suit_spin_box.setMinimum(config_fields["varia_suit_damage"].metadata["min"])
            self.varia_suit_spin_box.setMaximum(config_fields["varia_suit_damage"].metadata["max"])
            self.dark_suit_spin_box.setMinimum(config_fields["dark_suit_damage"].metadata["min"])
            self.dark_suit_spin_box.setMaximum(config_fields["dark_suit_damage"].metadata["max"])

            signal_handling.on_checked(self.safe_zone_logic_heal_check, self._persist_safe_zone_logic_heal)
            self.safe_zone_regen_spin.valueChanged.connect(self._persist_safe_zone_regen)
            self.varia_suit_spin_box.valueChanged.connect(self._persist_float("varia_suit_damage"))
            self.dark_suit_spin_box.valueChanged.connect(self._persist_float("dark_suit_damage"))
        else:
            self.dark_aether_box.setVisible(False)
            self.safe_zone_box.setVisible(False)

        if self.game_enum == RandovaniaGame.METROID_PRIME:
            config_fields = {
                field.name: field
                for field in dataclasses.fields(PrimeConfiguration)
            }
            self.heated_damage_spin.setMinimum(config_fields["heat_damage"].metadata["min"])
            self.heated_damage_spin.setMaximum(config_fields["heat_damage"].metadata["max"])

            signal_handling.on_checked(self.progressive_damage_reduction_check, self._persist_progressive_damage)
            signal_handling.on_checked(self.heated_damage_varia_check, self._persist_heat_protection_only_varia)
            self.heated_damage_spin.valueChanged.connect(self._persist_float("heat_damage"))

        else:
            self.progressive_damage_reduction_check.setVisible(False)
            self.heated_damage_box.setVisible(False)

    @property
    def uses_patches_tab(self) -> bool:
        return True

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        self.energy_tank_capacity_spin_box.setValue(config.energy_per_tank)

        if self.game_enum == RandovaniaGame.METROID_PRIME_ECHOES:
            self.dangerous_tank_check.setChecked(config.dangerous_energy_tank)
            self.safe_zone_logic_heal_check.setChecked(config.safe_zone.fully_heal)
            self.safe_zone_regen_spin.setValue(config.safe_zone.heal_per_second)
            self.varia_suit_spin_box.setValue(config.varia_suit_damage)
            self.dark_suit_spin_box.setValue(config.dark_suit_damage)

        elif self.game_enum == RandovaniaGame.METROID_PRIME:
            self.progressive_damage_reduction_check.setChecked(config.progressive_damage_reduction)
            self.heated_damage_varia_check.setChecked(config.heat_protection_only_varia)
            self.heated_damage_spin.setValue(config.heat_damage)

    def _persist_tank_capacity(self):
        with self._editor as editor:
            editor.set_configuration_field("energy_per_tank", int(self.energy_tank_capacity_spin_box.value()))

    def _persist_safe_zone_regen(self):
        with self._editor as editor:
            safe_zone = dataclasses.replace(
                editor.configuration.safe_zone,
                heal_per_second=self.safe_zone_regen_spin.value()
            )
            editor.set_configuration_field("safe_zone", safe_zone)

    def _persist_safe_zone_logic_heal(self, checked: bool):
        with self._editor as editor:
            safe_zone = dataclasses.replace(
                editor.configuration.safe_zone,
                fully_heal=checked
            )
            editor.set_configuration_field("safe_zone", safe_zone)

    def _persist_progressive_damage(self, checked: bool):
        with self._editor as editor:
            editor.set_configuration_field("progressive_damage_reduction", checked)

    def _persist_heat_protection_only_varia(self, checked: bool):
        with self._editor as editor:
            editor.set_configuration_field("heat_protection_only_varia", checked)

    def _persist_dangerous_tank(self, checked: bool):
        with self._editor as editor:
            editor.set_configuration_field("dangerous_energy_tank", checked)

