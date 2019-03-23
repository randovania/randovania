from pathlib import Path
from typing import List, Union
from unittest.mock import patch, MagicMock, call, ANY

import pytest

import randovania
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.game_patches import GamePatches
from randovania.games.prime import claris_randomizer, claris_random
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.permalink import Permalink

LayoutDescriptionMock = Union[MagicMock, LayoutDescription]


class CustomException(Exception):
    @classmethod
    def do_raise(cls, x):
        raise CustomException("test exception")


def _create_description_mock(permalink: Permalink, empty_patches: GamePatches):
    return MagicMock(spec=LayoutDescription(
        version=randovania.VERSION,
        permalink=permalink,
        patches=empty_patches,
        solver_path=()
    ))


@pytest.fixture(name="description")
def _description(empty_patches) -> LayoutDescription:
    return _create_description_mock(Permalink.default(), empty_patches)


@pytest.fixture(
    params=[False, True],
    name="mock_is_windows")
def _mock_is_windows(request):
    with patch("randovania.games.prime.claris_randomizer._is_windows", return_value=request.param):
        yield request.param


@patch("randovania.games.prime.claris_randomizer._process_command", autospec=True)
def test_run_with_args_success(mock_process_command: MagicMock,
                               mock_is_windows: bool,
                               ):
    # Setup
    args = [MagicMock(), MagicMock()]
    finish_string = "We are done!"
    status_update = MagicMock()
    lines = [
        "line 1",
        "line 2",
        finish_string,
        "post line"
    ]

    def side_effect(_, __, read_callback):
        for line in lines:
            read_callback(line)

    mock_process_command.side_effect = side_effect

    # Run
    claris_randomizer._run_with_args(args, "", finish_string, status_update)

    # Assert
    mock_process_command.assert_called_once_with(
        ([] if mock_is_windows else ["mono"]) + [str(x) for x in args], "", ANY)
    status_update.assert_has_calls([
        call("line 1"),
        call("line 2"),
        call(finish_string),
    ])


@patch("randovania.games.prime.claris_randomizer._process_command", autospec=True)
def test_run_with_args_failure(mock_process_command: MagicMock,
                               mock_is_windows: bool,
                               ):
    # Setup
    input_data = "asdf"
    finish_string = "We are done!"
    status_update = MagicMock()
    lines = [
        "line 1",
        "line 2",
        "post line"
    ]

    def side_effect(_, __, read_callback):
        for line in lines:
            read_callback(line)

    mock_process_command.side_effect = side_effect

    # Run
    with pytest.raises(RuntimeError) as error:
        claris_randomizer._run_with_args([], input_data, finish_string, status_update)

    # Assert
    mock_process_command.assert_called_once_with([] if mock_is_windows else ["mono"], input_data, ANY)
    status_update.assert_has_calls([
        call("line 1"),
        call("line 2"),
        call("post line"),
    ])
    assert str(error.value) == "External tool did not send '{}'. Did something happen?".format(finish_string)


@patch("randovania.games.prime.claris_randomizer.validate_game_files_path", autospec=True)
@patch("randovania.games.prime.claris_randomizer.get_data_path", autospec=True)
def test_base_args(mock_get_data_path: MagicMock,
                   mock_validate_game_files_path: MagicMock,
                   ):
    # Setup
    mock_get_data_path.return_value = Path("data")
    game_root = Path("root")

    # Run
    results = claris_randomizer._base_args(game_root)

    # Assert
    expected_results = [
        Path("data", "ClarisPrimeRandomizer", "Randomizer.exe"),
        Path("root"),
    ]

    assert results == expected_results
    mock_validate_game_files_path.assert_called_once_with(Path("root", "files"))


@pytest.mark.parametrize("has_menu_mod", [False, True])
@pytest.mark.parametrize("has_backup", [False, True, None])
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

    elif has_backup is None:
        backup_files_path = None

    # Run
    if has_menu_mod and has_backup is None:
        with pytest.raises(RuntimeError) as exc:
            claris_randomizer._ensure_no_menu_mod(game_root, backup_files_path, status_update)
        assert str(exc.value) == "Game at '{}' has Menu Mod, but no backup path given to restore".format(game_root)
    else:
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
        [Path("data", "ClarisEchoesMenu", "EchoesMenu.exe"), game_root.joinpath("files")],
        "",
        "Done!",
        status_update
    )
    assert game_root.joinpath("files", "menu_mod.txt").is_file()


@pytest.mark.parametrize("modern", [True])
@pytest.mark.parametrize("include_menu_mod", [False, True])
@pytest.mark.parametrize("has_backup_path", [False, True])
@patch("randovania.layout.layout_description.LayoutDescription.save_to_file", autospec=True)
@patch("randovania.interface_common.status_update_lib.create_progress_update_from_successive_messages", autospec=True)
@patch("randovania.games.prime.claris_randomizer._modern_api", autospec=True)
@patch("randovania.games.prime.claris_randomizer._add_menu_mod_to_files", autospec=True)
@patch("randovania.games.prime.claris_randomizer._create_pak_backups", autospec=True)
@patch("randovania.games.prime.claris_randomizer._ensure_no_menu_mod", autospec=True)
def test_apply_layout(
        mock_ensure_no_menu_mod: MagicMock,
        mock_create_pak_backups: MagicMock,
        mock_add_menu_mod_to_files: MagicMock,
        mock_modern_api: MagicMock,
        mock_create_progress_update_from_successive_messages: MagicMock,
        mock_save_to_file: MagicMock,
        modern: bool,
        include_menu_mod: bool,
        has_backup_path: bool,
):
    # Setup
    cosmetic_patches = MagicMock()
    description = LayoutDescription(
        version=randovania.VERSION,
        permalink=Permalink(
            seed_number=1,
            spoiler=False,
            patcher_configuration=PatcherConfiguration(
                menu_mod=include_menu_mod,
                warp_to_start=MagicMock(),
            ),
            layout_configuration=MagicMock()
        ),
        patches=MagicMock(),
        solver_path=(),
    )

    game_root = MagicMock(spec=Path())
    backup_files_path = MagicMock() if has_backup_path else None
    progress_update = MagicMock()
    status_update = mock_create_progress_update_from_successive_messages.return_value

    # Run
    claris_randomizer.apply_layout(description, cosmetic_patches, backup_files_path, progress_update, game_root, modern)

    # Assert
    mock_create_progress_update_from_successive_messages.assert_called_once_with(
        progress_update,
        400 if include_menu_mod else 100
    )
    mock_ensure_no_menu_mod.assert_called_once_with(game_root, backup_files_path, status_update)
    if has_backup_path:
        mock_create_pak_backups.assert_called_once_with(game_root, backup_files_path, status_update)
    else:
        mock_create_pak_backups.assert_not_called()
    game_root.joinpath.assert_called_once_with("files", "randovania.json")
    mock_save_to_file.assert_called_once_with(description, game_root.joinpath.return_value)

    if modern:
        mock_modern_api.assert_called_once_with(game_root, status_update, description, cosmetic_patches)
    else:
        mock_modern_api.assert_not_called()

    if include_menu_mod:
        mock_add_menu_mod_to_files.assert_called_once_with(game_root, status_update)
    else:
        mock_add_menu_mod_to_files.assert_not_called()


@patch("randovania.games.prime.patcher_file.create_patcher_file", autospec=True)
@patch("randovania.games.prime.claris_randomizer._base_args", autospec=True)
@patch("randovania.games.prime.claris_randomizer._run_with_args", autospec=True)
def test_modern_api(mock_run_with_args: MagicMock,
                    mock_base_args: MagicMock,
                    mock_create_patcher_file: MagicMock,
                    ):
    # Setup
    game_root = MagicMock(spec=Path())
    status_update = MagicMock()
    description = MagicMock()
    cosmetic_patches = MagicMock()

    mock_base_args.return_value = []
    mock_create_patcher_file.return_value = {"some_data": 123}

    # Run
    claris_randomizer._modern_api(game_root, status_update, description, cosmetic_patches)

    # Assert
    mock_base_args.assert_called_once_with(game_root)
    mock_create_patcher_file.assert_called_once_with(description, cosmetic_patches)
    mock_run_with_args.assert_called_once_with([], '{"some_data": 123}', "Randomized!", status_update)


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
        elevator.instance_id: AreaLocation(elevator.connected_elevator.world_asset_id,
                                           elevator.connected_elevator.area_asset_id)
    }
