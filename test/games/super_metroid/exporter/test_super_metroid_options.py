from randovania.games.game import RandovaniaGame
from randovania.games.super_metroid.exporter.options import SuperMetroidPerGameOptions


def test_round_trip(tmp_path):
    reference = SuperMetroidPerGameOptions(
        cosmetic_patches=RandovaniaGame.SUPER_METROID.data.layout.cosmetic_patches.default(),
        input_path=tmp_path.joinpath("input.smc"),
        output_directory=tmp_path.joinpath("output"),
        output_format="sfc",
    )

    # Run
    decoded = SuperMetroidPerGameOptions.from_json(reference.as_json)

    # Assert
    assert decoded == reference
