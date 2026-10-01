from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

from randovania.games.prime_hunters.gui.preset_settings.prime_hunters_goal_tab import PresetHuntersGoal
from randovania.games.prime_hunters.layout.prime_hunters_configuration import HuntersConfiguration
from randovania.interface_common.preset_editor import PresetEditor


def test_restricted_placement(
    skip_qtbot,
    prime_hunters_game_description,
    preset_manager,
):
    # Setup
    game = prime_hunters_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("5be21aac-ecac-4526-b5bb-a23b743ec5c9"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, HuntersConfiguration)

    tab = PresetHuntersGoal(editor := PresetEditor(preset, options), prime_hunters_game_description, MagicMock())
    assert isinstance(editor.configuration, HuntersConfiguration)
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)
    octolith_count = editor.configuration.octoliths.placed_octoliths

    tab.free_placement_radiobutton.setChecked(True)

    # Run
    tab.restrict_placement_radiobutton.setChecked(True)

    # Assert
    assert tab.restrict_placement_radiobutton.isChecked()
    assert editor.configuration.octoliths.placed_octoliths == octolith_count


def test_free_placement(
    skip_qtbot,
    prime_hunters_game_description,
    preset_manager,
):
    # Setup
    game = prime_hunters_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("5be21aac-ecac-4526-b5bb-a23b743ec5c9"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, HuntersConfiguration)

    tab = PresetHuntersGoal(editor := PresetEditor(preset, options), prime_hunters_game_description, MagicMock())
    assert isinstance(editor.configuration, HuntersConfiguration)
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)
    octolith_count = editor.configuration.octoliths.placed_octoliths
    tab.restrict_placement_radiobutton.setChecked(True)

    # Run
    tab.free_placement_radiobutton.setChecked(True)

    # Assert
    assert tab.free_placement_radiobutton.isChecked()
    assert editor.configuration.octoliths.placed_octoliths == octolith_count
