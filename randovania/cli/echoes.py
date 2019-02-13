import multiprocessing
import os
import random
import time
from argparse import ArgumentParser
from pathlib import Path

from randovania.cli import prime_database
from randovania.game_description import data_reader
from randovania.game_description.game_patches import GamePatches
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutRandomizedFlag, \
    LayoutSkyTempleKeyMode
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.permalink import Permalink
from randovania.layout.starting_location import StartingLocation
from randovania.layout.starting_resources import StartingResources
from randovania.resolver import debug, generator, resolver

__all__ = ["create_subparsers"]


def add_debug_argument(parser):
    parser.add_argument(
        "--debug",
        choices=range(4),
        type=int,
        default=0,
        help="The level of debug logging to print.")


def add_layout_configuration_arguments(parser):
    parser.add_argument(
        "--trick-level",
        type=str,
        choices=[layout.value for layout in LayoutTrickLevel],
        default=LayoutTrickLevel.NO_TRICKS.value,
        help="The level of tricks to use.")
    parser.add_argument(
        "--sky-temple-keys",
        type=str,
        choices=[mode.value for mode in LayoutSkyTempleKeyMode],
        default=LayoutSkyTempleKeyMode.FULLY_RANDOM.value,
        help="The Sky Temple Keys randomization mode.")
    parser.add_argument(
        "--skip-item-loss",
        action="store_true",
        help="Disables the item loss cutscene, disabling losing your items."
    )


def get_layout_configuration_from_args(args) -> LayoutConfiguration:
    return LayoutConfiguration.from_params(
        trick_level=LayoutTrickLevel(args.trick_level),
        sky_temple_keys=LayoutSkyTempleKeyMode(args.sky_temple_keys),
        elevators=LayoutRandomizedFlag.VANILLA,
        pickup_quantities={},
        starting_location=StartingLocation.default(),
        starting_resources=StartingResources.from_item_loss(not args.skip_item_loss),
    )


def validate_command_logic(args):
    debug._DEBUG_LEVEL = args.debug
    data = prime_database.decode_data_file(args)
    game = data_reader.decode_data(data)

    if args.layout_file is not None:
        description = LayoutDescription.from_file(Path(args.layout_file))
        configuration = description.permalink.layout_configuration
        patches = description.patches
    else:
        configuration = LayoutConfiguration.default()
        patches = GamePatches.with_game(game).assign_pickup_assignment(game.pickup_database.original_pickup_mapping)

    final_state_by_resolve = resolver.resolve(
        configuration=configuration,
        game=game,
        patches=patches
    )
    print(final_state_by_resolve)


def add_validate_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "validate",
        help="Validate a pickup distribution."
    )

    prime_database.add_data_file_argument(parser)
    parser.add_argument(
        "--debug",
        choices=range(4),
        type=int,
        default=0,
        help="The level of debug logging to print.")
    parser.add_argument(
        "layout_file",
        type=str,
        nargs="?",
        help="The layout seed log file to validate.")
    parser.set_defaults(func=validate_command_logic)


def create_permalink_logic(args):
    seed_number = args.seed
    if seed_number is None:
        seed_number = random.randint(0, 2 ** 31)

    permalink = Permalink(
        seed_number=seed_number,
        spoiler=True,
        patcher_configuration=PatcherConfiguration(
            menu_mod=args.menu_mod,
            warp_to_start=args.warp_to_start,
        ),
        layout_configuration=get_layout_configuration_from_args(args),
    )
    print(permalink.as_str)


def add_create_permalink_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "create-permalink",
        help="Creates a permalink for the given options."
    )

    add_layout_configuration_arguments(parser)
    parser.add_argument("--seed", type=int, default=None, help="The seed number to use")
    parser.add_argument("--no-menu-mod", action="store_false", help="Don't use menu mod",
                        default=True, dest="menu_mod")
    parser.add_argument("--no-warp-to-start", action="store_false", help="Don't add warp to start",
                        default=True, dest="warp_to_start")
    parser.set_defaults(func=create_permalink_logic)


def distribute_command_logic(args):
    debug._DEBUG_LEVEL = args.debug

    def status_update(s):
        pass

    permalink = Permalink.from_str(args.permalink)

    before = time.perf_counter()
    layout_description = generator.generate_list(permalink=permalink, status_update=status_update)
    after = time.perf_counter()
    print("Took {} seconds. Hash: {}".format(after - before, layout_description.shareable_hash))
    layout_description.save_to_file(args.output_file)


def add_distribute_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "distribute",
        help="Distribute pickups."
    )

    add_debug_argument(parser)
    parser.add_argument("permalink", type=str, help="The permalink to use")
    parser.add_argument(
        "output_file",
        type=Path,
        help="Where to place the seed log.")
    parser.set_defaults(func=distribute_command_logic)


def batch_distribute_helper(base_permalink: Permalink, seed_number: int, output_dir: Path) -> float:
    permalink = Permalink(
        seed_number=seed_number,
        spoiler=True,
        patcher_configuration=base_permalink.patcher_configuration,
        layout_configuration=base_permalink.layout_configuration,
    )

    start_time = time.perf_counter()
    description = generator.generate_list(permalink, None)
    delta_time = time.perf_counter() - start_time

    description.save_to_file(output_dir.joinpath("{}.json".format(seed_number)))
    return delta_time


def batch_distribute_command_logic(args):
    finished_count = 0

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    base_permalink = Permalink.from_str(args.permalink)

    def callback(result):
        nonlocal finished_count
        finished_count += 1
        print("Finished seed in {} seconds. At {} of {} seeds.".format(result, finished_count, args.seed_count))

    def error_callback(e):
        nonlocal finished_count
        finished_count += 1
        print("Failed to generate seed: {}".format(e))

    with multiprocessing.Pool() as pool:
        for seed_number in range(base_permalink.seed_number, base_permalink.seed_number + args.seed_count):
            pool.apply_async(
                func=batch_distribute_helper,
                args=(base_permalink, seed_number, output_dir),
                callback=callback,
                error_callback=error_callback,
            )
        pool.close()
        pool.join()


def add_batch_distribute_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "batch-distribute",
        help="Generate multiple seeds in parallel"
    )

    add_layout_configuration_arguments(parser)
    parser.add_argument("permalink", type=str, help="The permalink to use")
    parser.add_argument(
        "seed_count",
        type=int,
        help="How many seeds to generate.")
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Where to place the seed logs.")
    parser.set_defaults(func=batch_distribute_command_logic)


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "echoes",
        help="Actions regarding Metroid Prime 2: Echoes"
    )
    sub_parsers = parser.add_subparsers(dest="command")
    add_validate_command(sub_parsers)
    add_create_permalink_command(sub_parsers)
    add_distribute_command(sub_parsers)
    # add_randomize_command(sub_parsers)
    add_batch_distribute_command(sub_parsers)
    prime_database.create_subparsers(sub_parsers)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
