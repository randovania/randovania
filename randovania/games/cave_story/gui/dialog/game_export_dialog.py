import dataclasses
from pathlib import Path

from randovania.exporter.game_exporter import GameExportParams
from randovania.games.cave_story.exporter.game_exporter import CSGameExportParams
from randovania.games.cave_story.exporter.options import CSPerGameOptions
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog, add_field_validation, is_directory_validator, prompt_for_output_directory, spoiler_path_for,
    spoiler_path_for_directory
)
from randovania.gui.generated.cs_game_export_dialog_ui import Ui_CSGameExportDialog
from randovania.interface_common.options import Options


class CSGameExportDialog(GameExportDialog, Ui_CSGameExportDialog):
    @property
    def _game(self):
        return RandovaniaGame.CAVE_STORY

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__(options, patch_data, word_hash, spoiler, games)

        per_game = options.options_for_game(self._game)
        assert isinstance(per_game, CSPerGameOptions)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)

        if per_game.output_directory is not None:
            output_path = per_game.output_directory
            self.output_file_edit.setText(str(output_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.output_file_edit: lambda: is_directory_validator(self.output_file_edit),
            }
        )

    def save_options(self):
        with self._options as options:
            if self._has_spoiler:
                options.auto_save_spoiler = self.auto_save_spoiler

            per_game = options.options_for_game(self._game)
            assert isinstance(per_game, CSPerGameOptions)
            options.set_options_for_game(self._game, dataclasses.replace(
                per_game,
                output_directory=self.output_file,
            ))

    # Getters
    @property
    def output_file(self) -> Path:
        return Path(self.output_file_edit.text())

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    # Output File
    def _on_output_file_button(self):
        output_file = prompt_for_output_directory(self, "Cave Story Randomizer", self.output_file_edit)
        if output_file is not None:
            self.output_file_edit.setText(str(output_file))

    def get_game_export_params(self) -> GameExportParams:
        spoiler_output = spoiler_path_for_directory(self.auto_save_spoiler, self.output_file)

        return CSGameExportParams(
            spoiler_output=spoiler_output,
            output_path=self.output_file,
        )
