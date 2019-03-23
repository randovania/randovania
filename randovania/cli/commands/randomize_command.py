from argparse import ArgumentParser
from pathlib import Path

from randovania.games.prime import claris_randomizer
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink
from randovania.resolver import generator


def randomize_command_logic(args):
    def status_update(s):
        if args.verbose:
            print(s)

    if args.permalink is not None:
        layout_description = generator.generate_list(permalink=Permalink.from_str(args.permalink),
                                                     status_update=status_update,
                                                     validate_after_generation=True)
    else:
        layout_description = LayoutDescription.from_file(args.log_file)

    cosmetic_patches = CosmeticPatches(
        disable_hud_popup=args.disable_hud_popup,
        speed_up_credits=args.speed_up_credits)

    claris_randomizer.apply_layout(description=layout_description,
                                   cosmetic_patches=cosmetic_patches,
                                   backup_files_path=args.backup_files,
                                   progress_update=lambda x, _: status_update(x),
                                   game_root=args.game_files,
                                   )


def add_randomize_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "randomize",
        help="Randomizes a game files path."
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--permalink", type=str, help="The permalink to use")
    group.add_argument("--log-file", type=Path, help="A seed log file to use")

    parser.add_argument("--disable-hud-popup", action="store_true", help="Remove the HUD popup", default=False)
    parser.add_argument("--speed-up-credits", action="store_true", help="Speeds ups the credits sequence",
                        default=False)
    parser.add_argument("--verbose", action="store_true", help="Prints progress",
                        default=False)

    parser.add_argument(
        "--backup-files",
        type=Path,
        help="Folder where to place/restore backups, in case of menu mod.")

    parser.add_argument(
        "game_files",
        type=Path,
        help="Root of an extracted games file to randomize.")
    parser.set_defaults(func=randomize_command_logic)
