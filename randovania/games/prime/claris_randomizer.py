import os
import subprocess

from randovania import get_data_path
from randovania.interface_common.options import validate_game_files_path
from randovania.resolver.echoes import RandomizerConfiguration


def _get_randomizer_path():
    return os.path.join(get_data_path(), "ClarisPrimeRandomizer", "Randomizer.exe")


def has_randomizer_binary():
    return os.path.isfile(_get_randomizer_path())


def apply_seed(randomizer_config: RandomizerConfiguration,
               seed: int,
               remove_item_loss: bool,
               hud_memo_popup_removal: bool,
               game_root: str):
    game_files = os.path.join(game_root, "files")
    validate_game_files_path(game_files)

    args = [
        _get_randomizer_path(),
        game_files,
        "-s", str(seed),
        "-e", ",".join(str(pickup) for pickup in randomizer_config.exclude_pickups) or "none",
    ]
    if remove_item_loss:
        args.append("-i")
    if hud_memo_popup_removal:
        args.append("-h")
    if randomizer_config.randomize_elevators:
        args.append("-v")

    print("Running the Randomizer with: ", args)
    subprocess.run(args, check=True)
