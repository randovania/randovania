from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.game.game_enum import RandovaniaGame
from randovania.games.yokus_island_express.exporter.game_exporter import YokuGameExportParams
from randovania.games.yokus_island_express.exporter.options import YokuPerGameOptions
from randovania.games.yokus_island_express.gui.generated.yokus_island_express_game_export_dialog_ui import (
    Ui_YokuGameExportDialog,
)
from randovania.games.yokus_island_express.layout import YokuConfiguration
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog,
    add_field_validation,
    path_in_edit,
    prompt_for_input_directory,
    spoiler_path_for_directory,
)

if TYPE_CHECKING:
    from randovania.interface_common.options import Options, PerGameOptions


def is_game_folder_invalid(path: Path | None) -> bool:
    return path is None or not path.joinpath("data", "text", "randomizer_hard.csv").is_file()


class YokuGameExportDialog(GameExportDialog[YokuConfiguration], Ui_YokuGameExportDialog):
    """Asks for the game installation, which the seed is written into."""

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.YOKUS_ISLAND_EXPRESS

    def __init__(
        self,
        options: Options,
        configuration: YokuConfiguration,
        word_hash: str,
        spoiler: bool,
        games: list[RandovaniaGame],
    ):
        super().__init__(options, configuration, word_hash, spoiler, games)
        per_game = options.per_game_options(YokuPerGameOptions)

        self.input_folder_button.clicked.connect(self._on_input_folder_button)

        if per_game.input_path is not None:
            self.input_folder_edit.setText(str(per_game.input_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.input_folder_edit: lambda: is_game_folder_invalid(path_in_edit(self.input_folder_edit)),
            },
        )

    @property
    def input_path(self) -> Path:
        return Path(self.input_folder_edit.text())

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    def _on_input_folder_button(self) -> None:
        input_dir = prompt_for_input_directory(self, self.input_folder_edit)
        if input_dir is not None:
            self.input_folder_edit.setText(str(input_dir.absolute()))

    def update_per_game_options(self, per_game: PerGameOptions) -> YokuPerGameOptions:
        assert isinstance(per_game, YokuPerGameOptions)
        return dataclasses.replace(per_game, input_path=self.input_path)

    def get_game_export_params(self) -> YokuGameExportParams:
        return YokuGameExportParams(
            spoiler_output=spoiler_path_for_directory(self.auto_save_spoiler, self.input_path),
            input_path=self.input_path,
        )
