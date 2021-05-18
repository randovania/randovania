import json
import shutil

from randovania.games.patchers import csharp_subprocess
from randovania.games.patchers.csharp_subprocess import is_windows, process_command
from randovania.games.prime.dol_patcher import DolPatchesData

try:
    from asyncio.exceptions import IncompleteReadError
except ImportError:
    from asyncio.streams import IncompleteReadError
from pathlib import Path
from typing import Callable, List, Union, Optional

from randovania import get_data_path
from randovania.games.prime import dol_patcher
from randovania.interface_common import status_update_lib
from randovania.interface_common.game_workdir import validate_game_files_path
from randovania.interface_common.status_update_lib import ProgressUpdateCallable

CURRENT_PATCH_VERSION = 2


def _patch_version_file(game_root: Path) -> Path:
    return game_root.joinpath("randovania_patch_version.txt")


def get_patch_version(game_root: Path) -> int:
    file = _patch_version_file(game_root)
    if file.exists():
        return int(file.read_text("utf-8"))
    else:
        return 0


def write_patch_version(game_root: Path, version: int):
    _patch_version_file(game_root).write_text(str(version))


def _get_randomizer_folder() -> Path:
    return get_data_path().joinpath("ClarisPrimeRandomizer")


def _get_randomizer_path() -> Path:
    return _get_randomizer_folder().joinpath("Randomizer.exe")


def _get_menu_mod_path() -> Path:
    return get_data_path().joinpath("ClarisEchoesMenu", "EchoesMenu.exe")


def _run_with_args(args: List[Union[str, Path]],
                   input_data: str,
                   finish_string: str,
                   status_update: Callable[[str], None]):
    finished_updates = False

    new_args = [str(arg) for arg in args]
    print("Invoking external tool with: ", new_args)

    def read_callback(line: str):
        nonlocal finished_updates
        print(line)
        if not finished_updates:
            status_update(line)
            finished_updates = line == finish_string

    csharp_subprocess.process_command(new_args, input_data, read_callback)

    if not finished_updates:
        raise RuntimeError("External tool did not send '{}'. Did something happen?".format(finish_string))


def _base_args(game_root: Path,
               ) -> List[Union[str, Path]]:
    game_files = game_root / "files"
    validate_game_files_path(game_files)

    return [
        _get_randomizer_path(),
        game_root,
        # "-test",
    ]


def _ensure_no_menu_mod(
        game_root: Path,
        backup_files_path: Optional[Path],
        status_update: Callable[[str], None],
):
    """
    Ensures the given game_root has no menu mod, copying paks from the backup path if needed.
    :param game_root:
    :param backup_files_path:
    :param status_update:
    :return:
    """
    files_folder = game_root.joinpath("files")
    menu_mod_txt = files_folder.joinpath("menu_mod.txt")

    if menu_mod_txt.is_file():
        if backup_files_path is None:
            raise RuntimeError("Game at '{}' has Menu Mod, but no backup path given to restore".format(game_root))

        pak_folder = backup_files_path.joinpath("mp2_paks")
        if pak_folder.is_dir():
            for pak in pak_folder.glob("**/*.pak"):
                relative = pak.relative_to(pak_folder)
                status_update("Restoring {} from backup".format(relative))
                shutil.copy(pak, files_folder.joinpath(relative))

            menu_mod_txt.unlink()


_ECHOES_PAKS = tuple(["MiscData.pak"] + ["Metroid{}.pak".format(i) for i in range(1, 6)])


def _create_pak_backups(
        game_root: Path,
        backup_files_path: Path,
        status_update: Callable[[str], None],
):
    pak_folder = backup_files_path.joinpath("mp2_paks")
    pak_folder.mkdir(parents=True, exist_ok=True)

    files_folder = game_root.joinpath("files")
    for pak in _ECHOES_PAKS:
        target_file = pak_folder.joinpath(pak)
        if not target_file.exists():
            status_update("Backing up {}".format(pak))
            shutil.copy(files_folder.joinpath(pak), target_file)


def _add_menu_mod_to_files(
        game_root: Path,
        status_update: Callable[[str], None],
):
    files_folder = game_root.joinpath("files")
    _run_with_args(
        [_get_menu_mod_path(), files_folder],
        "",
        "Done!",
        status_update
    )
    files_folder.joinpath("menu_mod.txt").write_bytes(b"")


def apply_patcher_file(game_root: Path,
                       backup_files_path: Optional[Path],
                       patcher_data: dict,
                       progress_update: ProgressUpdateCallable,
                       ):
    """
    Applies the modifications listed in the given patcher_data to the game in game_root.
    :param game_root:
    :param backup_files_path:
    :param patcher_data:
    :param progress_update:
    :return:
    """
    menu_mod = patcher_data["menu_mod"]

    status_update = status_update_lib.create_progress_update_from_successive_messages(
        progress_update, 400 if menu_mod else 100)

    last_version = get_patch_version(game_root)
    if last_version > CURRENT_PATCH_VERSION:
        raise RuntimeError(f"Game at {game_root} was last patched with version {last_version}, "
                           f"which is above supported version {CURRENT_PATCH_VERSION}. "
                           f"\nPlease press 'Delete internal copy'.")

    _ensure_no_menu_mod(game_root, backup_files_path, status_update)
    if backup_files_path is not None:
        _create_pak_backups(game_root, backup_files_path, status_update)

    _run_with_args(_base_args(game_root),
                   json.dumps(patcher_data),
                   "Randomized!",
                   status_update)
    dol_patcher.apply_patches(game_root, DolPatchesData.from_json(patcher_data["dol_patches"]))
    write_patch_version(game_root, CURRENT_PATCH_VERSION)

    if menu_mod:
        _add_menu_mod_to_files(game_root, status_update)
