import dataclasses
from pathlib import Path

from PySide2.QtWidgets import QMessageBox

from randovania.exporter.game_exporter import GameExportParams
from randovania.games.dread.exporter.game_exporter import DreadGameExportParams
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.game_export_dialog import GameExportDialog
from randovania.gui.generated.dread_game_export_dialog_ui import Ui_DreadGameExportDialog
from randovania.gui.lib import common_qt_lib
from randovania.interface_common.options import Options
from randovania.layout.layout_description import LayoutDescription


class DreadGameExportDialog(GameExportDialog, Ui_DreadGameExportDialog):
    @property
    def _game(self):
        return RandovaniaGame.METROID_DREAD

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool):
        super().__init__(options, patch_data, word_hash, spoiler)
        self.setupUi(self)

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

        if per_game.input_path is not None:
            self.input_file_edit.setText(str(per_game.input_path))

        if per_game.output_directory is not None:
            output_path = per_game.output_directory
            self.output_file_edit.setText(str(output_path))

        self._validate_input_file()
        self._validate_output_file()

    def save_options(self):
        with self._options as options:
            if self._has_spoiler:
                options.auto_save_spoiler = self.auto_save_spoiler

            output_directory = self.output_file

            per_game = options.options_for_game(self._game)
            per_game_changes = {
                "input_path": self.input_file,
                "output_directory": output_directory,
            }
            options.set_options_for_game(self._game, dataclasses.replace(per_game, **per_game_changes))

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

    def _update_accept_button(self):
        self.accept_button.setEnabled(not (self.input_file_edit.has_error or self.output_file_edit.has_error))

    # Input file
    def _validate_input_file(self):
        if self.input_file_edit.text():
            has_error = not self.input_file.is_dir()
        else:
            has_error = True

        common_qt_lib.set_error_border_stylesheet(self.input_file_edit, has_error)
        self._update_accept_button()

    def _on_input_file_button(self):
        existing_file = None
        if self.input_file.is_dir():
            existing_file = self.input_file

        input_file = common_qt_lib.prompt_user_for_vanilla_input_file(self, self.patcher.valid_input_file_types,
                                                                      existing_file=existing_file)
        if input_file is not None:
            self.input_file_edit.setText(str(input_file.absolute()))

    # Output File
    def _validate_output_file(self):
        output_file = self.output_file
        if self.output_file_edit.text():
            has_error = not output_file.is_dir()
        else:
            has_error = True

        common_qt_lib.set_error_border_stylesheet(self.output_file_edit, has_error)
        self._update_accept_button()

    def _on_output_file_button(self):
        suggested_name = "DreadRandovania"
        if self.output_file_edit.text():
            suggested_name = str(self.output_file)

        output_file = common_qt_lib.prompt_user_for_output_file(self, suggested_name, [""])
        if output_file is None:
            return

        output_file = output_file.absolute()

        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
        except (FileNotFoundError, OSError) as error:
            QMessageBox.warning(self,
                                "Invalid output file",
                                "Unable to use '{}' as output file: {}".format(output_file, error),
                                )
            return

        self.output_file_edit.setText(str(output_file))

    def get_game_export_params(self) -> GameExportParams:
        spoiler_output = None
        if self.auto_save_spoiler:
            spoiler_output = self.output_file.parent.joinpath(
                self.output_file.with_suffix(f".{LayoutDescription.file_extension()}")
            )

        return DreadGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
        )
