import json
import logging
import shutil
from pathlib import Path
from typing import Callable, List, Union

from randovania import get_data_path
from randovania.games.patchers import csharp_subprocess
from randovania.games.patchers.exceptions import ExportFailure
from randovania.games.prime import echoes_dol_patcher
from randovania.interface_common.game_workdir import validate_game_files_path
from randovania.lib import status_update_lib
from randovania.lib.status_update_lib import ProgressUpdateCallable

try:
    from asyncio.exceptions import IncompleteReadError
except ImportError:
    from asyncio.streams import IncompleteReadError

CURRENT_PATCH_VERSION = 2
logger = logging.getLogger(__name__)


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
    logger.info("Invoking external tool with: %s", new_args)
    all_lines = []

    def read_callback(line: str):
        nonlocal finished_updates
        logger.info(line)
        all_lines.append(line)
        if not finished_updates:
            status_update(line)
            finished_updates = line == finish_string

    csharp_subprocess.process_command(new_args, input_data, read_callback)

    if not finished_updates:
        raise ExportFailure(
            "External tool did not send '{}'.".format(finish_string),
            "\n".join(all_lines),
        )


def _base_args(game_root: Path,
               ) -> List[Union[str, Path]]:
    game_files = game_root / "files"
    validate_game_files_path(game_files)

    return [
        _get_randomizer_path(),
        game_root,
        # "-test",
    ]


_ECHOES_PAKS = tuple(
    [
        "MiscData.pak",
        "FrontEnd.pak",
        "LogBook.pak",
    ]
    + ["Metroid{}.pak".format(i) for i in range(1, 6)])


def restore_pak_backups(
        game_root: Path,
        backup_files_path: Path,
        progress_update: ProgressUpdateCallable,
):
    """
    Ensures the given game_root has unmodified paks.
    :param game_root:
    :param backup_files_path:
    :param progress_update:
    :return:
    """
    pak_folder = backup_files_path.joinpath("paks")
    files_folder = game_root.joinpath("files")
    for i, pak in enumerate(_ECHOES_PAKS):
        progress_update("Restoring {} from backup".format(pak), i / len(_ECHOES_PAKS))
        shutil.copy(pak_folder.joinpath(pak), files_folder.joinpath(pak))

    files_folder.joinpath("menu_mod.txt").unlink(missing_ok=True)


def create_pak_backups(
        game_root: Path,
        backup_files_path: Path,
        progress_update: ProgressUpdateCallable,
):
    pak_folder = backup_files_path.joinpath("paks")
    pak_folder.mkdir(parents=True, exist_ok=True)

    files_folder = game_root.joinpath("files")
    for i, pak in enumerate(_ECHOES_PAKS):
        progress_update("Backing up {}".format(pak), i / len(_ECHOES_PAKS))
        shutil.copy(files_folder.joinpath(pak), pak_folder.joinpath(pak))


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
                       patcher_data: dict,
                       progress_update: ProgressUpdateCallable,
                       ):
    """
    Applies the modifications listed in the given patcher_data to the game in game_root.
    :param game_root:
    :param patcher_data:
    :param progress_update:
    :return:
    """
    menu_mod = patcher_data["menu_mod"]

    status_update = status_update_lib.create_progress_update_from_successive_messages(
        progress_update, 200 if menu_mod else 100)

    last_version = get_patch_version(game_root)
    if last_version > CURRENT_PATCH_VERSION:
        raise ExportFailure(f"Game at {game_root} was last patched with version {last_version}, "
                            f"which is above supported version {CURRENT_PATCH_VERSION}. "
                            f"\nPlease press 'Delete internal copy'.", None)

    _run_with_args(_base_args(game_root),
                   json.dumps(patcher_data),
                   "Randomized!",
                   status_update)
    echoes_dol_patcher.apply_patches(game_root,
                                     echoes_dol_patcher.EchoesDolPatchesData.from_json(patcher_data["dol_patches"]))
    write_patch_version(game_root, CURRENT_PATCH_VERSION)

    if menu_mod:
        _add_menu_mod_to_files(game_root, status_update)
