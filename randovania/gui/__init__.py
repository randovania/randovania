from PyQt5.QtWidgets import QApplication

from randovania.interface_common.options import Options


def application_options() -> Options:
    return QApplication.instance().options
