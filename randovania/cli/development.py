from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.cli.commands import benchmark
from randovania.cli.commands.new_game import add_create_databases, add_new_game_command
from randovania.cli.commands.refresh_presets import add_refresh_presets_command
from randovania.cli.commands.render_regions import render_regions_graph
from randovania.cli.commands.website import (
    create_export_videos_yaml_command,
    create_extract_game_data_command,
    create_readme_sections_command,
)

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
    create_export_videos_yaml_command(sub_parsers)
    create_readme_sections_command(sub_parsers)
    create_extract_game_data_command(sub_parsers)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)

    benchmark_parser = sub_parsers.add_parser(
        "benchmark", help="Actions for benchmarking Randovania in a consistent way."
    )
    benchmark.add_commands(benchmark_parser.add_subparsers(dest="command"))

    def bench_check_command(args):
        if args.command is None:
            benchmark_parser.print_help()
            raise SystemExit(1)

    benchmark_parser.set_defaults(func=bench_check_command)
