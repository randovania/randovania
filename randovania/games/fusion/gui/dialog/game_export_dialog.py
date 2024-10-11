from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.game.game_enum import RandovaniaGame
from randovania.games.fusion.exporter.game_exporter import FusionGameExportParams
from randovania.games.fusion.exporter.options import FusionPerGameOptions
from randovania.games.fusion.gui.generated.fusion_game_export_dialog_ui import Ui_FusionGameExportDialog
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog,
    add_field_validation,
    is_file_validator,
    output_file_validator,
    prompt_for_input_file,
    prompt_for_output_file,
    spoiler_path_for,
)

if TYPE_CHECKING:
    from randovania.interface_common.options import Options


def is_fusion_validator(path: Path | None) -> bool:
    """Validates if the given path is a proper input for Fusion.
    - If input doesn't exist, returns True.
    - If input MD5 matches the vanilla MD5, returns False.
    """

    # Expected MD5 hash for vanilla "Metroid Fusion (USA).gba"
    md5_expected = "af5040fc0f579800151ee2a683e2e5b5"

    if is_file_validator(path):
        return True
    assert path is not None
    with path.open("rb") as file:
        data = file.read()
        md5_returned = hashlib.md5(data).hexdigest()
    if md5_expected == md5_returned:
        return False
    else:
        return True


class FusionGameExportDialog(GameExportDialog, Ui_FusionGameExportDialog):
    """A window for asking the user for what is needed to export this specific game.

    The provided implementation assumes you need an ISO/ROM file, and produces a new ISO/ROM file."""

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.FUSION

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__(options, patch_data, word_hash, spoiler, games)

        self._base_output_name = f"Fusion - {word_hash}.{self.valid_file_type}"
        fusion_options = options.options_for_game(self.game_enum())
        assert isinstance(fusion_options, FusionPerGameOptions)

        # Input
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)

        if fusion_options.input_path is not None:
            self.input_file_edit.setText(str(fusion_options.input_path))

        if fusion_options.output_path is not None:
            output_path = fusion_options.output_path.joinpath(self._base_output_name)
            self.output_file_edit.setText(str(output_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.input_file_edit: lambda: is_fusion_validator(self.input_file),
                self.output_file_edit: lambda: output_file_validator(self.output_file),
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

    def update_per_game_options(self, fusion_options: FusionPerGameOptions) -> FusionPerGameOptions:
        assert isinstance(fusion_options, FusionPerGameOptions)
        return dataclasses.replace(
            fusion_options,
            input_path=self.input_file,
            output_path=Path(self.output_file).parent,
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
