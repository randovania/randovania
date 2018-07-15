import sys
from argparse import ArgumentParser
from typing import Optional, List

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QAction

from randovania import VERSION
from randovania.gui.data_editor import DataEditorWindow
from randovania.gui.history_window import HistoryWindow
from randovania.gui.iso_management_window import ISOManagementWindow
from randovania.gui.layout_generator_window import LayoutGeneratorWindow
from randovania.gui.mainwindow_ui import Ui_MainWindow
from randovania.gui.seed_searcher_window import SeedSearcherWindow
from randovania.interface_common.options import Options
from randovania.interface_common.update_checker import get_latest_version


class MainWindow(QMainWindow, Ui_MainWindow):
    newer_version_signal = pyqtSignal(str, str)
    is_preview_mode: bool = False

    menu_new_version: Optional[QAction] = None
    _current_version_url: Optional[str] = None

    def __init__(self, preview: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Randovania {}".format(VERSION))
        self.is_preview_mode = preview

        self.newer_version_signal.connect(self.display_new_version)
        _translate = QtCore.QCoreApplication.translate
        self.tabs = []
        self.windows: List[QMainWindow] = []

        self.tab_windows = [
            (HistoryWindow, "History"),
            (ISOManagementWindow, "ISO Management"),
        ]
        if preview:
            self.tab_windows.insert(1, (DataEditorWindow, "Data Editor"))

        for i, tab in enumerate(self.tab_windows):
            self.windows.append(tab[0](self))
            self.tabs.append(self.windows[i].centralWidget)
            self.tabWidget.insertTab(i, self.tabs[i], _translate("MainWindow", tab[1]))

        self.tabWidget.setCurrentIndex(0)

        get_latest_version(self.newer_version_signal.emit)

    def closeEvent(self, event):
        for window in self.windows:
            window.closeEvent(event)
        super().closeEvent(event)

    def display_new_version(self, new_version: str, new_version_url: str):
        if self.menu_new_version is None:
            self.menu_new_version = QAction("", self)
            self.menu_new_version.triggered.connect(self.open_version_link)
            self.menuBar.addAction(self.menu_new_version)

        self.menu_new_version.setText("New version available: {}".format(new_version))
        self._current_version_url = new_version_url

    def open_version_link(self):
        if self._current_version_url is None:
            raise RuntimeError("Called open_version_link, but _current_version_url is None")

        QDesktopServices.openUrl(QUrl(self._current_version_url))

    def get_tab(self, tab_class) -> Optional[QMainWindow]:
        for window in self.windows:
            if isinstance(window, tab_class):
                return window

    def focus_tab(self, tab: QMainWindow):
        index = self.windows.index(tab)
        self.tabWidget.setCurrentIndex(index)


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
