from pathlib import Path
from typing import Optional

from PySide2.QtWidgets import QMessageBox, QDialog

from randovania.gui.generated.game_input_dialog_ui import Ui_GameInputDialog
from randovania.gui.lib import common_qt_lib
from randovania.interface_common import simplified_patcher, game_workdir
from randovania.interface_common.options import Options

_VALID_GAME_TEXT = "(internal Metroid Prime 2 copy)"


class GameInputDialog(QDialog, Ui_GameInputDialog):
    _options: Options
    _has_game: bool
    _current_lock_state: bool = True

    def __init__(self, options: Options, default_iso_name: str, spoiler: bool):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self._options = options
        self.default_iso_name = default_iso_name
        self.check_extracted_game()

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

        if options.output_directory is not None:
            self.output_file_edit.setText(str(options.output_directory.joinpath(self.default_iso_name)))

        self._validate_input_file()
        self._validate_output_file()

    # Getters
    @property
    def input_file(self) -> Optional[Path]:
        if self._has_game:
            return None
        else:
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
        result = game_workdir.discover_game(self._options.game_files_path)
        self._has_game = result is not None
        self.input_file_edit.setEnabled(not self._has_game)

        if not self._has_game:
            self.input_file_button.setText("Select File")
        else:
            self.input_file_button.setText("Delete internal copy")
            game_id, _ = result
            if game_id.startswith("G2M"):
                self.input_file_edit.setText(_VALID_GAME_TEXT)
            else:
                self.input_file_edit.setText("(internal unknown game copy)")

    # Input file
    def _validate_input_file(self):
        if self._has_game:
            has_error = self.input_file_edit.text() != _VALID_GAME_TEXT
        else:
            has_error = not self.input_file.is_file()

        common_qt_lib.set_error_border_stylesheet(self.input_file_edit, has_error)
        self._update_accept_button()

    def _on_input_file_button(self):
        if self._has_game:
            simplified_patcher.delete_files_location(self._options)
            self.input_file_edit.setText("")
            self.check_extracted_game()
        else:
            input_file = common_qt_lib.prompt_user_for_input_iso(self)
            if input_file is not None:
                self.input_file_edit.setText(str(input_file.absolute()))

    # Output File
    def _validate_output_file(self):
        output_file = self.output_file
        has_error = output_file.is_dir() or not output_file.parent.is_dir()

        common_qt_lib.set_error_border_stylesheet(self.output_file_edit, has_error)
        self._update_accept_button()

    def _on_output_file_button(self):
        output_file = common_qt_lib.prompt_user_for_output_iso(self, self.default_iso_name)
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
