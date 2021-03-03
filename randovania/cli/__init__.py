import argparse
import logging
import os
import sys
from pathlib import Path

import randovania


def create_subparsers(root_parser):
    from randovania.cli import echoes, server, gui, prime_database
    echoes.create_subparsers(root_parser)
    prime_database.create_subparsers(root_parser)
    server.create_subparsers(root_parser)
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
    parser.add_argument("--configuration", type=Path,
                        help="Use the given configuration path instead of the included one.")

    return parser


def _run_args(parser, args):
    if args.configuration is not None:
        randovania.CONFIGURATION_FILE_PATH = args.configuration.absolute()

    if args.func is None:
        parser.print_help()
        raise SystemExit(1)

    logging.info("Executing from args...")
    args.func(args)


def run_pytest(argv):
    import pytest
    import pytest_asyncio.plugin
    import pytest_mock.plugin
    sys.exit(pytest.main(argv[2:], plugins=[pytest_asyncio.plugin, pytest_mock.plugin]))


def run_cli(argv):
    if len(argv) > 1 and argv[1] == "--pytest":
        run_pytest(argv)
    else:
        args = argv[1:]
        from randovania.cli import gui
        if gui.has_gui and not args:
            args = ["gui", "main"]

        logging.info("Creating parsers...")
        parser = _create_parser()
        _run_args(parser, parser.parse_args(args))
