import random
from argparse import ArgumentParser

from randovania.cli.echoes_lib import get_layout_configuration_from_args, add_layout_configuration_arguments
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.permalink import Permalink


def _print_permalink(permalink: Permalink):
    print(permalink.as_str)


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
    _print_permalink(permalink)


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
