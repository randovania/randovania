from randovania.games.game import RandovaniaGame
from randovania.games.prime2.exporter.options import EchoesPerGameOptions


def test_round_trip(tmp_path):
    reference = EchoesPerGameOptions(
        cosmetic_patches=RandovaniaGame.METROID_PRIME_ECHOES.data.layout.cosmetic_patches.default(),
        input_path=tmp_path.joinpath("input.iso"),
        output_directory=tmp_path.joinpath("output"),
    )

    # Run
    decoded = EchoesPerGameOptions.from_json(reference.as_json)

    # Assert
    assert decoded == reference
