from __future__ import annotations

import os
import re
import subprocess
import sys
import typing
from pathlib import Path
from subprocess import CalledProcessError

from PySide6 import QtCore, QtGui, QtWidgets

import randovania
from randovania import get_data_path

if typing.TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_connection.game_connection import GameConnection
    from randovania.gui.lib.qt_network_client import QtNetworkClient
    from randovania.gui.qt import RdvApplication
    from randovania.interface_common.options import Options


def map_set_checked(iterable: Iterator[QtWidgets.QCheckBox], new_status: bool) -> None:
    for checkbox in iterable:
        checkbox.setChecked(new_status)


def current_application() -> RdvApplication:
    return typing.cast("RdvApplication", QtWidgets.QApplication.instance())


def lock_application(value: bool) -> None:
    current_application().main_window.setEnabled(value)


def _prompt_user_for_file(
    window: QtWidgets.QWidget, caption: str, filter: str, dir: str | None = None, new_file: bool = False
) -> Path | None:
    """
    Helper function for all `prompt_user_for_*` functions.
    :param window:
    :param caption:
    :param filter:
    :param new_file: If false, prompt for an existing file.
    :return: A string if the user selected a file, None otherwise
    """
    if new_file:
        method = QtWidgets.QFileDialog.getSaveFileName
    else:
        method = QtWidgets.QFileDialog.getOpenFileName
    open_result = method(window, caption=caption, dir=dir if dir is not None else "", filter=filter)
    if not open_result or open_result == ("", ""):
        return None
    return Path(open_result[0])


def _prompt_user_for_directory(
    window: QtWidgets.QWidget, caption: str, dir: str | None = None, new_file: bool = False
) -> Path | None:
    dir = dir if dir is not None else ""
    if new_file:
        dialog = QtWidgets.QFileDialog(window)
        dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
        dialog.setOption(QtWidgets.QFileDialog.Option.ShowDirsOnly)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        dialog.setDirectory(dir)
        if dialog.exec_():
            new_open_result = dialog.selectedFiles()
            if not new_open_result:
                return None
            return Path(new_open_result[0])
        return None

    else:
        existing_open_result = QtWidgets.QFileDialog.getExistingDirectory(
            window, caption, dir, QtWidgets.QFileDialog.Option.ShowDirsOnly
        )
        if not existing_open_result or existing_open_result == ("", ""):
            return None
        return Path(existing_open_result)


def prompt_user_for_vanilla_input_file(
    window: QtWidgets.QWidget, extensions: list[str], existing_file: Path | None = None
) -> Path | None:
    """
    Shows an QFileDialog asking the user for a vanilla game file
    :param window:
    :param extensions:
    :param existing_file: An existing file to pre-fill with.
    :return: A string if the user selected a file, None otherwise
    """
    if extensions and extensions == [""]:
        return _prompt_user_for_directory(
            window, "Select the vanilla game folder", dir=str(existing_file) if existing_file is not None else None
        )
    return _prompt_user_for_file(
        window,
        caption="Select the vanilla game {}.".format("/".join(extensions)),
        dir=str(existing_file) if existing_file is not None else None,
        filter=";".join(f"*.{ext}" for ext in extensions),
    )


def prompt_user_for_output_file(window: QtWidgets.QWidget, default_name: str, extensions: list[str]) -> Path | None:
    """
    Shows an QFileDialog asking the user where to place the output file
    :param window:
    :param default_name: Name of a file that will be offered by default in the UI.
    :param extensions:
    :return: A string if the user selected a file, None otherwise
    """
    if extensions and extensions == [""]:
        return _prompt_user_for_directory(
            window, "Where to place the Randomized game directory", dir=default_name, new_file=False
        )

    return _prompt_user_for_file(
        window,
        caption="Where to place the Randomized game file.",
        dir=default_name,
        filter=";".join(f"*.{ext}" for ext in extensions),
        new_file=True,
    )


def prompt_user_for_output_game_log(window: QtWidgets.QWidget, default_name: str) -> Path | None:
    """
    Shows an QFileDialog asking the user for a Randovania seed log
    :param window:
    :param default_name:
    :return: A string if the user selected a file, None otherwise
    """
    from randovania.layout.layout_description import LayoutDescription

    return _prompt_user_for_file(
        window,
        caption="Select a Randovania seed log.",
        dir=default_name,
        filter=f"Randovania Game, *.{LayoutDescription.file_extension()}",
        new_file=True,
    )


def prompt_user_for_input_game_log(window: QtWidgets.QWidget) -> Path | None:
    """
    Shows an QFileDialog asking the user for a Randovania seed log
    :param window:
    :return: A string if the user selected a file, None otherwise
    """
    from randovania.layout.layout_description import LayoutDescription

    return _prompt_user_for_file(
        window,
        caption="Select a Randovania seed log.",
        filter=f"Randovania Game, *.{LayoutDescription.file_extension()}",
        new_file=False,
    )


def prompt_user_for_database_file(window: QtWidgets.QWidget) -> Path | None:
    """
    Shows an QFileDialog asking the user for a Randovania database file
    :param window:
    :return: A string if the user selected a file, None otherwise
    """
    return _prompt_user_for_file(window, caption="Select a Randovania database file.", filter="*.json")


def prompt_user_for_preset_file(window: QtWidgets.QWidget, new_file: bool, name: str | None = None) -> None | (Path):
    """
    Shows an QFileDialog asking the user for a Randovania preset file
    :param window:
    :param new_file: If it should be an existing file (False) or not.
    :return: A path if the user selected a file, None otherwise
    """
    from randovania.layout.versioned_preset import VersionedPreset

    return _prompt_user_for_file(
        window,
        caption="Select a Randovania Preset file.",
        filter=f"Randovania Preset, *.{VersionedPreset.file_extension()};;All Files (*.*)",
        dir=name,
        new_file=new_file,
    )


def prompt_user_for_preset_folder(window: QtWidgets.QWidget) -> None | Path:
    """
    Shows a QFileDialog asking the user for a directory in which to save multiple Randovania preset files
    :param parent:
    :return: A string if the user selected a directory, None otherwise
    """

    return _prompt_user_for_directory(window, caption="Select a directory in which to place preset files")


def set_default_window_icon(window: QtWidgets.QWidget) -> None:
    """
    Sets the window icon for the given widget to the default icon
    :param window:
    :return:
    """
    window.setWindowIcon(QtGui.QIcon(os.fspath(randovania.get_icon_path())))


class ErrorBorderWidget(QtWidgets.QWidget):
    has_error: bool


def set_error_border_stylesheet(edit: QtWidgets.QWidget, has_error: bool) -> None:
    widget = typing.cast("ErrorBorderWidget", edit)

    widget.has_error = has_error
    if has_error:
        widget.setStyleSheet(":enabled { border: 1px solid red; }:disabled { border: 1px solid red; background: #CCC }")
    else:
        widget.setStyleSheet("")


def set_edit_if_different(edit: QtWidgets.QLineEdit, new_text: str) -> None:
    """
    Sets the text of the given QLineEdit only if it differs from the current value.
    Prevents snapping the user's cursor to the end unnecessarily.
    :param edit:
    :param new_text:
    :return:
    """
    if edit.text() != new_text:
        edit.setText(new_text)


def set_edit_if_different_text(edit: QtWidgets.QTextEdit, new_text: str) -> None:
    if edit.toPlainText() != new_text:
        edit.setPlainText(new_text)


def get_network_client() -> QtNetworkClient:
    return current_application().network_client


def get_game_connection() -> GameConnection:
    return current_application().game_connection


def show_install_visual_cpp_redist(details: str) -> None:
    from PySide6 import QtWidgets

    download_url = "https://aka.ms/vs/16/release/vc_redist.x64.exe"
    support_url = "https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads"

    box = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Icon.Critical,
        "Unable to load Dolphin backend",
        "Please install the latest "
        f"<a href='{download_url}'>Microsoft Visual C++ Redistributable</a>.<br /><br />"
        f"For more details, see <a href='{support_url}'>Microsoft's webpage</a>.",
        QtWidgets.QMessageBox.StandardButton.Ok,
    )
    set_default_window_icon(box)
    box.setDetailedText(details)
    box.exec_()


def set_clipboard(text: str) -> None:
    from PySide6 import QtWidgets

    QtWidgets.QApplication.clipboard().setText(text)


class FallbackDialog(typing.NamedTuple):
    title: str
    text: str
    parent: QtWidgets.QWidget


def open_directory_in_explorer(path: Path, fallback_dialog: FallbackDialog | None = None) -> None:
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=True)
        else:
            subprocess.run(["xdg-open", path], check=True)

    except (OSError, CalledProcessError):
        if fallback_dialog is None:
            raise
        else:
            box = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Information,
                fallback_dialog.title,
                fallback_dialog.text,
                QtWidgets.QMessageBox.StandardButton.Ok,
                fallback_dialog.parent,
            )
            box.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            box.show()


def set_icon_data_paths(label: QtWidgets.QLabel) -> None:
    image_pattern = re.compile('<img src="data/(.*?)"/>')

    repl = rf'<img src="{get_data_path().as_posix()}/\g<1>"/>'
    new_text = image_pattern.sub(repl, label.text())
    label.setText(new_text)


def alert_user_on_generation(parent: QtWidgets.QWidget, options: Options) -> None:
    if options.audible_generation_alert:
        QtWidgets.QApplication.beep()
    if options.visual_generation_alert:
        QtWidgets.QApplication.alert(parent)
