from typing import Optional

import multiprocessing

from PyQt5 import QtCore
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QFileDialog

from randovania.gui import application_options
from randovania.gui.manage_game_window_ui import Ui_ManageGameWindow
from randovania.interface_common.options import CpuUsage


class ManageGameWindow(QMainWindow, Ui_ManageGameWindow):
    current_files_location: str

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.loadIsoButton.clicked.connect(self.load_iso)
        self.packageIsoButton.clicked.connect(self.package_iso)
        self.progressBar.setHidden(True)

        options = application_options()

        # File Location
        self.filesLocation.setText(options.game_files_path)
        self.changeFilesLocationButton.clicked.connect(self.prompt_new_files_location)
        self.resetFilesLocationButton.clicked.connect(self.reset_files_location)

        # Seed Generation
        self.generateSeedButton.clicked.connect(self.generate_new_seed)
        self.abortGenerateButton.clicked.connect(self.abort_seed_generation)

        # CPU Usage
        self.options_by_cpu_usage = {
            CpuUsage.FULL: self.maxUsageRadio,
            CpuUsage.HIGH: self.highUsageRadio,
            CpuUsage.BALANCED: self.balancedUsageRadio,
            CpuUsage.MINIMAL: self.minialUsageRadio
        }
        self.options_by_cpu_usage[options.cpu_usage].setChecked(True)
        for usage_ratio in self.options_by_cpu_usage.values():
            usage_ratio.clicked.connect(self.on_cpu_usage_changed)
        self.enable_cpu_options_by_cpu_count()

        # Seed
        self.currentSeedEdit.setValidator(QIntValidator(0, 2147483647))
        self.applySeedButton.clicked.connect(self.apply_seed)

    def load_iso(self):
        QFileDialog.getOpenFileName(self, filter="*.iso")

    def package_iso(self):
        self.progressBar.setHidden(False)

    def prompt_new_files_location(self):
        result = QFileDialog.getExistingDirectory()
        if result:
            self.set_current_files_location(result)

    def set_current_files_location(self, new_files_location: Optional[str]):
        options = application_options()
        options.game_files_path = new_files_location
        options.save_to_disk()
        self.filesLocation.setText(options.game_files_path)

    def reset_files_location(self):
        self.set_current_files_location(None)

    def update_num_seeds(self, seed_count: int):
        self.generationStatusLabel.setText(QtCore.QCoreApplication.translate(
            "ManageGameWindow", "Generating %n seed(s) so far...", n=seed_count
        ))

    def generate_new_seed(self):
        self.generateSeedButton.setEnabled(False)
        self.abortGenerateButton.setEnabled(True)

    def abort_seed_generation(self):
        self.generateSeedButton.setEnabled(True)
        self.abortGenerateButton.setEnabled(False)

    # CPU Usage
    def enable_cpu_options_by_cpu_count(self):
        cpu_count = multiprocessing.cpu_count()
        previous_count = None

        usages = list(sorted(self.options_by_cpu_usage.keys()))
        for usage in usages:
            this_count = usage.num_cpu_for_count(cpu_count)
            self.options_by_cpu_usage[usage].setEnabled(this_count != previous_count)
            previous_count = this_count

    def on_cpu_usage_changed(self):
        cpu_usage = [
            usage
            for usage, ratio in self.options_by_cpu_usage.items()
            if ratio.isChecked()
        ][0]
        options = application_options()
        options.cpu_usage = cpu_usage
        options.save_to_disk()

    def apply_seed(self):
        pass
