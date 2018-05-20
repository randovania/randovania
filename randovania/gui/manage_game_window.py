import os

import appdirs
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QFileDialog

from randovania.gui.manage_game_window_ui import Ui_ManageGameWindow


class ManageGameWindow(QMainWindow, Ui_ManageGameWindow):
    current_files_location: str

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.loadIsoButton.clicked.connect(self.load_iso)
        self.packageIsoButton.clicked.connect(self.package_iso)
        self.progressBar.setHidden(True)

        self.reset_files_location()
        self.changeFilesLocationButton.clicked.connect(self.prompt_new_files_location)
        self.resetFilesLocationButton.clicked.connect(self.reset_files_location)

        self.currentSeedEdit.setValidator(QIntValidator(0, 2147483647))

    def load_iso(self):
        QFileDialog.getOpenFileName(self, filter="*.iso")

    def package_iso(self):
        self.progressBar.setHidden(False)

    def prompt_new_files_location(self):
        result = QFileDialog.getExistingDirectory()
        if result:
            self.set_current_files_location(result)

    def set_current_files_location(self, new_files_location: str):
        self.current_files_location = new_files_location
        self.filesLocation.setText(self.current_files_location)

    def reset_files_location(self):
        self.set_current_files_location(self._default_files_location())

    def _default_files_location(self):
        return os.path.join(appdirs.user_data_dir("Randovania", False), "extracted_game")
