import functools
import random
from typing import Dict, Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QLabel, QMessageBox, QRadioButton, QFileDialog

from randovania.gui import TabService
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.common_qt_lib import application_options, prompt_user_for_input_iso
from randovania.gui.history_window import HistoryWindow
from randovania.gui.layout_generator_window_ui import Ui_LayoutGeneratorWindow
from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.resolver.generator import GenerationFailure
from randovania.resolver.layout_configuration import LayoutRandomizedFlag, LayoutLogic, LayoutMode, LayoutEnabledFlag
from randovania.resolver.layout_description import LayoutDescription


def _update_options_when_true(field_name: str, new_value, checked: bool):
    if checked:
        options = application_options()
        setattr(options, field_name, new_value)
        options.save_to_disk()


def show_failed_generation_exception(exception: Exception):
    QMessageBox.critical(None,
                         "An exception was raised",
                         "An unhandled Exception occurred:\n{}".format(exception))


class LayoutGeneratorWindow(QMainWindow, Ui_LayoutGeneratorWindow):
    tab_service: TabService
    _last_generated_layout: Optional[LayoutDescription] = None
    _layout_logic_radios: Dict[LayoutLogic, QRadioButton]
    _mode_radios: Dict[LayoutMode, QRadioButton]
    _sky_temple_radios: Dict[LayoutRandomizedFlag, QRadioButton]
    _item_loss_radios: Dict[LayoutEnabledFlag, QRadioButton]

    layout_generated_signal = pyqtSignal(LayoutDescription)
    failed_to_generate_signal = pyqtSignal(Exception)

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin):
        super().__init__()
        self.setupUi(self)

        self.tab_service = tab_service
        self.background_processor = background_processor

        # Connect to Events
        background_processor.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.display_help_box.toggled.connect(self.update_help_display)
        self.failed_to_generate_signal.connect(show_failed_generation_exception)
        self.layout_generated_signal.connect(self._on_layout_generated)

        # All code for the Randomize button
        self.seed_number_edit.setValidator(QIntValidator(0, 2 ** 31 - 1))

        # self.setup_initial_combo_selection()
        self.create_layout_button.clicked.connect(self._create_new_layout_pressed)
        self.view_details_button.clicked.connect(self._view_layout_details)

        # Update with Options
        options = application_options()
        self.setup_layout_radio_data(options)
        self.display_help_box.setChecked(options.display_generate_help)

    def update_help_display(self, enabled: bool):
        options = application_options()
        options.display_generate_help = enabled
        options.save_to_disk()

        for layouts in self.scroll_area_widget_contents.children():
            for element in layouts.children():
                if isinstance(element, QLabel):
                    element.setVisible(enabled)

    def get_current_seed_number_or_random_one(self) -> int:
        seed = self.seed_number_edit.text()
        if seed == "":
            return random.randint(0, 2 ** 31)
        else:
            return int(seed)

    def setup_initial_combo_selection(self):
        self.keys_selection_combo.setCurrentIndex(1)
        self.guaranteed_100_selection_combo.setCurrentIndex(1)

    def _on_layout_generated(self, layout: LayoutDescription):
        self._last_generated_layout = layout
        self.tab_service.get_tab(HistoryWindow).add_new_layout_to_history(layout)

        self.view_details_button.setEnabled(True)

    def _view_layout_details(self):
        if self._last_generated_layout is None:
            raise RuntimeError("_view_layout_details should never be called without a _last_generated_layout")

        window: HistoryWindow = self.tab_service.get_tab(HistoryWindow)
        window.change_selected_layout(self._last_generated_layout)
        self.tab_service.focus_tab(window)

    def _try_generate_layout(self, job, progress_update: ProgressUpdateCallable):
        try:
            resulting_layout = job(
                seed_number=self.get_current_seed_number_or_random_one(),
                progress_update=progress_update)
            self.layout_generated_signal.emit(resulting_layout)
            progress_update("Success!", 1)

        except GenerationFailure as generate_exception:
            self.failed_to_generate_signal.emit(generate_exception)
            progress_update("Error: {}".format(generate_exception), 1)

    def randomize_game_simplified(self):
        input_iso = prompt_user_for_input_iso(self)
        if input_iso is None:
            return

        self.randomize_given_iso(input_iso)

    def randomize_given_iso(self, input_iso: str):
        self.background_processor.run_in_background_thread(
            functools.partial(
                self._try_generate_layout,
                job=functools.partial(
                    simplified_patcher.create_layout_then_patch_iso,
                    input_iso=input_iso,
                )
            ),
            "Randomizing...")

    def create_new_layout(self):
        self.background_processor.run_in_background_thread(
            functools.partial(
                self._try_generate_layout,
                job=simplified_patcher.generate_layout
            ),
            "Creating a layout...")

    def _create_new_layout_pressed(self):
        """
        Listener to the "Randomize" button. This does the whole process when "advanced mode" is disabled, just generates
        layouts if enabled.
        """
        if application_options().advanced_options:
            self.create_new_layout()
        else:
            self.randomize_game_simplified()

    def setup_layout_radio_data(self, options: Options):
        # Setup config values to radio maps
        self._layout_logic_radios = {
            LayoutLogic.NO_GLITCHES: self.logic_noglitches_radio,
            LayoutLogic.EASY: self.logic_easy_radio,
            LayoutLogic.NORMAL: self.logic_normal_radio,
            LayoutLogic.HARD: self.logic_hard_radio,
        }
        self._mode_radios = {
            LayoutMode.STANDARD: self.mode_standard_radio,
            LayoutMode.MAJOR_ITEMS: self.mode_major_items_radio
        }
        self._item_loss_radios = {
            LayoutEnabledFlag.ENABLED: self.itemloss_enabled_radio,
            LayoutEnabledFlag.DISABLED: self.itemloss_disabled_radio,
        }
        self._sky_temple_radios = {
            LayoutRandomizedFlag.VANILLA: self.skytemple_vanilla_radio,
            LayoutRandomizedFlag.RANDOMIZED: self.skytemple_randomized_radio,
        }

        # Check the correct radio element
        self._layout_logic_radios[options.layout_configuration_logic].setChecked(True)
        self._mode_radios[options.layout_configuration_mode].setChecked(True)
        self._sky_temple_radios[options.layout_configuration_sky_temple_keys].setChecked(True)
        self._item_loss_radios[options.layout_configuration_item_loss].setChecked(True)

        # Connect the options changed events, after setting the initial values
        field_name_to_mapping = {
            "layout_configuration_logic": self._layout_logic_radios,
            "layout_configuration_mode": self._mode_radios,
            "layout_configuration_item_loss": self._item_loss_radios,
            "layout_configuration_sky_temple_keys": self._sky_temple_radios,
        }
        for field_name, mapping in field_name_to_mapping.items():
            for value, radio in mapping.items():
                radio.toggled.connect(
                    functools.partial(
                        _update_options_when_true, field_name, value))

    # Progress
    def enable_buttons_with_background_tasks(self, value: bool):
        self.create_layout_button.setEnabled(value)
