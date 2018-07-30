import os
import subprocess
from typing import Callable, List

from randovania import get_data_path
from randovania.interface_common.options import validate_game_files_path
from randovania.resolver.echoes import RandomizerConfiguration
from randovania.resolver.layout_configuration import LayoutEnabledFlag, LayoutRandomizedFlag
from randovania.resolver.layout_description import LayoutDescription


def _get_randomizer_folder():
    return os.path.join(get_data_path(), "ClarisPrimeRandomizer")


def _get_randomizer_path():
    return os.path.join(_get_randomizer_folder(), "Randomizer.exe")


def has_randomizer_binary():
    return os.path.isfile(_get_randomizer_path())


def _run_with_args(args: List[str],
                   status_update: Callable[[str], None]):
    print("Running the Randomizer with: ", args)
    finished_updates = False
    with subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=0, universal_newlines=True) as process:
        try:
            for line in process.stdout:
                x = line.strip()
                if x and not finished_updates:
                    status_update(x)
                    finished_updates = x == "Randomized!"
        except Exception:
            process.kill()
            raise


def _base_args(game_root: str,
               hud_memo_popup_removal: bool,
               ) -> List[str]:
    game_files = os.path.join(game_root, "files")
    validate_game_files_path(game_files)

    args = [
        _get_randomizer_path(),
        game_files,
        "-r",  # disable read key when finished, since it would crash
    ]
    if hud_memo_popup_removal:
        args.append("-h")
    return args


def apply_seed(randomizer_config: RandomizerConfiguration,
               seed: int,
               remove_item_loss: bool,
               hud_memo_popup_removal: bool,
               game_root: str,
               status_update: Callable[[str], None]):
    args = _base_args(game_root,
                      hud_memo_popup_removal=hud_memo_popup_removal)

    args += [
        "-s", str(seed),
        "-e", ",".join(str(pickup) for pickup in randomizer_config.exclude_pickups) or "none",
    ]
    if remove_item_loss:
        args.append("-i")
    if randomizer_config.randomize_elevators:
        args.append("-v")

    _run_with_args(args, status_update)


def apply_layout(
        layout: LayoutDescription,
        hud_memo_popup_removal: bool,
        game_root: str,
        status_update: Callable[[str], None]):
    args = _base_args(game_root,
                      hud_memo_popup_removal=hud_memo_popup_removal)

    args += [
        "-p", ",".join(str(pickup) for pickup in layout.pickup_mapping),
    ]
    if layout.configuration.item_loss == LayoutEnabledFlag.DISABLED:
        args.append("-i")
    if layout.configuration.elevators == LayoutRandomizedFlag.RANDOMIZED:
        args.append("-v")

    layout.save_to_file(os.path.join(game_root, "files", "randovania.json"))
    _run_with_args(args, status_update)


def disable_echoes_attract_videos(game_root: str,
                                  status_update: Callable[[str], None]):
    game_files = os.path.join(game_root, "files")
    args = [
        os.path.join(_get_randomizer_folder(), "DisableEchoesAttractVideos.exe"),
        game_files
    ]
    with subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=0, universal_newlines=True) as process:
        try:
            for line in process.stdout:
                x = line.strip()
                status_update(x)
        except Exception:
            process.kill()
            raise
