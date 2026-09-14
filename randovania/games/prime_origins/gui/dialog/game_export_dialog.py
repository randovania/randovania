from __future__ import annotations

import dataclasses
import platform
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime_origins.exporter.game_exporter import MPOGameExportParams
from randovania.games.prime_origins.exporter.options import MPOPerGameOptions
from randovania.games.prime_origins.gui.generated.prime_origins_game_export_dialog_ui import Ui_MPOGameExportDialog
from randovania.games.prime_origins.layout import MPOConfiguration
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
    # Checks whether data file and runner exist.
    current_platform = platform.system()
    if current_platform == "Windows":
        return path.joinpath("data.win").exists() and path.joinpath("MetroidPrimeOrigins.exe").exists()
    if current_platform == "Linux":
        # AppImage
        return (
            path.joinpath("MetroidPrimeOrigins.AppImage").exists()
            # Flatpak/non-packed
            or (path.joinpath("assets", "game.unx").exists() and path.joinpath("runner").exists())
        )
    if current_platform == "Darwin":
        return (
            path.joinpath("MetroidPrimeOrigins.app", "Contents", "Resources", "game.ios").exists()
            and path.joinpath("MetroidPrimeOrigins.app", "Contents", "MacOS", "Mac_Runner").exists()
        )

    return False


class MPOGameExportDialog(GameExportDialog[MPOConfiguration], Ui_MPOGameExportDialog):
    """A window for asking the user for what is needed to export this specific game.

    The provided implementation assumes you need an ISO/ROM file, and produces a new ISO/ROM file."""

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.PRIME_ORIGINS

    def __init__(
        self,
        options: Options,
        configuration: MPOConfiguration,
        word_hash: str,
        spoiler: bool,
        games: list[RandovaniaGame],
    ):
        super().__init__(options, configuration, word_hash, spoiler, games)
        per_game = options.per_game_options(MPOPerGameOptions)

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
    def _on_input_file_button(self) -> None:
        input_dir = prompt_for_input_directory(self, self.input_file_edit)
        if input_dir is not None:
            self.input_file_edit.setText(str(input_dir.absolute()))

    # Output File
    def _on_output_file_button(self) -> None:
        output_dir = prompt_for_output_directory(self, "AM2R Randomizer", self.output_file_edit)
        if output_dir is not None:
            self.output_file_edit.setText(str(output_dir))

    def update_per_game_options(self, per_game: PerGameOptions) -> MPOPerGameOptions:
        assert isinstance(per_game, MPOPerGameOptions)
        return dataclasses.replace(
            per_game,
            input_path=self.input_file,
            output_path=self.output_file,
        )

    def get_game_export_params(self) -> MPOGameExportParams:
        """Creates the GameExportParams for this specific game,
        based on the data provided by the user in this window."""

        spoiler_output = spoiler_path_for_directory(self.auto_save_spoiler, self.output_file)

        return MPOGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
        )
