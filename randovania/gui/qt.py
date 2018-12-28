import sys
from argparse import ArgumentParser

from PySide2 import QtCore
from PySide2.QtWidgets import QApplication, QMessageBox

from randovania.interface_common.options import Options


def catch_exceptions(t, val, tb):
    QMessageBox.critical(None,
                         "An exception was raised",
                         "An unhandled Exception occurred:\n{}".format(val))
    old_hook(t, val, tb)


old_hook = sys.excepthook


def show_main_window(app: QApplication, args):
    options = Options.with_default_data_dir()
    options.load_from_disk()

    from randovania.gui.main_window import MainWindow
    main_window = MainWindow(options, getattr(args, "preview", False))
    app.main_window = main_window
    main_window.show()


def show_data_editor(app: QApplication, args):
    from randovania.games.prime import default_data
    from randovania.gui.data_editor import DataEditorWindow

    app.data_visualizer = DataEditorWindow(default_data.decode_default_prime2(), True)
    app.data_visualizer.show()


def run(args):
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)

    sys.excepthook = catch_exceptions

    if getattr(args, "window", None) == "data-editor":
        show_data_editor(app, args)
    else:
        show_main_window(app, args)

    sys.exit(app.exec_())


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "gui",
        help="Run the Graphical User Interface"
    )
    parser.add_argument("--preview", action="store_true", help="Activates preview features")
    parser.add_argument("--data-editor", action="store_const", dest="window", const="data-editor",
                        help="Displays the data editor window")
    parser.set_defaults(func=run)
