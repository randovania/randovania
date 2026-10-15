from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.games.prime2.gui.generated.preset_echoes_energy_ui import Ui_PresetEchoesEnergy
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2_opr.layout.prime2_opr_configuration import EchoesOPRConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetEchoesEnergy(PresetTab[EchoesConfiguration | EchoesOPRConfiguration], Ui_PresetEchoesEnergy):
    def __init__(
        self,
        editor: PresetEditor[EchoesConfiguration | EchoesOPRConfiguration],
        game_description: GameDescription,
        window_manager: WindowManager,
    ) -> None:
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.energy_tank_capacity_spin_box.valueChanged.connect(self._persist_tank_capacity)
        signal_handling.on_checked(self.dangerous_tank_check, self._persist_dangerous_tank)

        # Dark Aether Damage
        config_fields = {field.name: field for field in dataclasses.fields(editor.configuration)}
        self.varia_suit_spin_box.setMinimum(config_fields["varia_suit_damage"].metadata["min"])
        self.varia_suit_spin_box.setMaximum(config_fields["varia_suit_damage"].metadata["max"])
        self.dark_suit_spin_box.setMinimum(config_fields["dark_suit_damage"].metadata["min"])
        self.dark_suit_spin_box.setMaximum(config_fields["dark_suit_damage"].metadata["max"])

        # Safe Zones
        signal_handling.on_checked(self.safe_zone_logic_heal_check, self._persist_safe_zone_logic_heal)
        self.safe_zone_regen_spin.valueChanged.connect(self._persist_safe_zone_regen)
        self.varia_suit_spin_box.valueChanged.connect(self._persist_float("varia_suit_damage"))
        self.dark_suit_spin_box.valueChanged.connect(self._persist_float("dark_suit_damage"))

    @classmethod
    def tab_title(cls) -> str:
        return "Energy"

    @classmethod
    def header_name(cls) -> str | None:
        return cls.GAME_MODIFICATIONS_HEADER

    def on_preset_changed(self, preset: Preset[EchoesConfiguration | EchoesOPRConfiguration]) -> None:
        config = preset.configuration

        self.energy_tank_capacity_spin_box.setValue(config.energy_per_tank)
        self.dangerous_tank_check.setChecked(config.dangerous_energy_tank)

        self.safe_zone_logic_heal_check.setChecked(config.safe_zone.fully_heal)
        self.safe_zone_regen_spin.setValue(config.safe_zone.heal_per_second)

        self.varia_suit_spin_box.setValue(config.varia_suit_damage)
        self.dark_suit_spin_box.setValue(config.dark_suit_damage)

    def _persist_tank_capacity(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("energy_per_tank", int(self.energy_tank_capacity_spin_box.value()))

    def _persist_safe_zone_regen(self) -> None:
        with self._editor as editor:
            configuration = editor.configuration
            safe_zone = dataclasses.replace(configuration.safe_zone, heal_per_second=self.safe_zone_regen_spin.value())
            editor.set_configuration_field("safe_zone", safe_zone)

    def _persist_safe_zone_logic_heal(self, checked: bool) -> None:
        with self._editor as editor:
            configuration = editor.configuration
            safe_zone = dataclasses.replace(configuration.safe_zone, fully_heal=checked)
            editor.set_configuration_field("safe_zone", safe_zone)

    def _persist_dangerous_tank(self, checked: bool) -> None:
        with self._editor as editor:
            editor.set_configuration_field("dangerous_energy_tank", checked)
