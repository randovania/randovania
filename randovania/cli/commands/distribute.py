import asyncio
import time
from argparse import ArgumentParser
from pathlib import Path

from randovania.cli import echoes_lib
from randovania.games.game import RandovaniaGame
from randovania.resolver import debug


def distribute_command_logic(args):
    from randovania.layout.permalink import Permalink
    from randovania.generator import generator

    async def _create_permalink(args_) -> Permalink:
        from randovania.interface_common.preset_manager import PresetManager

        preset_manager = PresetManager(None)
        preset = preset_manager.included_preset_with(RandovaniaGame(args_.game), args_.preset_name).get_preset()

        return Permalink(
            args_.seed_number,
            spoiler=True,
            presets={i: preset for i in range(args_.player_count)},
        )

    def status_update(s):
        if args.status_update:
            print(s)

    if args.permalink is not None:
        permalink = Permalink.from_str(args.permalink)
    else:
        permalink = asyncio.run(_create_permalink(args))
        print(f"Permalink: {permalink.as_base64_str}")

    if permalink.spoiler:
        debug.set_level(args.debug)

    extra_args = {}
    if args.no_retry:
        extra_args["attempts"] = 0

    before = time.perf_counter()
    layout_description = asyncio.run(generator.generate_and_validate_description(permalink=permalink, status_update=status_update,
                                                                                 validate_after_generation=args.validate,
                                                                                 timeout=None, **extra_args))
    after = time.perf_counter()
    print("Took {} seconds. Hash: {}".format(after - before, layout_description.shareable_hash))

    layout_description.save_to_file(args.output_file)


def add_distribute_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "distribute",
        help="Distribute pickups."
    )

    echoes_lib.add_debug_argument(parser)
    echoes_lib.add_validate_argument(parser)
    parser.add_argument("--no-retry", default=False, action="store_true", help="Disable retries in the generation.")
    parser.add_argument("--status-update", default=False, action="store_true", help="Print the status updates.")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--permalink", type=str, help="The permalink to use")
    group.add_argument("--preset-name", type=str, help="The name of the preset to use")

    parser.add_argument("--game", choices=[game.value for game in RandovaniaGame],
                        required=True, help="The name of the game of the preset to use.")
    parser.add_argument("--seed-number", type=int, default=0, help="If using a preset, the seed number. Defaults to 0.")
    parser.add_argument("--player-count", type=int, default=1,
                        help="If using a preset, the number of players. Defaults to 1.")

    parser.add_argument(
        "output_file",
        type=Path,
        help="Where to place the seed log.")
    parser.set_defaults(func=distribute_command_logic)
