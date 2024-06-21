from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.games.fusion.layout.fusion_configuration import FusionConfiguration
from randovania.games.game import RandovaniaGame
from randovania.games.planets_zebeth.layout.planets_zebeth_configuration import PlanetsZebethConfiguration
from randovania.games.prime1.layout.prime_configuration import DamageReduction, IngameDifficulty, PrimeConfiguration
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration
from randovania.gui.generated.preset_patcher_energy_ui import Ui_PresetPatcherEnergy
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetPatcherEnergy(PresetTab, Ui_PresetPatcherEnergy):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager) -> None:
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)
        self.game_enum = game_description.game

        self.energy_tank_capacity_spin_box.valueChanged.connect(self._persist_tank_capacity)
        signal_handling.on_checked(self.dangerous_tank_check, self._persist_dangerous_tank)

        # Aether Damage

        if self.game_enum == RandovaniaGame.METROID_PRIME_ECHOES:
            config_fields = {field.name: field for field in dataclasses.fields(EchoesConfiguration)}
            self.varia_suit_spin_box.setMinimum(config_fields["varia_suit_damage"].metadata["min"])
            self.varia_suit_spin_box.setMaximum(config_fields["varia_suit_damage"].metadata["max"])
            self.dark_suit_spin_box.setMinimum(config_fields["dark_suit_damage"].metadata["min"])
            self.dark_suit_spin_box.setMaximum(config_fields["dark_suit_damage"].metadata["max"])

            signal_handling.on_checked(self.safe_zone_logic_heal_check, self._persist_safe_zone_logic_heal)
            self.safe_zone_regen_spin.valueChanged.connect(self._persist_safe_zone_regen)
            self.varia_suit_spin_box.valueChanged.connect(self._persist_argument("varia_suit_damage"))
            self.dark_suit_spin_box.valueChanged.connect(self._persist_argument("dark_suit_damage"))
        else:
            self.dark_aether_box.setVisible(False)
            self.safe_zone_box.setVisible(False)
            self.dangerous_tank_check.setVisible(False)

        # Heat Damage

        if self.game_enum == RandovaniaGame.METROID_PRIME:
            config_fields = {field.name: field for field in dataclasses.fields(PrimeConfiguration)}
            self.heated_damage_spin.setMinimum(config_fields["heat_damage"].metadata["min"])
            self.heated_damage_spin.setMaximum(config_fields["heat_damage"].metadata["max"])

            for i, difficulty in enumerate(DamageReduction):
                self.damage_reduction_combo.setItemData(i, difficulty)
            signal_handling.on_combo(self.damage_reduction_combo, self._persist_suit_damage)
            self.heated_damage_spin.valueChanged.connect(self._persist_argument("heat_damage"))

        else:
            self.damage_reduction_box.setVisible(False)
            self.heated_damage_box.setVisible(False)

        # In-Game Difficulty

        if self.game_enum == RandovaniaGame.METROID_PRIME:
            for i, difficulty in enumerate(IngameDifficulty):
                self.ingame_difficulty_combo.setItemData(i, difficulty)
            signal_handling.on_combo(self.ingame_difficulty_combo, self._persist_ingame_difficulty)

        else:
            self.ingame_difficulty_box.setVisible(False)

    @classmethod
    def tab_title(cls) -> str:
        return "Energy"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(
            config,
            PrimeConfiguration
            | EchoesConfiguration
            | CorruptionConfiguration
            | AM2RConfiguration
            | FusionConfiguration
            | PlanetsZebethConfiguration,
        )
        self.energy_tank_capacity_spin_box.setValue(config.energy_per_tank)

        if self.game_enum == RandovaniaGame.METROID_PRIME_ECHOES:
            assert isinstance(config, EchoesConfiguration)
            self.dangerous_tank_check.setChecked(config.dangerous_energy_tank)
            self.safe_zone_logic_heal_check.setChecked(config.safe_zone.fully_heal)
            self.safe_zone_regen_spin.setValue(config.safe_zone.heal_per_second)
            self.varia_suit_spin_box.setValue(config.varia_suit_damage)
            self.dark_suit_spin_box.setValue(config.dark_suit_damage)

        elif self.game_enum == RandovaniaGame.METROID_PRIME:
            assert isinstance(config, PrimeConfiguration)
            signal_handling.set_combo_with_value(self.damage_reduction_combo, config.damage_reduction)
            self.heated_damage_spin.setValue(config.heat_damage)
            signal_handling.set_combo_with_value(self.ingame_difficulty_combo, config.ingame_difficulty)

    def _persist_tank_capacity(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("energy_per_tank", int(self.energy_tank_capacity_spin_box.value()))

    def _persist_safe_zone_regen(self) -> None:
        with self._editor as editor:
            configuration = editor.configuration
            assert isinstance(configuration, EchoesConfiguration)
            safe_zone = dataclasses.replace(configuration.safe_zone, heal_per_second=self.safe_zone_regen_spin.value())
            editor.set_configuration_field("safe_zone", safe_zone)

    def _persist_safe_zone_logic_heal(self, checked: bool) -> None:
        with self._editor as editor:
            configuration = editor.configuration
            assert isinstance(configuration, EchoesConfiguration)
            safe_zone = dataclasses.replace(configuration.safe_zone, fully_heal=checked)
            editor.set_configuration_field("safe_zone", safe_zone)

    def _persist_suit_damage(self, value: DamageReduction) -> None:
        with self._editor as editor:
            editor.set_configuration_field("damage_reduction", value)

    def _persist_dangerous_tank(self, checked: bool) -> None:
        with self._editor as editor:
            editor.set_configuration_field("dangerous_energy_tank", checked)

    def _persist_ingame_difficulty(self, value: IngameDifficulty) -> None:
        with self._editor as editor:
            editor.set_configuration_field("ingame_difficulty", value)
