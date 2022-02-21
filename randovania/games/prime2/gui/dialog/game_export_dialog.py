import dataclasses
import shutil
from pathlib import Path
from typing import Optional

from randovania.exporter.game_exporter import GameExportParams
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.exporter.game_exporter import EchoesGameExportParams
from randovania.gui.dialog.game_export_dialog import GameExportDialog, prompt_for_output_file, prompt_for_input_file
from randovania.gui.generated.echoes_game_export_dialog_ui import Ui_EchoesGameExportDialog
from randovania.gui.lib import common_qt_lib
from randovania.interface_common import game_workdir
from randovania.interface_common.options import Options
from randovania.layout.layout_description import LayoutDescription

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

    def default_output_file(self, seed_hash: str) -> str:
        return "Echoes Randomizer - {}".format(seed_hash)

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games=[]):
        super().__init__(options, patch_data, word_hash, spoiler, games)
        self.setupUi(self)

        self.default_output_name = self.default_output_file(word_hash)
        self.check_extracted_game()

        per_game = options.options_for_game(self._game)

        # Input
        self.input_file_edit.textChanged.connect(self._validate_input_file)
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Output
        self.output_file_edit.textChanged.connect(self._validate_output_file)
        self.output_file_button.clicked.connect(self._on_output_file_button)

        # Spoiler
        self.auto_save_spoiler_check.setEnabled(spoiler)
        self.auto_save_spoiler_check.setChecked(options.auto_save_spoiler)

        # Accept/Reject
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self.input_file_edit.has_error = False
        self.output_file_edit.has_error = False

        if self._prompt_input_file and per_game.input_path is not None:
            self.input_file_edit.setText(str(per_game.input_path))

        if per_game.output_directory is not None:
            output_path = per_game.output_directory.joinpath("{}.iso".format(
                self.default_output_name,
            ))
            self.output_file_edit.setText(str(output_path))

        self._validate_input_file()
        self._validate_output_file()

    def save_options(self):
        with self._options as options:
            if self._has_spoiler:
                options.auto_save_spoiler = self.auto_save_spoiler

            output_directory = self.output_file.parent

            per_game = options.options_for_game(self._game)
            per_game_changes = {
                "output_directory": output_directory,
            }
            if self._prompt_input_file:
                per_game_changes["input_path"] = self.input_file

            options.set_options_for_game(self._game, dataclasses.replace(per_game, **per_game_changes))

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

    def _update_accept_button(self):
        self.accept_button.setEnabled(not (self.input_file_edit.has_error or self.output_file_edit.has_error))

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
    def _validate_input_file(self):
        if self._prompt_input_file:
            has_error = not self.input_file.is_file()
        else:
            has_error = self.input_file_edit.text() != _VALID_GAME_TEXT

        common_qt_lib.set_error_border_stylesheet(self.input_file_edit, has_error)
        self._update_accept_button()

    def _on_input_file_button(self):
        if self._prompt_input_file:
            input_file = prompt_for_input_file(self, self.input_file, self.input_file_edit, ["iso"])
            if input_file is not None:
                self.input_file_edit.setText(str(input_file.absolute()))
        else:
            delete_internal_copy(self._options.internal_copies_path)
            self.input_file_edit.setText("")
            self.check_extracted_game()

    # Output File
    def _validate_output_file(self):
        output_file = self.output_file
        has_error = output_file.is_dir() or not output_file.parent.is_dir()

        common_qt_lib.set_error_border_stylesheet(self.output_file_edit, has_error)
        self._update_accept_button()

    def _on_output_file_button(self):
        output_file = prompt_for_output_file(
            self,
            self.output_file,
            [".iso"],
            "{}.iso".format(self.default_output_name),
            self.output_file_edit,
        )
        if output_file is not None:
            self.output_file_edit.setText(str(output_file))

    @property
    def _contents_file_path(self):
        return self._options.internal_copies_path.joinpath("prime2", "contents")

    def get_game_export_params(self) -> GameExportParams:
        spoiler_output = None
        if self.auto_save_spoiler:
            spoiler_output = self.output_file.parent.joinpath(
                self.output_file.with_suffix(f".{LayoutDescription.file_extension()}")
            )

        backup_files_path = self._options.internal_copies_path.joinpath("prime2", "vanilla")

        return EchoesGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
            contents_files_path=self._contents_file_path,
            backup_files_path=backup_files_path,
        )
