import asyncio
import copy
import json
import platform
import re
import shutil
from asyncio import StreamWriter, StreamReader
from collections import defaultdict
from pathlib import Path
from typing import Callable, List, Dict, Union, Optional

from randovania import get_data_path
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.echoes_elevator import Elevator, echoes_elevators
from randovania.games.prime import claris_random, patcher_file
from randovania.interface_common import status_update_lib
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.game_workdir import validate_game_files_path
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.layout.layout_description import LayoutDescription

_USELESS_PICKUP_NAME = "Energy Transfer Module"


def _get_randomizer_folder() -> Path:
    return get_data_path().joinpath("ClarisPrimeRandomizer")


def _get_randomizer_path() -> Path:
    return _get_randomizer_folder().joinpath("Randomizer.exe")


def _get_menu_mod_path() -> Path:
    return get_data_path().joinpath("ClarisEchoesMenu", "EchoesMenu.exe")


def _is_windows() -> bool:
    return platform.system() == "Windows"


async def _write_data(stream: StreamWriter, data: str):
    stream.write(data.encode("UTF-8"))
    stream.close()


async def _read_data(stream: StreamReader, read_callback: Callable[[str], None]):
    while True:
        try:
            line = await stream.readuntil(b"\r")
        except asyncio.streams.IncompleteReadError as incomplete:
            line = incomplete.partial
        if line:
            try:
                decoded = line.decode()
            except UnicodeDecodeError:
                decoded = line.decode("latin1")
            for x in re.split(r"[\r\n]", decoded.strip()):
                if x:
                    read_callback(x)
        else:
            break


async def _process_command_async(args: List[str], input_data: str, read_callback: Callable[[str], None]):
    process = await asyncio.create_subprocess_exec(*args,
                                                   stdin=asyncio.subprocess.PIPE,
                                                   stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.STDOUT)

    await asyncio.wait([
        _write_data(process.stdin, input_data),
        _read_data(process.stdout, read_callback),
    ])
    await process.wait()


def _process_command(args: List[str], input_data: str, read_callback: Callable[[str], None]):
    loop = asyncio.ProactorEventLoop()
    try:
        loop.run_until_complete(_process_command_async(args, input_data, read_callback))
    finally:
        loop.close()


def _run_with_args(args: List[Union[str, Path]],
                   input_data: str,
                   finish_string: str,
                   status_update: Callable[[str], None]):
    finished_updates = False

    new_args = [str(arg) for arg in args]
    if not _is_windows():
        new_args.insert(0, "mono")
    print("Invoking external tool with: ", new_args)

    def read_callback(line: str):
        nonlocal finished_updates
        print(line)
        if not finished_updates:
            status_update(line)
            finished_updates = line == finish_string

    _process_command(new_args, input_data, read_callback)

    if not finished_updates:
        raise RuntimeError("External tool did not send '{}'. Did something happen?".format(finish_string))


def _base_args(game_root: Path,
               ) -> List[Union[str, Path]]:
    game_files = game_root / "files"
    validate_game_files_path(game_files)

    return [
        _get_randomizer_path(),
        game_root,
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


def apply_layout(description: LayoutDescription,
                 cosmetic_patches: CosmeticPatches,
                 backup_files_path: Optional[Path],
                 progress_update: ProgressUpdateCallable,
                 game_root: Path,
                 ):
    """
    Applies the modifications listed in the given LayoutDescription to the game in game_root.
    :param use_modern_api:
    :param cosmetic_patches:
    :param description:
    :param game_root:
    :param backup_files_path: Path to use as pak backup, to remove/add menu mod.
    :param progress_update:
    :return:
    """

    patcher_configuration = description.permalink.patcher_configuration

    status_update = status_update_lib.create_progress_update_from_successive_messages(
        progress_update, 400 if patcher_configuration.menu_mod else 100)

    _ensure_no_menu_mod(game_root, backup_files_path, status_update)
    if backup_files_path is not None:
        _create_pak_backups(game_root, backup_files_path, status_update)
    description.save_to_file(game_root.joinpath("files", "randovania.json"))

    _modern_api(game_root, status_update, description, cosmetic_patches)

    if patcher_configuration.menu_mod:
        _add_menu_mod_to_files(game_root, status_update)


def _modern_api(game_root: Path,
                status_update: Callable[[str], None],
                description: LayoutDescription,
                cosmetic_patches: CosmeticPatches,
                ):
    """

    :param game_root:
    :param status_update:
    :param description:
    :param cosmetic_patches:
    :return:
    """
    patcher_data = patcher_file.create_patcher_file(description, cosmetic_patches)

    if description.permalink.spoiler:
        with game_root.joinpath("files", "patcher_data.json").open("w") as patcher_data_file:
            json.dump(patcher_data, patcher_data_file)

    _run_with_args(_base_args(game_root),
                   json.dumps(patcher_data),
                   "Randomized!",
                   status_update)


def try_randomize_elevators(randomizer: claris_random.Random,
                            ) -> List[Elevator]:
    elevator_database: List[Elevator] = copy.deepcopy(echoes_elevators)

    elevator_list = copy.copy(elevator_database)
    elevators_by_world: Dict[int, List[Elevator]] = defaultdict(list)
    for elevator in elevator_list:
        elevators_by_world[elevator.world_number].append(elevator)

    while elevator_list:
        source_elevators: List[Elevator] = max(elevators_by_world.values(), key=len)
        target_elevators: List[Elevator] = [
            elevator
            for elevator in elevator_list
            if elevator not in source_elevators
        ]
        source_elevator = source_elevators[0]
        target_elevator = target_elevators[randomizer.next_with_max(len(target_elevators) - 1)]

        source_elevator.connect_to(target_elevator)

        elevators_by_world[source_elevator.world_number].remove(source_elevator)
        elevators_by_world[target_elevator.world_number].remove(target_elevator)
        elevator_list.remove(source_elevator)
        elevator_list.remove(target_elevator)

    # TODO
    list3 = copy.copy(elevator_database)
    celevator_list3 = [list3[0]]
    while list3:
        celevator_list1 = []
        for celevator1 in celevator_list3:
            index = 0
            while index < len(list3):
                celevator2 = list3[index]
                if celevator2.world_number == celevator1.world_number or celevator2.area_asset_id == celevator1.destination_area:
                    celevator_list1.append(celevator2)
                    list3.remove(celevator2)
                else:
                    index += 1
        if celevator_list1:
            celevator_list3 = celevator_list1
        else:
            # Randomization failed
            return try_randomize_elevators(randomizer)

    return elevator_database


def elevator_connections_for_seed_number(seed_number: int,
                                         ) -> Dict[int, AreaLocation]:
    elevator_connection = {}
    for elevator in try_randomize_elevators(claris_random.Random(seed_number)):
        elevator_connection[elevator.instance_id] = AreaLocation(
            elevator.connected_elevator.world_asset_id,
            elevator.connected_elevator.area_asset_id
        )
    return elevator_connection
