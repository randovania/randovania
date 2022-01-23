import dataclasses
from pathlib import Path
from typing import Optional

from PySide2.QtWidgets import QMessageBox, QDialog, QLabel, QRadioButton

from randovania.games.game import RandovaniaGame
from randovania.gui.generated.game_input_dialog_ui import Ui_GameInputDialog
from randovania.gui.lib import common_qt_lib
from randovania.interface_common.options import Options
from randovania.patching.patcher import Patcher

_VALID_GAME_TEXT = "(internal game copy)"


class GameInputDialog(QDialog, Ui_GameInputDialog):
    _options: Options
    _has_spoiler: bool
    _game: RandovaniaGame
    _prompt_input_file: bool
    _current_lock_state: bool = True
    _selected_output_format: str

    def __init__(self, options: Options, patcher: Patcher, word_hash: str, spoiler: bool, game: RandovaniaGame):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self._options = options
        self._has_spoiler = spoiler
        self._game = game

        self.patcher = patcher
        self.default_output_name = patcher.default_output_file(word_hash)
        self.check_extracted_game()

        per_game = options.options_for_game(self._game)

        # Input
        if patcher.requires_input_file:
            file_format1, platform, file_format2 = game.data.gui().input_file_text
            description_text = "<html><head/><body><p>In order to create the randomized game, {} of {} for {} is necessary.</p>".format(
                file_format1, game.long_name, platform)
            if not patcher.uses_input_file_directly:
                description_text += "<p>After using it once, a copy is kept by Randovania for later use.</p>"
            description_text += "</body></html>"
            self.description_label.setText(description_text)

            self.input_file_label.setText(f"Input File (Vanilla {file_format2})")
            self.input_file_edit.setPlaceholderText(f"Path to vanilla {file_format2}")
            self.input_file_edit.textChanged.connect(self._validate_input_file)
            self.input_file_button.clicked.connect(self._on_input_file_button)
        else:
            self.input_file_label.setText("Game does not require input files.")
            self.input_file_edit.setVisible(False)
            self.input_file_button.setVisible(False)
            self.description_label.setVisible(False)

        # Output
        self.output_file_edit.textChanged.connect(self._validate_output_file)
        self.output_file_button.clicked.connect(self._on_output_file_button)

        # Output format
        if per_game.output_format is not None:
            self._selected_output_format = per_game.output_format
        else:
            self._selected_output_format = patcher.valid_output_file_types[0]

        if len(patcher.valid_output_file_types) > 1:
            layout = self.output_format_layout
            output_label = QLabel()
            output_label.setText("Output Format")
            layout.addWidget(output_label)
            for filetype in patcher.valid_output_file_types:
                radio = QRadioButton("." + filetype, self)
                if filetype == self._selected_output_format:
                    radio.setChecked(True)
                radio.toggled.connect(self._on_output_format_changed)
                layout.addWidget(radio)

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
            output_path = per_game.output_directory
            if self._selected_output_format:
                output_path = output_path.joinpath("{}.{}".format(self.default_output_name,
                                                                  self._selected_output_format))
            self.output_file_edit.setText(str(output_path))

        self._validate_input_file()
        self._validate_output_file()

    def save_options(self):
        with self._options as options:
            if self._has_spoiler:
                options.auto_save_spoiler = self.auto_save_spoiler

            output_directory = self.output_file
            if self._selected_output_format:
                output_directory = output_directory.parent

            per_game = options.options_for_game(self._game)
            per_game_changes = {
                "output_directory": output_directory,
                "output_format": self._selected_output_format,
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
        self._prompt_input_file = (self.patcher.uses_input_file_directly or
                                   not self.patcher.has_internal_copy(self._options.internal_copies_path))
        self.input_file_edit.setEnabled(self._prompt_input_file)

        if self._prompt_input_file:
            self.input_file_button.setText("Select File")
        else:
            self.input_file_button.setText("Delete internal copy")
            self.input_file_edit.setText(_VALID_GAME_TEXT)

    # Input file
    def _validate_input_file(self):
        has_error = False

        if self.patcher.requires_input_file:
            if self._prompt_input_file:
                if self._selected_output_format:
                    has_error = not self.input_file.is_file()
                elif self.input_file_edit.text():
                    has_error = not self.input_file.is_dir()
                else:
                    has_error = True
            else:
                has_error = self.input_file_edit.text() != _VALID_GAME_TEXT

        common_qt_lib.set_error_border_stylesheet(self.input_file_edit, has_error)
        self._update_accept_button()

    def _on_input_file_button(self):
        if self._prompt_input_file:
            existing_file = None
            if self._selected_output_format:
                if self.input_file.is_file():
                    existing_file = self.input_file
                elif self.input_file_edit.text() and self.input_file.parent.is_dir():
                    existing_file = self.input_file.parent
            else:
                if self.input_file.is_dir():
                    existing_file = self.input_file

            input_file = common_qt_lib.prompt_user_for_vanilla_input_file(self, self.patcher.valid_input_file_types,
                                                                          existing_file=existing_file)
            if input_file is not None:
                self.input_file_edit.setText(str(input_file.absolute()))
        else:
            self.patcher.delete_internal_copy(self._options.internal_copies_path)
            self.input_file_edit.setText("")
            self.check_extracted_game()

    # Output File
    def _validate_output_file(self):
        output_file = self.output_file
        if self._selected_output_format:
            has_error = output_file.is_dir() or not output_file.parent.is_dir()
        elif self.output_file_edit.text():
            has_error = not output_file.is_dir()
        else:
            has_error = True

        common_qt_lib.set_error_border_stylesheet(self.output_file_edit, has_error)
        self._update_accept_button()

    def _on_output_file_button(self):
        if self._selected_output_format:
            suggested_name = "{}.{}".format(self.default_output_name, self._selected_output_format)

            if self.output_file_edit.text() and self.output_file.parent.is_dir():
                suggested_name = str(self.output_file.parent.joinpath(suggested_name))
        else:
            suggested_name = self.default_output_name
            if self.output_file_edit.text():
                suggested_name = str(self.output_file)

        output_file = common_qt_lib.prompt_user_for_output_file(self, suggested_name,
                                                                self.patcher.valid_output_file_types)
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

    def _on_output_format_changed(self):
        button = self.sender()
        if button.isChecked():
            self._selected_output_format = button.text()[1:]
            current_filename = Path(self.output_file_edit.text())
            if str(current_filename) != '.':
                self.output_file_edit.setText(str(current_filename.with_suffix('.' + self._selected_output_format)))
                self._validate_output_file()
