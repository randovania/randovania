import functools

from PySide2 import QtCore
from PySide2.QtWidgets import QMainWindow, QComboBox

from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.logic_settings_window_ui import Ui_LogicSettingsWindow
from randovania.gui.tab_service import TabService
from randovania.interface_common.options import Options
from randovania.layout.layout_configuration import LayoutElevators, LayoutTrickLevel, LayoutSkyTempleKeyMode
from randovania.layout.starting_resources import StartingResourcesConfiguration


def _update_options_when_true(options: Options, field_name: str, new_value, checked: bool):
    if checked:
        with options:
            setattr(options, field_name, new_value)


def _update_options_by_value(options: Options, combo: QComboBox, new_index: int):
    with options:
        setattr(options, combo.options_field_name, combo.currentData())


def _on_item_loss_changed(options: Options, new_value: bool):
    with options:
        if new_value:
            options.layout_configuration_starting_resources = StartingResourcesConfiguration.VANILLA_ITEM_LOSS_ENABLED
        else:
            options.layout_configuration_starting_resources = StartingResourcesConfiguration.VANILLA_ITEM_LOSS_DISABLED


_TRICK_LEVEL_DESCRIPTION = {
    LayoutTrickLevel.NO_TRICKS: [
        "This mode requires no knowledge about the game, nor does it require any abuse "
        "of game mechanics, making it ideal for casual and first time players."
    ],
    LayoutTrickLevel.TRIVIAL: [
        "This mode includes strategies that abuses oversights in the game, such as being able to activate the "
        "Hive Dynamo Works portal from the other side of the chasm and bomb jumping in Temple Assembly Site."
    ],
    LayoutTrickLevel.EASY: ["This mode assumes you can do simple tricks."],
    LayoutTrickLevel.NORMAL: ["This mode expands on the Easy mode, including more difficult to execute tricks."],
    LayoutTrickLevel.HARD: ["This mode expands on Normal with additional tricks, such as Grand Abyss scan dash."],
    LayoutTrickLevel.HYPERMODE: [
        "This mode considers every single trick and path known to Randovania as valid, "
        "such as Polluted Mire without Space Jump. No OOB is included."
    ],
    LayoutTrickLevel.MINIMAL_RESTRICTIONS: [
        ("This mode only checks that Screw Attack, Dark Visor and Light Suit won't all be behind "
         "Ing Caches and Dark Water, removing the biggest reasons for a pure random layout to be impossible."),
        "Since there aren't many checks, out of bounds tricks will probably be necessary for many items."
    ],
}


def _get_trick_level_description(trick_level: LayoutTrickLevel) -> str:
    return "<html><head/><body>{}</body></html>".format(
        "".join(
            '<p align="justify">{}</p>'.format(item)
            for item in _TRICK_LEVEL_DESCRIPTION[trick_level]
        )
    )


class LogicSettingsWindow(QMainWindow, Ui_LogicSettingsWindow):
    _options: Options

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin, options: Options):
        super().__init__()
        self.setupUi(self)
        self._options = options

        # Update with Options
        self.setup_trick_level_elements()
        self.setup_elevator_elements()
        self.setup_sky_temple_elements()

        # Alignment
        self.vertical_layout_left.setAlignment(QtCore.Qt.AlignTop)
        self.vertical_layout_right.setAlignment(QtCore.Qt.AlignTop)

    def setup_trick_level_elements(self):
        # logic_combo_box
        for i, trick_level in enumerate(LayoutTrickLevel):
            self.logic_combo_box.setItemData(i, trick_level)

        self.logic_combo_box.currentIndexChanged.connect(self._on_trick_level_changed)

    def setup_elevator_elements(self):
        self.elevators_combo.setItemData(0, LayoutElevators.VANILLA)
        self.elevators_combo.setItemData(1, LayoutElevators.RANDOMIZED)

        self.elevators_combo.options_field_name = "layout_configuration_elevators"
        self.elevators_combo.currentIndexChanged.connect(functools.partial(_update_options_by_value,
                                                                           self._options,
                                                                           self.elevators_combo))

    def setup_sky_temple_elements(self):
        self.skytemple_combo.setItemData(0, LayoutSkyTempleKeyMode.ALL_BOSSES)
        self.skytemple_combo.setItemData(1, LayoutSkyTempleKeyMode.ALL_GUARDIANS)
        self.skytemple_combo.setItemData(2, int)

        self.skytemple_combo.options_field_name = "layout_configuration_sky_temple_keys"
        self.skytemple_combo.currentIndexChanged.connect(self._on_sky_temple_key_combo_changed)
        self.skytemple_slider.valueChanged.connect(self._on_sky_temple_key_combo_slider_changed)

    def _on_trick_level_changed(self):
        trick_level = self.logic_combo_box.currentData()
        _update_options_when_true(self._options, "layout_configuration_trick_level", trick_level, True)

    def _on_sky_temple_key_combo_changed(self):
        combo_enum = self.skytemple_combo.currentData()
        with self._options:
            if combo_enum is int:
                self.skytemple_slider.setEnabled(True)
                self._options.layout_configuration_sky_temple_keys = LayoutSkyTempleKeyMode(
                    self.skytemple_slider.value())
            else:
                self.skytemple_slider.setEnabled(False)
                self._options.layout_configuration_sky_temple_keys = combo_enum

    def _on_sky_temple_key_combo_slider_changed(self):
        self.skytemple_slider_label.setText(str(self.skytemple_slider.value()))
        self._on_sky_temple_key_combo_changed()

    # Options
    def on_options_changed(self):
        # Trick Level
        trick_level = self._options.layout_configuration_trick_level

        self.logic_combo_box.setCurrentIndex(self.logic_combo_box.findData(trick_level))
        self.logic_level_label.setText(_get_trick_level_description(trick_level))

        # Elevator
        self.elevators_combo.setCurrentIndex(
            self.elevators_combo.findData(self._options.layout_configuration_elevators))

        # Sky Temple Keys
        keys = self._options.layout_configuration_sky_temple_keys
        if isinstance(keys.value, int):
            self.skytemple_slider.setValue(keys.value)
            data = int
        else:
            data = keys
        self.skytemple_combo.setCurrentIndex(self.skytemple_combo.findData(data))
