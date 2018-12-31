import functools
from typing import Dict

from PySide2 import QtCore
from PySide2.QtWidgets import QMainWindow, QLabel, QRadioButton, QComboBox

from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.logic_settings_window_ui import Ui_LogicSettingsWindow
from randovania.gui.tab_service import TabService
from randovania.interface_common.options import Options
from randovania.resolver.layout_configuration import LayoutRandomizedFlag, LayoutTrickLevel, LayoutEnabledFlag, \
    LayoutSkyTempleKeyMode


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

        self.logic_combo_box.currentIndexChanged.connect(self._on_trick_level_changed)

    def setup_elevator_elements(self, options: Options):
        self.elevators_combo.setItemData(0, LayoutRandomizedFlag.VANILLA)
        self.elevators_combo.setItemData(1, LayoutRandomizedFlag.RANDOMIZED)

        self.elevators_combo.options_field_name = "layout_configuration_elevators"
        self.elevators_combo.currentIndexChanged.connect(functools.partial(_update_options_by_value,
                                                                           self._options,
                                                                           self.elevators_combo))

    def setup_item_loss_elements(self, options: Options):
        self.itemloss_check.stateChanged.connect(functools.partial(_on_item_loss_changed, self._options))

    def setup_sky_temple_elements(self, options: Options):
        for i, value in enumerate(LayoutSkyTempleKeyMode):
            self.skytemple_combo.setItemData(i, value)

        self.skytemple_combo.options_field_name = "layout_configuration_sky_temple_keys"
        self.skytemple_combo.currentIndexChanged.connect(functools.partial(_update_options_by_value,
                                                                           self._options,
                                                                           self.skytemple_combo))

    def _on_trick_level_changed(self):
        trick_level = self.logic_combo_box.currentData()
        _update_options_when_true(self._options, "layout_configuration_trick_level", trick_level, True)

    # Options
    def on_options_changed(self):
        # Trick Level
        trick_level = self._options.layout_configuration_trick_level
        for label in self._layout_logic_labels.values():
            label.hide()
        self.logic_combo_box.setCurrentIndex(self.logic_combo_box.findData(trick_level))
        self._layout_logic_labels[trick_level].show()

        # Elevator
        self.elevators_combo.setCurrentIndex(
            self.elevators_combo.findData(self._options.layout_configuration_elevators))

        # Item Loss
        self.itemloss_check.setChecked(self._options.layout_configuration_item_loss == LayoutEnabledFlag.ENABLED)

        # Sky Temple Keys
        self.skytemple_combo.setCurrentIndex(
            self.skytemple_combo.findData(self._options.layout_configuration_sky_temple_keys))
