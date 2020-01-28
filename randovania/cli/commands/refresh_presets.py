import json
from argparse import ArgumentParser

from randovania import get_data_path
from randovania.layout.preset import read_preset_file, save_preset_file


def refresh_presets_command_logic(args):

    base_path = get_data_path().joinpath("presets")

    with base_path.joinpath("presets.json").open() as presets_file:
        preset_list = json.load(presets_file)["presets"]

    for preset_relative_path in preset_list:
        preset_path = base_path.joinpath(preset_relative_path["path"])
        save_preset_file(
            read_preset_file(preset_path),
            preset_path
        )


def add_refresh_presets_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "refresh-presets",
        help="Loads the preset files and saves then again with the latest version"
    )

    parser.set_defaults(func=refresh_presets_command_logic)
