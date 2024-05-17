from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

import pytest

from randovania.games.am2r.gui.preset_settings.am2r_goal_tab import PresetAM2RGoal
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.interface_common.preset_editor import PresetEditor


@pytest.mark.parametrize(
    ("prefer_metroids", "prefer_bosses", "expected_max_slider"),
    [(False, False, 0), (False, True, 6), (True, False, 46), (True, True, 46)],
)
def test_preferred_dna(
    skip_qtbot,
    am2r_game_description,
    preset_manager,
    prefer_metroids: bool,
    prefer_bosses: bool,
    expected_max_slider: int,
):
    # Setup
    game = am2r_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, AM2RConfiguration)

    tab = PresetAM2RGoal(editor := PresetEditor(preset, options), am2r_game_description, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    assert tab.placed_slider.isEnabled()
    assert tab.placed_slider.value() > 0
    initial_slider_value = tab.placed_slider.value()

    # Run
    tab.prefer_metroids_check.setChecked(prefer_metroids)
    slider_value_after_first_set = tab.placed_slider.value()
    tab.prefer_bosses_check.setChecked(prefer_bosses)
    tab._update_slider_max()

    # Assert
    if not prefer_metroids:
        assert slider_value_after_first_set == 0
    # The slider value should never increase from what it was before
    assert slider_value_after_first_set >= tab.placed_slider.value()
    assert tab.num_preferred_locations == expected_max_slider
    assert tab.placed_slider.maximum() == expected_max_slider
    assert tab.placed_slider.isEnabled() == (expected_max_slider > 0)
    assert editor.configuration.artifacts.prefer_metroids == prefer_metroids
    assert editor.configuration.artifacts.prefer_bosses == prefer_bosses
    # If default value in configuration is smaller than the max allowed value, it shouldn't increase
    expected_artifacts = expected_max_slider
    if initial_slider_value < expected_max_slider:
        expected_artifacts = initial_slider_value
    # Also, if the previous slider value is already 0, then that should be the final result
    if slider_value_after_first_set == 0:
        expected_artifacts = 0

    assert editor.configuration.artifacts.placed_artifacts == expected_artifacts
    assert tab.placed_slider.value() == expected_artifacts


def test_restricted_placement(
    skip_qtbot,
    am2r_game_description,
    preset_manager,
):
    # Setup
    game = am2r_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, AM2RConfiguration)

    tab = PresetAM2RGoal(editor := PresetEditor(preset, options), am2r_game_description, MagicMock())
    assert isinstance(editor.configuration, AM2RConfiguration)
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)
    artifact_count = editor.configuration.artifacts.placed_artifacts
    tab.free_placement_radiobutton.setChecked(True)

    # Run
    tab.restrict_placement_radiobutton.setChecked(True)

    # Assert
    assert tab.prefer_metroids_check.isEnabled()
    assert tab.prefer_bosses_check.isEnabled()
    assert tab.restrict_placement_radiobutton.isChecked()
    assert editor.configuration.artifacts.placed_artifacts == artifact_count


def test_free_placement(
    skip_qtbot,
    am2r_game_description,
    preset_manager,
):
    # Setup
    game = am2r_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, AM2RConfiguration)

    tab = PresetAM2RGoal(editor := PresetEditor(preset, options), am2r_game_description, MagicMock())
    assert isinstance(editor.configuration, AM2RConfiguration)
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)
    artifact_count = editor.configuration.artifacts.placed_artifacts
    tab.restrict_placement_radiobutton.setChecked(True)

    # Run
    tab.free_placement_radiobutton.setChecked(True)

    # Assert
    assert not tab.prefer_metroids_check.isEnabled()
    assert not tab.prefer_bosses_check.isEnabled()
    assert tab.free_placement_radiobutton.isChecked()
    assert editor.configuration.artifacts.placed_artifacts == artifact_count
