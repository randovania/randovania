from PyQt5.QtWidgets import QApplication

from randovania.interface_common.options import Options


def application_options() -> Options:
    return QApplication.instance().options


def lock_application(value: bool):
    QApplication.instance().main_window.setEnabled(value)
