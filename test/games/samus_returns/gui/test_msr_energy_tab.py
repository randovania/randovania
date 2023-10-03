from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

from randovania.games.samus_returns.gui.preset_settings.msr_energy_tab import PresetMSREnergy
from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
from randovania.interface_common.preset_editor import PresetEditor


def test_increase_energy(skip_qtbot, msr_game_description, preset_manager):
    game = msr_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, MSRConfiguration)

    tab = PresetMSREnergy(editor := PresetEditor(preset, options), msr_game_description, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    tab.energy_tank_capacity_spin_box.stepUp()
    tab.energy_capacity_spin_box.stepUp()
    tab.on_preset_changed(editor.create_custom_preset_with())

    configuration = editor.configuration
    assert isinstance(configuration, MSRConfiguration)
    assert configuration.energy_per_tank == base_configuration.energy_per_tank + 1
    assert configuration.starting_energy == base_configuration.starting_energy + 1
