import dataclasses
from pathlib import Path

from randovania.exporter.game_exporter import GameExportParams
from randovania.games.dread.exporter.game_exporter import DreadGameExportParams
from randovania.games.dread.exporter.options import DreadPerGameOptions
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog, add_field_validation, prompt_for_output_directory, prompt_for_input_directory,
    is_directory_validator, spoiler_path_for
)
from randovania.gui.generated.dread_game_export_dialog_ui import Ui_DreadGameExportDialog
from randovania.interface_common.options import Options


class DreadGameExportDialog(GameExportDialog, Ui_DreadGameExportDialog):
    @property
    def _game(self):
        return RandovaniaGame.METROID_DREAD

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool):
        super().__init__(options, patch_data, word_hash, spoiler)

        per_game = options.options_for_game(self._game)
        assert isinstance(per_game, DreadPerGameOptions)

        # Input
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)

        if per_game.input_directory is not None:
            self.input_file_edit.setText(str(per_game.input_directory))

        if per_game.output_directory is not None:
            output_path = per_game.output_directory
            self.output_file_edit.setText(str(output_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.input_file_edit: lambda: is_directory_validator(self.input_file_edit),
                self.output_file_edit: lambda: is_directory_validator(self.output_file_edit),
            }
        )

    def save_options(self):
        with self._options as options:
            if self._has_spoiler:
                options.auto_save_spoiler = self.auto_save_spoiler

            per_game = options.options_for_game(self._game)
            assert isinstance(per_game, DreadPerGameOptions)
            options.set_options_for_game(self._game, dataclasses.replace(
                per_game,
                input_directory=self.input_file,
                output_directory=self.output_file,
            ))

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
        input_file = prompt_for_input_directory(self, self.input_file_edit)
        if input_file is not None:
            self.input_file_edit.setText(str(input_file.absolute()))

    # Output File
    def _on_output_file_button(self):
        output_file = prompt_for_output_directory(self, "DreadRandovania", self.output_file_edit)
        if output_file is not None:
            self.output_file_edit.setText(str(output_file))

    def get_game_export_params(self) -> GameExportParams:
        spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.output_file)

        return DreadGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
        )
