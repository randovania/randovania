import dataclasses
import shutil
from pathlib import Path
from typing import Optional

from randovania.exporter.game_exporter import GameExportParams
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.exporter.game_exporter import EchoesGameExportParams
from randovania.games.prime2.exporter.options import EchoesPerGameOptions
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog, prompt_for_output_file, prompt_for_input_file,
    add_field_validation, output_file_validator, spoiler_path_for
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


class EchoesGameExportDialog(GameExportDialog, Ui_EchoesGameExportDialog):
    _prompt_input_file: bool

    @property
    def _game(self):
        return RandovaniaGame.METROID_PRIME_ECHOES

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool):
        super().__init__(options, patch_data, word_hash, spoiler)

        self.default_output_name = f"Echoes Randomizer - {word_hash}"
        self.check_extracted_game()

        per_game = options.options_for_game(self._game)
        assert isinstance(per_game, EchoesPerGameOptions)

        # Input
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)

        if self._prompt_input_file and per_game.input_path is not None:
            self.input_file_edit.setText(str(per_game.input_path))

        if per_game.output_directory is not None:
            output_path = per_game.output_directory.joinpath(f"{self.default_output_name}.iso")
            self.output_file_edit.setText(str(output_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.input_file_edit: lambda: (not self.input_file.is_file() if self._prompt_input_file
                                               else self.input_file_edit.text() != _VALID_GAME_TEXT),
                self.output_file_edit: lambda: output_file_validator(self.output_file),
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

            options.set_options_for_game(self._game, dataclasses.replace(
                per_game,
                output_directory=self.output_file.parent,
                **per_game_changes,
            ))

    # Getters
    @property
    def input_file(self) -> Optional[Path]:
        if self._prompt_input_file:
            return Path(self.input_file_edit.text())

    @property
    def output_file(self) -> Path:
        return Path(self.output_file_edit.text())

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    # Checks
    def check_extracted_game(self):
        self._prompt_input_file = not has_internal_copy(self._contents_file_path)
        self.input_file_edit.setEnabled(self._prompt_input_file)

        if self._prompt_input_file:
            self.input_file_button.setText("Select File")
        else:
            self.input_file_button.setText("Delete internal copy")
            self.input_file_edit.setText(_VALID_GAME_TEXT)

    # Input file
    def _on_input_file_button(self):
        if self._prompt_input_file:
            input_file = prompt_for_input_file(self, self.input_file_edit, ["iso"])
            if input_file is not None:
                self.input_file_edit.setText(str(input_file.absolute()))
        else:
            delete_internal_copy(self._options.internal_copies_path)
            self.input_file_edit.setText("")
            self.check_extracted_game()

    # Output File
    def _on_output_file_button(self):
        output_file = prompt_for_output_file(self, [".iso"], f"{self.default_output_name}.iso", self.output_file_edit)
        if output_file is not None:
            self.output_file_edit.setText(str(output_file))

    @property
    def _contents_file_path(self):
        return self._options.internal_copies_path.joinpath("prime2", "contents")

    def get_game_export_params(self) -> GameExportParams:
        spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.output_file)
        backup_files_path = self._options.internal_copies_path.joinpath("prime2", "vanilla")

        return EchoesGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
            contents_files_path=self._contents_file_path,
            backup_files_path=backup_files_path,
        )
