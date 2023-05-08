from argparse import ArgumentParser
from pathlib import Path

from randovania.layout import preset_describer
from randovania.layout.layout_description import LayoutDescription


def describe_command_logic(args):
    description = LayoutDescription.from_file(args.layout_file)

    print(f"{description.player_count} players")
    for player in range(description.player_count):
        preset = description.get_preset(player)

        print(f"## Player {player + 1} - {preset.game.long_name}")
        for category, items in preset_describer.describe(preset):
            print()
            print(category)
            for item in items:
                print(f"    {item}")


def add_describe_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "describe",
        help="Describes a rdvgame file."
    )
    parser.add_argument(
        "layout_file",
        type=Path,
        help="The rdvgame file to validate.")

    parser.set_defaults(func=describe_command_logic)
