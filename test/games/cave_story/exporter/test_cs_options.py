from __future__ import annotations

from randovania.game.game_enum import RandovaniaGame
from randovania.games.cave_story.exporter.options import CSPerGameOptions


def test_round_trip(tmp_path):
    reference = CSPerGameOptions(
        cosmetic_patches=RandovaniaGame.CAVE_STORY.data.layout.cosmetic_patches.default(),
        output_directory=tmp_path.joinpath("output"),
    )

    # Run
    decoded = CSPerGameOptions.from_json(reference.as_json)

    # Assert
    assert decoded == reference
