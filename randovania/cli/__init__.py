import argparse
import os

import randovania
from randovania.cli import echoes, interactive
from randovania.gui import qt

games = [echoes]


def create_subparsers(root_parser):
    for game in games:
        game.create_subparsers(root_parser)
    interactive.create_subparsers(root_parser)
    qt.create_subparsers(root_parser)


def _print_version(args):
    print("Randovania {} from {}".format(
        randovania.VERSION,
        os.path.dirname(randovania.__file__)))


def run_cli():
    parser = argparse.ArgumentParser()
    create_subparsers(parser.add_subparsers(dest="game"))
    parser.add_argument("--version", action="store_const",
                        const=_print_version, dest="func")

    args = parser.parse_args()
    if getattr(args, "func", None) is None:
        args.func = qt.run
    args.func(args)
