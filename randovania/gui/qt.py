import sys
from argparse import ArgumentParser

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMessageBox

from randovania.interface_common.options import Options


def catch_exceptions(t, val, tb):
    QMessageBox.critical(None,
                         "An exception was raised",
                         "An unhandled Exception occurred:\n{}".format(val))
    old_hook(t, val, tb)


old_hook = sys.excepthook


def run(args):
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)

    sys.excepthook = catch_exceptions

    app.options = Options()
    app.options.load_from_disk()

    from randovania.gui.main_window import MainWindow
    main_window = MainWindow(getattr(args, "preview", False))
    app.main_window = main_window
    main_window.show()
    sys.exit(app.exec_())


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "gui",
        help="Run the Graphical User Interface"
    )
    parser.add_argument("--preview", action="store_true", help="Activates preview features")
    parser.set_defaults(func=run)
