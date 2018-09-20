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
from randovania.interface_common import status_update_lib
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.resolver.layout_description import LayoutDescription


def _translate(message, n=None):
    return QtCore.QCoreApplication.translate(
        "ManageGameWindow", message, n=n
    )


def _delete_files_location(game_files_path: str):
    if os.path.exists(game_files_path):
        shutil.rmtree(game_files_path)


class ISOManagementWindow(QMainWindow, Ui_ISOManagementWindow):
    current_files_location: str
    current_layout: Optional[LayoutDescription] = None
    _current_lock_state: bool = True

    def __init__(self, main_window, background_processor: BackgroundTaskMixin):
        super().__init__()
        self.setupUi(self)
        self.background_processor = background_processor

        options = application_options()

        # Progress
        background_processor.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)

        # Game Patching
        self.layout_identifier_label.default_text = self.layout_identifier_label.text()
        self.load_layout(None)
        self.apply_layout_button.clicked.connect(self.apply_layout_button_logic)
        self.show_advanced_options_check.setChecked(options.advanced_options)
        self.show_advanced_options_check.toggled.connect(self.set_advanced_options_visibility)
        self.show_advanced_options_check.setVisible(main_window.is_preview_mode)

        # File Location
        self.filesLocation.setText(options.game_files_path)
        self.changeFilesLocationButton.clicked.connect(self.prompt_new_files_location)
        self.resetFilesLocationButton.clicked.connect(self.reset_files_location)
        self.deleteFilesButton.clicked.connect(self.delete_current_files_location)

        # Layout
        self.remove_hud_popup_check.setChecked(options.hud_memo_popup_removal)
        self.remove_hud_popup_check.stateChanged.connect(persist_bool_option("hud_memo_popup_removal"))

        # ISO Packing
        self.loadIsoButton.clicked.connect(self.load_iso)
        self.packageIsoButton.clicked.connect(self.package_iso)

        self._refresh_advanced_options_visibility()

    def enable_buttons_with_background_tasks(self, value: bool):
        self._current_lock_state = value
        self._refresh_apply_layout_button_state()
        self.loadIsoButton.setEnabled(value)
        self.packageIsoButton.setEnabled(value)

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

        hud_memo_popup_removal = self.remove_hud_popup_check.isChecked()
        game_files_path = application_options().game_files_path

        def work(progress_update: ProgressUpdateCallable):
            def wrap_update(args: str):
                progress_update(args, 0)

            claris_randomizer.apply_layout(
                layout=self.current_layout,
                hud_memo_popup_removal=hud_memo_popup_removal,
                game_root=game_files_path,
                status_update=wrap_update
            )

        self.background_processor.run_in_background_thread(work, "Randomizing files...")

    def apply_layout_simplified(self):
        if self.current_layout is None:
            raise Exception("Trying to apply layout, but current_layout is None")

        hud_memo_popup_removal = self.remove_hud_popup_check.isChecked()
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

        def work(progress_update: ProgressUpdateCallable):
            updaters = status_update_lib.split_progress_update(
                progress_update,
                3
            )

            _delete_files_location(game_files_path)
            unpack_iso(
                iso=input_iso,
                game_files_path=game_files_path,
                progress_update=updaters[0],
            )
            claris_randomizer.apply_layout(
                layout=self.current_layout,
                hud_memo_popup_removal=hud_memo_popup_removal,
                game_root=game_files_path,
                status_update=status_update_lib.create_progress_update_from_successive_messages(
                    updaters[1], 100
                )
            )
            pack_iso(
                iso=output_iso,
                game_files_path=game_files_path,
                disable_attract_if_necessary=True,
                progress_update=updaters[2],
            )

        self.background_processor.run_in_background_thread(work, "Randomizing ISO...")

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

        def work(progress_update: ProgressUpdateCallable):
            unpack_iso(
                iso=iso,
                game_files_path=game_files_path,
                progress_update=progress_update,
            )

        self.background_processor.run_in_background_thread(work, "Will unpack ISO")

    def package_iso(self):
        open_result = QFileDialog.getSaveFileName(self, filter="*.iso")
        if not open_result or open_result == ("", ""):
            return

        iso, extension = open_result
        game_files_path = application_options().game_files_path

        def work(progress_update: ProgressUpdateCallable):
            pack_iso(
                iso=iso,
                game_files_path=game_files_path,
                disable_attract_if_necessary=True,
                progress_update=progress_update,
            )

        self.background_processor.run_in_background_thread(work, "Will pack ISO")
