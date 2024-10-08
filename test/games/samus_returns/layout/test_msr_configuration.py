from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.games.samus_returns.layout.msr_configuration import MSRArtifactConfig, MSRConfiguration


def test_has_unsupported_features(preset_manager):
    preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_SAMUS_RETURNS).get_preset()
    assert isinstance(preset.configuration, MSRConfiguration)

    configuration = preset.configuration

    configuration = dataclasses.replace(
        configuration,
        artifacts=MSRArtifactConfig(
            prefer_metroids=True,
            prefer_stronger_metroids=True,
            prefer_bosses=True,
            prefer_anywhere=False,
            required_artifacts=5,
            placed_artifacts=1,
        ),
    )

    assert configuration.unsupported_features() == [
        "The amount of required DNA cannot be higher than the total amount of placed DNA."
    ]


def test_no_unsupported_features(preset_manager):
    preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_SAMUS_RETURNS).get_preset()
    assert preset.configuration.unsupported_features() == []
