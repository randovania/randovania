import asyncio
import random
from argparse import ArgumentParser

from randovania.games.game import RandovaniaGame


def create_permalink(args):
    from randovania.layout.permalink import Permalink
    from randovania.layout.generator_parameters import GeneratorParameters
    from randovania.interface_common.preset_manager import PresetManager

    game: RandovaniaGame = RandovaniaGame(args.game)
    preset_manager = PresetManager(None)
    presets = []
    for preset_name in args.preset_name:
        versioned = preset_manager.included_preset_with(game, preset_name)
        if versioned is None:
            raise ValueError("Unknown included preset '{}' for game {}. Valid options are: {}".format(
                preset_name, game.long_name,
                [preset.name for preset in preset_manager.included_presets.values()
                 if preset.game == game]
            ))
        presets.append(versioned.get_preset())

    seed = args.seed_number
    if seed is None:
        seed = random.randint(0, 2 ** 31)

    return Permalink.from_parameters(
        GeneratorParameters(
            seed,
            spoiler=not args.race,
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
    parser.add_argument("--game", choices=[game.value for game in RandovaniaGame],
                        required=True, help="The name of the game of the preset to use.")
    parser.add_argument("--seed-number", type=int, help="The seed number. Defaults to 0.")
    parser.add_argument("--preset-name", required=True, type=str, help="The name of the presets to use", nargs='+')
    parser.add_argument("--race", default=False, action="store_true", help="Make a race permalink (without spoiler).")


def add_permalink_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "permalink",
        help="Creates a permalink"
    )
    add_permalink_arguments(parser)
    parser.set_defaults(func=permalink_command)
