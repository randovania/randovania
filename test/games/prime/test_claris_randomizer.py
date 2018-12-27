import subprocess
from pathlib import Path
from typing import List, Union
from unittest.mock import patch, MagicMock, call, ANY

import pytest

import randovania
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import TeleporterConnection
from randovania.game_description.resources import PickupDatabase
from randovania.games.prime import claris_randomizer, claris_random
from randovania.resolver.layout_configuration import LayoutEnabledFlag, LayoutRandomizedFlag, LayoutConfiguration
from randovania.resolver.layout_description import LayoutDescription
from randovania.resolver.patcher_configuration import PatcherConfiguration
from randovania.resolver.permalink import Permalink

LayoutDescriptionMock = Union[MagicMock, LayoutDescription]


class CustomException(Exception):
    @classmethod
    def do_raise(cls, x):
        raise CustomException("test exception")


def _create_description_mock(permalink: Permalink):
    return MagicMock(spec=LayoutDescription(
        version=randovania.VERSION,
        permalink=permalink,
        patches=GamePatches.empty(),
        solver_path=()
    ))


@pytest.fixture(name="description")
def _description() -> LayoutDescription:
    return _create_description_mock(Permalink.default())


@patch("subprocess.Popen", autospec=True)
def test_run_with_args_success(mock_popen: MagicMock,
                               ):
    # Setup
    args = [MagicMock(), MagicMock()]
    finish_string = "We are done!"
    status_update = MagicMock()
    process = mock_popen.return_value.__enter__.return_value
    process.stdout = [
        " line 1",
        "line 2 ",
        "   ",
        finish_string,
        " post line "
    ]

    # Run
    claris_randomizer._run_with_args(args, finish_string, status_update)

    # Assert
    mock_popen.assert_called_once_with(
        [str(x) for x in args],
        stdout=subprocess.PIPE, bufsize=0, universal_newlines=True
    )
    status_update.assert_has_calls([
        call("line 1"),
        call("line 2"),
        call(finish_string),
    ])
    process.kill.assert_not_called()


@patch("subprocess.Popen", autospec=True)
def test_run_with_args_failure(mock_popen: MagicMock,
                               ):
    # Setup
    finish_string = "We are done!"
    process = mock_popen.return_value.__enter__.return_value
    process.stdout = [" line 1"]

    # Run
    with pytest.raises(CustomException):
        claris_randomizer._run_with_args([], finish_string, CustomException.do_raise)

    # Assert
    mock_popen.assert_called_once_with([], stdout=subprocess.PIPE, bufsize=0, universal_newlines=True)
    process.kill.assert_called_once_with()


@pytest.mark.parametrize("hud_memo_popup_removal", [False, True])
@patch("randovania.games.prime.claris_randomizer.validate_game_files_path", autospec=True)
@patch("randovania.games.prime.claris_randomizer.get_data_path", autospec=True)
def test_base_args(mock_get_data_path: MagicMock,
                   mock_validate_game_files_path: MagicMock,
                   hud_memo_popup_removal: bool
                   ):
    # Setup
    mock_get_data_path.return_value = Path("data")
    game_root = Path("root")

    # Run
    results = claris_randomizer._base_args(game_root, hud_memo_popup_removal)

    # Assert
    expected_results = [
        Path("data", "ClarisPrimeRandomizer", "Randomizer.exe"),
        Path("root", "files"),
        "-r"
    ]
    if hud_memo_popup_removal:
        expected_results.append("-h")

    assert results == expected_results
    mock_validate_game_files_path.assert_called_once_with(Path("root", "files"))


@pytest.mark.parametrize("has_menu_mod", [False, True])
@pytest.mark.parametrize("has_backup", [False, True])
@patch("shutil.copy", autospec=True)
def test_ensure_no_menu_mod(mock_copy: MagicMock,
                            tmpdir,
                            has_menu_mod: bool,
                            has_backup: bool,
                            ):
    # Setup
    game_root = Path(tmpdir.join("root"))
    backup_files_path = Path(tmpdir.join("backup"))
    status_update = MagicMock()
    files_folder = game_root.joinpath("files")
    mod_txt = files_folder.joinpath("menu_mod.txt")
    paks = ("1.pak", "2.pak")

    if has_menu_mod:
        mod_txt.parent.mkdir(parents=True)
        mod_txt.write_bytes(b"")

    if has_backup:
        pak_folder = backup_files_path.joinpath("mp2_paks")
        pak_folder.mkdir(parents=True)
        for pak in paks:
            pak_folder.joinpath(pak).write_bytes(b"")

    # Run
    claris_randomizer._ensure_no_menu_mod(game_root, backup_files_path, status_update)

    # Assert
    if has_menu_mod:
        assert mod_txt.exists() != has_backup

    if has_menu_mod and has_backup:
        # In any order, because file systems don't have guaranteed order
        status_update.assert_has_calls([
            call("Restoring {} from backup".format(pak_name))
            for pak_name in paks
        ], any_order=True)
        mock_copy.assert_has_calls([
            call(backup_files_path.joinpath("mp2_paks", pak_name), files_folder.joinpath(pak_name))
            for pak_name in paks
        ], any_order=True)
    else:
        status_update.assert_not_called()
        mock_copy.assert_not_called()


@pytest.mark.parametrize("missing_pak", claris_randomizer._ECHOES_PAKS)
@patch("shutil.copy", autospec=True)
def test_create_pak_backups(mock_copy: MagicMock,
                            tmpdir,
                            missing_pak: str
                            ):
    # Setup
    game_root = Path(tmpdir.join("root"))
    backup_files_path = Path(tmpdir.join("backup"))
    status_update = MagicMock()

    pak_folder = backup_files_path.joinpath("mp2_paks")
    pak_folder.mkdir(parents=True)
    for pak in claris_randomizer._ECHOES_PAKS:
        if pak != missing_pak:
            pak_folder.joinpath(pak).write_bytes(b"")

    # Run
    claris_randomizer._create_pak_backups(game_root, backup_files_path, status_update)

    # Assert
    status_update.assert_called_once_with("Backing up {}".format(missing_pak))
    mock_copy.assert_called_once_with(game_root.joinpath("files", missing_pak),
                                      pak_folder.joinpath(missing_pak))


@patch("shutil.copy", autospec=True)
def test_create_pak_backups_no_existing(mock_copy: MagicMock,
                                        tmpdir,
                                        ):
    # Setup
    game_root = Path(tmpdir.join("root"))
    backup_files_path = Path(tmpdir.join("backup"))
    status_update = MagicMock()

    # Run
    claris_randomizer._create_pak_backups(game_root, backup_files_path, status_update)

    # Assert
    status_update.assert_has_calls([
        call("Backing up {}".format(pak))
        for pak in claris_randomizer._ECHOES_PAKS
    ])
    mock_copy.assert_has_calls([
        call(game_root.joinpath("files", pak), backup_files_path.joinpath("mp2_paks", pak))
        for pak in claris_randomizer._ECHOES_PAKS
    ])


@patch("randovania.games.prime.claris_randomizer._run_with_args", autospec=True)
@patch("randovania.games.prime.claris_randomizer.get_data_path", autospec=True)
def test_add_menu_mod_to_files(mock_get_data_path: MagicMock,
                               mock_run_with_args: MagicMock,
                               tmpdir,
                               ):
    # Setup
    mock_get_data_path.return_value = Path("data")
    game_root = Path(tmpdir.join("root"))
    status_update = MagicMock()
    game_root.joinpath("files").mkdir(parents=True)

    # Run
    claris_randomizer._add_menu_mod_to_files(game_root, status_update)

    # Assert
    mock_run_with_args.assert_called_once_with(
        [Path("data", "ClarisEchoesMenu", "EchoesMenu.exe"),
         game_root.joinpath("files")],
        "Done!",
        status_update
    )
    assert game_root.joinpath("files", "menu_mod.txt").is_file()


@patch("randovania.game_description.data_reader.read_databases", autospec=True)
def test_calculate_indices_no_item(mock_read_databases: MagicMock,
                                   echoes_pickup_database: PickupDatabase,
                                   ):
    # Setup
    description = LayoutDescription(
        version=randovania.VERSION,
        permalink=Permalink.default(),
        patches=GamePatches.empty(),
        solver_path=()
    )
    mock_read_databases.return_value = (None, echoes_pickup_database)

    # Run
    result = claris_randomizer._calculate_indices(description)

    # Assert
    mock_read_databases.assert_called_once_with(description.permalink.layout_configuration.game_data)
    useless_pickup = echoes_pickup_database.pickup_by_name(claris_randomizer._USELESS_PICKUP_NAME)
    useless_index = echoes_pickup_database.original_index(useless_pickup)
    assert result == [useless_index.index] * echoes_pickup_database.total_pickup_count


@patch("randovania.game_description.data_reader.read_databases", autospec=True)
def test_calculate_indices_original(mock_read_databases: MagicMock,
                                    echoes_pickup_database: PickupDatabase,
                                    ):
    # Setup
    description = LayoutDescription(
        version=randovania.VERSION,
        permalink=Permalink.default(),
        patches=GamePatches(
            echoes_pickup_database.original_pickup_mapping,
            {}, {}, {}
        ),
        solver_path=()
    )
    mock_read_databases.return_value = (None, echoes_pickup_database)

    # Run
    result = claris_randomizer._calculate_indices(description)

    # Assert
    mock_read_databases.assert_called_once_with(description.permalink.layout_configuration.game_data)
    assert result == [
        echoes_pickup_database.original_index(pickup).index
        for pickup in echoes_pickup_database.original_pickup_mapping.values()
    ]


@pytest.mark.parametrize("include_menu_mod", [False, True])
@pytest.mark.parametrize("elevators", [False, True])
@pytest.mark.parametrize("item_loss", [False, True])
@pytest.mark.parametrize("seed_number", [1000, 8500])
@patch("randovania.resolver.layout_description.LayoutDescription.save_to_file", autospec=True)
@patch("randovania.interface_common.status_update_lib.create_progress_update_from_successive_messages", autospec=True)
@patch("randovania.games.prime.claris_randomizer._add_menu_mod_to_files", autospec=True)
@patch("randovania.games.prime.claris_randomizer._calculate_indices", autospec=True)
@patch("randovania.games.prime.claris_randomizer._create_pak_backups", autospec=True)
@patch("randovania.games.prime.claris_randomizer._ensure_no_menu_mod", autospec=True)
@patch("randovania.games.prime.claris_randomizer._base_args", autospec=True)
@patch("randovania.games.prime.claris_randomizer._run_with_args", autospec=True)
def test_apply_layout(mock_run_with_args: MagicMock,
                      mock_base_args: MagicMock,
                      mock_ensure_no_menu_mod: MagicMock,
                      mock_create_pak_backups: MagicMock,
                      mock_calculate_indices: MagicMock,
                      mock_add_menu_mod_to_files: MagicMock,
                      mock_create_progress_update_from_successive_messages: MagicMock,
                      mock_save_to_file: MagicMock,
                      seed_number: int,
                      item_loss: bool,
                      elevators: bool,
                      include_menu_mod: bool,
                      ):
    # Setup
    hud_memo_popup_removal: bool = MagicMock()
    description = LayoutDescription(
        version=randovania.VERSION,
        permalink=Permalink(
            seed_number=seed_number,
            spoiler=False,
            patcher_configuration=PatcherConfiguration(
                disable_hud_popup=hud_memo_popup_removal,
                menu_mod=include_menu_mod,
            ),
            layout_configuration=LayoutConfiguration.from_params(
                trick_level=MagicMock(),
                sky_temple_keys=MagicMock(),
                item_loss=LayoutEnabledFlag.ENABLED if item_loss else LayoutEnabledFlag.DISABLED,
                elevators=LayoutRandomizedFlag.RANDOMIZED if elevators else LayoutRandomizedFlag.VANILLA,
                pickup_quantities={},
            )
        ),
        patches=GamePatches.empty(),
        solver_path=(),
    )

    game_root = MagicMock(spec=Path())
    backup_files_path = MagicMock()
    progress_update = MagicMock()
    status_update = mock_create_progress_update_from_successive_messages.return_value

    mock_calculate_indices.return_value = [10, 25, 1, 2, 5, 1]
    mock_base_args.return_value = []
    expected_args = [
        "-s", str(seed_number),
        "-p", "10,25,1,2,5,1"
    ]
    if not item_loss:
        expected_args.append("-i")
    if elevators:
        expected_args.append("-v")

    # Run
    claris_randomizer.apply_layout(description, game_root, backup_files_path, progress_update)

    # Assert
    mock_base_args.assert_called_once_with(game_root, hud_memo_popup_removal=hud_memo_popup_removal)
    mock_create_progress_update_from_successive_messages.assert_called_once_with(
        progress_update,
        400 if include_menu_mod else 100
    )
    mock_ensure_no_menu_mod.assert_called_once_with(game_root, backup_files_path, status_update)
    mock_create_pak_backups.assert_called_once_with(game_root, backup_files_path, status_update)
    mock_calculate_indices.assert_called_once_with(description)
    game_root.joinpath.assert_called_once_with("files", "randovania.json")
    mock_save_to_file.assert_called_once_with(description, game_root.joinpath.return_value)
    mock_run_with_args.assert_called_once_with(expected_args, "Randomized!", status_update)
    if include_menu_mod:
        mock_add_menu_mod_to_files.assert_called_once_with(game_root, status_update)
    else:
        mock_add_menu_mod_to_files.assert_not_called()


@patch("randovania.games.prime.claris_randomizer._get_randomizer_folder", autospec=True)
@patch("subprocess.Popen", autospec=True)
def test_disable_echoes_attract_videos_success(mock_popen: MagicMock,
                                               mock_get_randomizer_folder: MagicMock,
                                               ):
    # Setup
    mock_get_randomizer_folder.return_value = Path("randomizer_folder")
    game_root = Path("game_folder")
    status_update = MagicMock()

    process = mock_popen.return_value.__enter__.return_value
    process.stdout = [
        " line 1",
        "line 2 ",
        "   ",
        " line 3 "
    ]

    # Run
    claris_randomizer.disable_echoes_attract_videos(game_root, status_update)

    # Assert
    mock_get_randomizer_folder.assert_called_once_with()
    mock_popen.assert_called_once_with(
        [str(Path("randomizer_folder", "DisableEchoesAttractVideos.exe")),
         str(Path("game_folder", "files"))],
        stdout=subprocess.PIPE, bufsize=0, universal_newlines=True
    )
    status_update.assert_has_calls([
        call("line 1"),
        call("line 2"),
        call(""),
        call("line 3"),
    ])
    process.kill.assert_not_called()


@patch("randovania.games.prime.claris_randomizer._get_randomizer_folder", autospec=True)
@patch("subprocess.Popen", autospec=True)
def test_disable_echoes_attract_videos_failure(mock_popen: MagicMock,
                                               mock_get_randomizer_folder: MagicMock,
                                               ):
    # Setup
    game_root = MagicMock()
    status_update = MagicMock(side_effect=CustomException.do_raise)
    process = mock_popen.return_value.__enter__.return_value
    process.stdout = [
        " line 1",
    ]

    # Run
    with pytest.raises(CustomException):
        claris_randomizer.disable_echoes_attract_videos(game_root, status_update)

    # Assert
    mock_get_randomizer_folder.assert_called_once_with()
    mock_popen.assert_called_once_with(ANY, stdout=subprocess.PIPE, bufsize=0, universal_newlines=True)
    status_update.assert_called_once_with("line 1")
    process.kill.assert_called_once_with()


@pytest.mark.parametrize(["seed_number", "expected_ids"], [
    (5000, [38, 1245332, 129, 2162826, 393260, 122, 1245307, 3342446, 4522032,
            3538975, 152, 1638535, 1966093, 2097251, 524321, 589851, 1572998, 2949235]),
    (9000, [129, 2949235, 2162826, 1245307, 122, 1245332, 4522032, 38, 1638535,
            3342446, 2097251, 1572998, 589851, 1966093, 152, 393260, 3538975, 524321]),
    # This seed takes multiple tries
    (1157772449, [2162826, 38, 2949235, 1245307, 393260, 4522032, 129, 3342446, 1245332,
                  1638535, 2097251, 1966093, 152, 589851, 3538975, 1572998, 524321, 122])
])
def test_try_randomize_elevators(seed_number: int, expected_ids: List[int]):
    # Setup
    rng = claris_random.Random(seed_number)

    # Run
    result = claris_randomizer.try_randomize_elevators(rng)
    connected_ids = [elevator.connected_elevator.instance_id for elevator in result]

    # Assert
    assert connected_ids == expected_ids


@patch("randovania.games.prime.claris_random.Random", autospec=True)
@patch("randovania.games.prime.claris_randomizer.try_randomize_elevators", autospec=True)
def test_elevator_connections_for_seed_number(mock_try_randomize_elevators: MagicMock,
                                              mock_random: MagicMock):
    # Setup
    seed_number: int = MagicMock()
    elevator = MagicMock()
    mock_try_randomize_elevators.return_value = [
        elevator
    ]

    # Run
    result = claris_randomizer.elevator_connections_for_seed_number(seed_number)

    # Assert
    mock_random.assert_called_once_with(seed_number)
    mock_try_randomize_elevators.assert_called_once_with(mock_random.return_value)
    assert result == {
        elevator.instance_id: TeleporterConnection(elevator.connected_elevator.world_asset_id,
                                                   elevator.connected_elevator.area_asset_id)
    }
