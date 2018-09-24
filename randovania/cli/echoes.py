import random
from argparse import ArgumentParser

from randovania.cli import prime_database
from randovania.resolver import debug
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutLogic, LayoutMode, \
    LayoutRandomizedFlag, LayoutEnabledFlag, LayoutDifficulty

__all__ = ["create_subparsers"]


def add_resolver_config_arguments(parser):
    parser.add_argument(
        "--skip-item-loss",
        action="store_true",
        help="Assumes the Item Loss trigger is disabled."
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

    from randovania.resolver import generator
    layout_description = generator.generate_list(
        data=data,
        seed_number=seed_number,
        configuration=LayoutConfiguration(
            logic=LayoutLogic(args.logic),
            mode=LayoutMode.MAJOR_ITEMS if args.major_items_mode else LayoutMode.STANDARD,
            sky_temple_keys=LayoutRandomizedFlag.VANILLA if args.vanilla_sky_temple_keys else LayoutRandomizedFlag.RANDOMIZED,
            item_loss=LayoutEnabledFlag.ENABLED if args.skip_item_loss else LayoutEnabledFlag.DISABLED,
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
    parser.set_defaults(func=distribute_command_logic)


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "echoes",
        help="Actions regarding Metroid Prime 2: Echoes"
    )
    sub_parsers = parser.add_subparsers(dest="command")
    add_distribute_command(sub_parsers)
    prime_database.create_subparsers(sub_parsers)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
