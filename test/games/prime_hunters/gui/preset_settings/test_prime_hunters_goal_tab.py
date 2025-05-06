from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

import pytest

from randovania.games.prime_hunters.gui.preset_settings.prime_hunters_goal_tab import PresetHuntersGoal
from randovania.games.prime_hunters.layout.prime_hunters_configuration import HuntersConfiguration
from randovania.interface_common.preset_editor import PresetEditor


@pytest.mark.parametrize(
    ("prefer_bosses", "expected_max_slider"),
    [(False, 8), (True, 8)],
)
def test_preferred_octoliths(
    skip_qtbot,
    prime_hunters_game_description,
    preset_manager,
    prefer_bosses: bool,
    expected_max_slider: int,
):
    # Setup
    game = prime_hunters_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, HuntersConfiguration)

    tab = PresetHuntersGoal(editor := PresetEditor(preset, options), prime_hunters_game_description, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    assert tab.placed_slider.isEnabled()
    assert tab.placed_slider.value() > 0
    initial_slider_value = tab.placed_slider.value()

    # Run
    slider_value_after_first_set = tab.placed_slider.value()
    tab._update_slider_max()

    # Assert
    if not prefer_bosses:
        assert slider_value_after_first_set == 8
    # The slider value should never increase from what it was before
    assert slider_value_after_first_set >= tab.placed_slider.value()
    assert tab.placed_slider.maximum() == expected_max_slider
    assert tab.placed_slider.isEnabled() == (expected_max_slider > 0)

    configuration = editor.configuration
    assert isinstance(configuration, HuntersConfiguration)
    # If default value in configuration is smaller than the max allowed value, it shouldn't increase
    expected_octoliths = expected_max_slider
    if initial_slider_value < expected_max_slider:
        expected_octoliths = initial_slider_value
    # Also, if the previous slider value is already 0, then that should be the final result
    if slider_value_after_first_set == 0:
        expected_octoliths = 0

    assert configuration.octoliths.placed_octoliths == expected_octoliths
    assert tab.placed_slider.value() == expected_octoliths
