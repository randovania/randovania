import functools
import random
from typing import Dict, Optional

from PyQt5.QtCore import pyqtSignal, Qt, QEvent
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QLabel, QMessageBox, QRadioButton, QSpinBox

from randovania.gui import tab_service
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.common_qt_lib import application_options, prompt_user_for_input_iso
from randovania.gui.history_window import HistoryWindow
from randovania.gui.layout_generator_window_ui import Ui_LayoutGeneratorWindow
from randovania.interface_common import simplified_patcher
from randovania.interface_common.echoes import default_prime2_pickup_database
from randovania.interface_common.options import Options
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.resolver.exceptions import GenerationFailure
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


class CustomSpinBox(QSpinBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)

    def focusInEvent(self, event: QEvent):
        self.setFocusPolicy(Qt.WheelFocus)

    def focusOutEvent(self, event: QEvent):
        self.setFocusPolicy(Qt.StrongFocus)

    def eventFilter(self, obj: QSpinBox, event: QEvent) -> bool:
        if event.type() == QEvent.Wheel and isinstance(obj, QSpinBox):
            if obj.focusPolicy() == Qt.WheelFocus:
                event.accept()
                return False
            else:
                event.ignore()
                return True
        return super().eventFilter(obj, event)


class LayoutGeneratorWindow(QMainWindow, Ui_LayoutGeneratorWindow):
    tab_service: tab_service
    _last_generated_layout: Optional[LayoutDescription] = None
    _layout_logic_radios: Dict[LayoutLogic, QRadioButton]
    _mode_radios: Dict[LayoutMode, QRadioButton]
    _elevators_radios: Dict[LayoutRandomizedFlag, QRadioButton]
    _sky_temple_radios: Dict[LayoutRandomizedFlag, QRadioButton]
    _item_loss_radios: Dict[LayoutEnabledFlag, QRadioButton]
    _spinbox_for_item: Dict[str, QSpinBox] = {}
    _bulk_changing_quantity = False

    _total_item_count = 0
    _maximum_item_count = 0

    layout_generated_signal = pyqtSignal(LayoutDescription)
    failed_to_generate_signal = pyqtSignal(Exception)

    def __init__(self, tab_service: tab_service, background_processor: BackgroundTaskMixin):
        super().__init__()
        self.setupUi(self)
        self.mode_group.hide()

        self.tab_service = tab_service
        self.background_processor = background_processor

        # Connect to Events
        background_processor.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.display_help_box.toggled.connect(self.update_help_display)
        self.failed_to_generate_signal.connect(show_failed_generation_exception)
        self.layout_generated_signal.connect(self._on_layout_generated)
        self.itemquantity_reset_button.clicked.connect(self._reset_item_quantities)

        # All code for the Randomize button
        self.seed_number_edit.setValidator(QIntValidator(0, 2 ** 31 - 1))

        # self.setup_initial_combo_selection()
        self.create_layout_button.clicked.connect(self._create_new_layout_pressed)
        self.view_details_button.clicked.connect(self._view_layout_details)

        self.itemquantity_total_label.keep_visible_with_help_disabled = True
        self._create_item_toggles()

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
                if isinstance(element, QLabel) and not getattr(element, "keep_visible_with_help_disabled", False):
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
            progress_update("Generation Failure: {}".format(generate_exception), -1)

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
            LayoutLogic.TRIVIAL: self.logic_trivial_radio,
            LayoutLogic.EASY: self.logic_easy_radio,
            LayoutLogic.NORMAL: self.logic_normal_radio,
            LayoutLogic.HARD: self.logic_hard_radio,
            LayoutLogic.HYPERMODE: self.logic_hypermode_radio,
            LayoutLogic.MINIMAL_RESTRICTIONS: self.logic_minimalrestrictions_radio,
        }
        self._mode_radios = {
            LayoutMode.STANDARD: self.mode_standard_radio,
            LayoutMode.MAJOR_ITEMS: self.mode_major_items_radio
        }
        self._item_loss_radios = {
            LayoutEnabledFlag.ENABLED: self.itemloss_enabled_radio,
            LayoutEnabledFlag.DISABLED: self.itemloss_disabled_radio,
        }
        self._elevators_radios = {
            LayoutRandomizedFlag.VANILLA: self.elevators_vanilla_radio,
            LayoutRandomizedFlag.RANDOMIZED: self.elevators_randomized_radio,
        }
        self._sky_temple_radios = {
            LayoutRandomizedFlag.VANILLA: self.skytemple_vanilla_radio,
            LayoutRandomizedFlag.RANDOMIZED: self.skytemple_randomized_radio,
        }

        # Check the correct radio element
        self._layout_logic_radios[options.layout_configuration_logic].setChecked(True)
        self._mode_radios[options.layout_configuration_mode].setChecked(True)
        self._elevators_radios[options.layout_configuration_elevators].setChecked(True)
        self._sky_temple_radios[options.layout_configuration_sky_temple_keys].setChecked(True)
        self._item_loss_radios[options.layout_configuration_item_loss].setChecked(True)

        # Connect the options changed events, after setting the initial values
        field_name_to_mapping = {
            "layout_configuration_logic": self._layout_logic_radios,
            "layout_configuration_mode": self._mode_radios,
            "layout_configuration_item_loss": self._item_loss_radios,
            "layout_configuration_elevators": self._elevators_radios,
            "layout_configuration_sky_temple_keys": self._sky_temple_radios,
        }
        for field_name, mapping in field_name_to_mapping.items():
            for value, radio in mapping.items():
                radio.toggled.connect(
                    functools.partial(
                        _update_options_when_true, field_name, value))

    def _create_item_toggles(self):
        options = application_options()
        pickup_database = default_prime2_pickup_database()

        split_pickups = pickup_database.pickups_split_by_name()
        self._maximum_item_count = len(pickup_database.pickups)

        # TODO: Very specific logic that should be provided by data
        split_pickups.pop("Energy Transfer Module")

        num_rows = len(split_pickups) / 2
        for i, pickup in enumerate(sorted(split_pickups.keys())):
            row = 3 + i % num_rows
            column = (i // num_rows) * 2
            pickup_label = QLabel(self.itemquantity_group)
            pickup_label.setText(pickup)
            pickup_label.keep_visible_with_help_disabled = True
            self.gridLayout_2.addWidget(pickup_label, row, column, 1, 1)

            original_quantity = len(split_pickups[pickup])
            value = options.quantity_for_pickup(pickup)
            if value is None:
                value = original_quantity
            self._total_item_count += value

            spin_box = CustomSpinBox(self.itemquantity_group)
            spin_box.pickup_name = pickup
            spin_box.original_quantity = original_quantity
            spin_box.previous_value = value
            spin_box.setValue(value)
            spin_box.setFixedWidth(75)
            spin_box.setMaximum(self._maximum_item_count)
            spin_box.valueChanged.connect(functools.partial(self._change_item_quantity, spin_box))
            self._spinbox_for_item[pickup] = spin_box
            self.gridLayout_2.addWidget(spin_box, row, column + 1, 1, 1)

        self._update_item_quantity_total_label()

    def _reset_item_quantities(self):
        self._bulk_changing_quantity = True

        for pickup, pickup_list in default_prime2_pickup_database().pickups_split_by_name().items():
            if pickup not in self._spinbox_for_item:
                continue
            self._spinbox_for_item[pickup].setValue(len(pickup_list))

        application_options().save_to_disk()
        self._bulk_changing_quantity = False

    def _change_item_quantity(self, spin_box: QSpinBox, new_quantity: int):
        self._total_item_count -= spin_box.previous_value
        self._total_item_count += new_quantity
        spin_box.previous_value = new_quantity
        self._update_item_quantity_total_label()

        options = application_options()
        options.set_quantity_for_pickup(
            spin_box.pickup_name, new_quantity if new_quantity != spin_box.original_quantity else None)

        if not self._bulk_changing_quantity:
            options.save_to_disk()

    def _update_item_quantity_total_label(self):
        self.itemquantity_total_label.setText("Total Pickups: {}/{}".format(
            self._total_item_count, self._maximum_item_count))

    # Progress
    def enable_buttons_with_background_tasks(self, value: bool):
        self.create_layout_button.setEnabled(value)
