import datetime
import logging
import random
from functools import partial
from pathlib import Path
from typing import Optional

from PySide2.QtWidgets import QDialog, QMessageBox, QWidget, QMenu, QAction
from asyncqt import asyncSlot

from randovania.games.game import RandovaniaGame
from randovania.gui.generated.main_window_ui import Ui_MainWindow
from randovania.gui.lib import preset_describer, common_qt_lib, async_dialog
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.generation_failure_handling import GenerationFailureHandler
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.logic_settings_window import LogicSettingsWindow
from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options
from randovania.interface_common.preset_editor import PresetEditor
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink
from randovania.layout.preset import Preset
from randovania.layout.preset_migration import VersionedPreset, InvalidPreset
from randovania.resolver.exceptions import GenerationFailure


def persist_layout(data_dir: Path, description: LayoutDescription):
    history_dir = data_dir.joinpath("game_history")
    history_dir.mkdir(parents=True, exist_ok=True)

    date_format = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    file_path = history_dir.joinpath(
        f"{date_format}-{description.shareable_word_hash}.{description.file_extension()}")
    description.save_to_file(file_path)


class GenerateSeedTab(QWidget, BackgroundTaskMixin):
    _logic_settings_window: Optional[LogicSettingsWindow] = None
    _has_preset: bool = False
    _tool_button_menu: QMenu
    _action_delete: QAction

    def __init__(self, window: Ui_MainWindow, window_manager: WindowManager, options: Options):
        super().__init__()

        self.window = window
        self._window_manager = window_manager
        self.failure_handler = GenerationFailureHandler(self)
        self._options = options

    def setup_ui(self):
        window = self.window

        # Progress
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.progress_update_signal.connect(self.update_progress)
        self.window.stop_background_process_button.clicked.connect(self.stop_background_process)

        for game in RandovaniaGame:
            self.window.create_choose_game_combo.addItem(game.long_name, game)

        self.window.create_choose_game_combo.setVisible(self._window_manager.is_preview_mode)
        self.window.create_choose_game_label.setVisible(self._window_manager.is_preview_mode)
        self.window.num_players_spin_box.setVisible(self._window_manager.is_preview_mode)

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
        window.create_choose_game_combo.activated.connect(self._on_select_game)
        window.preset_tool_button.clicked.connect(self._on_customize_button)
        window.create_preset_combo.activated.connect(self._on_select_preset)
        window.create_generate_button.clicked.connect(partial(self._generate_new_seed, True))
        window.create_generate_race_button.clicked.connect(partial(self._generate_new_seed, False))

        self._action_delete.triggered.connect(self._on_delete_preset)
        action_export_preset.triggered.connect(self._on_export_preset)
        action_import_preset.triggered.connect(self._on_import_preset)

    @property
    def _current_preset_data(self) -> Optional[VersionedPreset]:
        return self._window_manager.preset_manager.preset_for_name(self.window.create_preset_combo.currentData())

    def enable_buttons_with_background_tasks(self, value: bool):
        self.window.stop_background_process_button.setEnabled(not value)
        self.window.create_generate_button.setEnabled(value)
        self.window.create_generate_race_button.setEnabled(value)

    def _create_button_for_preset(self, preset: VersionedPreset):
        create_preset_combo = self.window.create_preset_combo
        create_preset_combo.addItem(preset.name, preset.name)

    def _add_new_preset(self, preset: VersionedPreset):
        with self._options as options:
            options.selected_preset_name = preset.name

        if self._window_manager.preset_manager.add_new_preset(preset):
            self._create_button_for_preset(preset)
        self.on_preset_changed(preset.get_preset())

    @asyncSlot()
    async def _on_customize_button(self):
        if self._logic_settings_window is not None:
            self._logic_settings_window.raise_()
            return

        editor = PresetEditor(self._current_preset_data.get_preset())
        self._logic_settings_window = LogicSettingsWindow(self._window_manager, editor)

        self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())
        editor.on_changed = lambda: self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())

        result = await async_dialog.execute_dialog(self._logic_settings_window)
        self._logic_settings_window = None

        if result == QDialog.Accepted:
            self._add_new_preset(VersionedPreset.with_preset(editor.create_custom_preset_with()))

    def _on_delete_preset(self):
        self._window_manager.preset_manager.delete_preset(self._current_preset_data)
        self.window.create_preset_combo.removeItem(self.window.create_preset_combo.currentIndex())
        self._on_select_preset()

    def _on_export_preset(self):
        path = common_qt_lib.prompt_user_for_preset_file(self._window_manager, new_file=True)
        if path is not None:
            self._current_preset_data.save_to_file(path)

    def _on_import_preset(self):
        path = common_qt_lib.prompt_user_for_preset_file(self._window_manager, new_file=False)
        if path is not None:
            self.import_preset_file(path)

    def import_preset_file(self, path: Path):
        preset = VersionedPreset.from_file_sync(path)
        try:
            preset.get_preset()
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

    def select_game(self, game: RandovaniaGame):
        combo_index = self.window.create_choose_game_combo.findData(game)
        self.window.create_choose_game_combo.setCurrentIndex(combo_index)
        self._update_create_preset_combo(game)

    def _on_select_game(self):
        game = self.window.create_choose_game_combo.currentData()
        self._update_create_preset_combo(game)
        self._on_select_preset()

    def _update_create_preset_combo(self, game: RandovaniaGame):
        self.window.create_preset_combo.clear()
        for preset in self._window_manager.preset_manager.all_presets:
            if preset.game == game:
                self._create_button_for_preset(preset)

    def _on_select_preset(self):
        preset_data = self._current_preset_data
        try:
            self.on_preset_changed(preset_data.get_preset())
        except InvalidPreset as e:
            logging.exception(f"Invalid preset for {preset_data.name}")
            QMessageBox.warning(
                self._window_manager,
                "Incompatible Preset",
                f"Preset {preset_data.name} can't be used as it contains the following error:\n{e.original_exception}"
            )
            self.window.create_preset_combo.setCurrentIndex(0)
            self.on_preset_changed(self._window_manager.preset_manager.default_preset.get_preset())
            return

        with self._options as options:
            options.selected_preset_name = preset_data.name

    # Generate seed

    def _generate_new_seed(self, spoiler: bool):
        preset = self._current_preset_data
        num_players = self.window.num_players_spin_box.value()

        self.generate_seed_from_permalink(Permalink(
            seed_number=random.randint(0, 2 ** 31),
            spoiler=spoiler,
            presets={
                i: preset.get_preset()
                for i in range(num_players)
            },
        ))

    def generate_seed_from_permalink(self, permalink: Permalink):
        def work(progress_update: ProgressUpdateCallable):
            try:
                layout = simplified_patcher.generate_layout(progress_update=progress_update,
                                                            permalink=permalink,
                                                            options=self._options)
                progress_update(f"Success! (Seed hash: {layout.shareable_hash})", 1)
                persist_layout(self._options.data_dir, layout)
                self._window_manager.open_game_details(layout)

            except GenerationFailure as generate_exception:
                self.failure_handler.handle_failure(generate_exception)
                progress_update("Generation Failure: {}".format(generate_exception), -1)

        if self._window_manager.is_preview_mode:
            print(f"Permalink: {permalink.as_base64_str}")
        self.run_in_background_thread(work, "Creating a seed...")

    def on_options_changed(self, options: Options):
        if not self._has_preset:
            selected_preset = self._window_manager.preset_manager.preset_for_name(options.selected_preset_name)
            if selected_preset is not None:
                self.select_game(selected_preset.game)
                index = self.window.create_preset_combo.findText(selected_preset.name)
                if index != -1:
                    self.window.create_preset_combo.setCurrentIndex(index)
                    try:
                        self.on_preset_changed(self._current_preset_data.get_preset())
                        return
                    except InvalidPreset:
                        logging.exception(f"Invalid preset for {options.selected_preset_name}")
            else:
                self.select_game(RandovaniaGame.PRIME2)

            self.window.create_preset_combo.setCurrentIndex(0)
            self.on_preset_changed(self._window_manager.preset_manager.default_preset.get_preset())

    def on_preset_changed(self, preset: Preset):
        self._has_preset = True

        self.window.create_preset_description.setText(preset.description)
        self._action_delete.setEnabled(preset.base_preset_name is not None)

        create_preset_combo = self.window.create_preset_combo
        create_preset_combo.setCurrentIndex(create_preset_combo.findText(preset.name))

        categories = list(preset_describer.describe(preset))
        left_categories = categories[::2]
        right_categories = categories[1::2]

        self.window.create_describe_left_label.setText(preset_describer.merge_categories(left_categories))
        self.window.create_describe_right_label.setText(preset_describer.merge_categories(right_categories))

    def update_progress(self, message: str, percentage: int):
        self.window.progress_label.setText(message)
        if "Aborted" in message:
            percentage = 0
        if percentage >= 0:
            self.window.progress_bar.setRange(0, 100)
            self.window.progress_bar.setValue(percentage)
        else:
            self.window.progress_bar.setRange(0, 0)
