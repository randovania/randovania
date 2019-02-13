import time
from argparse import ArgumentParser
from pathlib import Path

from randovania.cli.echoes_lib import add_debug_argument
from randovania.layout.permalink import Permalink
from randovania.resolver import debug, generator


def distribute_command_logic(args):
    debug._DEBUG_LEVEL = args.debug

    def status_update(s):
        pass

    permalink = Permalink.from_str(args.permalink)

    before = time.perf_counter()
    layout_description = generator.generate_list(permalink=permalink, status_update=status_update)
    after = time.perf_counter()
    print("Took {} seconds. Hash: {}".format(after - before, layout_description.shareable_hash))
    layout_description.save_to_file(args.output_file)


def add_distribute_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "distribute",
        help="Distribute pickups."
    )

    add_debug_argument(parser)
    parser.add_argument("permalink", type=str, help="The permalink to use")
    parser.add_argument(
        "output_file",
        type=Path,
        help="Where to place the seed log.")
    parser.set_defaults(func=distribute_command_logic)
