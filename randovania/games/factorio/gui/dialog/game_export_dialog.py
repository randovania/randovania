from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.games.factorio.exporter.game_exporter import FactorioGameExportParams
from randovania.games.factorio.exporter.options import FactorioPerGameOptions
from randovania.games.factorio.gui.generated.factorio_game_export_dialog_ui import Ui_FactorioGameExportDialog
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog,
    add_field_validation,
    prompt_for_input_directory,
    prompt_for_output_directory,
    spoiler_path_for_directory,
)

if TYPE_CHECKING:
    from randovania.interface_common.options import Options, PerGameOptions


def _is_valid_input_dir(path: Path) -> bool:
    return path.joinpath("data", "base", "data.lua").is_file()


class FactorioGameExportDialog(GameExportDialog, Ui_FactorioGameExportDialog):
    """A window for asking the user for what is needed to export this specific game.

    The provided implementation assumes you need an ISO/ROM file, and produces a new ISO/ROM file."""

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.FACTORIO

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__(options, patch_data, word_hash, spoiler, games)
        per_game = options.options_for_game(self.game_enum())
        assert isinstance(per_game, FactorioPerGameOptions)

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
        output_dir = prompt_for_output_directory(self, "Factorio Mod", self.output_file_edit)
        if output_dir is not None:
            self.output_file_edit.setText(str(output_dir))

    def update_per_game_options(self, per_game: PerGameOptions) -> FactorioPerGameOptions:
        assert isinstance(per_game, FactorioPerGameOptions)
        return dataclasses.replace(
            per_game,
            input_path=self.input_file,
            output_path=self.output_file,
        )

    def get_game_export_params(self) -> FactorioGameExportParams:
        """Creates the GameExportParams for this specific game,
        based on the data provided by the user in this window."""
        spoiler_output = spoiler_path_for_directory(self.auto_save_spoiler, self.output_file)

        return FactorioGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
        )
