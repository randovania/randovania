import argparse
import os
import sys

import randovania
from randovania.cli import echoes, gui


def create_subparsers(root_parser):
    echoes.create_subparsers(root_parser)
    gui.create_subparsers(root_parser)


def _print_version(args):
    print("Randovania {} from {}".format(
        randovania.VERSION,
        os.path.dirname(randovania.__file__)))


def _create_parser():
    parser = argparse.ArgumentParser()

    create_subparsers(parser.add_subparsers(dest="game"))
    parser.add_argument("--version", action="store_const",
                        const=_print_version, dest="func")

    parser.set_defaults(func=(gui.open_gui if gui.has_gui
                              else lambda args: parser.print_help()))

    return parser


def _run_args(args):
    args.func(args)


def run_pytest(argv):
    import pytest
    sys.exit(pytest.main(argv[2:], plugins=["pytest_asyncio"]))


def run_cli(argv):
    if len(argv) > 1 and argv[1] == "--pytest":
        run_pytest(argv)
    else:
        _run_args(_create_parser().parse_args(argv[1:]))
