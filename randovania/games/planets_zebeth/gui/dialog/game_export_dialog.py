from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.game.game_enum import RandovaniaGame
from randovania.games.planets_zebeth.exporter.game_exporter import PlanetsZebethGameExportParams
from randovania.games.planets_zebeth.exporter.options import PlanetsZebethPerGameOptions
from randovania.games.planets_zebeth.gui.generated.planets_zebeth_game_export_dialog_ui import (
    Ui_PlanetsZebethGameExportDialog,
)
from randovania.games.planets_zebeth.layout import PlanetsZebethConfiguration
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
    return path.joinpath("data.win").exists() and path.joinpath("Metroid Planets v1.27g.exe").exists()


class PlanetsZebethGameExportDialog(GameExportDialog[PlanetsZebethConfiguration], Ui_PlanetsZebethGameExportDialog):
    """A window for asking the user for what is needed to export this specific game.

    The provided implementation assumes you need an ISO/ROM file, and produces a new ISO/ROM file."""

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PLANETS_ZEBETH

    def __init__(
        self,
        options: Options,
        configuration: PlanetsZebethConfiguration,
        word_hash: str,
        spoiler: bool,
        games: list[RandovaniaGame],
    ):
        super().__init__(options, configuration, word_hash, spoiler, games)
        per_game = options.per_game_options(PlanetsZebethPerGameOptions)

        # Input
        self.input_folder_button.clicked.connect(self._on_input_folder_button)

        # Output
        self.output_folder_button.clicked.connect(self._on_output_folder_button)

        if per_game.input_path is not None:
            self.input_folder_edit.setText(str(per_game.input_path))

        if per_game.output_path is not None:
            self.output_folder_edit.setText(str(per_game.output_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.input_folder_edit: lambda: not (
                    self.input_folder.is_dir() and _is_valid_input_dir(self.input_folder)
                ),
                self.output_folder_edit: lambda: not (
                    self.output_folder.is_dir() and self.output_folder != self.input_folder
                ),
            },
        )

    @property
    def input_folder(self) -> Path:
        return Path(self.input_folder_edit.text())

    @property
    def output_folder(self) -> Path:
        return Path(self.output_folder_edit.text())

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    # Input file
    def _on_input_folder_button(self):
        input_dir = prompt_for_input_directory(self, self.input_folder_edit)
        if input_dir is not None:
            self.input_folder_edit.setText(str(input_dir.absolute()))

    # Output File
    def _on_output_folder_button(self):
        output_dir = prompt_for_output_directory(self, "Planets Zebeth Randomizer", self.output_folder_edit)
        if output_dir is not None:
            self.output_folder_edit.setText(str(output_dir))

    def update_per_game_options(self, per_game: PlanetsZebethPerGameOptions) -> PlanetsZebethPerGameOptions:
        return dataclasses.replace(
            per_game,
            input_path=self.input_folder,
            output_path=self.output_folder,
        )

    def get_game_export_params(self) -> PlanetsZebethGameExportParams:
        spoiler_output = spoiler_path_for_directory(self.auto_save_spoiler, self.output_folder)

        return PlanetsZebethGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_folder,
            output_path=self.output_folder,
        )
