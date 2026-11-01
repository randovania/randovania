from __future__ import annotations

from pathlib import Path

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.games.yokus_island_express.exporter.game_exporter import YokuGameExportParams
from randovania.games.yokus_island_express.exporter.options import YokuPerGameOptions
from randovania.games.yokus_island_express.gui.dialog.game_export_dialog import YokuGameExportDialog
from randovania.games.yokus_island_express.layout.yokus_island_express_configuration import YokuConfiguration
from randovania.games.yokus_island_express.layout.yokus_island_express_cosmetic_patches import YokuCosmeticPatches
from randovania.interface_common.preset_manager import PresetManager


@pytest.fixture
def configuration() -> YokuConfiguration:
    preset = PresetManager(None).default_preset_for_game(RandovaniaGame.YOKUS_ISLAND_EXPRESS).get_preset()
    assert isinstance(preset.configuration, YokuConfiguration)
    return preset.configuration


def _game_folder(tmp_path: Path) -> Path:
    game = tmp_path.joinpath("game")
    game.joinpath("data", "text").mkdir(parents=True)
    game.joinpath("data", "text", "randomizer_hard.csv").write_text("Name\n")
    return game


def test_save_options(skip_qtbot, options, configuration):
    window = YokuGameExportDialog(options, configuration, "MyHash", True, [])
    window.input_folder_edit.setText("somewhere/game")

    # Run
    window.save_options()

    # Assert
    per_game = options.per_game_options(YokuPerGameOptions)
    assert per_game.input_path == Path("somewhere/game")


def test_get_game_export_params(skip_qtbot, tmp_path, options, configuration):
    game = _game_folder(tmp_path)

    with options:
        options.set_per_game_options(
            YokuPerGameOptions(
                cosmetic_patches=YokuCosmeticPatches.default(),
                input_path=game,
            )
        )

    window = YokuGameExportDialog(options, configuration, "MyHash", False, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert window.accept_button.isEnabled()
    assert result == YokuGameExportParams(
        spoiler_output=None,
        input_path=game,
    )


def test_spoiler_goes_into_the_game_folder(skip_qtbot, tmp_path, options, configuration):
    game = _game_folder(tmp_path)
    window = YokuGameExportDialog(options, configuration, "MyHash", True, [])
    window.input_folder_edit.setText(str(game))
    window.auto_save_spoiler_check.setChecked(True)

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result.spoiler_output is not None
    assert result.spoiler_output.parent == game


def test_invalid_game_folder(skip_qtbot, tmp_path, options, configuration):
    window = YokuGameExportDialog(options, configuration, "MyHash", True, [])

    # Run
    window.input_folder_edit.setText(str(tmp_path))

    # Assert
    assert not window.accept_button.isEnabled()

    window.input_folder_edit.setText(str(_game_folder(tmp_path)))
    assert window.accept_button.isEnabled()
