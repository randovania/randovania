import random
from functools import partial
from itertools import zip_longest
from typing import Optional

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QDialog, QMessageBox, QWidget

from randovania.gui.dialog.logic_settings_window import LogicSettingsWindow
from randovania.gui.generated.main_window_ui import Ui_MainWindow
from randovania.gui.lib import preset_describer
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options
from randovania.interface_common.preset_editor import PresetEditor
from randovania.interface_common.preset_manager import PresetManager
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.layout.permalink import Permalink
from randovania.layout.preset import Preset
from randovania.resolver.exceptions import GenerationFailure


class GenerateSeedTab(QWidget):
    _current_lock_state: bool = True
    _logic_settings_window = None
    _current_preset: Preset = None

    preset_manager: PresetManager
    failed_to_generate_signal = Signal(GenerationFailure)

    def __init__(self, background_processor: BackgroundTaskMixin, window: Ui_MainWindow,
                 window_manager: WindowManager, options: Options):
        super().__init__()

        self.background_processor = background_processor
        self.window = window
        self._window_manager = window_manager
        self._options = options
        self.preset_manager = PresetManager(options.data_dir)

        self.failed_to_generate_signal.connect(self._show_failed_generation_exception)

    def setup_ui(self):
        window = self.window

        # Progress
        self.background_processor.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)

        for preset in self.preset_manager.all_presets:
            self._create_button_for_preset(preset)

        window.create_customize_button.clicked.connect(self._on_customize_button)
        window.create_delete_button.clicked.connect(self._on_delete_preset_button)
        window.create_preset_combo.activated.connect(self._on_select_preset)
        window.create_generate_button.clicked.connect(partial(self._generate_new_seed, True))
        window.create_generate_race_button.clicked.connect(partial(self._generate_new_seed, False))

    def _show_failed_generation_exception(self, exception: GenerationFailure):
        QMessageBox.critical(self._window_manager,
                             "An error occurred while generating a seed",
                             "{}\n\nSome errors are expected to occur, please try again.".format(exception))

    @property
    def _current_preset_data(self) -> Optional[Preset]:
        return self.preset_manager.preset_for_name(self.window.create_preset_combo.currentData())

    def enable_buttons_with_background_tasks(self, value: bool):
        self._current_lock_state = value
        self.window.welcome_tab.setEnabled(value)

    def _create_button_for_preset(self, preset: Preset):
        create_preset_combo = self.window.create_preset_combo
        create_preset_combo.addItem(preset.name, preset.name)

    def _on_customize_button(self):
        editor = PresetEditor(self._current_preset_data)
        self._logic_settings_window = LogicSettingsWindow(self._window_manager, editor)

        self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())
        editor.on_changed = lambda: self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())

        result = self._logic_settings_window.exec_()
        self._logic_settings_window = None

        if result == QDialog.Accepted:
            new_preset = editor.create_custom_preset_with()

            with self._options as options:
                options.selected_preset_name = new_preset.name

            if self.preset_manager.add_new_preset(new_preset):
                self._create_button_for_preset(new_preset)
            self.on_preset_changed(new_preset)

    def _on_delete_preset_button(self):
        self.preset_manager.delete_preset(self._current_preset_data)
        self.window.create_preset_combo.removeItem(self.window.create_preset_combo.currentIndex())
        self._on_select_preset()

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
                self.window.show_seed_tab(layout)

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
            self.on_preset_changed(self.preset_manager.default_preset)

    def on_preset_changed(self, preset: Preset):
        self._current_preset = preset

        self.window.create_preset_description.setText(preset.description)
        self.window.create_delete_button.setEnabled(preset.base_preset_name is not None)

        create_preset_combo = self.window.create_preset_combo
        create_preset_combo.setCurrentIndex(create_preset_combo.findText(preset.name))

        categories = list(preset_describer.describe(preset))
        left_categories = categories[::2]
        right_categories = categories[1::2]

        self.window.create_describe_left_label.setText(preset_describer.merge_categories(left_categories))
        self.window.create_describe_right_label.setText(preset_describer.merge_categories(right_categories))


