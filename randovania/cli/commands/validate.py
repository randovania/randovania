import asyncio
import time
from argparse import ArgumentParser
from pathlib import Path

from randovania.cli.echoes_lib import add_debug_argument
from randovania.layout.layout_description import LayoutDescription
from randovania.resolver import debug, resolver


def validate_command_logic(args):
    debug.set_level(args.debug)

    description = LayoutDescription.from_file(args.layout_file)

    if description.permalink.player_count != 1:
        raise ValueError(f"Validator does not support layouts with more than 1 player.")

    configuration = description.permalink.presets[0].configuration
    patches = description.all_patches[0]

    before = time.perf_counter()
    final_state_by_resolve = asyncio.run(resolver.resolve(
        configuration=configuration,
        patches=patches
    ))
    after = time.perf_counter()
    print("Took {} seconds. Game is {}.".format(
        after - before,
        "possible" if final_state_by_resolve is not None else "impossible")
    )


def add_validate_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "validate",
        help="Validate a pickup distribution."
    )

    add_debug_argument(parser)
    parser.add_argument(
        "layout_file",
        type=Path,
        help="The layout seed log file to validate.")
    parser.set_defaults(func=validate_command_logic)
