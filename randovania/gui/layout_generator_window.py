import functools
from typing import Dict

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QMainWindow, QLabel, QRadioButton, QSpinBox

from randovania.game_description.default_database import default_prime2_pickup_database
from randovania.gui import tab_service
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.common_qt_lib import application_options
from randovania.gui.layout_generator_window_ui import Ui_LayoutGeneratorWindow
from randovania.interface_common.options import Options
from randovania.resolver.layout_configuration import LayoutRandomizedFlag, LayoutTrickLevel, LayoutMode, \
    LayoutEnabledFlag


def _update_options_when_true(field_name: str, new_value, checked: bool):
    if checked:
        options = application_options()
        setattr(options, field_name, new_value)
        options.save_to_disk()


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
    _layout_logic_radios: Dict[LayoutTrickLevel, QRadioButton]
    _mode_radios: Dict[LayoutMode, QRadioButton]
    _elevators_radios: Dict[LayoutRandomizedFlag, QRadioButton]
    _sky_temple_radios: Dict[LayoutRandomizedFlag, QRadioButton]
    _item_loss_radios: Dict[LayoutEnabledFlag, QRadioButton]
    _spinbox_for_item: Dict[str, QSpinBox] = {}
    _bulk_changing_quantity = False

    _total_item_count = 0
    _maximum_item_count = 0

    def __init__(self, tab_service: tab_service, background_processor: BackgroundTaskMixin):
        super().__init__()
        self.setupUi(self)
        self.mode_group.hide()

        self.tab_service = tab_service
        self.background_processor = background_processor

        # Connect to Events
        background_processor.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.display_help_box.toggled.connect(self.update_help_display)
        self.itemquantity_reset_button.clicked.connect(self._reset_item_quantities)

        # All code for the Randomize button
        # self.seed_number_edit.setValidator(QIntValidator(0, 2 ** 31 - 1))

        # self.setup_initial_combo_selection()
        # self.create_layout_button.clicked.connect(self._create_new_layout_pressed)
        # self.view_details_button.clicked.connect(self._view_layout_details)

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

    def setup_initial_combo_selection(self):
        self.keys_selection_combo.setCurrentIndex(1)
        self.guaranteed_100_selection_combo.setCurrentIndex(1)

    def setup_layout_radio_data(self, options: Options):
        # Setup config values to radio maps
        self._layout_logic_radios = {
            LayoutTrickLevel.NO_TRICKS: self.logic_noglitches_radio,
            LayoutTrickLevel.TRIVIAL: self.logic_trivial_radio,
            LayoutTrickLevel.EASY: self.logic_easy_radio,
            LayoutTrickLevel.NORMAL: self.logic_normal_radio,
            LayoutTrickLevel.HARD: self.logic_hard_radio,
            LayoutTrickLevel.HYPERMODE: self.logic_hypermode_radio,
            LayoutTrickLevel.MINIMAL_RESTRICTIONS: self.logic_minimalrestrictions_radio,
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
        self._layout_logic_radios[options.layout_configuration_trick_level].setChecked(True)
        self._mode_radios[options.layout_configuration_mode].setChecked(True)
        self._elevators_radios[options.layout_configuration_elevators].setChecked(True)
        self._sky_temple_radios[options.layout_configuration_sky_temple_keys].setChecked(True)
        self._item_loss_radios[options.layout_configuration_item_loss].setChecked(True)

        # Connect the options changed events, after setting the initial values
        field_name_to_mapping = {
            "layout_configuration_trick_level": self._layout_logic_radios,
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

        self._maximum_item_count = pickup_database.total_pickup_count
        pickup_names = set(pickup_database.all_pickup_names)

        # TODO: Very specific logic that should be provided by data
        pickup_names.remove("Energy Transfer Module")

        num_rows = len(pickup_names) / 2
        for i, pickup_name in enumerate(sorted(pickup_names)):
            row = 3 + i % num_rows
            column = (i // num_rows) * 2
            pickup_label = QLabel(self.itemquantity_group)
            pickup_label.setText(pickup_name)
            pickup_label.keep_visible_with_help_disabled = True
            self.gridLayout_2.addWidget(pickup_label, row, column, 1, 1)

            original_quantity = pickup_database.original_quantity_for(pickup_database.pickup_by_name(pickup_name))
            value = options.quantity_for_pickup(pickup_name)
            if value is None:
                value = original_quantity
            self._total_item_count += value

            spin_box = CustomSpinBox(self.itemquantity_group)
            spin_box.pickup_name = pickup_name
            spin_box.original_quantity = original_quantity
            spin_box.previous_value = value
            spin_box.setValue(value)
            spin_box.setFixedWidth(75)
            spin_box.setMaximum(self._maximum_item_count)
            spin_box.valueChanged.connect(functools.partial(self._change_item_quantity, spin_box))
            self._spinbox_for_item[pickup_name] = spin_box
            self.gridLayout_2.addWidget(spin_box, row, column + 1, 1, 1)

        self._update_item_quantity_total_label()

    def _reset_item_quantities(self):
        self._bulk_changing_quantity = True

        pickup_database = default_prime2_pickup_database()
        for pickup_name in pickup_database.all_pickup_names:
            if pickup_name in self._spinbox_for_item:
                self._spinbox_for_item[pickup_name].setValue(
                    pickup_database.original_quantity_for(pickup_database.pickup_by_name(pickup_name)))

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
        # self.create_layout_button.setEnabled(value)
        pass
