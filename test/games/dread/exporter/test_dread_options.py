from __future__ import annotations

from randovania.game.game_enum import RandovaniaGame
from randovania.games.dread.exporter.game_exporter import DreadModPlatform
from randovania.games.dread.exporter.options import DreadPerGameOptions


def test_round_trip(tmp_path):
    reference = DreadPerGameOptions(
        cosmetic_patches=RandovaniaGame.METROID_DREAD.data.layout.cosmetic_patches.default(),
        input_directory=tmp_path.joinpath("input"),
        target_platform=DreadModPlatform.ATMOSPHERE,
        output_preference="{}",
    )

    # Run
    decoded = DreadPerGameOptions.from_json(reference.as_json)

    # Assert
    assert decoded == reference
