from pathlib import Path
from typing import Iterator, Optional

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QCheckBox, QApplication, QFileDialog, QMainWindow, QWidget, QComboBox

from randovania import get_data_path


def map_set_checked(iterable: Iterator[QCheckBox], new_status: bool):
    for checkbox in iterable:
        checkbox.setChecked(new_status)


def lock_application(value: bool):
    QApplication.instance().main_window.setEnabled(value)


def _prompt_user_for_file(window: QMainWindow, caption: str, filter: str) -> Optional[Path]:
    """
    Helper function for all `prompt_user_for_*` functions.
    :param window:
    :param caption:
    :param filter:
    :return: A string if the user selected a file, None otherwise
    """
    open_result = QFileDialog.getOpenFileName(window, caption=caption, filter=filter)
    if not open_result or open_result == ("", ""):
        return None
    return Path(open_result[0])


def prompt_user_for_input_iso(window: QMainWindow) -> Optional[Path]:
    """
    Shows an QFileDialog asking the user for a vanilla Game ISO
    :param window:
    :return: A string if the user selected a file, None otherwise
    """
    return _prompt_user_for_file(window, caption="Select the vanilla Game ISO.", filter="*.iso")


def prompt_user_for_seed_log(window: QMainWindow) -> Optional[Path]:
    """
    Shows an QFileDialog asking the user for a Randovania seed log
    :param window:
    :return: A string if the user selected a file, None otherwise
    """
    return _prompt_user_for_file(window, caption="Select a Randovania seed log.", filter="*.json")


def prompt_user_for_database_file(window: QMainWindow) -> Optional[Path]:
    """
    Shows an QFileDialog asking the user for a Randovania database file
    :param window:
    :return: A string if the user selected a file, None otherwise
    """
    return _prompt_user_for_file(window, caption="Select a Randovania database file.", filter="*.json")


def set_default_window_icon(window: QWidget):
    """
    Sets the window icon for the given widget to the default icon
    :param window:
    :return:
    """
    window.setWindowIcon(QIcon(str(get_data_path().joinpath("icons", "sky_temple_key_NqN_icon.ico"))))


def set_combo_with_value(combo: QComboBox, value):
    """
    Searches all items of the given combo for the given value and changes the current index to that one.
    :param combo:
    :param value:
    :return:
    """
    combo.setCurrentIndex(combo.findData(value))
