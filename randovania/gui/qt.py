import sys

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QFileDialog
from argparse import ArgumentParser

from .mainwindow_ui import Ui_MainWindow
from .manage_game_window_ui import Ui_ManageGameWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.yell_pressed)

    def yell_pressed(self):
        print("AEHOOOOOOOOOOOOOOOOOOOOOO")
        self.manage_game_window = ManageGameWindow()
        self.setCentralWidget(self.manage_game_window.centralWidget)



class ManageGameWindow(QMainWindow, Ui_ManageGameWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.loadIsoButton.clicked.connect(self.load_iso)
        self.packageIsoButton.clicked.connect(self.package_iso)
        self.progressBar.sizePolicy().setRetainSizeWhenHidden(True)
        self.progressBar.setHidden(True)

    def load_iso(self):
        QFileDialog.getOpenFileName(self, filter="*.iso")

    def package_iso(self):
        self.progressBar.setHidden(False)

def run(args):
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "gui",
        help="Run the Graphical User Interface"
    )
    parser.set_defaults(func=run)
