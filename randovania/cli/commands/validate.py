from argparse import ArgumentParser
from pathlib import Path

from randovania.cli import prime_database
from randovania.cli.echoes_lib import add_debug_argument
from randovania.game_description import data_reader
from randovania.layout.layout_description import LayoutDescription
from randovania.resolver import debug, resolver


def validate_command_logic(args):
    debug._DEBUG_LEVEL = args.debug
    data = prime_database.decode_data_file(args)
    game = data_reader.decode_data(data)

    description = LayoutDescription.from_file(args.layout_file)
    configuration = description.permalink.layout_configuration
    patches = description.patches

    final_state_by_resolve = resolver.resolve(
        configuration=configuration,
        game=game,
        patches=patches
    )
    print(final_state_by_resolve)


def add_validate_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "validate",
        help="Validate a pickup distribution."
    )

    prime_database.add_data_file_argument(parser)
    add_debug_argument(parser)
    parser.add_argument(
        "layout_file",
        type=Path,
        help="The layout seed log file to validate.")
    parser.set_defaults(func=validate_command_logic)
