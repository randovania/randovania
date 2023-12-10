from __future__ import annotations

from randovania.games.game import RandovaniaGame
from randovania.games.samus_returns.exporter.game_exporter import MSRModPlatform
from randovania.games.samus_returns.exporter.options import MSRPerGameOptions


def test_round_trip(tmp_path):
    reference = MSRPerGameOptions(
        cosmetic_patches=RandovaniaGame.METROID_SAMUS_RETURNS.data.layout.cosmetic_patches.default(),
        input_directory=tmp_path.joinpath("input"),
        target_platform=MSRModPlatform.LUMA,
        output_preference="{}",
    )

    # Run
    decoded = MSRPerGameOptions.from_json(reference.as_json)

    # Assert
    assert decoded == reference
