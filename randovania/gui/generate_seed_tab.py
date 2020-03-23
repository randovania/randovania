import datetime
import json
import random
from functools import partial
from pathlib import Path
from typing import Optional

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QDialog, QMessageBox, QWidget, QMenu, QAction

from randovania.gui.dialog.logic_settings_window import LogicSettingsWindow
from randovania.gui.generated.main_window_ui import Ui_MainWindow
from randovania.gui.lib import preset_describer, common_qt_lib
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options
from randovania.interface_common.preset_editor import PresetEditor
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink
from randovania.layout.preset import Preset, save_preset_file, read_preset_file
from randovania.resolver.exceptions import GenerationFailure


def persist_layout(data_dir: Path, description: LayoutDescription):
    history_dir = data_dir.joinpath("game_history")
    history_dir.mkdir(parents=True, exist_ok=True)

    date_format = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    file_path = history_dir.joinpath(
        f"{date_format}-{description.permalink.preset.slug_name}.{description.file_extension()}")
    description.save_to_file(file_path)


class GenerateSeedTab(QWidget):
    _current_lock_state: bool = True
    _logic_settings_window = None
    _current_preset: Preset = None
    _tool_button_menu: QMenu
    _action_delete: QAction

    failed_to_generate_signal = Signal(GenerationFailure)

    def __init__(self, background_processor: BackgroundTaskMixin, window: Ui_MainWindow,
                 window_manager: WindowManager, options: Options):
        super().__init__()

        self.background_processor = background_processor
        self.window = window
        self._window_manager = window_manager
        self._options = options

        self.failed_to_generate_signal.connect(self._show_failed_generation_exception)

    def setup_ui(self):
        window = self.window

        # Progress
        self.background_processor.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)

        for preset in self._window_manager.preset_manager.all_presets:
            self._create_button_for_preset(preset)

        # Menu
        self._tool_button_menu = QMenu(window.preset_tool_button)
        window.preset_tool_button.setMenu(self._tool_button_menu)

        self._action_delete = QAction(window)
        self._action_delete.setText("Delete")
        self._tool_button_menu.addAction(self._action_delete)

        action_export_preset = QAction(window)
        action_export_preset.setText("Export")
        self._tool_button_menu.addAction(action_export_preset)

        action_import_preset = QAction(window)
        action_import_preset.setText("Import")
        self._tool_button_menu.addAction(action_import_preset)

        # Signals
        window.create_customize_button.clicked.connect(self._on_customize_button)
        window.create_preset_combo.activated.connect(self._on_select_preset)
        window.create_generate_button.clicked.connect(partial(self._generate_new_seed, True))
        window.create_generate_race_button.clicked.connect(partial(self._generate_new_seed, False))

        self._action_delete.triggered.connect(self._on_delete_preset)
        action_export_preset.triggered.connect(self._on_export_preset)
        action_import_preset.triggered.connect(self._on_import_preset)

    def _show_failed_generation_exception(self, exception: GenerationFailure):
        QMessageBox.critical(self._window_manager,
                             "An error occurred while generating a seed",
                             "{}\n\nSome errors are expected to occur, please try again.".format(exception))

    @property
    def _current_preset_data(self) -> Optional[Preset]:
        return self._window_manager.preset_manager.preset_for_name(self.window.create_preset_combo.currentData())

    def enable_buttons_with_background_tasks(self, value: bool):
        self._current_lock_state = value
        self.window.welcome_tab.setEnabled(value)

    def _create_button_for_preset(self, preset: Preset):
        create_preset_combo = self.window.create_preset_combo
        create_preset_combo.addItem(preset.name, preset.name)

    def _add_new_preset(self, preset: Preset):
        with self._options as options:
            options.selected_preset_name = preset.name

        if self._window_manager.preset_manager.add_new_preset(preset):
            self._create_button_for_preset(preset)
        self.on_preset_changed(preset)

    def _on_customize_button(self):
        editor = PresetEditor(self._current_preset_data)
        self._logic_settings_window = LogicSettingsWindow(self._window_manager, editor)

        self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())
        editor.on_changed = lambda: self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())

        result = self._logic_settings_window.exec_()
        self._logic_settings_window = None

        if result == QDialog.Accepted:
            self._add_new_preset(editor.create_custom_preset_with())

    def _on_delete_preset(self):
        self._window_manager.preset_manager.delete_preset(self._current_preset_data)
        self.window.create_preset_combo.removeItem(self.window.create_preset_combo.currentIndex())
        self._on_select_preset()

    def _on_export_preset(self):
        path = common_qt_lib.prompt_user_for_preset_file(self._window_manager, new_file=True)
        if path is not None:
            save_preset_file(self._current_preset_data, path)

    def _on_import_preset(self):
        path = common_qt_lib.prompt_user_for_preset_file(self._window_manager, new_file=False)
        if path is None:
            return

        try:
            preset = read_preset_file(path)
        except (ValueError, KeyError):
            QMessageBox.critical(
                self._window_manager,
                "Error loading preset",
                "The file at '{}' contains an invalid preset.".format(path)
            )
            return

        if self._window_manager.preset_manager.preset_for_name(preset.name) is not None:
            user_response = QMessageBox.warning(
                self._window_manager,
                "Preset name conflict",
                "A preset named '{}' already exists. Do you want to overwrite it?".format(preset.name),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if user_response == QMessageBox.No:
                return

        self._add_new_preset(preset)

    def _on_select_preset(self):
        preset_data = self._current_preset_data
        self.on_preset_changed(preset_data)
        with self._options as options:
            options.selected_preset_name = preset_data.name

    # Generate seed

    def _generate_new_seed(self, spoiler: bool):
        self.generate_seed_from_permalink(Permalink(
            seed_number=random.randint(0, 2 ** 31),
            spoiler=spoiler,
            preset=self._current_preset_data,
        ))

    def generate_seed_from_permalink(self, permalink: Permalink):
        def work(progress_update: ProgressUpdateCallable):
            try:
                layout = simplified_patcher.generate_layout(progress_update=progress_update,
                                                            permalink=permalink,
                                                            options=self._options)
                progress_update(f"Success! (Seed hash: {layout.shareable_hash})", 1)
                persist_layout(self._options.data_dir, layout)
                self._window_manager.show_seed_tab(layout)

            except GenerationFailure as generate_exception:
                self.failed_to_generate_signal.emit(generate_exception)
                progress_update("Generation Failure: {}".format(generate_exception), -1)

        self.background_processor.run_in_background_thread(work, "Creating a seed...")

    def on_options_changed(self, options: Options):
        if self._current_preset is None:
            preset_name = options.selected_preset_name
            if preset_name is not None:
                index = self.window.create_preset_combo.findText(preset_name)
                if index != -1:
                    self.window.create_preset_combo.setCurrentIndex(index)
                    self.on_preset_changed(self._current_preset_data)
                    return

            self.window.create_preset_combo.setCurrentIndex(0)
            self.on_preset_changed(self._window_manager.preset_manager.default_preset)

    def on_preset_changed(self, preset: Preset):
        self._current_preset = preset

        self.window.create_preset_description.setText(preset.description)
        self._action_delete.setEnabled(preset.base_preset_name is not None)

        create_preset_combo = self.window.create_preset_combo
        create_preset_combo.setCurrentIndex(create_preset_combo.findText(preset.name))

        categories = list(preset_describer.describe(preset))
        left_categories = categories[::2]
        right_categories = categories[1::2]

        self.window.create_describe_left_label.setText(preset_describer.merge_categories(left_categories))
        self.window.create_describe_right_label.setText(preset_describer.merge_categories(right_categories))
