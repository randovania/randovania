import random
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.permalink import Permalink, PERMALINK_MAX_SEED
from randovania.layout.preset import read_preset_file


def permalink_command_logic(args):
    seed_number: Optional[int] = args.seed_number
    if seed_number is None:
        seed_number = random.randint(0, PERMALINK_MAX_SEED)

    spoiler: bool = args.spoiler

    preset_path = Path(args.preset)
    if preset_path.is_file():
        preset = read_preset_file(preset_path)
    else:
        preset_manager = PresetManager(None)
        preset = preset_manager.preset_for_name(args.preset)
        if preset is None:
            raise ValueError(f"No preset known with name {args.preset}")

    permalink = Permalink(seed_number, spoiler, preset)
    print(permalink.as_str)


def add_permalink_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "permalink",
        help="Creates a permalink based on given preset"
    )

    parser.add_argument("--seed-number", type=int, help="The seed number to use for the permalink. "
                                                        "A random number is used if missing.")
    spoiler_group = parser.add_mutually_exclusive_group()
    spoiler_group.add_argument("--spoiler", action="store_true", default=True,
                               help="Have spoiler log enabled on the permalink. The default.")
    spoiler_group.add_argument("--no-spoiler", action="store_false", dest="spoiler",
                               help="Disable spoiler log.")

    parser.add_argument("--preset", type=str, required=True, help="A path to a preset file to use, or the name of a "
                                                                  "default preset to use.")
    parser.set_defaults(func=permalink_command_logic)

