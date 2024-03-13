from __future__ import annotations

import dataclasses

from randovania.games.fusion.layout.fusion_configuration import FusionArtifactConfig, FusionConfiguration
from randovania.games.game import RandovaniaGame


def test_has_unsupported_features(preset_manager):
    preset = preset_manager.default_preset_for_game(RandovaniaGame.FUSION).get_preset()
    assert isinstance(preset.configuration, FusionConfiguration)

    configuration = preset.configuration

    configuration = dataclasses.replace(
        configuration,
        artifacts=FusionArtifactConfig(
            prefer_bosses=True, prefer_anywhere=False, required_artifacts=5, placed_artifacts=1
        ),
    )

    assert configuration.unsupported_features() == [
        "The amount of required Infant Metroids cannot be higher than the total amount of placed Metroids."
    ]


def test_no_unsupported_features(preset_manager):
    preset = preset_manager.default_preset_for_game(RandovaniaGame.FUSION).get_preset()
    assert preset.configuration.unsupported_features() == []
