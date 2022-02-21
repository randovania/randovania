from pathlib import Path
from typing import Optional

from PySide2 import QtWidgets
from PySide2.QtWidgets import QMessageBox

from randovania.exporter.game_exporter import GameExportParams
from randovania.gui.lib import common_qt_lib
from randovania.interface_common.options import Options


class GameExportDialog(QtWidgets.QDialog):
    _options: Options
    _patch_data: dict
    _word_hash: str
    _has_spoiler: bool
    _games: list

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games=[]):
        super().__init__()
        common_qt_lib.set_default_window_icon(self)
        self._options = options
        self._patch_data = patch_data
        self._word_hash = word_hash
        self._has_spoiler = spoiler
        self._games = games

    def save_options(self):
        """Ensure that the current state of the dialog is saved to options."""
        raise NotImplementedError()

    def get_game_export_params(self) -> GameExportParams:
        """Get the export params defined by the user. It'll be sent over to the `GameExporter`."""
        raise NotImplementedError()


def prompt_for_output_file(parent: QtWidgets.QWidget, previous_output: Path,
                           valid_output_file_types: list[str],
                           suggested_name: str, output_file_edit: QtWidgets.QLineEdit) -> Optional[Path]:
    if output_file_edit.text() and previous_output.parent.is_dir():
        suggested_name = str(previous_output.parent.joinpath(suggested_name))

    output_file = common_qt_lib.prompt_user_for_output_file(
        parent, suggested_name, valid_output_file_types
    )
    if output_file is None:
        return None

    output_file = output_file.absolute()

    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
    except (FileNotFoundError, OSError) as error:
        QMessageBox.warning(
            parent,
            "Invalid output file",
            "Unable to use '{}' as output file: {}".format(output_file, error),
        )
        return None

    return output_file


def prompt_for_input_file(parent: QtWidgets.QWidget, input_file: Path, input_file_edit: QtWidgets.QLineEdit,
                          valid_input_file_types: list[str]) -> Optional[Path]:
    existing_file = None
    if input_file.is_file():
        existing_file = input_file
    elif input_file_edit.text() and input_file.parent.is_dir():
        existing_file = input_file.parent

    return common_qt_lib.prompt_user_for_vanilla_input_file(parent, valid_input_file_types,
                                                            existing_file=existing_file)
