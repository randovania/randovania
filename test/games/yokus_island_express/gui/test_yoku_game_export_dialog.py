from __future__ import annotations

from pathlib import Path

from randovania.games.yokus_island_express.exporter.game_exporter import YokuGameExportParams
from randovania.games.yokus_island_express.exporter.options import YokuPerGameOptions
from randovania.games.yokus_island_express.gui.dialog.game_export_dialog import YokuGameExportDialog
from randovania.games.yokus_island_express.layout.yokus_island_express_cosmetic_patches import YokuCosmeticPatches


def _game_folder(tmp_path: Path) -> Path:
    game = tmp_path.joinpath("game")
    game.joinpath("data", "text").mkdir(parents=True)
    game.joinpath("data", "text", "randomizer_hard.csv").write_text("Name\n")
    return game


def test_save_options(skip_qtbot, options):
    window = YokuGameExportDialog(options, {}, "MyHash", True, [])
    window.input_folder_edit.setText("somewhere/game")
    window.output_folder_edit.setText("somewhere/saves")
    window.save_slot_combo.setCurrentIndex(2)

    # Run
    window.save_options()

    # Assert
    per_game = options.per_game_options(YokuPerGameOptions)
    assert per_game.input_path == Path("somewhere/game")
    assert per_game.output_path == Path("somewhere/saves")
    assert per_game.save_slot == 2


def test_get_game_export_params(skip_qtbot, tmp_path, options):
    game = _game_folder(tmp_path)
    saves = tmp_path.joinpath("saves")
    saves.mkdir()

    with options:
        options.set_per_game_options(
            YokuPerGameOptions(
                cosmetic_patches=YokuCosmeticPatches.default(),
                input_path=game,
                output_path=saves,
                save_slot=1,
            )
        )

    window = YokuGameExportDialog(options, {}, "MyHash", False, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert window.accept_button.isEnabled()
    assert window.save_slot_combo.currentText() == "Slot 2 (1.save)"
    assert result == YokuGameExportParams(
        spoiler_output=None,
        input_path=game,
        output_path=saves,
        save_slot=1,
    )


def test_invalid_game_folder(skip_qtbot, tmp_path, options):
    saves = tmp_path.joinpath("saves")
    saves.mkdir()
    window = YokuGameExportDialog(options, {}, "MyHash", True, [])
    window.output_folder_edit.setText(str(saves))

    # Run
    window.input_folder_edit.setText(str(tmp_path))

    # Assert
    assert not window.accept_button.isEnabled()

    window.input_folder_edit.setText(str(_game_folder(tmp_path)))
    assert window.accept_button.isEnabled()
