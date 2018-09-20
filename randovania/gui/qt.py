import os
import sys
from argparse import ArgumentParser
from typing import Optional

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QAction

from randovania import VERSION
from randovania.gui.TabService import TabService
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.data_editor import DataEditorWindow
from randovania.gui.history_window import HistoryWindow
from randovania.gui.iso_management_window import ISOManagementWindow
from randovania.gui.layout_generator_window import LayoutGeneratorWindow
from randovania.gui.mainwindow_ui import Ui_MainWindow
from randovania.interface_common.options import Options
from randovania.interface_common.update_checker import get_latest_version


class MainWindow(QMainWindow, Ui_MainWindow, TabService, BackgroundTaskMixin):
    newer_version_signal = pyqtSignal(str, str)
    is_preview_mode: bool = False

    menu_new_version: Optional[QAction] = None
    _current_version_url: Optional[str] = None

    @property
    def _tab_widget(self):
        return self.tabWidget

    def __init__(self, preview: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Randovania {}".format(VERSION))
        self.is_preview_mode = preview
        self.setAcceptDrops(True)

        # Signals
        self.newer_version_signal.connect(self.display_new_version)
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.progress_update_signal.connect(self.update_progress)
        self.stop_background_process_button.clicked.connect(self.stop_background_process)

        _translate = QtCore.QCoreApplication.translate
        self.tabs = []

        self.tab_windows = [
            (LayoutGeneratorWindow, "Randomize"),
            (HistoryWindow, "Layout Details"),
            (DataEditorWindow, "Data Visualizer"),
            (ISOManagementWindow, "Advanced"),
        ]

        for i, tab in enumerate(self.tab_windows):
            self.windows.append(tab[0](self, self))
            self.tabs.append(self.windows[i].centralWidget)
            self.tabWidget.insertTab(i, self.tabs[i], _translate("MainWindow", tab[1]))

        self.tabWidget.setCurrentIndex(0)

        get_latest_version(self.newer_version_signal.emit)

    def closeEvent(self, event):
        self.stop_background_process()
        for window in self.windows:
            window.closeEvent(event)
        super().closeEvent(event)

    def dragEnterEvent(self, event):
        for url in event.mimeData().urls():
            if os.path.splitext(url.toLocalFile())[1] == ".iso":
                event.acceptProposedAction()
                return

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            iso_path = url.toLocalFile()
            if os.path.splitext(iso_path)[1] == ".iso":
                self.get_tab(LayoutGeneratorWindow).randomize_given_iso(iso_path)
                return

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

    # Background Process

    def enable_buttons_with_background_tasks(self, value: bool):
        self.stop_background_process_button.setEnabled(not value)

    def update_progress(self, message: str, percentage: int):
        self.progress_label.setText(message)
        if "Aborted" in message:
            percentage = 0
        if percentage >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percentage)
        else:
            self.progress_bar.setRange(0, 0)


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
