from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from randovania.game.game_enum import RandovaniaGame

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction

_GAMES_PATH = Path(__file__).parents[2].joinpath("games")


async def update_expected_seed_hash_logic(args: Namespace) -> int:
    from randovania.generator import generator
    from randovania.interface_common.preset_manager import PresetManager
    from randovania.layout.generator_parameters import GeneratorParameters

    games = [RandovaniaGame(game) for game in args.games]
    if not games:
        games = list(RandovaniaGame.all_games())

    preset_manager = PresetManager(None)

    for game in games:
        test_data = game.data.test_data()

        preset = preset_manager.default_preset_for_game(game).get_preset()
        generator_parameters = GeneratorParameters(
            seed_number=test_data.generator_test_seed_number,
            spoiler=True,
            development=True,
            presets=[preset],
        )

        print(f"Calculating for {game.long_name}...")
        result = await generator.generate_and_validate_description(
            generator_params=generator_parameters,
            status_update=None,
            resolve_after_generation=False,
            resolver_timeout=None,
            attempts=0,
            use_world_graph=True,
        )

        if result.shareable_hash != test_data.expected_seed_hash:
            print(f"> Updating game_data.py for new hash {result.shareable_hash}")
            data_path = _GAMES_PATH.joinpath(game.value, "game_data.py")
            data_path.write_text(
                data_path.read_text().replace(
                    f'expected_seed_hash="{test_data.expected_seed_hash}",',
                    f'expected_seed_hash="{result.shareable_hash}",',
                )
            )
        else:
            print("> No hash update needed.")

    return 0


def add_update_expected_seed_hash_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "update-expected-seed-hash", help="Updates the `expected_seed_hash` in the game's game_data.py."
    )
    parser.add_argument(
        "games",
        type=str,
        nargs="*",
        choices=[game.value for game in RandovaniaGame.all_games()],
        help="The game to update the hash for. Defaults to all games.",
    )

    parser.set_defaults(func=update_expected_seed_hash_logic)
