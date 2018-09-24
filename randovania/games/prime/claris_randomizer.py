import os
import shutil
import subprocess
from typing import Callable, List

import py

from randovania import get_data_path
from randovania.interface_common import status_update_lib
from randovania.interface_common.options import validate_game_files_path
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.resolver.layout_configuration import LayoutEnabledFlag, LayoutRandomizedFlag
from randovania.resolver.layout_description import LayoutDescription


def _get_randomizer_folder() -> str:
    return os.path.join(get_data_path(), "ClarisPrimeRandomizer")


def _get_randomizer_path() -> str:
    return os.path.join(_get_randomizer_folder(), "Randomizer.exe")


def _get_menu_mod_path() -> str:
    return os.path.join(get_data_path(), "ClarisEchoesMenu", "EchoesMenu.exe")


def has_randomizer_binary():
    return os.path.isfile(_get_randomizer_path())


def _run_with_args(args: List[str],
                   finish_string: str,
                   status_update: Callable[[str], None]):
    print("Invoking external tool with: ", args)
    finished_updates = False
    with subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=0, universal_newlines=True) as process:
        try:
            for line in process.stdout:
                x = line.strip()
                if x:
                    print(x)
                    if not finished_updates:
                        status_update(x)
                        finished_updates = x == finish_string
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


def _ensure_no_menu_mod(
        game_root: str,
        backup_files_path: str,
        status_update: Callable[[str], None],
        ):
    pak_folder = py.path.local(backup_files_path).join("mp2_paks")
    files_folder = py.path.local(game_root).join("files")
    menu_mod_txt = files_folder.join("menu_mod.txt")

    if menu_mod_txt.isfile() and pak_folder.isdir():
        for pak in pak_folder.visit("*.pak"):
            status_update("Restoring {} from backup".format(pak.relto(pak_folder)))
            pak.copy(files_folder.join(pak.relto(pak_folder)))
        menu_mod_txt.remove()


def _create_pak_backups(
        game_root: str,
        backup_files_path: str,
        status_update: Callable[[str], None],
        ):

    pak_folder = py.path.local(backup_files_path).join("mp2_paks")
    pak_folder.ensure_dir()

    files_folder = py.path.local(game_root).join("files")
    for pak in ["MiscData.pak"] + ["Metroid{}.pak".format(i) for i in range(1, 6)]:
        if not pak_folder.join(pak).exists():
            status_update("Backing up {}".format(pak))
            files_folder.join(pak).copy(pak_folder.join(pak))


def _add_menu_mod_to_files(
        game_root: str,
        status_update: Callable[[str], None],
        ):

    files_folder = py.path.local(game_root).join("files")
    _run_with_args(
        [
            _get_menu_mod_path(),
            str(files_folder)
        ],
        "Done!",
        status_update
    )
    files_folder.join("menu_mod.txt").ensure()


def apply_layout(
        layout: LayoutDescription,
        hud_memo_popup_removal: bool,
        include_menu_mod: bool,
        game_root: str,
        backup_files_path: str,
        progress_update: ProgressUpdateCallable,
        ):
    args = _base_args(game_root,
                      hud_memo_popup_removal=hud_memo_popup_removal)

    status_update = status_update_lib.create_progress_update_from_successive_messages(
        progress_update, 400 if include_menu_mod else 100)

    _ensure_no_menu_mod(game_root, backup_files_path, status_update)
    _create_pak_backups(game_root, backup_files_path, status_update)

    args += [
        "-p", ",".join(str(pickup) for pickup in layout.pickup_mapping),
    ]
    if layout.configuration.item_loss == LayoutEnabledFlag.DISABLED:
        args.append("-i")
    if layout.configuration.elevators == LayoutRandomizedFlag.RANDOMIZED:
        args.append("-v")

    layout.save_to_file(os.path.join(game_root, "files", "randovania.json"))
    _run_with_args(args, "Randomized!", status_update)

    if include_menu_mod:
        _add_menu_mod_to_files(game_root, status_update)


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
