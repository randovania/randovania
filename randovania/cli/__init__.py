from __future__ import annotations

import logging
import sys
import typing
from argparse import ArgumentParser
from pathlib import Path

import randovania

if typing.TYPE_CHECKING:
    from argparse import Namespace, _SubParsersAction


def create_subparsers(root_parser: _SubParsersAction) -> None:
    from randovania.cli import database, gui, layout

    layout.create_subparsers(root_parser)
    database.create_subparsers(root_parser)
    gui.create_subparsers(root_parser)
    if not randovania.is_frozen():
        from randovania.cli import development, server

        development.create_subparsers(root_parser)
        server.create_subparsers(root_parser)


def _print_version(args: Namespace) -> None:
    print(f"Randovania {randovania.VERSION} from {Path(randovania.__file__).parent}")


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="randovania")

    create_subparsers(parser.add_subparsers(dest="game"))
    parser.add_argument("--version", action="store_const", const=_print_version, dest="func")
    parser.add_argument(
        "--configuration", type=Path, help="Use the given configuration path instead of the included one."
    )

    return parser


def _run_args(parser: ArgumentParser, args: Namespace) -> int:
    if args.configuration is not None:
        randovania.CONFIGURATION_FILE_PATH = args.configuration.absolute()

    if args.func is None:
        parser.print_help()
        raise SystemExit(1)

    logging.debug("Executing from args...")
    return args.func(args) or 0


def run_pytest(argv: list[str]) -> None:
    import pytest
    import pytest_asyncio.plugin
    import pytest_localftpserver.plugin  # type: ignore[import-untyped]
    import pytest_mock.plugin

    sys.exit(pytest.main(argv[2:], plugins=[pytest_asyncio.plugin, pytest_mock.plugin, pytest_localftpserver.plugin]))


def run_cli(argv: list[str]) -> None:
    if len(argv) > 1 and argv[1] == "--pytest":
        run_pytest(argv)
    else:
        args = argv[1:]
        from randovania.cli import gui

        if gui.has_gui and not args:
            args = ["gui", "main"]

        logging.debug("Creating parsers...")
        parser = create_parser()
        raise SystemExit(_run_args(parser, parser.parse_args(args)))
