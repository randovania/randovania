import sys
from multiprocessing import connection
from unittest.mock import patch, MagicMock, ANY, call

import pytest

from randovania.games.patchers.gamecube import iso_packager

work_around_pytest_qt_bug = False  # TODO: pytest-qt bug


@patch("nod.ExtractionContext", autospec=work_around_pytest_qt_bug)
@patch("nod.open_disc_from_image", autospec=work_around_pytest_qt_bug)
def test_disc_unpack_process_valid(mock_open_disc_from_image: MagicMock,
                                   mock_extraction_context: MagicMock,
                                   ):
    # TODO: invalid ISO

    # Setup
    output_pipe = MagicMock()
    iso = MagicMock()
    game_files_path = MagicMock()

    disc = MagicMock()
    mock_open_disc_from_image.return_value = disc, False
    data_partition = disc.get_data_partition.return_value

    def set_progress_side_effect(callable):
        callable("first path", 0.5)

    context = mock_extraction_context.return_value
    context.set_progress_callback.side_effect = set_progress_side_effect

    # Run
    iso_packager._disc_unpack_process(output_pipe, iso, game_files_path)

    # Assert
    mock_open_disc_from_image.assert_called_once_with(str(iso))
    disc.get_data_partition.assert_called_once_with()
    mock_extraction_context.assert_called_once_with()
    context.set_progress_callback.assert_called_once_with(ANY)
    data_partition.extract_to_directory.assert_called_once_with(str(game_files_path), context)

    output_pipe.send.assert_has_calls([
        call((False, "first path", 0.5)),
        call((True, None, 100)),
    ])


@patch("nod.ExtractionContext", autospec=work_around_pytest_qt_bug)
@patch("nod.open_disc_from_image", autospec=work_around_pytest_qt_bug)
def test_disc_unpack_process_invalid(mock_open_disc_from_image: MagicMock,
                                     mock_extraction_context: MagicMock,
                                     ):
    # Setup
    output_pipe = MagicMock()
    iso = MagicMock()
    game_files_path = MagicMock()

    disc = MagicMock()
    mock_open_disc_from_image.return_value = disc, False
    disc.get_data_partition.return_value = None

    # Run
    iso_packager._disc_unpack_process(output_pipe, iso, game_files_path)

    # Assert
    mock_open_disc_from_image.assert_called_once_with(str(iso))
    disc.get_data_partition.assert_called_once_with()
    mock_extraction_context.assert_not_called()

    output_pipe.send.assert_called_once_with(
        (True, "Could not find a data partition in '{}'.\nIs it a valid Metroid Prime 2 ISO?".format(iso), 0)
    )


@patch("nod.DiscBuilderGCN", autospec=work_around_pytest_qt_bug)
def test_disc_pack_process_success(mock_disc_builder: MagicMock,
                                   ):
    # Setup
    status_queue = MagicMock()
    iso = MagicMock()
    game_files_path = MagicMock()
    disc_builder = mock_disc_builder.return_value

    def builder_side_effect(_, callback):
        callback(0.5, "file one", 123456)
        return disc_builder

    mock_disc_builder.side_effect = builder_side_effect

    # Run
    iso_packager._disc_pack_process(status_queue, iso, game_files_path)

    # Assert
    mock_disc_builder.assert_called_once_with(str(iso), ANY)
    disc_builder.build_from_directory.assert_called_once_with(str(game_files_path))
    status_queue.send.assert_has_calls([
        call((False, "file one", 0.5)),
        call((True, None, 100)),
    ])


@patch("nod.DiscBuilderGCN", autospec=work_around_pytest_qt_bug)
def test_disc_pack_process_failure(mock_disc_builder: MagicMock,
                                   ):
    # Setup
    status_queue = MagicMock()
    iso = MagicMock()
    game_files_path = MagicMock()

    mock_disc_builder.side_effect = RuntimeError("Failure to do stuff")

    # Run
    iso_packager._disc_pack_process(status_queue, iso, game_files_path)

    # Assert
    mock_disc_builder.assert_called_once_with(str(iso), ANY)
    status_queue.send.assert_called_once_with((True, "Failure to do stuff", 0))


def test_shared_process_code_success():
    # Setup
    mock_target = MagicMock()
    iso = MagicMock()
    game_files_path = MagicMock()
    on_finish_message = MagicMock()
    progress_update = MagicMock()

    process = MagicMock()

    def process_effect(target, args):
        output_pipe: connection.Connection = args[0]
        output_pipe.send((False, "Message 1", 0.2))
        output_pipe.send((False, "Message 2", 0.5))
        output_pipe.send((True, None, 100))
        return process

    # Run
    with patch("multiprocessing.Process", side_effect=process_effect,
               autospec=work_around_pytest_qt_bug) as mock_process:
        iso_packager._shared_process_code(mock_target, iso, game_files_path, on_finish_message, progress_update)

    mock_process.assert_called_once_with(target=mock_target, args=(ANY, iso, game_files_path))
    process.start.assert_called_once_with()
    process.terminate.assert_called_once_with()
    progress_update.assert_has_calls([
        call("", 0),
        call("Message 1", 0.2),
        call("Message 2", 0.5),
        call(on_finish_message, 1),
    ])


def test_shared_process_code_failure():
    # Setup
    mock_target = MagicMock()
    iso = MagicMock()
    game_files_path = MagicMock()
    on_finish_message = MagicMock()
    progress_update = MagicMock()

    process = MagicMock()

    def process_effect(target, args):
        output_pipe: connection.Connection = args[0]
        output_pipe.send((False, "Message 1", 0.2))
        output_pipe.send((True, "You got an error!", 100))
        return process

    # Run
    with patch("multiprocessing.Process", side_effect=process_effect,
               autospec=work_around_pytest_qt_bug) as mock_process:
        with pytest.raises(RuntimeError) as exception:
            iso_packager._shared_process_code(mock_target, iso, game_files_path, on_finish_message, progress_update)

    mock_process.assert_called_once_with(target=mock_target, args=(ANY, iso, game_files_path))
    process.start.assert_called_once_with()
    process.terminate.assert_called_once_with()
    progress_update.assert_has_calls([
        call("", 0),
        call("Message 1", 0.2),
    ])
    assert str(exception.value) == "You got an error!"


@patch("randovania.games.patchers.gamecube.iso_packager._shared_process_code", autospec=True)
def test_unpack_iso_success(mock_shared_process_code: MagicMock,
                            ):
    # Setup
    iso = MagicMock()
    game_files_path = MagicMock()
    progress_update = MagicMock()

    # Run
    iso_packager.unpack_iso(iso, game_files_path, progress_update)

    # Assert
    game_files_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_shared_process_code.assert_called_once_with(
        target=iso_packager._disc_unpack_process,
        iso=iso,
        game_files_path=game_files_path,
        on_finish_message="Finished extracting ISO",
        progress_update=progress_update
    )


@patch("randovania.games.patchers.gamecube.iso_packager._shared_process_code", autospec=True)
def test_unpack_iso_failure(mock_shared_process_code: MagicMock,
                            ):
    # Setup
    iso = MagicMock()
    game_files_path = MagicMock()
    progress_update = MagicMock()
    exception_message = "Nah, don't wanna"

    game_files_path.mkdir.side_effect = OSError(exception_message)

    # Run
    with pytest.raises(RuntimeError) as exception:
        iso_packager.unpack_iso(iso, game_files_path, progress_update)

    # Assert
    game_files_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_shared_process_code.assert_not_called()
    assert str(exception.value) == "Unable to create files dir {}:\n{}".format(game_files_path, exception_message)


@pytest.mark.parametrize("iso_too_big", [False, True])
@patch("randovania.games.patchers.gamecube.iso_packager.nod")
@patch("randovania.games.patchers.gamecube.iso_packager._shared_process_code", autospec=True)
@patch("randovania.games.patchers.gamecube.iso_packager.validate_game_files_path", autospec=True)
def test_pack_iso(mock_validate_game_files_path: MagicMock,
                  mock_shared_process_code: MagicMock,
                  mock_nod: MagicMock,
                  iso_too_big: bool):
    # Setup
    iso = MagicMock()
    game_files_path = MagicMock()
    progress_update = MagicMock()

    sizes = [None if iso_too_big else 1]

    mock_calculate_total_size_required = mock_nod.DiscBuilderGCN.calculate_total_size_required
    mock_calculate_total_size_required.side_effect = sizes
    mock_nod.VERSION = "1.1.0"

    def run():
        iso_packager.pack_iso(iso, game_files_path, progress_update)

    # Run
    if iso_too_big:
        with pytest.raises(RuntimeError) as exception:
            run()
        assert str(exception.value) == "Image built with given directory would pass the maximum size."
    else:
        run()

    # Assert
    mock_validate_game_files_path.assert_called_once_with(game_files_path.joinpath.return_value)

    mock_calculate_total_size_required.assert_has_calls([
        call(str(game_files_path))
        for _ in sizes
    ])

    if iso_too_big:
        mock_shared_process_code.assert_not_called()
    else:
        mock_shared_process_code.assert_called_once_with(
            target=iso_packager._disc_pack_process,
            iso=iso,
            game_files_path=game_files_path,
            on_finish_message="Finished packing ISO",
            progress_update=progress_update
        )


@patch("randovania.games.patchers.gamecube.iso_packager.nod")
@patch("randovania.games.patchers.gamecube.iso_packager.validate_game_files_path", autospec=True)
def test_pack_iso_invalid_version(mock_validate_game_files_path: MagicMock,
                                  mock_nod: MagicMock,
                                  ):
    # Setup
    game_files_path = MagicMock()
    mock_nod.VERSION = "1.0.0"

    # Run
    with pytest.raises(RuntimeError) as exception:
        iso_packager.pack_iso(None, game_files_path, None)

    # Assert
    mock_validate_game_files_path.assert_called_once_with(game_files_path.joinpath.return_value)
    assert str(exception.value) == "Installed nod version (1.0) is older than required 1.1.0"


def test_can_process_iso_success():
    assert iso_packager.can_process_iso()


def test_can_process_iso_failure():
    with patch.dict(sys.modules, nod=None):
        del sys.modules["randovania.games.patchers.gamecube.iso_packager"]
        from randovania.games.patchers.gamecube.iso_packager import can_process_iso
        assert not can_process_iso()
