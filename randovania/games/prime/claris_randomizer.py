import copy
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Callable, List, Dict, Union

from randovania import get_data_path
from randovania.game_description import data_reader
from randovania.game_description.echoes_elevator import Elevator, echoes_elevators
from randovania.game_description.node import TeleporterConnection
from randovania.games.prime import claris_random
from randovania.interface_common import status_update_lib
from randovania.interface_common.game_workdir import validate_game_files_path
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.resolver.layout_configuration import LayoutEnabledFlag, LayoutRandomizedFlag
from randovania.resolver.layout_description import LayoutDescription

_USELESS_PICKUP_NAME = "Energy Transfer Module"


def _get_randomizer_folder() -> Path:
    return get_data_path().joinpath("ClarisPrimeRandomizer")


def _get_randomizer_path() -> Path:
    return _get_randomizer_folder().joinpath("Randomizer.exe")


def _get_menu_mod_path() -> Path:
    return get_data_path().joinpath("ClarisEchoesMenu", "EchoesMenu.exe")


def _run_with_args(args: List[Union[str, Path]],
                   finish_string: str,
                   status_update: Callable[[str], None]):
    finished_updates = False

    new_args = [str(arg) for arg in args]
    print("Invoking external tool with: ", new_args)
    with subprocess.Popen(new_args, stdout=subprocess.PIPE, bufsize=0, universal_newlines=True) as process:
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
    if not finished_updates:
        raise RuntimeError("External tool did not send '{}'. Did something happen?".format(finish_string))


def _base_args(game_root: Path,
               hud_memo_popup_removal: bool,
               ) -> List[str]:
    game_files = game_root / "files"
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
        game_root: Path,
        backup_files_path: Path,
        status_update: Callable[[str], None],
):
    pak_folder = backup_files_path.joinpath("mp2_paks")
    files_folder = game_root.joinpath("files")
    menu_mod_txt = files_folder.joinpath("menu_mod.txt")

    if menu_mod_txt.is_file() and pak_folder.is_dir():
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
        [
            _get_menu_mod_path(),
            files_folder
        ],
        "Done!",
        status_update
    )
    files_folder.joinpath("menu_mod.txt").write_bytes(b"")


def _calculate_indices(description: LayoutDescription) -> List[int]:
    pickup_database = data_reader.read_databases(description.permalink.layout_configuration.game_data)[1]
    useless_pickup = pickup_database.pickup_by_name(_USELESS_PICKUP_NAME)

    indices = [pickup_database.original_index(useless_pickup).index] * pickup_database.total_pickup_count
    for index, pickup in description.patches.pickup_assignment.items():
        indices[index.index] = pickup_database.original_index(pickup).index

    return indices


def apply_layout(description: LayoutDescription,
                 game_root: Path,
                 backup_files_path: Path,
                 progress_update: ProgressUpdateCallable):
    """
    Applies the modifications listed in the given LayoutDescription to the game in game_root.
    :param description:
    :param game_root:
    :param backup_files_path: Path to use as pak backup, to remove/add menu mod.
    :param progress_update:
    :return:
    """

    patcher_configuration = description.permalink.patcher_configuration
    args = _base_args(game_root, hud_memo_popup_removal=patcher_configuration.disable_hud_popup)

    status_update = status_update_lib.create_progress_update_from_successive_messages(
        progress_update, 400 if patcher_configuration.menu_mod else 100)

    _ensure_no_menu_mod(game_root, backup_files_path, status_update)
    _create_pak_backups(game_root, backup_files_path, status_update)

    indices = _calculate_indices(description)

    args += [
        "-s", str(description.permalink.seed_number),
        "-p", ",".join(str(index) for index in indices),
    ]
    if description.permalink.layout_configuration.item_loss == LayoutEnabledFlag.DISABLED:
        args.append("-i")
    if description.permalink.layout_configuration.elevators == LayoutRandomizedFlag.RANDOMIZED:
        args.append("-v")

    description.save_to_file(game_root.joinpath("files", "randovania.json"))
    _run_with_args(args, "Randomized!", status_update)

    if patcher_configuration.menu_mod:
        _add_menu_mod_to_files(game_root, status_update)


def disable_echoes_attract_videos(game_root: Path,
                                  status_update: Callable[[str], None],
                                  ):
    game_files = game_root.joinpath("files")
    args = [
        str(_get_randomizer_folder().joinpath("DisableEchoesAttractVideos.exe")),
        str(game_files)
    ]
    with subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=0, universal_newlines=True) as process:
        try:
            for line in process.stdout:
                x = line.strip()
                status_update(x)
        except Exception:
            process.kill()
            raise


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
                                         ) -> Dict[int, TeleporterConnection]:
    elevator_connection = {}
    for elevator in try_randomize_elevators(claris_random.Random(seed_number)):
        elevator_connection[elevator.instance_id] = TeleporterConnection(
            elevator.connected_elevator.world_asset_id,
            elevator.connected_elevator.area_asset_id
        )
    return elevator_connection
