from randovania.games.dread.exporter.game_exporter import DreadModFormat
from randovania.games.dread.exporter.options import DreadPerGameOptions
from randovania.games.game import RandovaniaGame


def test_round_trip(tmp_path):
    reference = DreadPerGameOptions(
        cosmetic_patches=RandovaniaGame.METROID_DREAD.data.layout.cosmetic_patches.default(),
        input_directory=tmp_path.joinpath("input"),
        output_directory=tmp_path.joinpath("output"),
        output_format=DreadModFormat.ATMOSPHERE,
        output_to_ryujinx=False,
    )

    # Run
    decoded = DreadPerGameOptions.from_json(reference.as_json)

    # Assert
    assert decoded == reference
