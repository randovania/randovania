import asyncio
import random
from argparse import ArgumentParser

from randovania.games.game import RandovaniaGame
from randovania.layout.permalink import Permalink


async def permalink_command_body(args):
    from randovania.interface_common.preset_manager import PresetManager

    preset_manager = PresetManager(None)
    versioned_preset = preset_manager.included_preset_with(RandovaniaGame(args.game), args.preset)
    if versioned_preset is None:
        raise ValueError(f"Unknown preset: {args.preset}")

    seed = args.seed
    if seed is None:
        seed = random.randint(0, 2 ** 31)

    preset = versioned_preset.get_preset()
    permalink = Permalink(
        seed_number=seed,
        spoiler=not args.race,
        presets={i: preset for i in range(args.player_count)}
    )
    print(permalink.as_base64_str)

    Permalink.from_str(permalink.as_base64_str)


def permalink_command(args):
    asyncio.run(permalink_command_body(args))


def add_permalink_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "permalink",
        help="Creates a permalink"
    )
    parser.add_argument("--game", choices=[game.value for game in RandovaniaGame],
                        required=True, help="The name of the game of the preset to use.")
    parser.add_argument("--preset", type=str, required=True, help="The name of the preset to use.")
    parser.add_argument("--player-count", type=int, default=1, help="The number of players in the permalink.")
    parser.add_argument("--seed", type=int, help="The seed number.")
    parser.add_argument("--race", default=False, action="store_true", help="Make a race permalink (without spoiler).")

    parser.set_defaults(func=permalink_command)
