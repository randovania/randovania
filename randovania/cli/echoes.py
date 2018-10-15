import multiprocessing
import os
import random
import time
from argparse import ArgumentParser

from randovania.cli import prime_database
from randovania.resolver import debug, generator
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutLogic, LayoutMode, \
    LayoutRandomizedFlag, LayoutEnabledFlag, LayoutDifficulty

__all__ = ["create_subparsers"]


def add_layout_configuration_arguments(parser):
    parser.add_argument(
        "--logic",
        type=str,
        choices=[layout.value for layout in LayoutLogic],
        default=LayoutLogic.NO_GLITCHES.value,
        help="The seed number to generate with.")
    parser.add_argument(
        "--major-items-mode",
        default=False,
        action="store_true",
        help="If set, will use the Major Item mode")
    parser.add_argument(
        "--vanilla-sky-temple-keys",
        default=False,
        action="store_true",
        help="If set, Sky Temple Keys won't be randomized.")
    parser.add_argument(
        "--skip-item-loss",
        action="store_true",
        help="Disables the item loss cutscene, disabling losing your items."
    )


def get_layout_configuration_from_args(args) -> LayoutConfiguration:
    return LayoutConfiguration(
        logic=LayoutLogic(args.logic),
        mode=LayoutMode.MAJOR_ITEMS if args.major_items_mode else LayoutMode.STANDARD,
        sky_temple_keys=LayoutRandomizedFlag.VANILLA if args.vanilla_sky_temple_keys else LayoutRandomizedFlag.RANDOMIZED,
        item_loss=LayoutEnabledFlag.DISABLED if args.skip_item_loss else LayoutEnabledFlag.ENABLED,
        elevators=LayoutRandomizedFlag.VANILLA,
        hundo_guaranteed=LayoutEnabledFlag.DISABLED,
        difficulty=LayoutDifficulty.NORMAL,
        pickup_quantities={}
    )


def distribute_command_logic(args):
    debug._DEBUG_LEVEL = args.debug
    data = prime_database.decode_data_file(args)

    def status_update(s):
        pass

    seed_number = args.seed
    if seed_number is None:
        seed_number = random.randint(0, 2 ** 31)

    print("Using seed: {}".format(seed_number))

    layout_description = generator.generate_list(
        data=data,
        seed_number=seed_number,
        configuration=get_layout_configuration_from_args(args),
        status_update=status_update
    )
    layout_description.save_to_file(args.output_file)


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

    start_time = time.perf_counter()
    description = generator.generate_list(data, seed_number, configuration, None)
    delta_time = time.perf_counter() - start_time

    description.save_to_file(os.path.join(args.output_dir, "{}.json".format(description.seed_number)))
    return delta_time


def batch_distribute_command_logic(args):
    finished_count = 0

    print("Starting batch generation with configuration: {}".format(
        get_layout_configuration_from_args(args).as_str
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
    add_distribute_command(sub_parsers)
    add_batch_distribute_command(sub_parsers)
    prime_database.create_subparsers(sub_parsers)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
