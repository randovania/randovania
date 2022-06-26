from pathlib import Path
from unittest.mock import MagicMock, call

import pytest
from PySide6 import QtCore

from randovania.games.game import RandovaniaGame
from randovania.games.prime1.exporter.options import PrimePerGameOptions
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.games.prime2.exporter.game_exporter import EchoesGameExportParams
from randovania.games.prime2.exporter.options import EchoesPerGameOptions
from randovania.games.prime2.gui.dialog.game_export_dialog import EchoesGameExportDialog
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.interface_common.options import Options


@pytest.mark.parametrize("has_output_dir", [False, True])
def test_on_output_file_button_exists(skip_qtbot, tmp_path, mocker, has_output_dir):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    if has_output_dir:
        output_directory = tmp_path.joinpath("output_path")
        expected_default_name = str(tmp_path.joinpath("output_path", "Echoes Randomizer - MyHash"))
        output_directory.mkdir()
    else:
        output_directory = None
        expected_default_name = "Echoes Randomizer - MyHash"

    options = MagicMock()
    options.options_for_game.return_value = EchoesPerGameOptions(
        cosmetic_patches=EchoesCosmeticPatches.default(),
        output_directory=output_directory,
    )

    window = EchoesGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = tmp_path.joinpath("foo", "game.iso")

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, expected_default_name + ".iso",
                                        ["iso"])
    assert window.output_file_edit.text() == str(tmp_path.joinpath("foo", "game.iso"))
    assert tmp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmpdir, mocker):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    options = MagicMock()
    options.options_for_game.return_value = EchoesPerGameOptions(
        cosmetic_patches=EchoesCosmeticPatches.default(),
        output_directory=None,
    )
    window = EchoesGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = None

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "Echoes Randomizer - MyHash.iso", ["iso"])
    assert window.output_file_edit.text() == ""


@pytest.mark.parametrize("is_prime_multi", [False, True])
def test_save_options(skip_qtbot, tmp_path, is_prime_multi):
    options = Options(tmp_path)
    games = [RandovaniaGame.METROID_PRIME_ECHOES]
    if is_prime_multi:
        games.append(RandovaniaGame.METROID_PRIME)
    window = EchoesGameExportDialog(options, {}, "MyHash", True, games)
    window.output_file_edit.setText("somewhere/game.iso")
    if is_prime_multi:
        skip_qtbot.mouseClick(window.prime_models_check, QtCore.Qt.LeftButton)
        window.prime_file_edit.setText("somewhere/prime.iso")

    # Run
    window.save_options()

    # Assert
    assert options.options_for_game(RandovaniaGame.METROID_PRIME_ECHOES).output_directory == Path("somewhere")
    if is_prime_multi:
        assert options.options_for_game(RandovaniaGame.METROID_PRIME).input_path == Path("somewhere/prime.iso")
        assert options.options_for_game(RandovaniaGame.METROID_PRIME_ECHOES).use_external_models == {
            RandovaniaGame.METROID_PRIME}


def test_on_input_file_button(skip_qtbot, tmp_path, mocker):
    # Setup
    tmp_path.joinpath("existing.iso").write_bytes(b"foo")
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_vanilla_input_file", autospec=True,
                               side_effect=[
                                   None,
                                   tmp_path.joinpath("some/game.iso"),
                                   tmp_path.joinpath("existing.iso"),
                                   tmp_path.joinpath("missing_again.iso"),
                               ])

    options = MagicMock()
    options.internal_copies_path = tmp_path.joinpath("internal_copies")
    options.options_for_game.return_value = EchoesPerGameOptions(
        cosmetic_patches=EchoesCosmeticPatches.default(),
        input_path=None,
    )

    contents_path = tmp_path.joinpath("internal_copies", "prime2", "contents")
    contents_path.mkdir(parents=True)
    mocker.patch("randovania.interface_common.game_workdir.discover_game", side_effect=[
        ("G2M", 1),
        None,
    ])

    window = EchoesGameExportDialog(options, {}, "MyHash", True, [])
    assert window.input_file_edit.text() == "(internal game copy)"
    assert not window.input_file_edit.has_error

    # Deletes the internal data
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.LeftButton)
    assert window.input_file_edit.text() == ""
    assert window.input_file_edit.has_error

    # User cancelled, stays unchanged
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.LeftButton)
    assert window.input_file_edit.text() == ""
    assert window.input_file_edit.has_error

    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("some/game.iso"))
    assert window.input_file_edit.has_error

    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("existing.iso"))
    assert not window.input_file_edit.has_error

    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("missing_again.iso"))
    assert window.input_file_edit.has_error

    mock_prompt.assert_has_calls([
        call(window, ["iso"], existing_file=None),
        call(window, ["iso"], existing_file=None),
        call(window, ["iso"], existing_file=None),
        call(window, ["iso"], existing_file=tmp_path.joinpath("existing.iso")),
    ])


@pytest.mark.parametrize("is_prime_multi", [False, True])
@pytest.mark.parametrize("use_external_models", [False, True])
def test_get_game_export_params(skip_qtbot, tmp_path, is_prime_multi, use_external_models):
    # Setup
    games = [RandovaniaGame.METROID_PRIME_ECHOES]
    if is_prime_multi:
        games.append(RandovaniaGame.METROID_PRIME)
        prime_path = tmp_path.joinpath("input/prime.iso")
    else:
        prime_path = None

    if use_external_models:
        models = {RandovaniaGame.METROID_PRIME}
    else:
        models = {}

    options = MagicMock()
    options.internal_copies_path = tmp_path.joinpath("internal_copies")
    options.options_for_game.side_effect = [
        EchoesPerGameOptions(
            cosmetic_patches=EchoesCosmeticPatches.default(),
            input_path=tmp_path.joinpath("input/game.iso"),
            output_directory=tmp_path.joinpath("output"),
            use_external_models=models,
        ),
        PrimePerGameOptions(
            cosmetic_patches=PrimeCosmeticPatches.default(),
            input_path=prime_path,
        )
    ]
    window = EchoesGameExportDialog(options, {}, "MyHash", True, games)

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == EchoesGameExportParams(
        spoiler_output=tmp_path.joinpath("output", "Echoes Randomizer - MyHash.rdvgame"),
        input_path=tmp_path.joinpath("input/game.iso"),
        output_path=tmp_path.joinpath("output", "Echoes Randomizer - MyHash.iso"),
        contents_files_path=tmp_path.joinpath("internal_copies", "prime2", "contents"),
        backup_files_path=tmp_path.joinpath("internal_copies", "prime2", "vanilla"),
        asset_cache_path=tmp_path.joinpath("internal_copies", "prime2", "prime1_models"),
        prime_path=prime_path,
        use_prime_models=is_prime_multi and use_external_models,
    )
