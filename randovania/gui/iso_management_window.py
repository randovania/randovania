import random
from pathlib import Path
from typing import Optional, Iterator, Callable

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox

from randovania.games.prime.iso_packager import unpack_iso, pack_iso
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.common_qt_lib import application_options, persist_bool_option, prompt_user_for_input_iso, \
    prompt_user_for_seed_log
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

        # Randomize
        self.randomize_and_export_button.clicked.connect(self._randomize_and_export)
        self.randomize_log_only_button.clicked.connect(self._create_log_file_pressed)
        self.create_from_log_button.clicked.connect(self._randomize_from_file)

        # Game Patching
        self.create_spoiler_check.setChecked(options.create_spoiler)
        self.create_spoiler_check.stateChanged.connect(self._persist_option_then_notify("create_spoiler"))
        self.remove_hud_popup_check.setChecked(options.hud_memo_popup_removal)
        self.remove_hud_popup_check.stateChanged.connect(self._persist_option_then_notify("hud_memo_popup_removal"))
        self.include_menu_mod_check.setChecked(options.include_menu_mod)
        self.include_menu_mod_check.stateChanged.connect(self._persist_option_then_notify("include_menu_mod"))

        # Post setup update
        self.loaded_game_updated.emit()
        self._on_settings_changed()

    def enable_buttons_with_background_tasks(self, value: bool):
        self._current_lock_state = value
        self._refresh_game_buttons_state()
        self._refresh_randomize_button_state()

    def _persist_option_then_notify(self, attribute_name: str):
        persist = persist_bool_option(attribute_name)

        def wrap(value: int):
            persist(bool(value))
            self._on_settings_changed()

        return wrap

    def _on_settings_changed(self):
        self.permalink_edit.setText("LIES!")
        self._refresh_randomize_button_state()

    # Checks

    def _check_has_input_game(self):
        if not self._has_game:
            raise ValueError("No game available. Please load one using 'Load Game'")

    def _check_has_output_directory(self):
        if application_options().output_directory is None:
            raise ValueError("No output directory. Please select one using 'Select Folder'")

    def _ensure_seed_number_exists(self):
        if self.seed_number_edit.text() == "":
            self._generate_new_seed_number()

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

        with application_options() as options:
            if output_folder.is_dir():
                options.output_directory = output_folder
            else:
                options.output_directory = None

    def _change_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self)
        if not folder or folder == "":
            return

        self.output_folder_edit.setText(folder)

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

    def _on_new_seed_number(self):
        self._on_settings_changed()

    def _generate_new_seed_number(self):
        self.seed_number_edit.setText(str(random.randint(0, 2 ** 31)))

    def _import_permalink_from_field(self):
        permalink = self.permalink_edit.text()
        print(permalink)

    # Randomize
    def _refresh_randomize_button_state(self):
        self.randomize_and_export_button.setEnabled(self._current_lock_state)
        self.randomize_log_only_button.setEnabled(self._current_lock_state and application_options().create_spoiler)
        self.create_from_log_button.setEnabled(self._current_lock_state)

    def _try_generate_layout(self, job, progress_update: ProgressUpdateCallable):
        try:
            job(seed_number=self.get_current_seed_number(),
                progress_update=progress_update)
            progress_update("Success!", 1)

        except GenerationFailure as generate_exception:
            self.failed_to_generate_signal.emit(generate_exception)
            progress_update("Generation Failure: {}".format(generate_exception), -1)

    def _background_exporter(self, job,
                             message: str, **kawgs):
        def work(progress_update: ProgressUpdateCallable):
            try:
                job(progress_update=progress_update,
                    options=application_options(),
                    **kawgs)
                progress_update("Success!", 1)

            except GenerationFailure as generate_exception:
                self.failed_to_generate_signal.emit(generate_exception)
                progress_update("Generation Failure: {}".format(generate_exception), -1)

        self.background_processor.run_in_background_thread(work, message)

    def _pre_export_checks(self,
                           checks: Iterator[Callable[[], None]],
                           ) -> bool:
        try:
            for check in checks:
                check()
            return True

        except ValueError as e:
            QMessageBox.warning(self,
                                "Missing configuration",
                                str(e))
            return False

    def _randomize_and_export(self):
        """
        Listener to the "Randomize" button.
        """
        if not self._pre_export_checks([self._check_has_input_game,
                                        self._check_has_output_directory,
                                        self._ensure_seed_number_exists]):
            return

        self._background_exporter(
            simplified_patcher.create_layout_then_export_iso,
            message="Randomizing...",
            seed_number=self.get_current_seed_number(),
        )

    def _create_log_file_pressed(self):
        """
        Listener to the "Create only log file" button.
        """
        if not self._pre_export_checks([self._check_has_output_directory,
                                        self._ensure_seed_number_exists]):
            return

        self._background_exporter(
            simplified_patcher.create_layout_then_export,
            message="Creating a layout...",
            seed_number=self.get_current_seed_number(),
        )

    def _randomize_from_file(self):
        if not self._pre_export_checks([self._check_has_output_directory]):
            return

        json_path = prompt_user_for_seed_log(self)
        if json_path is None:
            return

        layout = LayoutDescription.from_file(json_path)

        self._background_exporter(
            simplified_patcher.patch_game_with_existing_layout,
            message="Randomizing...",
            layout=layout
        )
