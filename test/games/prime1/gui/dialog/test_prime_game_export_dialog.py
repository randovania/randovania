from pathlib import Path
from unittest.mock import MagicMock, call

import pytest
from PySide6 import QtCore

from randovania.games.game import RandovaniaGame
from randovania.games.prime1.exporter.game_exporter import PrimeGameExportParams
from randovania.games.prime1.exporter.options import PrimePerGameOptions
from randovania.games.prime1.gui.dialog.game_export_dialog import PrimeGameExportDialog
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.games.prime2.exporter.options import EchoesPerGameOptions
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.interface_common.options import Options


@pytest.mark.parametrize("has_output_dir", [False, True])
def test_on_output_file_button_exists(skip_qtbot, tmp_path, mocker, has_output_dir):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    if has_output_dir:
        output_directory = tmp_path.joinpath("output_path")
        expected_default_name = str(tmp_path.joinpath("output_path", "Prime Randomizer - MyHash"))
        output_directory.mkdir()
    else:
        output_directory = None
        expected_default_name = "Prime Randomizer - MyHash"

    options = MagicMock()
    options.options_for_game.return_value = PrimePerGameOptions(
        cosmetic_patches=PrimeCosmeticPatches.default(),
        output_directory=output_directory,
        output_format="iso",
    )

    window = PrimeGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = tmp_path.joinpath("foo", "game.iso")

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, expected_default_name + ".iso",
                                        window.valid_output_file_types)
    assert window.output_file_edit.text() == str(tmp_path.joinpath("foo", "game.iso"))
    assert tmp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmp_path, mocker):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    options = MagicMock()
    options.options_for_game.return_value = PrimePerGameOptions(
        cosmetic_patches=PrimeCosmeticPatches.default(),
        output_directory=None,
        output_format="iso",
    )
    window = PrimeGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = None
    assert window.output_file_edit.text() == ""

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "Prime Randomizer - MyHash.iso", window.valid_output_file_types)
    assert window.output_file_edit.text() == ""


@pytest.mark.parametrize("is_prime_multi", [False, True])
def test_save_options(skip_qtbot, tmp_path, is_prime_multi):
    options = Options(tmp_path)
    games = [RandovaniaGame.METROID_PRIME]
    if is_prime_multi:
        games.append(RandovaniaGame.METROID_PRIME_ECHOES)
    window = PrimeGameExportDialog(options, {}, "MyHash", True, games)
    window.output_file_edit.setText("somewhere/game.iso")

    if is_prime_multi:
        skip_qtbot.mouseClick(window.echoes_models_check, QtCore.Qt.LeftButton)
        window.echoes_file_edit.setText("somewhere/echoes.iso")

    # Run
    window.save_options()

    # Assert
    assert options.options_for_game(RandovaniaGame.METROID_PRIME).output_directory == Path("somewhere")
    if is_prime_multi:
        assert options.options_for_game(RandovaniaGame.METROID_PRIME).use_external_models == {
            RandovaniaGame.METROID_PRIME_ECHOES}
        assert options.options_for_game(RandovaniaGame.METROID_PRIME_ECHOES).input_path == Path("somewhere/echoes.iso")


@pytest.mark.parametrize("test_echoes", [False, True])
def test_on_input_file_button(skip_qtbot, tmp_path, mocker, test_echoes):
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
    options.options_for_game.side_effect = [PrimePerGameOptions(
        cosmetic_patches=PrimeCosmeticPatches.default(),
        input_path=None,
        output_format="iso",
        use_external_models=[RandovaniaGame.METROID_PRIME_ECHOES]
    ),
        EchoesPerGameOptions(
            cosmetic_patches=EchoesCosmeticPatches.default(),
            input_path=None,
        )
    ]

    games = [RandovaniaGame.METROID_PRIME]
    if test_echoes:
        mocker.patch("randovania.games.prime2.gui.dialog.game_export_dialog.has_internal_copy", return_value=False)
        games.append(RandovaniaGame.METROID_PRIME_ECHOES)

    window = PrimeGameExportDialog(options, {}, "MyHash", True, games)

    if test_echoes:
        button = window.echoes_file_button
        file_edit = window.echoes_file_edit
    else:
        button = window.input_file_button
        file_edit = window.input_file_edit

    assert file_edit.text() == ""
    assert file_edit.has_error

    skip_qtbot.mouseClick(button, QtCore.Qt.LeftButton)
    assert file_edit.text() == ""
    assert file_edit.has_error

    skip_qtbot.mouseClick(button, QtCore.Qt.LeftButton)
    assert file_edit.text() == str(tmp_path.joinpath("some/game.iso"))
    assert file_edit.has_error

    skip_qtbot.mouseClick(button, QtCore.Qt.LeftButton)
    assert file_edit.text() == str(tmp_path.joinpath("existing.iso"))
    assert not file_edit.has_error

    skip_qtbot.mouseClick(button, QtCore.Qt.LeftButton)
    assert file_edit.text() == str(tmp_path.joinpath("missing_again.iso"))
    assert file_edit.has_error

    if not test_echoes:
        mock_prompt.assert_has_calls([
            call(window, window.valid_input_file_types, existing_file=None),
            call(window, window.valid_input_file_types, existing_file=None),
            call(window, window.valid_input_file_types, existing_file=None),
            call(window, window.valid_input_file_types, existing_file=tmp_path.joinpath("existing.iso")),
        ])


@pytest.mark.parametrize("is_echoes_multi", [False, True])
@pytest.mark.parametrize("use_external_models", [False, True])
def test_get_game_export_params(skip_qtbot, tmp_path, is_echoes_multi, use_external_models):
    # Setup
    games = [RandovaniaGame.METROID_PRIME]
    echoes_path = None
    if is_echoes_multi:
        games.append(RandovaniaGame.METROID_PRIME_ECHOES)
        if use_external_models:
            echoes_path = tmp_path.joinpath("input/echoes.iso")

    if use_external_models:
        models = {RandovaniaGame.METROID_PRIME_ECHOES}
    else:
        models = {}

    options = MagicMock()
    options.internal_copies_path = tmp_path.joinpath("internal_copies")
    options.options_for_game.side_effect = [
        PrimePerGameOptions(
            cosmetic_patches=PrimeCosmeticPatches.default(),
            input_path=tmp_path.joinpath("input/game.iso"),
            output_directory=tmp_path.joinpath("output"),
            output_format="iso",
            use_external_models=models,
        ),
        EchoesPerGameOptions(
            cosmetic_patches=EchoesCosmeticPatches.default(),
            input_path=echoes_path
        ),
    ]

    window = PrimeGameExportDialog(options, {}, "MyHash", True, games)

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == PrimeGameExportParams(
        spoiler_output=tmp_path.joinpath("output", "Prime Randomizer - MyHash.rdvgame"),
        input_path=tmp_path.joinpath("input/game.iso"),
        output_path=tmp_path.joinpath("output", "Prime Randomizer - MyHash.iso"),
        echoes_input_path=echoes_path,
        asset_cache_path=tmp_path.joinpath("internal_copies", "prime1", "prime2_models"),
        use_echoes_models=is_echoes_multi and use_external_models,
        cache_path=tmp_path.joinpath("internal_copies", "prime1", "randomprime_cache"),
    )
