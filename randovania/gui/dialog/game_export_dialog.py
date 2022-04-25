from pathlib import Path
from typing import Optional, TypeVar, Type, Callable

from PySide6 import QtWidgets
from PySide6.QtWidgets import QMessageBox

from randovania.exporter.game_exporter import GameExportParams
from randovania.games.game import RandovaniaGame
from randovania.gui.lib import common_qt_lib
from randovania.interface_common.options import Options
from randovania.layout.layout_description import LayoutDescription

T = TypeVar("T")


def _try_get_field(obj, field_name: str, cls: Type[T]) -> Optional[T]:
    return getattr(obj, field_name, None)


class GameExportDialog(QtWidgets.QDialog):
    _options: Options
    _patch_data: dict
    _word_hash: str
    _has_spoiler: bool
    _games: list[RandovaniaGame]

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__()
        common_qt_lib.set_default_window_icon(self)
        self._options = options
        self._patch_data = patch_data
        self._word_hash = word_hash
        self._has_spoiler = spoiler
        self._games = games

        if (func := _try_get_field(self, "setupUi", None)) is not None:
            func(self)

        # Spoiler
        if (check := _try_get_field(self, "auto_save_spoiler_check", QtWidgets.QCheckBox)) is not None:
            check.setEnabled(spoiler)
            check.setChecked(options.auto_save_spoiler)

        # Accept/Reject
        if (btn := _try_get_field(self, "accept_button", QtWidgets.QPushButton)) is not None:
            btn.clicked.connect(self.accept)

        if (btn := _try_get_field(self, "cancel_button", QtWidgets.QPushButton)) is not None:
            btn.clicked.connect(self.reject)

    def save_options(self):
        """Ensure that the current state of the dialog is saved to options."""
        raise NotImplementedError()

    def get_game_export_params(self) -> GameExportParams:
        """Get the export params defined by the user. It'll be sent over to the `GameExporter`."""
        raise NotImplementedError()


def _prompt_for_output_common(parent: QtWidgets.QWidget, suggested_name: str,
                              valid_output_file_types: list[str]) -> Optional[Path]:
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


def prompt_for_output_file(parent: QtWidgets.QWidget, valid_output_file_types: list[str], suggested_name: str,
                           output_file_edit: QtWidgets.QLineEdit) -> Optional[Path]:
    if output_file_edit.text() and (previous_output := Path(output_file_edit.text()).parent).is_dir():
        suggested_name = str(previous_output.joinpath(suggested_name))

    return _prompt_for_output_common(
        parent, suggested_name, valid_output_file_types
    )


def prompt_for_output_directory(parent: QtWidgets.QWidget, suggested_name: str,
                                output_file_edit: QtWidgets.QLineEdit) -> Optional[Path]:
    if output_file_edit.text():
        suggested_name = output_file_edit.text()

    return _prompt_for_output_common(
        parent, suggested_name, [""]
    )


def prompt_for_input_file(parent: QtWidgets.QWidget, input_file_edit: QtWidgets.QLineEdit,
                          valid_input_file_types: list[str]) -> Optional[Path]:
    existing_file = None
    if input_file_edit.text():
        input_file = Path(input_file_edit.text())
        if input_file.is_file():
            existing_file = input_file
        elif input_file.parent.is_dir():
            existing_file = input_file.parent

    return common_qt_lib.prompt_user_for_vanilla_input_file(parent, valid_input_file_types,
                                                            existing_file=existing_file)


def prompt_for_input_directory(parent: QtWidgets.QWidget, input_file_edit: QtWidgets.QLineEdit) -> Optional[Path]:
    existing_file = None
    if input_file_edit.text():
        input_file = Path(input_file_edit.text())
        if input_file.is_dir():
            existing_file = input_file

    return common_qt_lib.prompt_user_for_vanilla_input_file(parent, [""], existing_file=existing_file)


def spoiler_path_for(save_spoiler: bool, output_file: Path) -> Optional[Path]:
    if save_spoiler:
        return output_file.with_suffix(f".{LayoutDescription.file_extension()}")
    else:
        return None


def spoiler_path_for_directory(save_spoiler: bool, output_dir: Path) -> Optional[Path]:
    if save_spoiler:
        return output_dir.joinpath(f"spoiler.{LayoutDescription.file_extension()}")
    else:
        return None


def add_field_validation(accept_button: QtWidgets.QPushButton, fields: dict[QtWidgets.QLineEdit, Callable[[], bool]]):
    def accept_validation():
        accept_button.setEnabled(not any(f.has_error for f in fields.keys()))

    def make_validation(obj, check_err):
        def field_validation():
            common_qt_lib.set_error_border_stylesheet(obj, check_err())
            accept_validation()

        return field_validation

    accept_button.update_validation = accept_validation
    for field, check_error_function in fields.items():
        common_qt_lib.set_error_border_stylesheet(field, check_error_function())
        field.field_validation = make_validation(field, check_error_function)
        field.textChanged.connect(field.field_validation)

    accept_validation()


def path_in_edit(line: QtWidgets.QLineEdit) -> Optional[Path]:
    if line.text():
        return Path(line.text())
    else:
        return None


def update_validation(widget: QtWidgets.QLineEdit):
    if hasattr(widget, "field_validation"):
        widget.field_validation()


def output_file_validator(output_file: Path) -> bool:
    return output_file.is_dir() or not output_file.parent.is_dir()


def is_directory_validator(line: QtWidgets.QLineEdit) -> bool:
    return not line.text() or not Path(line.text()).is_dir()


def is_file_validator(file: Optional[Path]) -> bool:
    """Returns False when the given path is not None and is a file, True otherwise"""
    if file is None:
        return True
    else:
        return not file.is_file()
