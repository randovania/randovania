import dataclasses
import shutil
from pathlib import Path

from PySide6.QtWidgets import QLineEdit, QPushButton

from randovania.exporter.game_exporter import GameExportParams
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.exporter.options import PrimePerGameOptions
from randovania.games.prime2.exporter.game_exporter import EchoesGameExportParams
from randovania.games.prime2.exporter.options import EchoesPerGameOptions
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog, prompt_for_output_file, prompt_for_input_file,
    add_field_validation, output_file_validator, spoiler_path_for, is_file_validator, update_validation
)
from randovania.gui.generated.echoes_game_export_dialog_ui import Ui_EchoesGameExportDialog
from randovania.interface_common import game_workdir
from randovania.interface_common.options import Options

_VALID_GAME_TEXT = "(internal game copy)"


def has_internal_copy(contents_file_path: Path) -> bool:
    result = game_workdir.discover_game(contents_file_path)
    if result is not None:
        game_id, _ = result
        if game_id.startswith("G2M"):
            return True
    return False


def delete_internal_copy(internal_copies_path: Path):
    internal_copies_path = internal_copies_path.joinpath("prime2")
    if internal_copies_path.exists():
        shutil.rmtree(internal_copies_path)


def check_extracted_game(input_file_edit: QLineEdit, input_file_button: QPushButton, contents_file_path: Path) -> bool:
    prompt_input_file = not has_internal_copy(contents_file_path)
    input_file_edit.setEnabled(prompt_input_file)

    if prompt_input_file:
        input_file_button.setText("Select File")
    else:
        input_file_button.setText("Delete internal copy")
        input_file_edit.setText(_VALID_GAME_TEXT)

    return prompt_input_file


def echoes_input_validator(input_file: Path | None, prompt_input_file: bool, input_file_edit: QLineEdit) -> bool:
    if prompt_input_file:
        return is_file_validator(input_file)
    else:
        return input_file_edit.text() != _VALID_GAME_TEXT


class EchoesGameExportDialog(GameExportDialog, Ui_EchoesGameExportDialog):
    _prompt_input_file: bool
    _use_prime_models: bool

    @property
    def _game(self):
        return RandovaniaGame.METROID_PRIME_ECHOES

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__(options, patch_data, word_hash, spoiler, games)

        self.default_output_name = f"Echoes Randomizer - {word_hash}"
        self._prompt_input_file = check_extracted_game(self.input_file_edit, self.input_file_button,
                                                       self._contents_file_path)

        per_game = options.options_for_game(self._game)
        assert isinstance(per_game, EchoesPerGameOptions)

        # Input
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)

        # Prime input
        self.prime_file_button.clicked.connect(self._on_prime_file_button)

        if RandovaniaGame.METROID_PRIME in games:
            self._use_prime_models = RandovaniaGame.METROID_PRIME in per_game.use_external_models
            self.prime_models_check.setChecked(self._use_prime_models)
            self._on_prime_models_check()
            self.prime_models_check.clicked.connect(self._on_prime_models_check)

            prime_options = options.options_for_game(RandovaniaGame.METROID_PRIME)
            assert isinstance(prime_options, PrimePerGameOptions)
            if prime_options.input_path is not None:
                self.prime_file_edit.setText(str(prime_options.input_path))

        else:
            self._use_prime_models = False
            self.prime_models_check.hide()
            self.prime_file_edit.hide()
            self.prime_file_label.hide()
            self.prime_file_button.hide()

        if self._prompt_input_file and per_game.input_path is not None:
            self.input_file_edit.setText(str(per_game.input_path))

        if per_game.output_directory is not None:
            output_path = per_game.output_directory.joinpath(f"{self.default_output_name}.iso")
            self.output_file_edit.setText(str(output_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.input_file_edit: lambda: echoes_input_validator(self.input_file, self._prompt_input_file,
                                                                     self.input_file_edit),
                self.output_file_edit: lambda: output_file_validator(self.output_file),
                self.prime_file_edit: lambda: self._use_prime_models and is_file_validator(self.prime_file),
            }
        )

    def save_options(self):
        with self._options as options:
            if self._has_spoiler:
                options.auto_save_spoiler = self.auto_save_spoiler

            per_game = options.options_for_game(self._game)
            assert isinstance(per_game, EchoesPerGameOptions)

            per_game_changes = {}
            if self._prompt_input_file:
                per_game_changes["input_path"] = self.input_file

            use_external_models = per_game.use_external_models.copy()
            if not self.prime_models_check.isHidden():
                if self._use_prime_models:
                    use_external_models.add(RandovaniaGame.METROID_PRIME)
                else:
                    use_external_models.discard(RandovaniaGame.METROID_PRIME)

            options.set_options_for_game(self._game, dataclasses.replace(
                per_game,
                output_directory=self.output_file.parent,
                use_external_models=use_external_models,
                **per_game_changes,
            ))

            if self._use_prime_models:
                from randovania.games.prime1.exporter.options import PrimePerGameOptions
                prime_options = options.options_for_game(RandovaniaGame.METROID_PRIME)
                assert isinstance(prime_options, PrimePerGameOptions)
                options.set_options_for_game(RandovaniaGame.METROID_PRIME, dataclasses.replace(
                    prime_options,
                    input_path=self.prime_file,
                ))

    # Getters
    @property
    def input_file(self) -> Path | None:
        if self._prompt_input_file:
            return Path(self.input_file_edit.text())

    @property
    def output_file(self) -> Path:
        return Path(self.output_file_edit.text())

    @property
    def prime_file(self) -> Path | None:
        return Path(self.prime_file_edit.text()) if self.prime_file_edit.text() else None

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    # Checks

    # Input file
    def _on_input_file_button(self):
        if self._prompt_input_file:
            input_file = prompt_for_input_file(self, self.input_file_edit, ["iso"])
            if input_file is not None:
                self.input_file_edit.setText(str(input_file.absolute()))
        else:
            delete_internal_copy(self._options.internal_copies_path)
            self.input_file_edit.setText("")
            self._prompt_input_file = check_extracted_game(self.input_file_edit, self.input_file_button,
                                                           self._contents_file_path)

    # Output File
    def _on_output_file_button(self):
        output_file = prompt_for_output_file(self, ["iso"], f"{self.default_output_name}.iso", self.output_file_edit)
        if output_file is not None:
            self.output_file_edit.setText(str(output_file))

    # Prime input
    def _on_prime_file_button(self):
        prime_file = prompt_for_input_file(self, self.prime_file_edit, ["iso"])
        if prime_file is not None:
            self.prime_file_edit.setText(str(prime_file.absolute()))

    def _on_prime_models_check(self):
        use_prime_models = self.prime_models_check.isChecked()
        self._use_prime_models = use_prime_models
        self.prime_file_edit.setEnabled(use_prime_models)
        self.prime_file_label.setEnabled(use_prime_models)
        self.prime_file_button.setEnabled(use_prime_models)
        update_validation(self.prime_file_edit)

    @property
    def _contents_file_path(self):
        return self._options.internal_copies_path.joinpath("prime2", "contents")

    def get_game_export_params(self) -> GameExportParams:
        spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.output_file)
        backup_files_path = self._options.internal_copies_path.joinpath("prime2", "vanilla")
        asset_cache_path = self._options.internal_copies_path.joinpath("prime2", "prime1_models")

        return EchoesGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
            contents_files_path=self._contents_file_path,
            backup_files_path=backup_files_path,
            asset_cache_path=asset_cache_path,
            prime_path=self.prime_file,
            use_prime_models=self._use_prime_models,
        )
