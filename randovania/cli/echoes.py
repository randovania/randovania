import multiprocessing
import os
import random
import time
from argparse import ArgumentParser
from pathlib import Path

from randovania.cli import prime_database
from randovania.game_description import data_reader
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import TeleporterConnection
from randovania.games.prime import claris_randomizer, claris_random
from randovania.resolver import debug, generator, resolver
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutSkyTempleKeyMode
from randovania.resolver.layout_description import LayoutDescription
from randovania.resolver.patcher_configuration import PatcherConfiguration
from randovania.resolver.permalink import Permalink

__all__ = ["create_subparsers"]


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
        item_loss=LayoutEnabledFlag.DISABLED if args.skip_item_loss else LayoutEnabledFlag.ENABLED,
        elevators=LayoutRandomizedFlag.VANILLA,
        pickup_quantities={}
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
        patches = GamePatches(
            game.pickup_database.original_pickup_mapping,
            {},
            {},
            {}
        )

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


def distribute_command_logic(args):
    debug._DEBUG_LEVEL = args.debug

    def status_update(s):
        pass

    seed_number = args.seed
    if seed_number is None:
        seed_number = random.randint(0, 2 ** 31)

    print("Using seed: {}".format(seed_number))
    permalink = Permalink(
        seed_number=seed_number,
        spoiler=True,
        patcher_configuration=PatcherConfiguration.default(),
        layout_configuration=get_layout_configuration_from_args(args),
    )

    before = time.perf_counter()
    layout_description = generator.generate_list(permalink=permalink, status_update=status_update)
    after = time.perf_counter()
    print("Took {} seconds. Hash: {}".format(
        after - before,
        hash(tuple(layout_description.pickup_assignment.items()))
    ))
    layout_description.save_to_file(Path(args.output_file))


def add_distribute_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "distribute",
        help="Distribute pickups."
    )

    add_layout_configuration_arguments(parser)
    prime_database.add_data_file_argument(parser)
    parser.add_argument(
        "output_file",
        type=str,
        help="Where to place the seed log.")
    parser.add_argument(
        "--debug",
        choices=range(4),
        type=int,
        default=0,
        help="The level of debug logging to print.")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="The seed number to generate with.")
    parser.set_defaults(func=distribute_command_logic)


def batch_distribute_helper(args, seed_number) -> float:
    data = prime_database.decode_data_file(args)
    configuration = get_layout_configuration_from_args(args)
    permalink = Permalink(
        seed_number=seed_number,
        spoiler=True,
        patcher_configuration=PatcherConfiguration.default(),
        layout_configuration=configuration,
    )

    start_time = time.perf_counter()
    description = generator.generate_list(permalink, None)
    delta_time = time.perf_counter() - start_time

    description.save_to_file(Path(args.output_dir, "{}.json".format(seed_number)))
    return delta_time


def batch_distribute_command_logic(args):
    finished_count = 0

    print("Starting batch generation with configuration: {}".format(
        get_layout_configuration_from_args(args)
    ))
    os.makedirs(args.output_dir, exist_ok=True)

    def callback(result):
        nonlocal finished_count
        finished_count += 1
        print("Finished seed in {} seconds. At {} of {} seeds.".format(result, finished_count, args.seed_count))

    def error_callback(e):
        nonlocal finished_count
        finished_count += 1
        print("Failed to generate seed: {}".format(e))

    with multiprocessing.Pool() as pool:
        for seed_number in range(args.starting_seed, args.starting_seed + args.seed_count):
            pool.apply_async(
                func=batch_distribute_helper,
                args=(args, seed_number),
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
    prime_database.add_data_file_argument(parser)
    parser.add_argument(
        "starting_seed",
        type=int,
        help="The starting seed to generate.")
    parser.add_argument(
        "seed_count",
        type=int,
        help="How many seeds to generate.")
    parser.add_argument(
        "output_dir",
        type=str,
        help="Where to place the seed logs.")
    parser.set_defaults(func=batch_distribute_command_logic)


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "echoes",
        help="Actions regarding Metroid Prime 2: Echoes"
    )
    sub_parsers = parser.add_subparsers(dest="command")
    add_validate_command(sub_parsers)
    add_distribute_command(sub_parsers)
    add_batch_distribute_command(sub_parsers)
    prime_database.create_subparsers(sub_parsers)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
