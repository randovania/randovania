import time
from argparse import ArgumentParser
from pathlib import Path

from randovania.cli import echoes_lib
from randovania.generator import generator
from randovania.interface_common import simplified_patcher
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.layout.permalink import Permalink
from randovania.resolver import debug


def distribute_command_logic(args):
    debug.set_level(args.debug)

    def status_update(s):
        pass

    permalink = Permalink.from_str(args.permalink)

    before = time.perf_counter()
    layout_description = generator.generate_description(permalink=permalink, status_update=status_update,
                                                        validate_after_generation=args.validate, timeout=None)
    after = time.perf_counter()
    print("Took {} seconds. Hash: {}".format(after - before, layout_description.shareable_hash))

    layout_description.save_to_file(args.output_file)
    simplified_patcher.write_patcher_file_to_disk(
        args.output_file.with_suffix(".patcher-json"),
        layout_description,
        CosmeticPatches.default(),
    )


def add_distribute_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "distribute",
        help="Distribute pickups."
    )

    echoes_lib.add_debug_argument(parser)
    echoes_lib.add_validate_argument(parser)
    parser.add_argument("permalink", type=str, help="The permalink to use")
    parser.add_argument(
        "output_file",
        type=Path,
        help="Where to place the seed log.")
    parser.set_defaults(func=distribute_command_logic)
