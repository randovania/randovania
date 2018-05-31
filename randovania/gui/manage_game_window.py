import multiprocessing
import os
import shutil
import threading
from typing import Optional, Callable

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox

from randovania.games.prime import binary_data
from randovania.games.prime.claris_randomizer import apply_seed
from randovania.games.prime.iso_packager import unpack_iso, pack_iso
from randovania.gui import application_options
from randovania.gui.manage_game_window_ui import Ui_ManageGameWindow
from randovania.interface_common.options import CpuUsage
from randovania.resolver.echoes import RandomizerConfiguration, search_seed_with_options


class AbortBackgroundTask(Exception):
    pass


def _translate(message, n=None):
    return QtCore.QCoreApplication.translate(
        "ManageGameWindow", message, n=n
    )


class ManageGameWindow(QMainWindow, Ui_ManageGameWindow):
    current_files_location: str
    _progressUpdateSignal = pyqtSignal(str, int)
    _backgroundTasksButtonLockSignal = pyqtSignal(bool)
    _background_thread: threading.Thread
    abort_background_task_requested: bool = False

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._background_thread = None
        self._backgroundTasksButtonLockSignal.connect(self.enable_buttons_with_background_tasks)

        # Progress
        self._progressUpdateSignal.connect(self.update_progress)
        self.stopBackgroundProcessButton.clicked.connect(self.stop_background_process)

        options = application_options()

        # File Location
        self.filesLocation.setText(options.game_files_path)
        self.changeFilesLocationButton.clicked.connect(self.prompt_new_files_location)
        self.resetFilesLocationButton.clicked.connect(self.reset_files_location)
        self.deleteFilesButton.clicked.connect(self.delete_files_location)

        # Seed Generation
        self.generateSeedButton.clicked.connect(self.generate_new_seed)

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
        self.stopBackgroundProcessButton.setEnabled(not value)
        self.loadIsoButton.setEnabled(value)
        self.packageIsoButton.setEnabled(value)

    def stop_background_process(self):
        self.abort_background_task_requested = True

    def run_in_background_thread(self,
                                 target,
                                 starting_message: str,
                                 kwargs=None):
        def status_update(message: str, progress: int):
            if self.abort_background_task_requested:
                self._progressUpdateSignal.emit("{} - Aborted".format(message), progress)
                raise AbortBackgroundTask()
            else:
                self._progressUpdateSignal.emit(message, progress)

        def thread(**_kwargs):
            try:
                target(status_update=status_update, **_kwargs)
            except AbortBackgroundTask:
                pass
            except RuntimeError as e:
                status_update("Error: {}".format(e), -1)
            finally:
                self._backgroundTasksButtonLockSignal.emit(True)
                self._background_thread = None

        if self._background_thread:
            raise RuntimeError("Trying to start a new background thread while one exists already.")
        self.abort_background_task_requested = False
        status_update(starting_message, 0)
        self._backgroundTasksButtonLockSignal.emit(False)
        self._background_thread = threading.Thread(target=thread, kwargs=kwargs)
        self._background_thread.start()

    def closeEvent(self, event):
        self.abort_background_task_requested = True
        super().closeEvent(event)

    # File Location
    def prompt_new_files_location(self):
        result = QFileDialog.getExistingDirectory(directory=application_options().game_files_path)
        if result:
            self.set_current_files_location(result)

    def set_current_files_location(self, new_files_location: Optional[str]):
        options = application_options()
        options.game_files_path = new_files_location
        options.save_to_disk()
        self.filesLocation.setText(options.game_files_path)

    def reset_files_location(self):
        self.set_current_files_location(None)

    def delete_files_location(self):
        game_files_path = application_options().game_files_path
        if os.path.exists(game_files_path):
            shutil.rmtree(game_files_path)

    # Seed Generation
    def generate_new_seed(self):
        options = application_options()

        def gui_seed_searcher(status_update: Callable[[str, int], None]):
            def seed_report(seed_count: int):
                status_update(_translate("Generating %n seed(s) so far...", n=seed_count),
                              -1)

            seed, final_seed_count = search_seed_with_options(data=binary_data.decode_default_prime2(),
                                                              options=options,
                                                              seed_report=seed_report)
            status_update(
                _translate("Seed '{}' found after %n seed(s).", n=final_seed_count).format(seed),
                100
            )
            self.currentSeedEdit.setText(str(seed))

        self.run_in_background_thread(
            gui_seed_searcher,
            _translate("Generating %n seed(s) so far...", n=0)
        )

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

        def gui_seed_searcher(status_update: Callable[[str, int], None]):
            def randomizer_update(message: str):
                if message == "Randomized!":
                    status_update(message, 100)
                else:
                    status_update(message, -1)

            apply_seed(randomizer_config=RandomizerConfiguration.from_options(options),
                       seed=int(self.currentSeedEdit.text()),
                       remove_item_loss=options.remove_item_loss,
                       hud_memo_popup_removal=options.hud_memo_popup_removal,
                       game_root=options.game_files_path,
                       status_update=randomizer_update)

        self.run_in_background_thread(
            gui_seed_searcher,
            _translate("Generating %n seed(s) so far...", n=0)
        )

    # ISO Packing
    def load_iso(self):
        open_result = QFileDialog.getOpenFileName(self, filter="*.iso")
        if not open_result or open_result == ("", ""):
            return

        iso, extension = open_result
        game_files_path = application_options().game_files_path

        def work(status_update):
            unpack_iso(
                iso=iso,
                game_files_path=game_files_path,
                progress_update=status_update,
            )

        self.run_in_background_thread(work, "Will unpack ISO")

    def package_iso(self):
        open_result = QFileDialog.getSaveFileName(self, filter="*.iso")
        if not open_result or open_result == ("", ""):
            return

        iso, extension = open_result
        game_files_path = application_options().game_files_path

        def work(status_update):
            pack_iso(
                iso=iso,
                game_files_path=game_files_path,
                progress_update=status_update,
            )

        self.run_in_background_thread(work, "Will pack ISO")

    def update_progress(self, message: str, percentage: int):
        self.progressLabel.setText(message)
        if percentage >= 0:
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(percentage)
        else:
            self.progressBar.setRange(0, 0)
