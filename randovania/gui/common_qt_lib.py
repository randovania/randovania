from typing import Iterator

from PyQt5.QtWidgets import QCheckBox, QApplication

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
