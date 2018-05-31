import sys
from argparse import ArgumentParser

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox

from randovania.gui.data_editor import DataEditorWindow
from randovania.gui.mainwindow_ui import Ui_MainWindow
from randovania.gui.manage_game_window import ManageGameWindow
from randovania.gui.randomize_window import RandomizeWindow
from randovania.interface_common.options import Options


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, preview: bool):
        super().__init__()
        self.setupUi(self)

        self.manage_game_window = ManageGameWindow()
        self.randomize_window = RandomizeWindow()
        self.data_editor_window = DataEditorWindow()

        _translate = QtCore.QCoreApplication.translate

        self.fileTab = self.manage_game_window.centralWidget
        self.tabWidget.insertTab(0, self.fileTab, _translate("MainWindow", "Game Management"))

        self.configurationTab = self.randomize_window.centralWidget
        self.tabWidget.insertTab(1, self.configurationTab, _translate("MainWindow", "Configuration"))

        if preview:
            self.dataEditorTab = self.data_editor_window.centralWidget
            self.tabWidget.insertTab(2, self.dataEditorTab, _translate("MainWindow", "Data Editor"))

        self.tabWidget.setCurrentIndex(0)

    def closeEvent(self, event):
        self.manage_game_window.closeEvent(event)
        super().closeEvent(event)


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
