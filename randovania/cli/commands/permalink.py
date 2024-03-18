from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

from randovania.games.game import RandovaniaGame

if TYPE_CHECKING:
    from argparse import ArgumentParser


def create_permalink(args):
    from randovania.interface_common.preset_manager import PresetManager
    from randovania.layout.generator_parameters import GeneratorParameters
    from randovania.layout.permalink import Permalink

    game: RandovaniaGame = RandovaniaGame(args.game)
    preset_manager = PresetManager(None)
    presets = []
    for preset_name in args.preset_name:
        versioned = preset_manager.included_preset_with(game, preset_name)
        if versioned is None:
            options = [preset.name for preset in preset_manager.included_presets.values() if preset.game == game]
            raise ValueError(
                f"Unknown included preset '{preset_name}' for game {game.long_name}. Valid options are: {options}"
            )
        presets.append(versioned.get_preset())

    seed = args.seed_number
    if seed is None:
        seed = random.randint(0, 2**31)

    return Permalink.from_parameters(
        GeneratorParameters(
            seed,
            spoiler=not args.race,
            development=args.development,
            presets=presets,
        ),
    )


async def permalink_command_body(args):
    from randovania.layout.permalink import Permalink

    permalink = create_permalink(args)
    print(permalink.as_base64_str)
    Permalink.from_str(permalink.as_base64_str)


def permalink_command(args):
    asyncio.run(permalink_command_body(args))


def add_permalink_arguments(parser: ArgumentParser):
    parser.add_argument(
        "--game",
        choices=[game.value for game in RandovaniaGame],
        required=True,
        help="The name of the game of the preset to use.",
    )
    parser.add_argument("--seed-number", type=int, help="The seed number. Defaults to 0.")
    parser.add_argument("--preset-name", required=True, type=str, help="The name of the presets to use", nargs="+")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--race", default=False, action="store_true", help="Make a race permalink (without spoiler).")
    group.add_argument(
        "--development",
        default=False,
        action="store_true",
        help="Disables features that maximize randomness in order to make easier to investigate bugs.",
    )


def add_permalink_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser("permalink", help="Creates a permalink")
    add_permalink_arguments(parser)
    parser.set_defaults(func=permalink_command)
