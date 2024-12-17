from __future__ import annotations

import dataclasses
import platform
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.game.game_enum import RandovaniaGame
from randovania.games.factorio.exporter.game_exporter import FactorioGameExportParams
from randovania.games.factorio.exporter.options import FactorioPerGameOptions
from randovania.games.factorio.gui.generated.factorio_game_export_dialog_ui import Ui_FactorioGameExportDialog
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog,
    add_field_validation,
    is_directory_validator,
    prompt_for_output_directory,
    spoiler_path_for_directory,
)
from randovania.lib import windows_lib

if TYPE_CHECKING:
    from randovania.interface_common.options import Options, PerGameOptions


def get_global_user_data_dir() -> Path:
    match platform.system():
        case "Windows":
            return windows_lib.get_appdata().joinpath("Factorio")
        case "Darwin":
            return Path("~/Library/Application Support/factorio")
        case "Linux":
            return Path("~/.factorio")
        case _:
            raise RuntimeError("Unsupported platform")


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

        # Output
        self.use_default_button.clicked.connect(self._on_use_default_button)
        self.output_file_button.clicked.connect(self._on_output_file_button)

        if per_game.output_path is not None:
            self.output_file_edit.setText(str(per_game.output_path))
        else:
            self._on_use_default_button()

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.output_file_edit: lambda: is_directory_validator(self.output_file_edit),
            },
        )

    # Getters
    @property
    def output_file(self) -> Path:
        return Path(self.output_file_edit.text())

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    def _on_use_default_button(self) -> None:
        global_dir = get_global_user_data_dir()
        self.output_file_edit.setText(str(global_dir.joinpath("mods")))

    # Output File
    def _on_output_file_button(self) -> None:
        output_dir = prompt_for_output_directory(self, "Factorio Mod", self.output_file_edit)
        if output_dir is not None:
            self.output_file_edit.setText(str(output_dir))

    def update_per_game_options(self, per_game: PerGameOptions) -> FactorioPerGameOptions:
        assert isinstance(per_game, FactorioPerGameOptions)
        return dataclasses.replace(
            per_game,
            output_path=self.output_file,
        )

    def get_game_export_params(self) -> FactorioGameExportParams:
        """Creates the GameExportParams for this specific game,
        based on the data provided by the user in this window."""
        spoiler_output = spoiler_path_for_directory(self.auto_save_spoiler, self.output_file)

        return FactorioGameExportParams(
            spoiler_output=spoiler_output,
            output_path=self.output_file,
        )
