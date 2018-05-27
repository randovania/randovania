import argparse

from randovania.cli import echoes, interactive
from randovania.gui import qt

games = [echoes]


def create_subparsers(root_parser):
    for game in games:
        game.create_subparsers(root_parser)
    interactive.create_subparsers(root_parser)
    qt.create_subparsers(root_parser)


def run_cli():
    parser = argparse.ArgumentParser()
    create_subparsers(parser.add_subparsers(dest="game"))

    args = parser.parse_args()
    if args.game is None:
        args.func = qt.run
    args.func(args)
