from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.games.fusion.exporter.game_exporter import FusionGameExportParams
from randovania.games.fusion.exporter.options import FusionPerGameOptions
from randovania.games.fusion.gui.generated.fusion_game_export_dialog_ui import Ui_FusionGameExportDialog
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog,
    add_field_validation,
    prompt_for_input_file,
    prompt_for_output_file,
    spoiler_path_for,
)

if TYPE_CHECKING:
    from randovania.interface_common.options import Options


class FusionGameExportDialog(GameExportDialog, Ui_FusionGameExportDialog):
    """A window for asking the user for what is needed to export this specific game.

    The provided implementation assumes you need an ISO/ROM file, and produces a new ISO/ROM file."""

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.FUSION

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__(options, patch_data, word_hash, spoiler, games)

        self._base_output_name = f"MARS - {word_hash}.gba"
        per_game = options.options_for_game(self.game_enum())
        assert isinstance(per_game, FusionPerGameOptions)

        # Input
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)

        if per_game.input_path is not None:
            self.input_file_edit.setText(str(per_game.input_path))

        if per_game.output_path is not None:
            output_path = per_game.output_path.joinpath(self._base_output_name)
            self.output_file_edit.setText(str(output_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.input_file_edit: lambda: False,
                self.output_file_edit: lambda: False,
            },
        )

    @property
    def valid_file_type(self) -> str:
        return "gba"

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
        input_file = prompt_for_input_file(self, self.input_file_edit, [self.valid_file_type])
        if input_file is not None:
            self.input_file_edit.setText(str(input_file.absolute()))

    # Output File
    def _on_output_file_button(self):
        output_file = prompt_for_output_file(
            self, [self.valid_file_type], self._base_output_name, self.output_file_edit
        )
        if output_file is not None:
            self.output_file_edit.setText(str(output_file))

    def update_per_game_options(self, per_game: FusionPerGameOptions) -> FusionPerGameOptions:
        assert isinstance(per_game, FusionPerGameOptions)
        return dataclasses.replace(
            per_game,
            input_path=self.input_file,
            output_path=self.output_file,
        )

    def get_game_export_params(self) -> FusionGameExportParams:
        """Creates the GameExportParams for this specific game,
        based on the data provided by the user in this window."""

        spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.output_file)

        return FusionGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
        )
