from unittest.mock import patch, MagicMock, ANY, call

import pytest
import os

from randovania.patching.patchers.gamecube import iso_packager


def test_unpack_iso_bad_iso(mocker):
    # Setup
    iso = MagicMock()
    game_files_path = MagicMock()

    mock_nod = mocker.patch("randovania.patching.patchers.gamecube.iso_packager.nod")

    disc = MagicMock()
    mock_nod.open_disc_from_image.return_value = disc, False
    disc.get_data_partition.return_value = None

    # Run
    with pytest.raises(RuntimeError, match=f"Could not find a data partition in '{iso}'."
                                           f"\nIs it a valid Metroid Prime 2 ISO?"):
        iso_packager.unpack_iso(iso, game_files_path, MagicMock())

    # Assert
    mock_nod.open_disc_from_image.assert_called_once_with(iso)
    disc.get_data_partition.assert_called_once_with()
    mock_nod.ExtractionContext.assert_not_called()


def test_unpack_iso_success(mocker):
    # Setup
    iso = MagicMock()
    game_files_path = MagicMock()
    progress_update = MagicMock()

    mock_disc = MagicMock()

    mock_nod = mocker.patch("randovania.patching.patchers.gamecube.iso_packager.nod")
    mock_nod.open_disc_from_image.return_value = (mock_disc, False)

    # Run
    iso_packager.unpack_iso(iso, game_files_path, progress_update)

    # Assert
    game_files_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_nod.open_disc_from_image.assert_called_once_with(iso)
    mock_disc.get_data_partition.assert_called_once_with()
    mock_disc.get_data_partition.return_value.extract_to_directory.assert_called_once_with(
        os.fspath(game_files_path), mock_nod.ExtractionContext.return_value,
    )
    mock_nod.ExtractionContext.return_value.set_progress_callback.assert_called_once_with(progress_update)


def test_unpack_iso_failure():
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
    assert str(exception.value) == f"Unable to create files dir {game_files_path}:\n{exception_message}"


@pytest.mark.parametrize("iso_too_big", [False, True])
@patch("randovania.patching.patchers.gamecube.iso_packager.nod")
@patch("randovania.patching.patchers.gamecube.iso_packager.validate_game_files_path", autospec=True)
def test_pack_iso(mock_validate_game_files_path: MagicMock,
                  mock_nod: MagicMock,
                  iso_too_big: bool):
    # Setup
    iso = MagicMock()
    game_files_path = MagicMock()
    progress_update = MagicMock()

    sizes = [None if iso_too_big else 1]

    mock_calculate_total_size_required = mock_nod.DiscBuilderGCN.calculate_total_size_required
    mock_calculate_total_size_required.side_effect = sizes

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
        call(game_files_path)
        for _ in sizes
    ])

    if iso_too_big:
        mock_nod.DiscBuilderGCN.assert_not_called()
    else:
        mock_nod.DiscBuilderGCN.assert_called_once_with(iso, ANY)
        mock_nod.DiscBuilderGCN.return_value.build_from_directory.assert_called_once_with(game_files_path)
        progress_update.assert_called_once_with("Finished packing ISO", 1)
