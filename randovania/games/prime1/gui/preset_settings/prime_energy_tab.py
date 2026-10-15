from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.games.prime1.gui.generated.preset_prime_energy_ui import Ui_PresetPrimeEnergy
from randovania.games.prime1.layout.prime_configuration import DamageReduction, IngameDifficulty, PrimeConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetPrimeEnergy(PresetTab[PrimeConfiguration], Ui_PresetPrimeEnergy):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager) -> None:
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.energy_tank_capacity_spin_box.valueChanged.connect(self._persist_tank_capacity)

        # Heat Damage
        config_fields = {field.name: field for field in dataclasses.fields(PrimeConfiguration)}
        self.heated_damage_spin.setMinimum(config_fields["heat_damage"].metadata["min"])
        self.heated_damage_spin.setMaximum(config_fields["heat_damage"].metadata["max"])

        # Damage Reduction
        for i, reduction in enumerate(DamageReduction):
            self.damage_reduction_combo.setItemData(i, reduction)
        signal_handling.on_combo(self.damage_reduction_combo, self._persist_suit_damage)
        self.heated_damage_spin.valueChanged.connect(self._persist_float("heat_damage"))

        # In-Game Difficulty
        for i, difficulty in enumerate(IngameDifficulty):
            self.ingame_difficulty_combo.setItemData(i, difficulty)
        signal_handling.on_combo(self.ingame_difficulty_combo, self._persist_ingame_difficulty)

    @classmethod
    def tab_title(cls) -> str:
        return "Energy"

    @classmethod
    def header_name(cls) -> str | None:
        return cls.GAME_MODIFICATIONS_HEADER

    def on_preset_changed(self, preset: Preset[PrimeConfiguration]) -> None:
        config = preset.configuration

        self.energy_tank_capacity_spin_box.setValue(config.energy_per_tank)
        signal_handling.set_combo_with_value(self.damage_reduction_combo, config.damage_reduction)
        self.heated_damage_spin.setValue(config.heat_damage)
        signal_handling.set_combo_with_value(self.ingame_difficulty_combo, config.ingame_difficulty)

    def _persist_tank_capacity(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("energy_per_tank", int(self.energy_tank_capacity_spin_box.value()))

    def _persist_suit_damage(self, value: DamageReduction) -> None:
        with self._editor as editor:
            editor.set_configuration_field("damage_reduction", value)

    def _persist_ingame_difficulty(self, value: IngameDifficulty) -> None:
        with self._editor as editor:
            editor.set_configuration_field("ingame_difficulty", value)
