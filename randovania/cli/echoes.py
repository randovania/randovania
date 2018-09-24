import random
import random
import sys
from argparse import ArgumentParser

from randovania.cli import prime_database
from randovania.games.prime import log_parser
from randovania.interface_common.options import MAX_DIFFICULTY
from randovania.resolver import debug
from randovania.resolver.echoes import run_resolver, RandomizerConfiguration, \
    ResolverConfiguration, print_path_for_state
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutLogic, LayoutMode, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutDifficulty

__all__ = ["create_subparsers"]


def build_resolver_configuration(args):
    return ResolverConfiguration(
        args.difficulty,
        args.minimum_difficulty,
        set(),
        not args.skip_item_loss
    )


def add_resolver_config_arguments(parser):
    parser.add_argument(
        "--difficulty",
        type=int,
        default=0,
        choices=range(MAX_DIFFICULTY + 1),
        help=
        "The difficulty level to check with. Higher numbers implies in harder tricks."
    )
    parser.add_argument(
        "--minimum-difficulty",
        type=int,
        default=0,
        choices=range(6),
        help=
        "Also check if the seed needs the given difficulty."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--enable-tricks",
        action="store_true",
        dest="tricks",
        default=True,
        help=
        "Enable trick usage in the validation. This is always on. Use the GUI otherwise."
    )

    parser.add_argument(
        "--skip-item-loss",
        action="store_true",
        help="Assumes the Item Loss trigger is disabled."
    )
    parser.add_argument(
        "--print-final-path",
        action="store_true",
        help=
        "If seed is possible, print the sequence of events/pickups taken to reach the ending."
    )


def build_randomizer_configuration(args):
    return RandomizerConfiguration(
        args.exclude_pickups,
        args.randomize_elevators
    )


def add_randomizer_configuration_arguments(parser):
    parser.add_argument(
        "--exclude-pickups",
        nargs='+',
        type=int,
        default=[],
        help="Pickups to exclude from the randomization."
    )
    parser.add_argument(
        "--randomize-elevators",
        action="store_true",
        help="Randomize elevators as well."
    )


def distribute_command_logic(args):
    debug._DEBUG_LEVEL = args.debug
    data = prime_database.decode_data_file(args)
    resolver_config = build_resolver_configuration(args)

    def status_update(s):
        pass

    seed_number = args.seed
    if seed_number is None:
        seed_number = random.randint(0, 2 ** 31)

    print("Using seed: {}".format(seed_number))

    from randovania.resolver import generator
    layout_description = generator.generate_list(
        data=data,
        seed_number=seed_number,
        configuration=LayoutConfiguration(
            logic=LayoutLogic.NO_GLITCHES,
            mode=LayoutMode.MAJOR_ITEMS if args.major_items_mode else LayoutMode.STANDARD,
            sky_temple_keys=LayoutRandomizedFlag.VANILLA if args.vanilla_sky_temple_keys else LayoutRandomizedFlag.RANDOMIZED,
            item_loss=LayoutEnabledFlag.ENABLED if resolver_config.item_loss else LayoutEnabledFlag.DISABLED,
            elevators=LayoutRandomizedFlag.VANILLA,
            hundo_guaranteed=LayoutEnabledFlag.DISABLED,
            difficulty=LayoutDifficulty.NORMAL,
        ),
        status_update=status_update
    )
    layout_description.save_to_file(args.output_file)


def add_distribute_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "distribute",
        help="Distribute pickups."
    )

    add_resolver_config_arguments(parser)
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
    parser.set_defaults(func=distribute_command_logic)


def validate_command_logic(args):
    debug._DEBUG_LEVEL = args.debug
    data = prime_database.decode_data_file(args)
    randomizer_log = log_parser.parse_log(args.logfile)
    resolver_config = build_resolver_configuration(args)

    final_state = run_resolver(data, randomizer_log, resolver_config)
    if final_state:
        if args.print_final_path:
            print_path_for_state(final_state,
                                 GamePatches(resolver_config.item_loss, randomizer_log.pickup_mapping),
                                 True,
                                 True)
    else:
        print("Impossible.")
        raise SystemExit(1)


def add_validate_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "validate",
        help="Validate a randomizer log."
    )

    parser.add_argument(
        "logfile",
        type=str,
        help="Path to the log file of a Randomizer run.")
    add_resolver_config_arguments(parser)
    prime_database.add_data_file_argument(parser)
    parser.add_argument(
        "--debug",
        choices=range(4),
        type=int,
        default=0,
        help="The level of debug logging to print.")
    parser.set_defaults(func=validate_command_logic)


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "echoes",
        help="Actions regarding Metroid Prime 2: Echoes"
    )
    sub_parsers = parser.add_subparsers(dest="command")
    add_validate_command(sub_parsers)
    add_distribute_command(sub_parsers)
    prime_database.create_subparsers(sub_parsers)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
