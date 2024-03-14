from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.cli.commands.new_game import add_create_databases, add_new_game_command
from randovania.cli.commands.refresh_presets import add_refresh_presets_command
from randovania.cli.commands.render_regions import render_regions_graph

if TYPE_CHECKING:
    from argparse import ArgumentParser

__all__ = ["create_subparsers"]


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser("development", help="Actions that helps Randovania development")
    sub_parsers = parser.add_subparsers(dest="command")
    add_refresh_presets_command(sub_parsers)
    add_new_game_command(sub_parsers)
    add_create_databases(sub_parsers)
    render_regions_graph(sub_parsers)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
