import functools
import random
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox

from randovania.games.prime.iso_packager import unpack_iso, pack_iso
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.common_qt_lib import application_options, persist_bool_option, prompt_user_for_input_iso, \
    prompt_user_for_seed_log
from randovania.gui.history_window import HistoryWindow
from randovania.gui.iso_management_window_ui import Ui_ISOManagementWindow
from randovania.gui.tab_service import TabService
from randovania.interface_common import simplified_patcher, game_workdir
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.resolver.exceptions import GenerationFailure
from randovania.resolver.layout_description import LayoutDescription


def show_failed_generation_exception(exception: GenerationFailure):
    QMessageBox.critical(None,
                         "An error occurred while generating a seed",
                         "{}\n\nSome errors are expected to occur, please try again.".format(exception))


class ISOManagementWindow(QMainWindow, Ui_ISOManagementWindow):
    tab_service: TabService
    _has_game: bool
    _current_lock_state: bool = True
    _last_generated_layout: Optional[LayoutDescription] = None

    loaded_game_updated = pyqtSignal()
    layout_generated_signal = pyqtSignal(LayoutDescription)
    failed_to_generate_signal = pyqtSignal(GenerationFailure)

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin):
        super().__init__()
        self.setupUi(self)
        self.tab_service = tab_service
        self.background_processor = background_processor

        options = application_options()
        output_directory = options.output_directory

        # Progress
        background_processor.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.layout_generated_signal.connect(self._on_layout_generated)
        self.failed_to_generate_signal.connect(show_failed_generation_exception)

        # ISO Packing
        self.loaded_game_updated.connect(self._update_displayed_game)
        self.load_game_button.clicked.connect(self.load_game)
        self.export_game_button.hide()
        self.export_game_button.clicked.connect(self.export_game)
        self.clear_game_button.clicked.connect(self.delete_loaded_game)
        self.output_folder_edit.setText(str(output_directory) if output_directory is not None else "")
        self.output_folder_edit.textChanged.connect(self._on_new_output_directory)
        self.output_folder_button.clicked.connect(self._change_output_folder)

        # Seed/Permalink
        self.seed_number_edit.setValidator(QIntValidator(0, 2 ** 31 - 1))
        self.seed_number_edit.textChanged.connect(self._on_new_seed_number)
        self.seed_number_button.clicked.connect(self._generate_new_seed_number)

        self.permalink_import_button.clicked.connect(self._import_permalink_from_field)
        self.permalink_import_log_button.clicked.connect(self._create_permalink_from_file)

        # Randomize
        self.randomize_and_export_button.clicked.connect(self._randomize_and_export)
        self.create_log_button.clicked.connect(self._create_log_file_pressed)
        self.patch_game_button.hide()

        # Game Patching
        self.create_spoiler_check.setChecked(True)  # TODO
        self.remove_hud_popup_check.stateChanged.connect(persist_bool_option("include_spoiler"))
        self.remove_hud_popup_check.setChecked(options.hud_memo_popup_removal)
        self.remove_hud_popup_check.stateChanged.connect(persist_bool_option("hud_memo_popup_removal"))
        self.include_menu_mod_check.setChecked(options.include_menu_mod)
        self.include_menu_mod_check.stateChanged.connect(persist_bool_option("include_menu_mod"))

        # Post setup update
        self.loaded_game_updated.emit()

    def enable_buttons_with_background_tasks(self, value: bool):
        self._current_lock_state = value
        self._refresh_game_buttons_state()
        self.randomize_and_export_button.setEnabled(value)
        self.create_log_button.setEnabled(value)

    # ISO Packing
    def load_game(self):
        iso = prompt_user_for_input_iso(self)
        if iso is None:
            return

        game_files_path = application_options().game_files_path

        def work(progress_update: ProgressUpdateCallable):
            unpack_iso(
                iso=iso,
                game_files_path=game_files_path,
                progress_update=progress_update,
            )
            self.loaded_game_updated.emit()

        self.background_processor.run_in_background_thread(work, "Will unpack ISO")

    def delete_loaded_game(self):
        self.loaded_game_updated.emit()

    def export_game(self):
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

    def _on_new_output_directory(self, output_folder: str):
        output_folder = Path(output_folder)

        options = application_options()
        if output_folder.is_dir():
            options.output_directory = output_folder
        else:
            options.output_directory = None
        options.save_to_disk()

    def _change_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self)
        if not folder or folder == "":
            return

        self.output_folder_edit.setText(folder)

    def _check_input_output_configured(self):
        if not self._has_game:
            raise ValueError("No game available. Please load one using 'Load Game'")

        if application_options().output_directory is None:
            raise ValueError("No output directory. Please select one using 'Select Folder'")

    def _update_displayed_game(self):
        result = game_workdir.discover_game(application_options().game_files_path)

        if result is None:
            self._has_game = False
            self.loaded_game_label.setText("No Game Loaded")
        else:
            game_id, game_name = result
            self._has_game = True
            self.loaded_game_label.setText("{}: {}".format(game_id, game_name))

        self._refresh_game_buttons_state()

    def _refresh_game_buttons_state(self):
        """
        Relevant after loading a new game or when changing background task lock.
        """
        self.load_game_button.setEnabled(self._current_lock_state)
        self.export_game_button.setEnabled(self._current_lock_state and self._has_game)
        self.clear_game_button.setEnabled(self._current_lock_state and self._has_game)

    # Seed Number / Permalink
    def get_current_seed_number(self) -> int:
        seed = self.seed_number_edit.text()
        if seed == "":
            raise RuntimeError("Invalid seed number. Did you forget to call _ensure_seed_number_exists?")
        else:
            return int(seed)

    def _ensure_seed_number_exists(self):
        if self.seed_number_edit.text() == "":
            self._generate_new_seed_number()

    def _on_new_seed_number(self):
        self._update_permalink()

    def _generate_new_seed_number(self):
        self.seed_number_edit.setText(str(random.randint(0, 2 ** 31)))

    def _update_permalink(self):
        self.permalink_edit.setText("LIES!")

    def _import_permalink_from_field(self):
        permalink = self.permalink_edit.text()
        print(permalink)

    def _create_permalink_from_file(self):
        json_path = prompt_user_for_seed_log(self)
        if json_path is None:
            return
        print(json_path)

    # Randomize
    def _try_generate_layout(self, job, progress_update: ProgressUpdateCallable):
        try:
            resulting_layout = job(
                seed_number=self.get_current_seed_number(),
                progress_update=progress_update)
            self.layout_generated_signal.emit(resulting_layout)
            progress_update("Success!", 1)

        except GenerationFailure as generate_exception:
            self.failed_to_generate_signal.emit(generate_exception)
            progress_update("Generation Failure: {}".format(generate_exception), -1)

    def randomize_loaded_game(self):
        self.background_processor.run_in_background_thread(
            functools.partial(
                self._try_generate_layout,
                job=simplified_patcher.create_layout_then_export_iso
            ),
            "Randomizing...")

    def create_new_layout(self):
        self.background_processor.run_in_background_thread(
            functools.partial(
                self._try_generate_layout,
                job=simplified_patcher.generate_layout
            ),
            "Creating a layout...")

    def _randomize_and_export(self):
        """
        Listener to the "Randomize" button.
        """
        try:
            self._check_input_output_configured()
        except ValueError as e:
            QMessageBox.warning(self,
                                "Missing configuration",
                                str(e))
            return

        self._ensure_seed_number_exists()
        self.randomize_loaded_game()

    def _create_log_file_pressed(self):
        """
        Listener to the "Create only log file" button.
        """
        self._ensure_seed_number_exists()
        self.create_new_layout()

    # Layout Details
    def _on_layout_generated(self, layout: LayoutDescription):
        self._last_generated_layout = layout
        self.tab_service.get_tab(HistoryWindow).add_new_layout_to_history(layout)
        # self.view_details_button.setEnabled(True)

    def _view_layout_details(self):
        if self._last_generated_layout is None:
            raise RuntimeError("_view_layout_details should never be called without a _last_generated_layout")

        window: HistoryWindow = self.tab_service.get_tab(HistoryWindow)
        window.change_selected_layout(self._last_generated_layout)
        self.tab_service.focus_tab(window)
