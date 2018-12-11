import functools
from typing import Dict

from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QLabel, QRadioButton, QComboBox

from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.logic_settings_window_ui import Ui_LogicSettingsWindow
from randovania.gui.tab_service import TabService
from randovania.interface_common.options import Options
from randovania.resolver.layout_configuration import LayoutRandomizedFlag, LayoutTrickLevel, LayoutEnabledFlag


def _update_options_when_true(options: Options, field_name: str, new_value, checked: bool):
    if checked:
        with options:
            setattr(options, field_name, new_value)


def _update_options_by_value(options: Options, combo: QComboBox, new_index: int):
    with options:
        setattr(options, combo.options_field_name, combo.currentData())


def _on_item_loss_changed(options: Options, new_value: bool):
    with options:
        options.layout_configuration_item_loss = LayoutEnabledFlag.ENABLED if new_value else LayoutEnabledFlag.DISABLED


class LogicSettingsWindow(QMainWindow, Ui_LogicSettingsWindow):
    _options: Options
    _layout_logic_labels: Dict[LayoutTrickLevel, QLabel]
    _elevators_radios: Dict[LayoutRandomizedFlag, QRadioButton]
    _sky_temple_radios: Dict[LayoutRandomizedFlag, QRadioButton]
    _item_loss_radios: Dict[LayoutEnabledFlag, QRadioButton]

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin, options: Options):
        super().__init__()
        self.setupUi(self)
        self._options = options

        # Update with Options
        self.setup_trick_level_elements(self._options)
        self.setup_elevator_elements(self._options)
        self.setup_item_loss_elements(self._options)
        self.setup_sky_temple_elements(self._options)

        # Alignment
        self.vertical_layout_left.setAlignment(QtCore.Qt.AlignTop)
        self.vertical_layout_right.setAlignment(QtCore.Qt.AlignTop)

    def setup_initial_combo_selection(self):
        self.keys_selection_combo.setCurrentIndex(1)

    def setup_trick_level_elements(self, options: Options):
        # logic_combo_box
        self._layout_logic_labels = {
            LayoutTrickLevel.NO_TRICKS: self.logic_noglitches_label,
            LayoutTrickLevel.TRIVIAL: self.logic_trivial_label,
            LayoutTrickLevel.EASY: self.logic_easy_label,
            LayoutTrickLevel.NORMAL: self.logic_normal_label,
            LayoutTrickLevel.HARD: self.logic_hard_label,
            LayoutTrickLevel.HYPERMODE: self.logic_hypermode_label,
            LayoutTrickLevel.MINIMAL_RESTRICTIONS: self.logic_minimalrestrictions_label,
        }

        for i, trick_level in enumerate(LayoutTrickLevel):
            self.logic_combo_box.setItemData(i, trick_level)

        self.logic_combo_box.setCurrentIndex(self.logic_combo_box.findData(options.layout_configuration_trick_level))
        self.logic_combo_box.currentIndexChanged.connect(self._on_trick_level_changed)
        self._refresh_trick_level_labels()

    def setup_elevator_elements(self, options: Options):
        self.elevators_combo.setItemData(0, LayoutRandomizedFlag.VANILLA)
        self.elevators_combo.setItemData(1, LayoutRandomizedFlag.RANDOMIZED)

        self.elevators_combo.options_field_name = "layout_configuration_elevators"
        self.elevators_combo.setCurrentIndex(self.elevators_combo.findData(options.layout_configuration_elevators))
        self.elevators_combo.currentIndexChanged.connect(functools.partial(_update_options_by_value,
                                                                           self._options,
                                                                           self.elevators_combo))

    def setup_item_loss_elements(self, options: Options):
        self.itemloss_check.setChecked(options.layout_configuration_item_loss == LayoutEnabledFlag.ENABLED)
        self.itemloss_check.stateChanged.connect(functools.partial(_on_item_loss_changed, self._options))

    def setup_sky_temple_elements(self, options: Options):
        # Setup config values to radio maps
        self._sky_temple_radios = {
            LayoutRandomizedFlag.VANILLA: self.skytemple_vanilla_radio,
            LayoutRandomizedFlag.RANDOMIZED: self.skytemple_randomized_radio,
        }

        # Check the correct radio element
        self._sky_temple_radios[options.layout_configuration_sky_temple_keys].setChecked(True)

        # Connect the options changed events, after setting the initial values
        for value, radio in self._sky_temple_radios.items():
            radio.toggled.connect(functools.partial(_update_options_when_true,
                                                    self._options,
                                                    "layout_configuration_sky_temple_keys",
                                                    value))

    def _on_trick_level_changed(self):
        trick_level = self.logic_combo_box.currentData()
        _update_options_when_true(self._options, "layout_configuration_trick_level", trick_level, True)
        self._refresh_trick_level_labels()

    def _refresh_trick_level_labels(self):
        for label in self._layout_logic_labels.values():
            label.hide()
        self._layout_logic_labels[self.logic_combo_box.currentData()].show()
