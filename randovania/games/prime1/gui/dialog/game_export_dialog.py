import dataclasses
from pathlib import Path

from randovania.exporter.game_exporter import GameExportParams
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.exporter.game_exporter import PrimeGameExportParams
from randovania.gui.dialog.game_export_dialog import GameExportDialog, prompt_for_output_file, prompt_for_input_file
from randovania.gui.generated.prime_game_export_dialog_ui import Ui_PrimeGameExportDialog
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.multi_format_output_mixin import MultiFormatOutputMixin
from randovania.interface_common.options import Options
from randovania.layout.layout_description import LayoutDescription
from randovania.games.prime2.gui.dialog.game_export_dialog import has_internal_copy, delete_internal_copy, _VALID_GAME_TEXT


class PrimeGameExportDialog(GameExportDialog, MultiFormatOutputMixin, Ui_PrimeGameExportDialog):
    _prompt_input_file_echoes: bool
    _echoes_internal_path: Path

    @property
    def _game(self):
        return RandovaniaGame.METROID_PRIME

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games=[]):
        super().__init__(options, patch_data, word_hash, spoiler, games)
        self.setupUi(self)

        self.default_output_name = self.default_output_file(word_hash)
        self.input_file_button.setText("Select File")

        per_game = options.options_for_game(self._game)

        # Input
        self.input_file_edit.textChanged.connect(self._validate_input_file)
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)

        # Output format
        self.setup_multi_format(per_game.output_format)

        # Spoiler
        self.auto_save_spoiler_check.setEnabled(spoiler)
        self.auto_save_spoiler_check.setChecked(options.auto_save_spoiler)

        # Accept/Reject
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Echoes ISO input
        if RandovaniaGame.METROID_PRIME_ECHOES in games:
            self._echoes_internal_path = options.internal_copies_path.joinpath("prime2", "contents")
            self.check_extracted_echoes()
        else:
            self.echoes_file_edit.hide()
            self.echoes_file_label.hide()
            self.echoes_file_button.hide()

        self.input_file_edit.has_error = False
        self.output_file_edit.has_error = False

        if per_game.input_path is not None:
            self.input_file_edit.setText(str(per_game.input_path))

        if per_game.output_directory is not None:
            output_path = per_game.output_directory.joinpath("{}.{}".format(
                self.default_output_name,
                self._selected_output_format,
            ))
            self.output_file_edit.setText(str(output_path))

        self._validate_input_file()
        self._validate_output_file()

    def default_output_file(self, seed_hash: str) -> str:
        return "Prime Randomizer - {}".format(seed_hash)

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

            output_directory = self.output_file
            if self._selected_output_format:
                output_directory = output_directory.parent

            per_game = options.options_for_game(self._game)
            per_game_changes = {
                "input_path": self.input_file,
                "output_directory": output_directory,
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
    def echoes_file(self) -> Path:
        return Path(self.echoes_file_edit.text())

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    def _update_accept_button(self):
        self.accept_button.setEnabled(not (self.input_file_edit.has_error or self.output_file_edit.has_error))

    # Input file
    def _validate_input_file(self):
        has_error = not self.input_file.is_file()
        common_qt_lib.set_error_border_stylesheet(self.input_file_edit, has_error)
        self._update_accept_button()

    def _on_input_file_button(self):
        input_file = prompt_for_input_file(self, self.input_file, self.input_file_edit, self.valid_input_file_types)
        if input_file is not None:
            self.input_file_edit.setText(str(input_file.absolute()))

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
            self.valid_output_file_types,
            "{}.{}".format(self.default_output_name, self._selected_output_format),
            self.output_file_edit,
        )
        if output_file is not None:
            self.output_file_edit.setText(str(output_file))

    def _on_echoes_file_button(self):
        if self._prompt_input_file_echoes:
            input_file = prompt_for_input_file(self, self.input_file, self.input_file_edit, ["iso"])
            if input_file is not None:
                self.echoes_file_edit.setText(str(input_file.absolute()))
        else:
            delete_internal_copy(self._options.internal_copies_path)
            self.echoes_file_edit.setText("")
            self.check_extracted_game()

    def get_game_export_params(self) -> GameExportParams:
        spoiler_output = None
        if self.auto_save_spoiler:
            spoiler_output = self.output_file.parent.joinpath(
                self.output_file.with_suffix(f".{LayoutDescription.file_extension()}")
            )

        return PrimeGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
        )

    def check_extracted_echoes(self):
        self._prompt_input_file_echoes = not has_internal_copy(self._echoes_internal_path)
        self.echoes_file_edit.setEnabled(self._prompt_input_file_echoes)

        if self._prompt_input_file_echoes:
            self.echoes_file_button.setText("Select File")
        else:
            self.echoes_file_button.setText("Delete internal copy")
            self.echoes_file_edit.setText(_VALID_GAME_TEXT)
