from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

from caver.patcher import CSPlatform

from randovania.games.cave_story.exporter.game_exporter import CSGameExportParams
from randovania.games.cave_story.exporter.options import CSPerGameOptions
from randovania.games.cave_story.gui.generated.cs_game_export_dialog_ui import Ui_CSGameExportDialog
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog,
    add_field_validation,
    is_directory_validator,
    prompt_for_output_directory,
    spoiler_path_for_directory,
)

if TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExportParams
    from randovania.interface_common.options import Options


class CSGameExportDialog(GameExportDialog, Ui_CSGameExportDialog):
    @classmethod
    def game_enum(cls):
        return RandovaniaGame.CAVE_STORY

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__(options, patch_data, word_hash, spoiler, games)

        per_game = options.options_for_game(self.game_enum())
        assert isinstance(per_game, CSPerGameOptions)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)
        self.tweaked_radio.clicked.connect(self._on_platform_radio_clicked)
        self.freeware_radio.clicked.connect(self._on_platform_radio_clicked)

        # Target Platform
        if per_game.platform is CSPlatform.FREEWARE:
            self.freeware_radio.setChecked(True)
        else:
            self.tweaked_radio.setChecked(True)

        self._on_platform_radio_clicked()

        if per_game.output_directory is not None:
            output_path = per_game.output_directory
            self.output_file_edit.setText(str(output_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.output_file_edit: lambda: is_directory_validator(self.output_file_edit),
            },
        )

    def update_per_game_options(self, per_game: CSPerGameOptions) -> CSPerGameOptions:
        return dataclasses.replace(per_game, output_directory=self.output_file, platform=self.target_platform)

    # Getters
    @property
    def output_file(self) -> Path:
        return Path(self.output_file_edit.text())

    @property
    def target_platform(self) -> CSPlatform:
        if self.freeware_radio.isChecked():
            return CSPlatform.FREEWARE
        else:
            return CSPlatform.TWEAKED

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    # Output File
    def _on_output_file_button(self):
        output_file = prompt_for_output_directory(self, "Cave Story Randomizer", self.output_file_edit)
        if output_file is not None:
            self.output_file_edit.setText(str(output_file))

    def _on_platform_radio_clicked(self):
        if self.freeware_radio.isChecked():
            self.description_label.setText(
                "The original release of Cave Story. Compatible with Windows and Linux via Wine."
            )
        elif self.tweaked_radio.isChecked():
            self.description_label.setText(
                """A community port with several improvements, \
                such as widescreen, native controller support and in-game remapping. \
                Compatible with Windows and Linux.

                Click <a href=\"https://oneninefour.cl/tweaked/\">here</a> for more details."""
            )

        self.description_label.update()

    def get_game_export_params(self) -> GameExportParams:
        spoiler_output = spoiler_path_for_directory(self.auto_save_spoiler, self.output_file)

        return CSGameExportParams(
            spoiler_output=spoiler_output, output_path=self.output_file, platform=self.target_platform
        )
