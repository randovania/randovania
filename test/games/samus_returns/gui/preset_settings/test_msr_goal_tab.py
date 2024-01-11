from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

import pytest

from randovania.games.samus_returns.gui.preset_settings.msr_goal_tab import PresetMSRGoal
from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
from randovania.interface_common.preset_editor import PresetEditor


@pytest.mark.parametrize(
    ("prefer_metroids", "prefer_stronger_metroids", "prefer_bosses", "expected_max_slider"),
    [
        (False, False, False, 0),
        (True, False, False, 25),
        (False, True, False, 14),
        (False, False, True, 4),
        (True, True, False, 39),
        (True, False, True, 29),
        (False, True, True, 18),
        (True, True, True, 39),
    ],
)
def test_preferred_dna(
    skip_qtbot,
    msr_game_description,
    preset_manager,
    prefer_metroids: bool,
    prefer_stronger_metroids: bool,
    prefer_bosses: bool,
    expected_max_slider: int,
):
    # Setup
    game = msr_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, MSRConfiguration)

    tab = PresetMSRGoal(editor := PresetEditor(preset, options), msr_game_description, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    assert tab.dna_slider.isEnabled()
    assert tab.dna_slider.value() > 0
    initial_slider_value = tab.dna_slider.value()

    # Run
    tab.prefer_metroids_check.setChecked(prefer_metroids)
    tab.prefer_stronger_metroids_check.setChecked(prefer_stronger_metroids)
    slider_value_after_first_set = tab.dna_slider.value()
    tab.prefer_bosses_check.setChecked(prefer_bosses)
    tab._update_slider_max()

    # Assert
    if not prefer_metroids and not prefer_stronger_metroids:
        assert slider_value_after_first_set == 0
    # The slider value should never increase from what it was before
    assert slider_value_after_first_set >= tab.dna_slider.value()
    assert tab.num_preferred_locations == expected_max_slider
    assert tab.dna_slider.maximum() == expected_max_slider
    assert tab.dna_slider.isEnabled() == (expected_max_slider > 0)

    configuration = editor.configuration
    assert isinstance(configuration, MSRConfiguration)
    assert configuration.artifacts.prefer_metroids == prefer_metroids
    assert configuration.artifacts.prefer_stronger_metroids == prefer_stronger_metroids
    assert configuration.artifacts.prefer_bosses == prefer_bosses
    # If default value in configuration is smaller than the max allowed value, it shouldn't increase
    expected_artifacts = expected_max_slider
    if initial_slider_value < expected_max_slider:
        expected_artifacts = initial_slider_value
    # Also, if the previous slider value is already 0, then that should be the final result
    if slider_value_after_first_set == 0:
        expected_artifacts = 0

    assert configuration.artifacts.required_artifacts == expected_artifacts
    assert tab.dna_slider.value() == expected_artifacts


def test_restricted_placement(
    skip_qtbot,
    msr_game_description,
    preset_manager,
):
    # Setup
    game = msr_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, MSRConfiguration)

    tab = PresetMSRGoal(editor := PresetEditor(preset, options), msr_game_description, MagicMock())
    assert isinstance(editor.configuration, MSRConfiguration)
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)
    artifact_count = editor.configuration.artifacts.required_artifacts

    tab.free_placement_radiobutton.setChecked(True)

    # Run
    tab.restrict_placement_radiobutton.setChecked(True)

    # Assert
    assert tab.prefer_metroids_check.isEnabled()
    assert tab.prefer_stronger_metroids_check.isEnabled()
    assert tab.prefer_bosses_check.isEnabled()
    assert tab.restrict_placement_radiobutton.isChecked()
    assert editor.configuration.artifacts.required_artifacts == artifact_count


def test_free_placement(
    skip_qtbot,
    msr_game_description,
    preset_manager,
):
    # Setup
    game = msr_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, MSRConfiguration)

    tab = PresetMSRGoal(editor := PresetEditor(preset, options), msr_game_description, MagicMock())
    assert isinstance(editor.configuration, MSRConfiguration)
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)
    artifact_count = editor.configuration.artifacts.required_artifacts
    tab.restrict_placement_radiobutton.setChecked(True)

    # Run
    tab.free_placement_radiobutton.setChecked(True)

    # Assert
    assert not tab.prefer_metroids_check.isEnabled()
    assert not tab.prefer_stronger_metroids_check.isEnabled()
    assert not tab.prefer_bosses_check.isEnabled()
    assert tab.free_placement_radiobutton.isChecked()
    assert editor.configuration.artifacts.required_artifacts == artifact_count
