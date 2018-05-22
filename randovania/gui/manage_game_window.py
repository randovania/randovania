import threading
from typing import Optional, BinaryIO

import multiprocessing

import os

import nod
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QApplication

from randovania import get_data_path
from randovania.games.prime import binary_data
from randovania.games.prime.claris_randomizer import apply_seed
from randovania.games.prime.iso_packager import unpack_iso
from randovania.gui import application_options, lock_application
from randovania.gui.manage_game_window_ui import Ui_ManageGameWindow
from randovania.interface_common.options import CpuUsage
from randovania.resolver.echoes import RandomizerConfiguration, ResolverConfiguration, search_seed


class AbortGeneration(Exception):
    pass


def _disc_extract_process(status_queue, input_file: str, output_directory: str):
    def progress_callback(path, progress):
        status_queue.put_nowait((False, int(progress * 100)))

    def _helper():
        result = nod.open_disc_from_image(input_file)
        if not result:
            return True, "Could not open file '{}'".format(input_file)

        disc, is_wii = result
        data_partition = disc.get_data_partition()
        if not data_partition:
            return True, "Could not find a data partition in '{}'.\nIs it a valid Metroid Prime 2 ISO?".format(
                input_file)

        context = nod.ExtractionContext()
        context.set_progress_callback(progress_callback)
        return True, data_partition.extract_to_directory(output_directory, context)

    status_queue.put_nowait(_helper())


class ManageGameWindow(QMainWindow, Ui_ManageGameWindow):
    current_files_location: str
    _progressBarUpdateSignal = pyqtSignal(int)
    _backgroundTasksButtonLockSignal = pyqtSignal(bool)
    _fullApplicationLockSignal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._background_thread = None
        self.abort_seed_generation_requested = None
        self._progressBarUpdateSignal.connect(self.progressBar.setValue)
        self._backgroundTasksButtonLockSignal.connect(self.enable_buttons_with_background_tasks)
        self._fullApplicationLockSignal.connect(lock_application)

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
        self.currentSeedEdit.textChanged.connect(self.on_new_seed)
        self.applySeedButton.setEnabled(False)
        self.applySeedButton.clicked.connect(self.apply_seed)

        # ISO Packing
        self.loadIsoButton.clicked.connect(self.load_iso)
        self.packageIsoButton.clicked.connect(self.package_iso)

    def enable_buttons_with_background_tasks(self, value: bool):
        self.generateSeedButton.setEnabled(value)
        self.loadIsoButton.setEnabled(value)
        self.packageIsoButton.setEnabled(value)

    # File Location
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

    # Seed Generation
    def update_num_seeds(self, seed_count: int):
        self.generationStatusLabel.setText(QtCore.QCoreApplication.translate(
            "ManageGameWindow", "Generating %n seed(s) so far...", n=seed_count
        ))

    def generate_new_seed(self):
        if self._background_thread:
            return

        self.enable_buttons_with_background_tasks(False)
        self.abortGenerateButton.setEnabled(True)
        self.abort_seed_generation_requested = None

        options = application_options()
        randomizer_config = RandomizerConfiguration.from_options(options)
        resolver_config = ResolverConfiguration.from_options(options)
        cpu_count = options.cpu_usage.num_cpu_for_count(multiprocessing.cpu_count())

        def seed_report(seed_count: int):
            self.update_num_seeds(seed_count)
            if self.abort_seed_generation_requested:
                raise AbortGeneration()

        def gui_seed_searcher():
            data = binary_data.decode_default_prime2()

            try:
                seed, seed_count = search_seed(data=data,
                                               randomizer_config=randomizer_config,
                                               resolver_config=resolver_config,
                                               cpu_count=cpu_count,
                                               seed_report=seed_report)

                self.generationStatusLabel.setText(QtCore.QCoreApplication.translate(
                    "ManageGameWindow", "Seed '{}' found after %n seed(s).", n=seed_count
                ).format(seed))
                self.currentSeedEdit.setText(str(seed))

            except AbortGeneration:
                self.generationStatusLabel.setText(QtCore.QCoreApplication.translate(
                    "ManageGameWindow", "Seed generation aborted."))

            self.enable_buttons_with_background_tasks(True)
            self.abortGenerateButton.setEnabled(False)

        self._background_thread = threading.Thread(target=gui_seed_searcher)
        seed_report(0)
        self._background_thread.start()

    def abort_seed_generation(self):
        self.abort_seed_generation_requested = True

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

    # Seed
    def on_new_seed(self, value):
        self.applySeedButton.setEnabled(bool(value))

    def apply_seed(self):
        options = application_options()
        try:
            apply_seed(RandomizerConfiguration.from_options(options),
                       int(self.currentSeedEdit.text()),
                       options.remove_item_loss, options.hud_memo_popup_removal, options.game_files_path)
        except Exception as e:
            QMessageBox.critical(self, "Randomizer Error", "Error calling Randomizer.exe:\n{}".format(e))

    # ISO Packing
    def load_iso(self):
        open_result = QFileDialog.getOpenFileName(self, filter="*.iso")
        if not open_result or open_result == ("", ""):
            return

        iso, extension = open_result
        game_files_path = application_options().game_files_path

        self._progressBarUpdateSignal.emit(0)
        self.run_in_background_thread(
            unpack_iso,
            kwargs={
                "iso": iso,
                "game_files_path": game_files_path,
                "progress_update": self._progressBarUpdateSignal.emit
            }
        )

    def package_iso(self):
        QMessageBox.warning(self, "Sorry", "Not yet implemented")

    def run_in_background_thread(self, target, args=(), kwargs=None):
        def thread(*_args, **_kwargs):
            try:
                target(*_args, **_kwargs)
            except RuntimeError as e:
                QMessageBox.warning(self, "File Error", str(e))
            self._fullApplicationLockSignal.emit(True)
            self._background_thread = None

        self._fullApplicationLockSignal.emit(False)
        self._background_thread = threading.Thread(target=thread, args=args, kwargs=kwargs)
        self._background_thread.start()
