from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from randovania.cli.cli_lib import add_debug_argument
from randovania.exporter import game_exporter

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction


def hash_input_command_logic(args: Namespace) -> int:
    input_path: Path = args.input_path
    if input_path.is_dir():
        print(game_exporter.input_hash_for_directory(input_path))
    else:
        print(game_exporter.input_hash_for_file(input_path))
    return 0


def add_hash_input_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "hash-input", help="Hashes a path with the same algorithm used by the game exporter."
    )
    add_debug_argument(parser)
    parser.add_argument("input_path", type=Path, help="The file or directory to hash.")

    parser.set_defaults(func=hash_input_command_logic)
