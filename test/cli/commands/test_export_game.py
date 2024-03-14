from pathlib import Path
from unittest.mock import MagicMock

from caver.patcher import CSPlatform

from randovania.cli.commands import export_game
from randovania.games.cave_story.exporter.game_exporter import CSGameExportParams
from randovania.games.dread.exporter.game_exporter import DreadGameExportParams, DreadModPlatform
from randovania.games.game import RandovaniaGame


def test_add_parser_arguments_for(game_enum: RandovaniaGame) -> None:
    parser = MagicMock()

    export_game._add_parser_arguments_for(parser, game_enum.exporter.export_params_type())

    parser.add_argument.assert_any_call(
        "--spoiler-output",
        type=Path,
        required=False,
    )


def test_get_export_params_from_cli_cave_story() -> None:
    result = export_game.get_export_params_from_cli(
        RandovaniaGame.CAVE_STORY,
        [
            "--output-path",
            "output-path",
            "--platform",
            "freeware",
        ],
    )
    assert result == CSGameExportParams(
        spoiler_output=None,
        output_path=Path("output-path"),
        platform=CSPlatform.FREEWARE,
    )


def test_get_export_params_from_cli_dread() -> None:
    result = export_game.get_export_params_from_cli(
        RandovaniaGame.METROID_DREAD,
        [
            "--input-path",
            "input-path",
            "--output-path",
            "output-path",
            "--target-platform",
            "ryujinx",
            "--clean-output-path",
        ],
    )
    assert result == DreadGameExportParams(
        spoiler_output=None,
        input_path=Path("input-path"),
        output_path=Path("output-path"),
        target_platform=DreadModPlatform.RYUJINX,
        use_exlaunch=False,
        clean_output_path=True,
        post_export=None,
    )
