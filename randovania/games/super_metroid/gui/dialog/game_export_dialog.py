import dataclasses
from pathlib import Path

from randovania.exporter.game_exporter import GameExportParams
from randovania.games.game import RandovaniaGame
from randovania.games.super_metroid.exporter.game_exporter import SuperMetroidGameExportParams
from randovania.games.super_metroid.exporter.options import SuperMetroidPerGameOptions
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog, prompt_for_output_file, prompt_for_input_file, output_file_validator, add_field_validation,
    spoiler_path_for
)
from randovania.gui.generated.super_metroid_game_export_dialog_ui import Ui_SuperMetroidGameExportDialog
from randovania.gui.lib.multi_format_output_mixin import MultiFormatOutputMixin
from randovania.interface_common.options import Options


class SuperMetroidGameExportDialog(GameExportDialog, MultiFormatOutputMixin, Ui_SuperMetroidGameExportDialog):
    @property
    def _game(self):
        return RandovaniaGame.SUPER_METROID

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__(options, patch_data, word_hash, spoiler, games)

        self._base_output_name = f"SM Randomizer - {word_hash}"
        per_game = options.options_for_game(self._game)
        assert isinstance(per_game, SuperMetroidPerGameOptions)

        # Input
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)

        # Output format
        self.setup_multi_format(per_game.output_format)

        if per_game.input_path is not None:
            self.input_file_edit.setText(str(per_game.input_path))

        if per_game.output_directory is not None:
            output_path = per_game.output_directory.joinpath(self.default_output_name)
            self.output_file_edit.setText(str(output_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.input_file_edit: lambda: not self.input_file.is_file(),
                self.output_file_edit: lambda: output_file_validator(self.output_file),
            }
        )

    @property
    def valid_input_file_types(self) -> list[str]:
        return ["smc", "sfc"]

    @property
    def valid_output_file_types(self) -> list[str]:
        return ["smc", "sfc"]

    def save_options(self):
        with self._options as options:
            if self._has_spoiler:
                options.auto_save_spoiler = self.auto_save_spoiler

            per_game = options.options_for_game(self._game)
            assert isinstance(per_game, SuperMetroidPerGameOptions)
            options.set_options_for_game(self._game, dataclasses.replace(
                per_game,
                input_path=self.input_file,
                output_directory=self.output_file.parent,
                output_format=self._selected_output_format,
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
        input_file = prompt_for_input_file(self, self.input_file_edit, self.valid_input_file_types)
        if input_file is not None:
            self.input_file_edit.setText(str(input_file.absolute()))

    # Output File
    def _on_output_file_button(self):
        output_file = prompt_for_output_file(self, self.valid_output_file_types, self.default_output_name,
                                             self.output_file_edit)
        if output_file is not None:
            self.output_file_edit.setText(str(output_file))

    def get_game_export_params(self) -> GameExportParams:
        spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.output_file)

        return SuperMetroidGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
        )
