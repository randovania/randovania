from __future__ import annotations

import dataclasses

from randovania.game_description import default_database
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.dread.layout.dread_configuration import DreadArtifactConfig, DreadConfiguration
from randovania.games.game import RandovaniaGame
from randovania.layout.base.trick_level import LayoutTrickLevel


def test_has_unsupported_features(preset_manager):
    preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_DREAD).get_preset()
    assert isinstance(preset.configuration, DreadConfiguration)

    configuration = preset.configuration

    gd = default_database.game_description_for(preset.game)
    suitless = gd.resource_database.get_by_type_and_index(ResourceType.TRICK, "Suitless")

    configuration = dataclasses.replace(
        configuration,
        trick_level=configuration.trick_level.set_level_for_trick(suitless, LayoutTrickLevel.HYPERMODE),
        artifacts=DreadArtifactConfig(
            prefer_emmi=False,
            prefer_major_bosses=False,
            required_artifacts=1,
        ),
    )

    assert configuration.unsupported_features() == [
        "Metroid DNA on non-boss/EMMI",
        "Enabled Heat/Cold Runs",
    ]


def test_no_unsupported_features(preset_manager):
    preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_DREAD).get_preset()
    assert preset.configuration.unsupported_features() == []
