import sys
from argparse import ArgumentParser

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow

from randovania.gui.mainwindow_ui import Ui_MainWindow
from randovania.gui.manage_game_window import ManageGameWindow
from randovania.gui.randomize_window import RandomizeWindow
from randovania.interface_common.options import Options


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.manage_game_window = ManageGameWindow()
        self.randomize_window = RandomizeWindow()

        _translate = QtCore.QCoreApplication.translate

        self.fileTab = self.manage_game_window.centralWidget
        self.tabWidget.insertTab(0, self.fileTab, _translate("MainWindow", "Game Management"))

        self.configurationTab = self.randomize_window.centralWidget
        self.tabWidget.insertTab(1, self.configurationTab, _translate("MainWindow", "Configuration"))

        self.tabWidget.setCurrentIndex(0)


def run(args):
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)

    app.options = Options()
    app.options.load_from_disk()

    main_window = MainWindow()
    app.main_window = main_window
    main_window.show()
    sys.exit(app.exec_())


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "gui",
        help="Run the Graphical User Interface"
    )
    parser.set_defaults(func=run)
