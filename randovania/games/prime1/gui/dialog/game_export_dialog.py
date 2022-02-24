import dataclasses
from pathlib import Path
from typing import Optional

from randovania.exporter.game_exporter import GameExportParams
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.exporter.game_exporter import PrimeGameExportParams
from randovania.games.prime2.gui.dialog.game_export_dialog import (
    has_internal_copy, delete_internal_copy, check_extracted_game, echoes_input_validator
)
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog, prompt_for_output_file, prompt_for_input_file,
    spoiler_path_for, add_field_validation, output_file_validator,
)
from randovania.gui.generated.prime_game_export_dialog_ui import Ui_PrimeGameExportDialog
from randovania.gui.lib.multi_format_output_mixin import MultiFormatOutputMixin
from randovania.interface_common.options import Options


class PrimeGameExportDialog(GameExportDialog, MultiFormatOutputMixin, Ui_PrimeGameExportDialog):
    _prompt_input_file_echoes = False
    _echoes_contents_path: Path
    _use_echoes_models: bool

    @property
    def _game(self):
        return RandovaniaGame.METROID_PRIME

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games=[]):
        super().__init__(options, patch_data, word_hash, spoiler, games)

        self._base_output_name = f"Prime Randomizer - {word_hash}"
        per_game = options.options_for_game(self._game)

        # Input
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)

        # Output format
        self.setup_multi_format(per_game.output_format)

        # Echoes input
        self.echoes_file_button.clicked.connect(self._on_echoes_file_button)

        # Echoes ISO input
        if RandovaniaGame.METROID_PRIME_ECHOES in games:
            self._use_echoes_models = True
            self.echoes_models_check.setChecked(True)
            self.echoes_models_check.clicked.connect(self._on_echoes_models_check)
            self._echoes_contents_path = options.internal_copies_path.joinpath("prime2", "contents")
            self._prompt_input_file_echoes = check_extracted_game(self.echoes_file_edit, self.echoes_file_button,
                                                                  self._echoes_contents_path)
            echoes_options = options.options_for_game(RandovaniaGame.METROID_PRIME_ECHOES)
            if self._prompt_input_file_echoes and echoes_options.input_path is not None:
                self.echoes_file_edit.setText(str(echoes_options.input_path))
        else:
            self._use_echoes_models = False
            self._echoes_contents_path = None
            self.echoes_models_check.hide()
            self.echoes_file_edit.hide()
            self.echoes_file_label.hide()
            self.echoes_file_button.hide()

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
                self.echoes_file_edit: lambda: (self._use_echoes_models
                                                and echoes_input_validator(self.echoes_file,
                                                                           self._prompt_input_file_echoes,
                                                                           self.echoes_file_edit)),
            }
        )

    @property
    def valid_input_file_types(self) -> list[str]:
        return ["iso"]

    @property
    def valid_output_file_types(self) -> list[str]:
        return ["iso", "ciso", "gcz"]

    def save_options(self):
        with self._options as options:
            if self._has_spoiler:
                options.auto_save_spoiler = self.auto_save_spoiler

            per_game = options.options_for_game(self._game)
            per_game_changes = {
                "input_path": self.input_file,
                "output_directory": self.output_file.parent,
                "output_format": self._selected_output_format,
            }

            if self._prompt_input_file_echoes:
                echoes_options = options.options_for_game(RandovaniaGame.METROID_PRIME_ECHOES)
                echoes_changes = {
                    "input_path": self.echoes_file
                }
                options.set_options_for_game(self._game, dataclasses.replace(echoes_options, **echoes_changes))

            options.set_options_for_game(self._game, dataclasses.replace(per_game, **per_game_changes))

    # Getters
    @property
    def input_file(self) -> Path:
        return Path(self.input_file_edit.text())

    @property
    def output_file(self) -> Path:
        return Path(self.output_file_edit.text())

    @property
    def echoes_file(self) -> Optional[Path]:
        if self._prompt_input_file_echoes:
            return Path(self.echoes_file_edit.text())

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

    # Echoes input
    def _on_echoes_models_check(self):
        use_echoes_models = self.echoes_models_check.isChecked()
        self._use_echoes_models = use_echoes_models
        if self._prompt_input_file_echoes:
            self.echoes_file_edit.setEnabled(use_echoes_models)
        self.echoes_file_label.setEnabled(use_echoes_models)
        self.echoes_file_button.setEnabled(use_echoes_models)

    def _on_echoes_file_button(self):
        if self._prompt_input_file_echoes:
            input_file = prompt_for_input_file(self, self.input_file_edit, ["iso"])
            if input_file is not None:
                self.echoes_file_edit.setText(str(input_file.absolute()))
        else:
            delete_internal_copy(self._options.internal_copies_path)
            self.echoes_file_edit.setText("")
            self._prompt_input_file_echoes = check_extracted_game(self.echoes_file_edit, self.echoes_file_button,
                                                                  self._echoes_contents_path)

    def get_game_export_params(self) -> GameExportParams:
        spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.output_file)
        asset_cache_path = self._options.internal_copies_path.joinpath("prime1", "prime2_models")

        if self._use_echoes_models:
            backup_files_path = self._options.internal_copies_path.joinpath("prime2", "vanilla")
        else:
            backup_files_path = None

        return PrimeGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
            echoes_input_path=self.echoes_file,
            echoes_contents_path=self._echoes_contents_path,
            echoes_backup_path=backup_files_path,
            asset_cache_path=asset_cache_path,
            use_echoes_models=self._use_echoes_models,
        )
