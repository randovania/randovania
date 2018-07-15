import os
import shutil
from typing import Optional, Callable

from PyQt5 import QtCore
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QFileDialog

from randovania.games.prime import claris_randomizer
from randovania.games.prime.iso_packager import unpack_iso, pack_iso
from randovania.gui.common_qt_lib import application_options, persist_bool_option
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.iso_management_window_ui import Ui_ISOManagementWindow
from randovania.resolver.echoes import RandomizerConfiguration
from randovania.resolver.layout_description import LayoutDescription


def _translate(message, n=None):
    return QtCore.QCoreApplication.translate(
        "ManageGameWindow", message, n=n
    )


class ISOManagementWindow(QMainWindow, Ui_ISOManagementWindow, BackgroundTaskMixin):
    current_files_location: str
    current_layout: Optional[LayoutDescription] = None

    def __init__(self, main_window):
        super().__init__()
        self.setupUi(self)
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)

        # Progress
        self.progress_update_signal.connect(self.update_progress)
        self.stopBackgroundProcessButton.clicked.connect(self.stop_background_process)

        options = application_options()

        # Game Patching
        self.layout_identifier_label.default_text = self.layout_identifier_label.text()
        self.load_layout(None)
        self.apply_layout_button.clicked.connect(self.apply_layout)
        self.current_seed_edit.setValidator(QIntValidator(0, 2147483647))
        self.current_seed_edit.textChanged.connect(self.on_seed_changed)
        self.apply_seed_button.clicked.connect(self.apply_seed)
        self.apply_seed_button.setEnabled(False)
        self.current_seed_edit.hide()
        self.apply_seed_button.hide()

        # File Location
        self.filesLocation.setText(options.game_files_path)
        self.changeFilesLocationButton.clicked.connect(self.prompt_new_files_location)
        self.resetFilesLocationButton.clicked.connect(self.reset_files_location)
        self.deleteFilesButton.clicked.connect(self.delete_files_location)

        # Layout
        self.remove_hud_popup.setChecked(options.hud_memo_popup_removal)
        self.remove_hud_popup.stateChanged.connect(persist_bool_option("hud_memo_popup_removal"))

        # ISO Packing
        self.loadIsoButton.clicked.connect(self.load_iso)
        self.packageIsoButton.clicked.connect(self.package_iso)

    def enable_buttons_with_background_tasks(self, value: bool):
        self.apply_layout_button.setEnabled(value)
        self.stopBackgroundProcessButton.setEnabled(not value)
        self.loadIsoButton.setEnabled(value)
        self.packageIsoButton.setEnabled(value)

    def closeEvent(self, event):
        self.stop_background_process()
        super().closeEvent(event)

    # Game Patching
    def load_layout(self, layout: Optional[LayoutDescription]):
        self.current_layout = layout
        if layout is not None:
            self.layout_identifier_label.setText(layout.configuration.as_str)
        else:
            self.layout_identifier_label.setText(self.layout_identifier_label.default_text)
        self.apply_layout_button.setEnabled(layout is not None)

    def apply_layout(self):
        if self.current_layout is None:
            raise Exception("Trying to apply layout, but current_layout is None")

        hud_memo_popup_removal = self.remove_hud_popup.isChecked()
        game_files_path = application_options().game_files_path

        def work(status_update: Callable[[str, int], None]):
            def wrap_update(args: str):
                status_update(args, 0)

            claris_randomizer.apply_layout(
                layout=self.current_layout,
                hud_memo_popup_removal=hud_memo_popup_removal,
                game_root=game_files_path,
                status_update=wrap_update
            )

        self.run_in_background_thread(work, "Randomizing files...")

    def on_seed_changed(self, value):
        self.apply_seed_button.setEnabled(value != "")

    def load_seed(self, value: int):
        self.current_seed_edit.setText(str(value))

    def apply_seed(self):
        seed_number = int(self.current_seed_edit.text())

        hud_memo_popup_removal = self.remove_hud_popup.isChecked()

        options = application_options()
        configuration = RandomizerConfiguration.from_options(options)
        game_files_path = options.game_files_path
        remove_item_loss = options.remove_item_loss

        def work(status_update: Callable[[str, int], None]):
            def wrap_update(args: str):
                status_update(args, 0)

            claris_randomizer.apply_seed(
                randomizer_config=configuration,
                seed=seed_number,
                remove_item_loss=remove_item_loss,
                hud_memo_popup_removal=hud_memo_popup_removal,
                game_root=game_files_path,
                status_update=wrap_update
            )

        self.run_in_background_thread(work, "Randomizing files...")

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
