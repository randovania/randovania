import os
import shutil
from typing import Optional, Callable

from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QFileDialog

from randovania.games.prime import claris_randomizer
from randovania.games.prime.iso_packager import unpack_iso, pack_iso
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.common_qt_lib import application_options, persist_bool_option
from randovania.gui.iso_management_window_ui import Ui_ISOManagementWindow
from randovania.resolver.layout_description import LayoutDescription


def _translate(message, n=None):
    return QtCore.QCoreApplication.translate(
        "ManageGameWindow", message, n=n
    )


def _delete_files_location(game_files_path: str):
    if os.path.exists(game_files_path):
        shutil.rmtree(game_files_path)


class ISOManagementWindow(QMainWindow, Ui_ISOManagementWindow, BackgroundTaskMixin):
    current_files_location: str
    current_layout: Optional[LayoutDescription] = None
    _current_lock_state: bool = True

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
        self.apply_layout_button.clicked.connect(self.apply_layout_button_logic)
        self.show_advanced_options_check.setChecked(options.advanced_options)
        self.show_advanced_options_check.toggled.connect(self.set_advanced_options_visibility)

        # File Location
        self.filesLocation.setText(options.game_files_path)
        self.changeFilesLocationButton.clicked.connect(self.prompt_new_files_location)
        self.resetFilesLocationButton.clicked.connect(self.reset_files_location)
        self.deleteFilesButton.clicked.connect(self.delete_current_files_location)

        # Layout
        self.remove_hud_popup.setChecked(options.hud_memo_popup_removal)
        self.remove_hud_popup.stateChanged.connect(persist_bool_option("hud_memo_popup_removal"))

        # ISO Packing
        self.loadIsoButton.clicked.connect(self.load_iso)
        self.packageIsoButton.clicked.connect(self.package_iso)

        self._refresh_advanced_options_visibility()

    def enable_buttons_with_background_tasks(self, value: bool):
        self._current_lock_state = value
        self._refresh_apply_layout_button_state()
        self.stopBackgroundProcessButton.setEnabled(not value)
        self.loadIsoButton.setEnabled(value)
        self.packageIsoButton.setEnabled(value)

    def closeEvent(self, event):
        self.stop_background_process()
        super().closeEvent(event)

    # Advanced Options
    def set_advanced_options_visibility(self, new_value: bool):
        options = application_options()
        options.advanced_options = new_value
        options.save_to_disk()
        self._refresh_advanced_options_visibility()

    def _refresh_advanced_options_visibility(self):
        advanced_options = application_options().advanced_options
        self.files_box.setVisible(advanced_options)
        self.iso_box.setVisible(advanced_options)

    # Game Patching
    def load_layout(self, layout: Optional[LayoutDescription]):
        self.current_layout = layout
        if layout is not None:
            self.layout_identifier_label.setText(layout.configuration.as_str)
        else:
            self.layout_identifier_label.setText(self.layout_identifier_label.default_text)
        self._refresh_apply_layout_button_state()

    def _refresh_apply_layout_button_state(self):
        self.apply_layout_button.setEnabled(self._current_lock_state and self.current_layout is not None)

    def apply_layout_button_logic(self):
        if application_options().advanced_options:
            self.apply_layout()
        else:
            self.apply_layout_simplified()

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

    def apply_layout_simplified(self):
        if self.current_layout is None:
            raise Exception("Trying to apply layout, but current_layout is None")

        hud_memo_popup_removal = self.remove_hud_popup.isChecked()
        game_files_path = application_options().game_files_path

        open_result = QFileDialog.getOpenFileName(self, caption="Select the vanilla Game ISO.", filter="*.iso")
        if not open_result or open_result == ("", ""):
            return

        input_iso = open_result[0]

        open_result = QFileDialog.getSaveFileName(self, caption="Select where the randomized ISO location.",
                                                  filter="*.iso")
        if not open_result or open_result == ("", ""):
            return

        output_iso = open_result[0]

        def work(status_update: Callable[[str, int], None]):
            offset = 0
            middle_steps = 0

            def iso_update(message: str, status: int):
                status_update(message, int((status + offset) / 3))

            def wrap_update(args: str):
                nonlocal middle_steps
                middle_steps += 1
                status_update(args, int((100 + min(middle_steps, 100)) / 3))

            _delete_files_location(game_files_path)
            unpack_iso(
                iso=input_iso,
                game_files_path=game_files_path,
                progress_update=iso_update,
            )
            claris_randomizer.apply_layout(
                layout=self.current_layout,
                hud_memo_popup_removal=hud_memo_popup_removal,
                game_root=game_files_path,
                status_update=wrap_update
            )
            offset = 200
            pack_iso(
                iso=output_iso,
                game_files_path=game_files_path,
                disable_attract_if_necessary=True,
                progress_update=iso_update,
            )

        self.run_in_background_thread(work, "Randomizing ISO...")

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

    def delete_current_files_location(self):
        _delete_files_location(application_options().game_files_path)

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
                disable_attract_if_necessary=True,
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
