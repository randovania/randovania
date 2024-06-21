from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

import pytest

from randovania.games.planets_zebeth.gui.preset_settings.planets_zebeth_goal_tab import PresetPlanetsZebethGoal
from randovania.games.planets_zebeth.layout.planets_zebeth_configuration import PlanetsZebethConfiguration
from randovania.interface_common.preset_editor import PresetEditor


@pytest.mark.parametrize(
    ("vanilla_tourian_keys", "expected_max_slider"),
    [(True, 2), (False, 9)],
)
def test_keys(
    skip_qtbot,
    planets_zebeth_game_description,
    preset_manager,
    vanilla_tourian_keys: bool,
    expected_max_slider: int,
):
    # Setup
    game = planets_zebeth_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, PlanetsZebethConfiguration)

    tab = PresetPlanetsZebethGoal(editor := PresetEditor(preset, options), planets_zebeth_game_description, MagicMock())
    assert isinstance(editor.configuration, PlanetsZebethConfiguration)
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    assert not tab.keys_slider.isEnabled()
    assert tab.keys_slider.value() == 2
    initial_slider_value = tab.keys_slider.value()

    # Run
    tab.vanilla_tourian_keys_check.setChecked(vanilla_tourian_keys)
    slider_value_after_first_set = tab.keys_slider.value()
    tab._update_slider()

    # Assert
    # The slider value should never increase from what it was before
    assert slider_value_after_first_set >= tab.keys_slider.value()
    assert tab.keys_slider.value() == 2
    assert not tab.keys_slider.isEnabled() == vanilla_tourian_keys
    assert editor.configuration.artifacts.vanilla_tourian_keys == vanilla_tourian_keys
    # If default value in configuration is smaller than the max allowed value, it shouldn't increase
    expected_artifacts = expected_max_slider
    if initial_slider_value < expected_max_slider:
        expected_artifacts = initial_slider_value
    # Also, if the previous slider value is already 0, then that should be the final result
    if slider_value_after_first_set == 0:
        expected_artifacts = 0

    assert editor.configuration.artifacts.required_artifacts == expected_artifacts
    assert tab.keys_slider.value() == expected_artifacts
