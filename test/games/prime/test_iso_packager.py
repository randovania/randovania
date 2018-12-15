import sys
from multiprocessing import connection
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY, call

import pytest

from randovania.games.prime import iso_packager


@patch("nod.ExtractionContext", autospec=True)
@patch("nod.open_disc_from_image", autospec=True)
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
    mock_extraction_context.called_once_with()
    context.set_progress_callback.assert_called_once_with(ANY)
    data_partition.extract_to_directory.assert_called_once_with(str(game_files_path), context)

    output_pipe.send.assert_has_calls([
        call((False, "first path", 0.5)),
        call((True, None, 100)),
    ])


@patch("nod.ExtractionContext", autospec=True)
@patch("nod.open_disc_from_image", autospec=True)
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


@patch("nod.DiscBuilderGCN", autospec=True)
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


@patch("nod.DiscBuilderGCN", autospec=True)
def test_disc_pack_process_failure(mock_disc_builder: MagicMock,
                                   ):
    # Setup
    status_queue = MagicMock()
    iso = MagicMock()
    game_files_path = MagicMock()

    def builder_side_effect(_, __):
        raise RuntimeError("Failure to do stuff")

    mock_disc_builder.side_effect = builder_side_effect

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
    with patch("multiprocessing.Process", side_effect=process_effect, autospec=True) as mock_process:
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
    with patch("multiprocessing.Process", side_effect=process_effect, autospec=True) as mock_process:
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


@patch("randovania.games.prime.iso_packager._shared_process_code", autospec=True)
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


@patch("randovania.games.prime.iso_packager._shared_process_code", autospec=True)
def test_unpack_iso_failure(mock_shared_process_code: MagicMock,
                            ):
    # Setup
    iso = MagicMock()
    game_files_path = MagicMock()
    progress_update = MagicMock()
    exception_message = "Nah, don't wanna"

    def raise_exception(*args, **kwargs):
        raise OSError(exception_message)

    game_files_path.mkdir.side_effect = raise_exception

    # Run
    with pytest.raises(RuntimeError) as exception:
        iso_packager.unpack_iso(iso, game_files_path, progress_update)

    # Assert
    game_files_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_shared_process_code.assert_not_called()
    assert str(exception.value) == "Unable to create files dir {}:\n{}".format(game_files_path, exception_message)


@patch("randovania.games.prime.claris_randomizer.disable_echoes_attract_videos", autospec=True)
def test_disable_attract_videos_helper(mock_disable_echoes_attract_videos: MagicMock,
                                       ):
    # Setup
    output_pipe = MagicMock()
    game_files_path = MagicMock()

    def side_effect(_, progress_update):
        progress_update("Have an update!")
        pass

    mock_disable_echoes_attract_videos.side_effect = side_effect

    # Run
    iso_packager._disable_attract_videos_helper(output_pipe, None, game_files_path)

    # Assert
    mock_disable_echoes_attract_videos.assert_called_once_with(game_files_path, ANY)
    game_files_path.joinpath.assert_called_once_with("files", "attract_videos_disabled.txt")
    game_files_path.joinpath.return_value.write_bytes.assert_called_once_with(b"")
    output_pipe.send.assert_has_calls([
        call((False, "Have an update!", -1)),
        call((True, None, -1)),
    ])


@pytest.mark.parametrize("already_disabled", [False, True])
@patch("randovania.games.prime.iso_packager._shared_process_code", autospec=True)
def test_disable_attract_videos(mock_shared_process_code: MagicMock,
                                tmpdir,
                                already_disabled: bool,
                                ):
    # Setup
    game_files_path = Path(tmpdir)
    progress_update = MagicMock()

    if already_disabled:
        game_files_path.joinpath("files").mkdir(parents=True)
        game_files_path.joinpath("files", "attract_videos_disabled.txt").write_bytes(b"")

    # Run
    iso_packager._disable_attract_videos(game_files_path, progress_update)

    # Assert
    if already_disabled:
        mock_shared_process_code.assert_not_called()
    else:
        mock_shared_process_code.assert_called_once_with(
            target=iso_packager._disable_attract_videos_helper,
            iso=ANY,
            game_files_path=game_files_path,
            on_finish_message="Finished disabling attract videos.",
            progress_update=progress_update
        )


def test_can_process_iso_success():
    assert iso_packager.can_process_iso()


def test_can_process_iso_failure():
    with patch.dict(sys.modules, nod=None):
        del sys.modules["randovania.games.prime.iso_packager"]
        from randovania.games.prime.iso_packager import can_process_iso
        assert not can_process_iso()
