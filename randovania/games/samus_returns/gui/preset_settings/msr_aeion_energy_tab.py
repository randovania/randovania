from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from randovania.games.samus_returns.gui.generated.preset_msr_aeion_and_energy_ui import Ui_PresetMSRAeionAndEnergy
from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetMSRAeionAndEnergy(PresetTab, Ui_PresetMSRAeionAndEnergy):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.aeion_capacity_spin_box.valueChanged.connect(self._persist_capacity)

        self._constant_damage_widgets = [
            ("constant_heat_damage", self.constant_heat_damage_check, self.constant_heat_damage_spin_box),
            ("constant_lava_damage", self.constant_lava_damage_check, self.constant_lava_damage_spin_box),
        ]

        for field_name, check, spin in self._constant_damage_widgets:
            signal_handling.on_checked(
                check,
                functools.partial(
                    self._persist_constant_environment_damage_enabled,
                    field_name,
                    spin,
                ),
            )
            spin.valueChanged.connect(self._persist_argument(field_name))

    @classmethod
    def tab_title(cls) -> str:
        return "Aeion & Energy"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, MSRConfiguration)
        self.aeion_capacity_spin_box.setValue(config.starting_aeion)

        for config_name, check, spin in self._constant_damage_widgets:
            config_value = getattr(config, config_name)
            constant_enabled = config_value is not None
            check.setChecked(constant_enabled)
            spin.setEnabled(constant_enabled)
            if constant_enabled:
                spin.setValue(config_value)

    def _persist_capacity(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("starting_aeion", int(self.aeion_capacity_spin_box.value()))

    def _persist_constant_environment_damage_enabled(
        self, field_name: str, spin: QtWidgets.QSpinBox, checked: bool
    ) -> None:
        with self._editor as editor:
            editor.set_configuration_field(field_name, spin.value() if checked else None)
