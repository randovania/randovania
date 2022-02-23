from randovania.games.game import RandovaniaGame
from randovania.games.prime1.exporter.options import PrimePerGameOptions


def test_round_trip(tmp_path):
    reference = PrimePerGameOptions(
        cosmetic_patches=RandovaniaGame.METROID_PRIME.data.layout.cosmetic_patches.default(),
        input_path=tmp_path.joinpath("input.iso"),
        output_directory=tmp_path.joinpath("output"),
        output_format="ciso",
    )

    # Run
    decoded = PrimePerGameOptions.from_json(reference.as_json)

    # Assert
    assert decoded == reference
