import dataclasses
import pytest
import uuid
from unittest.mock import MagicMock

from PySide6 import QtCore

from randovania.games.am2r.gui.preset_settings.am2r_goal_tab import PresetAM2RGoal
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.games.game import RandovaniaGame
from randovania.interface_common.preset_editor import PresetEditor

@pytest.mark.parametrize("prefer_metroids, prefer_bosses, expected_max_slider", [(False, False, 0), (False, True, 6), (True, False, 46), (True, True, 46)])
def test_preferred_dna(skip_qtbot, am2r_game_description, preset_manager, prefer_metroids: bool, prefer_bosses: bool, expected_max_slider: int):
    # Setup
    game = am2r_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, AM2RConfiguration)

    tab = PresetAM2RGoal(editor := PresetEditor(preset, options), am2r_game_description, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    assert tab.dna_slider.isEnabled() and tab.dna_slider.value() > 0
    initial_slider_value = tab.dna_slider.value()

    # Run
    tab.prefer_metroids_check.setChecked(prefer_metroids)
    slider_value_after_first_set = tab.dna_slider.value()
    tab.prefer_bosses_check.setChecked(prefer_bosses)
    tab._update_slider_max()

    # Assert
    if not prefer_metroids:
        assert slider_value_after_first_set == 0
    # The slider value should never increase from what it was before
    assert slider_value_after_first_set >= tab.dna_slider.value()
    assert tab.num_preferred_locations == expected_max_slider
    assert tab.dna_slider.maximum() == expected_max_slider
    assert tab.dna_slider.isEnabled() == (expected_max_slider > 0)
    assert editor.configuration.artifacts.prefer_metroids == prefer_metroids
    assert editor.configuration.artifacts.prefer_bosses == prefer_bosses
    # If default value in configuration is smaller than the max allowed value, it shouldn't increase
    expected_artifacts = expected_max_slider
    if initial_slider_value < expected_max_slider:
        expected_artifacts = initial_slider_value
    # Also, if the previous slider value is already 0, then that should be the final result
    if slider_value_after_first_set == 0:
        expected_artifacts = 0

    assert editor.configuration.artifacts.required_artifacts == expected_artifacts
    assert tab.dna_slider.value() == expected_artifacts
