import functools
from typing import Dict

from PyQt5.QtWidgets import QMainWindow, QLabel, QRadioButton

from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.common_qt_lib import application_options
from randovania.gui.logic_settings_window_ui import Ui_LogicSettingsWindow
from randovania.gui.tab_service import TabService
from randovania.interface_common.options import Options
from randovania.resolver.layout_configuration import LayoutRandomizedFlag, LayoutTrickLevel, LayoutMode, \
    LayoutEnabledFlag


def _update_options_when_true(field_name: str, new_value, checked: bool):
    if checked:
        options = application_options()
        setattr(options, field_name, new_value)
        options.save_to_disk()


class LogicSettingsWindow(QMainWindow, Ui_LogicSettingsWindow):
    _layout_logic_radios: Dict[LayoutTrickLevel, QRadioButton]
    _mode_radios: Dict[LayoutMode, QRadioButton]
    _elevators_radios: Dict[LayoutRandomizedFlag, QRadioButton]
    _sky_temple_radios: Dict[LayoutRandomizedFlag, QRadioButton]
    _item_loss_radios: Dict[LayoutEnabledFlag, QRadioButton]

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin):
        super().__init__()
        self.setupUi(self)
        self.mode_group.hide()

        # Connect to Events
        self.display_help_box.toggled.connect(self.update_help_display)

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
                radio.toggled.connect(functools.partial(_update_options_when_true, field_name, value))
