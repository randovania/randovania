from __future__ import annotations

import dataclasses
import platform
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
    is_directory_validator,
    path_in_edit,
    prompt_for_input_directory,
    prompt_for_output_directory,
    spoiler_path_for_directory,
)
from randovania.lib import windows_lib

if TYPE_CHECKING:
    from randovania.interface_common.options import Options, PerGameOptions

SAVE_SLOTS = 3


def default_save_folder() -> Path | None:
    if platform.system() != "Windows":
        return None
    return windows_lib.get_appdata().joinpath("Villa Gorilla", "Yoku's Island Express")


def is_game_folder_invalid(path: Path | None) -> bool:
    return path is None or not path.joinpath("data", "text", "randomizer_hard.csv").is_file()


class YokuGameExportDialog(GameExportDialog[YokuConfiguration], Ui_YokuGameExportDialog):
    """Asks for the input path (the game installation), the output path (the save folder) and the save slot."""

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

        for slot in range(SAVE_SLOTS):
            self.save_slot_combo.addItem(f"Slot {slot + 1} ({slot}.save)", slot)
        self.save_slot_combo.setCurrentIndex(max(self.save_slot_combo.findData(per_game.save_slot), 0))

        self.input_folder_button.clicked.connect(self._on_input_folder_button)
        self.output_folder_button.clicked.connect(self._on_output_folder_button)
        self.use_default_button.clicked.connect(self._on_use_default_button)
        self.use_default_button.setEnabled(default_save_folder() is not None)

        if per_game.input_path is not None:
            self.input_folder_edit.setText(str(per_game.input_path))

        if per_game.output_path is not None:
            self.output_folder_edit.setText(str(per_game.output_path))
        else:
            self._on_use_default_button()

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.input_folder_edit: lambda: is_game_folder_invalid(path_in_edit(self.input_folder_edit)),
                self.output_folder_edit: lambda: is_directory_validator(self.output_folder_edit),
            },
        )

    @property
    def input_path(self) -> Path:
        return Path(self.input_folder_edit.text())

    @property
    def output_path(self) -> Path:
        return Path(self.output_folder_edit.text())

    @property
    def save_slot(self) -> int:
        return self.save_slot_combo.currentData()

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    def _on_input_folder_button(self) -> None:
        input_dir = prompt_for_input_directory(self, self.input_folder_edit)
        if input_dir is not None:
            self.input_folder_edit.setText(str(input_dir.absolute()))

    def _on_output_folder_button(self) -> None:
        output_dir = prompt_for_output_directory(self, "Yoku's Island Express", self.output_folder_edit)
        if output_dir is not None:
            self.output_folder_edit.setText(str(output_dir))

    def _on_use_default_button(self) -> None:
        folder = default_save_folder()
        if folder is not None:
            self.output_folder_edit.setText(str(folder))

    def update_per_game_options(self, per_game: PerGameOptions) -> YokuPerGameOptions:
        assert isinstance(per_game, YokuPerGameOptions)
        return dataclasses.replace(
            per_game,
            input_path=self.input_path,
            output_path=self.output_path,
            save_slot=self.save_slot,
        )

    def get_game_export_params(self) -> YokuGameExportParams:
        return YokuGameExportParams(
            spoiler_output=spoiler_path_for_directory(self.auto_save_spoiler, self.output_path),
            input_path=self.input_path,
            output_path=self.output_path,
            save_slot=self.save_slot,
        )
