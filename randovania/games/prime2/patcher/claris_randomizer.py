from __future__ import annotations

import json
import logging
import shutil
from typing import TYPE_CHECKING

from randovania import get_data_path, monitoring
from randovania.games.prime2.patcher import csharp_subprocess
from randovania.interface_common.game_workdir import validate_game_files_path
from randovania.lib import json_lib, status_update_lib
from randovania.patching.patchers.exceptions import UnableToExportError

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from randovania.lib.status_update_lib import ProgressUpdateCallable

CURRENT_PATCH_VERSION = 4
logger = logging.getLogger(__name__)


class ClarisRandomizerExportError(UnableToExportError):
    def __init__(self, reason: str, output: str | None):
        super().__init__(reason)
        self.output = output

    def detailed_text(self) -> str:
        result = []
        if self.output is not None:
            result.append(self.output)
        return "\n".join(result)


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


def _get_custom_data_path() -> Path:
    from randovania.interface_common import persistence

    return persistence.local_data_dir().joinpath("CustomEchoesRandomizerData.json")


def _get_menu_mod_path() -> Path:
    return _get_randomizer_folder().joinpath("EchoesMenu.exe")


def _run_with_args(args: list[str | Path], input_data: str, finish_string: str, status_update: Callable[[str], None]):
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
        raise ClarisRandomizerExportError(
            f"External tool did not send '{finish_string}'.",
            "\n".join(all_lines),
        )


def _base_args(
    game_root: Path,
) -> list[str | Path]:
    game_files = game_root / "files"
    validate_game_files_path(game_files)

    return [
        _get_randomizer_path(),
        game_root,
        # "-test",
        "-data:" + str(_get_custom_data_path()),
    ]


_ECHOES_PAKS = tuple(
    [
        "AudioGrp.pak",
        "FrontEnd.pak",
        "GGuiSys.pak",
        "LogBook.pak",
        "MidiData.pak",
        "MiscData.pak",
        "NoARAM.pak",
        "SamGunFx.pak",
        "SamGunFxLow.pak",
        "SamGunFxMulti.pak",
        "SamusGun.pak",
        "SamusGunLow.pak",
        "SlideShow.pak",
        "Standard.ntwk",
        "TestAnim.pak",
    ]
    + [f"Metroid{i}.pak" for i in range(1, 6)]
)


@monitoring.trace_function
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
        progress_update(f"Restoring {pak} from backup", i / len(_ECHOES_PAKS))
        shutil.copy(pak_folder.joinpath(pak), files_folder.joinpath(pak))

    files_folder.joinpath("menu_mod.txt").unlink(missing_ok=True)


@monitoring.trace_function
def create_pak_backups(
    game_root: Path,
    backup_files_path: Path,
    progress_update: ProgressUpdateCallable,
):
    pak_folder = backup_files_path.joinpath("paks")
    pak_folder.mkdir(parents=True, exist_ok=True)

    files_folder = game_root.joinpath("files")
    for i, pak in enumerate(_ECHOES_PAKS):
        progress_update(f"Backing up {pak}", i / len(_ECHOES_PAKS))
        shutil.copy(files_folder.joinpath(pak), pak_folder.joinpath(pak))


@monitoring.trace_function
def add_menu_mod_to_files(
    game_root: Path,
    progress_update: ProgressUpdateCallable,
):
    status_update = status_update_lib.create_progress_update_from_successive_messages(progress_update, 300)
    files_folder = game_root.joinpath("files")
    _run_with_args([_get_menu_mod_path(), files_folder], "", "Done!", status_update)
    files_folder.joinpath("menu_mod.txt").write_bytes(b"")


@monitoring.trace_function
def apply_patcher_file(
    game_root: Path,
    patcher_data: dict,
    randomizer_data: dict,
    progress_update: ProgressUpdateCallable,
):
    """
    Applies the modifications listed in the given patcher_data to the game in game_root.
    :param game_root:
    :param patcher_data:
    :param randomizer_data: The RandomizerData.json contents to use.
    :param progress_update:
    :return:
    """
    status_update = status_update_lib.create_progress_update_from_successive_messages(progress_update, 300)

    last_version = get_patch_version(game_root)
    if last_version > CURRENT_PATCH_VERSION:
        raise UnableToExportError(
            "The internal game copy was outdated and has been deleted. Please export again and select an ISO.",
        )

    json_lib.write_path(_get_custom_data_path(), randomizer_data)
    _run_with_args(_base_args(game_root), json.dumps(patcher_data), "Randomized!", status_update)
    write_patch_version(game_root, CURRENT_PATCH_VERSION)
