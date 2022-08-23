import os
import platform
import re
import subprocess
import typing
from pathlib import Path
from typing import Iterator

from PySide6 import QtWidgets, QtGui

import randovania
from randovania import get_data_path


def map_set_checked(iterable: Iterator[QtWidgets.QCheckBox], new_status: bool):
    for checkbox in iterable:
        checkbox.setChecked(new_status)


def lock_application(value: bool):
    QtWidgets.QApplication.instance().main_window.setEnabled(value)


def _prompt_user_for_file(window: QtWidgets.QWidget,
                          caption: str,
                          filter: str,
                          dir: str | None = None,
                          new_file: bool = False) -> Path | None:
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
    open_result = method(window, caption=caption, dir=dir, filter=filter)
    if not open_result or open_result == ("", ""):
        return None
    return Path(open_result[0])


def _prompt_user_for_directory(window: QtWidgets.QWidget,
                               caption: str,
                               dir: str | None = None,
                               new_file: bool = False) -> Path | None:
    if new_file:
        dialog = QtWidgets.QFileDialog(window)
        dialog.setFileMode(QtWidgets.QFileDialog.FileMode.DirectoryOnly)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dialog.setDirectory(dir)
        if dialog.exec_():
            open_result = dialog.selectedFiles()
            if not open_result:
                return None
            return Path(open_result[0])
        return None

    else:
        open_result = QtWidgets.QFileDialog.getExistingDirectory(window, caption, dir,
                                                                 QtWidgets.QFileDialog.ShowDirsOnly)
        if not open_result or open_result == ("", ""):
            return None
        return Path(open_result)


def prompt_user_for_vanilla_input_file(window: QtWidgets.QWidget, extensions: list[str],
                                       existing_file: Path | None = None) -> Path | None:
    """
    Shows an QFileDialog asking the user for a vanilla game file
    :param window:
    :param extensions:
    :param existing_file: An existing file to pre-fill with.
    :return: A string if the user selected a file, None otherwise
    """
    if extensions and extensions == [""]:
        return _prompt_user_for_directory(window, "Select the vanilla game folder",
                                          dir=str(existing_file) if existing_file is not None else None)
    return _prompt_user_for_file(
        window,
        caption="Select the vanilla game {}.".format("/".join(extensions)),
        dir=str(existing_file) if existing_file is not None else None,
        filter=";".join(f"*.{ext}" for ext in extensions),
    )


def prompt_user_for_output_file(window: QtWidgets.QWidget,
                                default_name: str,
                                extensions: list[str]) -> Path | None:
    """
    Shows an QFileDialog asking the user where to place the output file
    :param window:
    :param default_name: Name of a file that will be offered by default in the UI.
    :param extensions:
    :return: A string if the user selected a file, None otherwise
    """
    if extensions and extensions == [""]:
        return _prompt_user_for_directory(window, "Where to place the Randomized game directory",
                                          dir=default_name,
                                          new_file=False)

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
    return _prompt_user_for_file(window, caption="Select a Randovania seed log.",
                                 dir=default_name,
                                 filter=f"Randovania Game, *.{LayoutDescription.file_extension()}",
                                 new_file=True)


def prompt_user_for_input_game_log(window: QtWidgets.QWidget) -> Path | None:
    """
    Shows an QFileDialog asking the user for a Randovania seed log
    :param window:
    :return: A string if the user selected a file, None otherwise
    """
    from randovania.layout.layout_description import LayoutDescription
    return _prompt_user_for_file(window, caption="Select a Randovania seed log.",
                                 filter=f"Randovania Game, *.{LayoutDescription.file_extension()}",
                                 new_file=False)


def prompt_user_for_database_file(window: QtWidgets.QWidget) -> Path | None:
    """
    Shows an QFileDialog asking the user for a Randovania database file
    :param window:
    :return: A string if the user selected a file, None otherwise
    """
    return _prompt_user_for_file(window, caption="Select a Randovania database file.", filter="*.json")


def prompt_user_for_preset_file(window: QtWidgets.QWidget, new_file: bool, name: str | None = None) -> None | (
        Path):
    """
    Shows an QFileDialog asking the user for a Randovania preset file
    :param window:
    :param new_file: If it should be an existing file (False) or not.
    :return: A path if the user selected a file, None otherwise
    """
    from randovania.layout.versioned_preset import VersionedPreset
    return _prompt_user_for_file(window, caption="Select a Randovania Preset file.",
                                 filter=f"Randovania Preset, *.{VersionedPreset.file_extension()};;"
                                        f"All Files (*.*)",
                                 dir=name,
                                 new_file=new_file)


def set_default_window_icon(window: QtWidgets.QWidget):
    """
    Sets the window icon for the given widget to the default icon
    :param window:
    :return:
    """
    window.setWindowIcon(QtGui.QIcon(os.fspath(randovania.get_icon_path())))


def set_combo_with_value(combo: QtWidgets.QComboBox, value):
    """
    Searches all items of the given combo for the given value and changes the current index to that one.
    :param combo:
    :param value:
    :return:
    """
    combo.setCurrentIndex(combo.findData(value))


def set_error_border_stylesheet(edit: QtWidgets.QWidget, has_error: bool):
    edit.has_error = has_error
    if has_error:
        edit.setStyleSheet(":enabled { border: 1px solid red; }"
                           ":disabled { border: 1px solid red; background: #CCC }")
    else:
        edit.setStyleSheet("")


def set_edit_if_different(edit: QtWidgets.QLineEdit, new_text: str):
    """
    Sets the text of the given QLineEdit only if it differs from the current value.
    Prevents snapping the user's cursor to the end unnecessarily.
    :param edit:
    :param new_text:
    :return:
    """
    if edit.text() != new_text:
        edit.setText(new_text)


def get_network_client():
    from randovania.gui.lib.qt_network_client import QtNetworkClient
    return typing.cast(QtNetworkClient, QtWidgets.QApplication.instance().network_client)


def get_game_connection():
    from randovania.game_connection.game_connection import GameConnection
    return typing.cast(GameConnection, QtWidgets.QApplication.instance().game_connection)


def show_install_visual_cpp_redist(details: str):
    from PySide6 import QtWidgets

    download_url = 'https://aka.ms/vs/16/release/vc_redist.x64.exe'
    support_url = 'https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads'

    box = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Critical,
        "Unable to load Dolphin backend",
        "Please install the latest "
        f"<a href='{download_url}'>Microsoft Visual C++ Redistributable</a>.<br /><br />"
        f"For more details, see <a href='{support_url}'>Microsoft's webpage</a>.",
        QtWidgets.QMessageBox.Ok,
    )
    set_default_window_icon(box)
    box.setDetailedText(details)
    box.exec_()


def set_clipboard(text: str):
    from PySide6 import QtWidgets
    QtWidgets.QApplication.clipboard().setText(text)


def open_directory_in_explorer(path: Path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])


def set_icon_data_paths(label: QtWidgets.QLabel):
    image_pattern = re.compile('<img src="data/(.*?)"/>')

    repl = fr'<img src="{get_data_path().as_posix()}/\g<1>"/>'
    new_text = image_pattern.sub(repl, label.text())
    label.setText(new_text)
