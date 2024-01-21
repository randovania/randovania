from __future__ import annotations

import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.games.prime1.layout.artifact_mode import LayoutArtifactMode
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration


def test_has_unsupported_features(preset_manager):
    preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME).get_preset()
    assert isinstance(preset.configuration, PrimeConfiguration)

    configuration = preset.configuration

    configuration = dataclasses.replace(
        configuration,
        artifact_required=LayoutArtifactMode.FIVE,
        artifact_target=LayoutArtifactMode.ONE,
    )

    assert configuration.unsupported_features() == [
        "The amount of required artifacts cannot be higher than the total amount of shuffled artifacts."
    ]


def test_no_unsupported_features(preset_manager):
    preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME).get_preset()
    assert preset.configuration.unsupported_features() == []
