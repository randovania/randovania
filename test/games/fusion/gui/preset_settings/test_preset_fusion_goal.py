from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

from randovania.games.fusion.gui.preset_settings.fusion_goal_tab import PresetFusionGoal
from randovania.games.fusion.layout.fusion_configuration import FusionArtifactConfig, FusionConfiguration
from randovania.interface_common.preset_editor import PresetEditor


def test_fusion_goal_tab(
    skip_qtbot,
    fusion_game_description,
    preset_manager,
):
    # Setup
    game = fusion_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("bb84005f-b0f1-4e7e-8057-f4275ff4b2a3"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, FusionConfiguration)

    tab = PresetFusionGoal(editor := PresetEditor(preset, options), fusion_game_description, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)
    assert isinstance(editor.configuration, FusionConfiguration)

    assert tab.placed_slider.isEnabled()
    assert tab.placed_slider.value() > 0
    assert tab.required_slider.value() > 0

    # Run
    tab.placed_slider.setValue(0)

    # Assert
    assert tab.required_slider.value() == 0

    expected_artifacts = FusionArtifactConfig(
        required_artifacts=tab.required_slider.value(), placed_artifacts=tab.placed_slider.value()
    )
    assert editor.configuration.artifacts == expected_artifacts
