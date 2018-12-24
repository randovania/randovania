from pathlib import Path
from typing import Iterator, Optional, Callable

from PySide2.QtWidgets import QCheckBox, QApplication, QFileDialog, QMainWindow

from randovania.interface_common.options import Options


def map_set_checked(iterable: Iterator[QCheckBox], new_status: bool):
    for checkbox in iterable:
        checkbox.setChecked(new_status)


def lock_application(value: bool):
    QApplication.instance().main_window.setEnabled(value)


def prompt_user_for_input_iso(window: QMainWindow) -> Optional[Path]:
    """
    Shows an QFileDialog asking the user for a vanilla Game ISO
    :param window:
    :return: A string if the user selected a file, None otherwise
    """
    open_result = QFileDialog.getOpenFileName(window, caption="Select the vanilla Game ISO.", filter="*.iso")
    if not open_result or open_result == ("", ""):
        return None
    return Path(open_result[0])


def prompt_user_for_seed_log(window: QMainWindow) -> Optional[Path]:
    """
    Shows an QFileDialog asking the user for a Randovania seed log
    :param window:
    :return: A string if the user selected a file, None otherwise
    """
    open_result = QFileDialog.getOpenFileName(window, caption="Select a Randovania seed log.", filter="*.json")
    if not open_result or open_result == ("", ""):
        return None
    return Path(open_result[0])
