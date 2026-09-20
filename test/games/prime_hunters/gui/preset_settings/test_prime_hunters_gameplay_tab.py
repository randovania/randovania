from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

from randovania.games.prime_hunters.gui.preset_settings.prime_hunters_gameplay_tab import PresetHuntersGameplay
from randovania.games.prime_hunters.layout.prime_hunters_configuration import HuntersConfiguration
from randovania.interface_common.preset_editor import PresetEditor


def test_energy_increase(skip_qtbot, prime_hunters_game_description, preset_manager):
    game = prime_hunters_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("5be21aac-ecac-4526-b5bb-a23b743ec5c9"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, HuntersConfiguration)

    tab = PresetHuntersGameplay(editor := PresetEditor(preset, options), prime_hunters_game_description, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    tab.energy_capacity_spin_box.setValue(222)
    tab.on_preset_changed(editor.create_custom_preset_with())

    configuration = editor.configuration
    assert isinstance(configuration, HuntersConfiguration)
    assert configuration.starting_energy == base_configuration.starting_energy + 123


def test_skip_planet_intros(skip_qtbot, prime_hunters_game_description, preset_manager):
    game = prime_hunters_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("5be21aac-ecac-4526-b5bb-a23b743ec5c9"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, HuntersConfiguration)

    tab = PresetHuntersGameplay(editor := PresetEditor(preset, options), prime_hunters_game_description, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    tab.skip_planet_intros_check.setChecked(True)
    tab.on_preset_changed(editor.create_custom_preset_with())

    configuration = editor.configuration
    assert isinstance(configuration, HuntersConfiguration)
    assert configuration.skip_planet_intros is True
