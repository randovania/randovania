from __future__ import annotations

import dataclasses

from randovania.games.am2r.layout.am2r_configuration import AM2RArtifactConfig, AM2RConfiguration
from randovania.games.game import RandovaniaGame


def test_has_unsupported_features(preset_manager):
    preset = preset_manager.default_preset_for_game(RandovaniaGame.AM2R).get_preset()
    assert isinstance(preset.configuration, AM2RConfiguration)

    configuration = preset.configuration

    configuration = dataclasses.replace(
        configuration,
        artifacts=AM2RArtifactConfig(
            prefer_metroids=True, prefer_bosses=True, prefer_anywhere=False, required_artifacts=5, placed_artifacts=1
        ),
        darkness_min=4,
        darkness_max=0,
        submerged_water_chance=1000,
        submerged_lava_chance=1000,
    )

    assert configuration.unsupported_features() == [
        "The amount of required DNA cannot be higher than the total amount of placed DNA.",
        "The minimum darkness value cannot be higher than the maximum darkness value.",
        (
            "The probability of a room being submerged in water and being submerged in "
            "lava cannot be higher than 100% combined."
        ),
    ]


def test_no_unsupported_features(preset_manager):
    preset = preset_manager.default_preset_for_game(RandovaniaGame.AM2R).get_preset()
    assert preset.configuration.unsupported_features() == []
