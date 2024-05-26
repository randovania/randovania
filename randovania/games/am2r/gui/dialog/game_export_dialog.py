from __future__ import annotations

import dataclasses
import platform
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.games.am2r.exporter.game_exporter import AM2RGameExportParams
from randovania.games.am2r.exporter.options import AM2RPerGameOptions
from randovania.games.am2r.gui.generated.am2r_game_export_dialog_ui import Ui_AM2RGameExportDialog
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog,
    add_field_validation,
    prompt_for_input_directory,
    prompt_for_output_directory,
    spoiler_path_for_directory,
)

if TYPE_CHECKING:
    from randovania.interface_common.options import Options


def _is_valid_input_dir(path: Path) -> bool:
    # Checks whether data file and runner exist.
    current_platform = platform.system()
    if current_platform == "Windows":
        return path.joinpath("data.win").exists() and path.joinpath("AM2R.exe").exists()
    if current_platform == "Linux":
        # AppImage
        return (
            path.joinpath("AM2R.AppImage").exists()
            # Flatpak/non-packed
            or path.joinpath("assets", "game.unx").exists()
            and path.joinpath("runner").exists()
        )
    if current_platform == "Darwin":
        return (
            path.joinpath("AM2R.app", "Contents", "Resources", "game.ios").exists()
            and path.joinpath("AM2R.app", "Contents", "MacOS", "Mac_Runner").exists()
        )

    return False


class AM2RGameExportDialog(GameExportDialog, Ui_AM2RGameExportDialog):
    @classmethod
    def game_enum(cls):
        return RandovaniaGame.AM2R

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__(options, patch_data, word_hash, spoiler, games)
        per_game = options.options_for_game(self.game_enum())
        assert isinstance(per_game, AM2RPerGameOptions)

        # Input
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)

        if per_game.input_path is not None:
            self.input_file_edit.setText(str(per_game.input_path))

        if per_game.output_path is not None:
            self.output_file_edit.setText(str(per_game.output_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.input_file_edit: lambda: not (self.input_file.is_dir() and _is_valid_input_dir(self.input_file)),
                self.output_file_edit: lambda: not (self.output_file.is_dir() and self.output_file != self.input_file),
            },
        )

    # Getters
    @property
    def input_file(self) -> Path:
        return Path(self.input_file_edit.text())

    @property
    def output_file(self) -> Path:
        return Path(self.output_file_edit.text())

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    # Input file
    def _on_input_file_button(self):
        input_dir = prompt_for_input_directory(self, self.input_file_edit)
        if input_dir is not None:
            self.input_file_edit.setText(str(input_dir.absolute()))

    # Output File
    def _on_output_file_button(self):
        output_dir = prompt_for_output_directory(self, "AM2R Randomizer", self.output_file_edit)
        if output_dir is not None:
            self.output_file_edit.setText(str(output_dir))

    def update_per_game_options(self, per_game: AM2RPerGameOptions) -> AM2RPerGameOptions:
        return dataclasses.replace(
            per_game,
            input_path=self.input_file,
            output_path=self.output_file,
        )

    def get_game_export_params(self) -> AM2RGameExportParams:
        spoiler_output = spoiler_path_for_directory(self.auto_save_spoiler, self.output_file)

        return AM2RGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
        )
