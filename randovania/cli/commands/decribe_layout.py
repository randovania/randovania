from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from randovania.layout import preset_describer
from randovania.layout.layout_description import LayoutDescription

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction


def describe_command_logic(args: Namespace) -> None:
    description = LayoutDescription.from_file(args.layout_file)

    print(f"{description.world_count} players")
    for player in range(description.world_count):
        preset = description.get_preset(player)

        print(f"## Player {player + 1} - {preset.game.long_name}")
        for category, items in preset_describer.describe(preset):
            print()
            print(category)
            for item in items:
                print(f"    {item}")


def add_describe_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser("describe", help="Describes a rdvgame file.")
    parser.add_argument("layout_file", type=Path, help="The rdvgame file to validate.")

    parser.set_defaults(func=describe_command_logic)
