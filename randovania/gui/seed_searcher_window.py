import multiprocessing
from typing import Dict, Iterator, Callable

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow

from randovania.games.prime import binary_data
from randovania.games.prime.claris_randomizer import apply_seed
from randovania.gui.common_qt_lib import application_options
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.seed_searcher_window_ui import Ui_SeedSearcherWindow
from randovania.interface_common.options import CpuUsage
from randovania.resolver.data_reader import read_resource_database
from randovania.resolver.echoes import search_seed_with_options, RandomizerConfiguration
from randovania.resolver.resources import PickupEntry


def _map_set_checked(iterable: Iterator[QtWidgets.QCheckBox], new_status: bool):
    for checkbox in iterable:
        checkbox.setChecked(new_status)


def _translate(message, n=None):
    return QtCore.QCoreApplication.translate(
        "SeedSearcherWindow", message, n=n
    )


class SeedSearcherWindow(QMainWindow, Ui_SeedSearcherWindow, BackgroundTaskMixin):
    _on_bulk_change: bool = False

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Background Processing
        self.progress_update_signal.connect(self.update_progress)
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.stopBackgroundProcessButton.clicked.connect(self.stop_background_process)

        data = binary_data.decode_default_prime2()
        self.resource_database = read_resource_database(data["resource_database"])

        options = application_options()

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

        # Layout
        self.generateSeedButton.clicked.connect(self.generate_new_seed)
        self.currentSeedEdit.setValidator(QIntValidator(0, 2147483647))
        self.currentSeedEdit.textChanged.connect(self.on_new_seed)
        self.applySeedButton.setEnabled(False)
        self.applySeedButton.clicked.connect(self.apply_seed)

        # Exclusion Selection
        self.exclusion_indices = {
            entry: i
            for i, entry in enumerate(self.resource_database.pickups)
        }
        self.exclude_checkboxes: Dict[PickupEntry, QtWidgets.QCheckBox] = {}
        self.create_exclusion_checkboxes()
        self.clearExcludedPickups.clicked.connect(self.unselect_all_exclusions)
        self.filterPickupsEdit.textChanged.connect(self.update_exclusion_filter)

    # Background Processing
    def closeEvent(self, event):
        self.stop_background_process()
        super().closeEvent(event)

    def enable_buttons_with_background_tasks(self, value: bool):
        self.generateSeedButton.setEnabled(value)
        self.stopBackgroundProcessButton.setEnabled(not value)

    def update_progress(self, message: str, percentage: int):
        self.statusLabel.setText(message)

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

    # Exclusion Selection
    def create_exclusion_checkboxes(self):
        excluded_pickups = application_options().excluded_pickups
        self.excludedItemsContentLayout.setAlignment(Qt.AlignTop)

        for entry in self.resource_database.pickups:
            checkbox = QtWidgets.QCheckBox(self.excludedItemsContents)
            checkbox.setCheckable(True)
            checkbox.setChecked(self.exclusion_indices[entry] in excluded_pickups)
            self.excludedItemsContentLayout.addWidget(checkbox)

            checkbox.setText("{} - {} - {}".format(
                QtCore.QCoreApplication.translate("EchoesDatabase", entry.world, "world"),
                QtCore.QCoreApplication.translate("EchoesDatabase", entry.room, "room"),
                QtCore.QCoreApplication.translate("EchoesDatabase", entry.item, "item")
            ))
            checkbox.stateChanged.connect(self.on_exclusion_list_changed)
            self.exclude_checkboxes[entry] = checkbox

    def on_exclusion_list_changed(self):
        if self._on_bulk_change:
            return

        options = application_options()
        options.excluded_pickups = {
            self.exclusion_indices[entry]
            for entry, checkbox in self.exclude_checkboxes.items()
            if checkbox.isChecked()
        }
        options.save_to_disk()

    def unselect_all_exclusions(self):
        self._on_bulk_change = True
        _map_set_checked(self.exclude_checkboxes.values(), False)
        self._on_bulk_change = False
        self.on_exclusion_list_changed()

    def update_exclusion_filter(self, value: str):
        for checkbox in self.exclude_checkboxes.values():
            if value:
                checkbox.setHidden(value.lower() not in checkbox.text().lower())
            else:
                checkbox.setHidden(False)
