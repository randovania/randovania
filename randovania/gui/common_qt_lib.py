from typing import Iterator, Optional

from PyQt5.QtWidgets import QCheckBox, QApplication, QFileDialog, QMainWindow

from randovania.interface_common.options import Options


def map_set_checked(iterable: Iterator[QCheckBox], new_status: bool):
    for checkbox in iterable:
        checkbox.setChecked(new_status)


def persist_bool_option(attribute_name: str):
    def callback(value: bool):
        options = application_options()
        setattr(options, attribute_name, value)
        options.save_to_disk()

    return callback


def application_options() -> Options:
    return QApplication.instance().options


def lock_application(value: bool):
    QApplication.instance().main_window.setEnabled(value)


def prompt_user_for_input_iso(window: QMainWindow) -> Optional[str]:
    """
    Shows an QFileDialog asking the user for a vanilla Game ISO
    :param window:
    :return: A string if the user selected a file, None otherwise
    """
    open_result = QFileDialog.getOpenFileName(window, caption="Select the vanilla Game ISO.", filter="*.iso")
    if not open_result or open_result == ("", ""):
        return
    return open_result[0]
