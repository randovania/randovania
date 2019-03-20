import functools
from typing import Optional

from PySide2 import QtCore
from PySide2.QtWidgets import QMainWindow, QComboBox

from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.world_list import WorldList
from randovania.games.prime import default_data
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.common_qt_lib import set_combo_with_value
from randovania.gui.logic_settings_window_ui import Ui_LogicSettingsWindow
from randovania.gui.tab_service import TabService
from randovania.interface_common.options import Options
from randovania.layout.layout_configuration import LayoutElevators, LayoutTrickLevel, LayoutSkyTempleKeyMode
from randovania.layout.starting_location import StartingLocationConfiguration, StartingLocation


def _update_options_when_true(options: Options, field_name: str, new_value, checked: bool):
    if checked:
        with options:
            setattr(options, field_name, new_value)


def _update_options_by_value(options: Options, combo: QComboBox, new_index: int):
    with options:
        setattr(options, combo.options_field_name, combo.currentData())


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
    world_list: WorldList

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin, options: Options):
        super().__init__()
        self.setupUi(self)
        self._options = options

        # Update with Options
        self.setup_trick_level_elements()
        self.setup_elevator_elements()
        self.setup_sky_temple_elements()
        self.setup_starting_area_elements()

        # Alignment
        self.trick_level_layout.setAlignment(QtCore.Qt.AlignTop)
        self.elevator_layout.setAlignment(QtCore.Qt.AlignTop)
        self.goal_layout.setAlignment(QtCore.Qt.AlignTop)
        self.starting_area_layout.setAlignment(QtCore.Qt.AlignTop)

    # Options
    def on_options_changed(self, options: Options):
        # Trick Level
        trick_level = options.layout_configuration_trick_level

        set_combo_with_value(self.logic_combo_box, trick_level)
        self.logic_level_label.setText(_get_trick_level_description(trick_level))

        # Elevator
        set_combo_with_value(self.elevators_combo, options.layout_configuration_elevators)

        # Sky Temple Keys
        keys = options.layout_configuration_sky_temple_keys
        if isinstance(keys.value, int):
            self.skytemple_slider.setValue(keys.value)
            data = int
        else:
            data = keys
        set_combo_with_value(self.skytemple_combo, data)

        # Starting Area
        starting_location = options.layout_configuration.starting_location
        set_combo_with_value(self.startingarea_combo, starting_location.configuration)

        if starting_location.configuration == StartingLocationConfiguration.CUSTOM:
            area_location = starting_location.custom_location
            world = self.world_list.world_by_asset_id(area_location.world_asset_id)

            set_combo_with_value(self.specific_starting_world_combo, world)
            set_combo_with_value(self.specific_starting_area_combo, world.area_by_asset_id(area_location.area_asset_id))

    # Trick Level
    def setup_trick_level_elements(self):
        # logic_combo_box
        for i, trick_level in enumerate(LayoutTrickLevel):
            self.logic_combo_box.setItemData(i, trick_level)

        self.logic_combo_box.currentIndexChanged.connect(self._on_trick_level_changed)

    def _on_trick_level_changed(self):
        trick_level = self.logic_combo_box.currentData()
        _update_options_when_true(self._options, "layout_configuration_trick_level", trick_level, True)

    # Elevator
    def setup_elevator_elements(self):
        self.elevators_combo.setItemData(0, LayoutElevators.VANILLA)
        self.elevators_combo.setItemData(1, LayoutElevators.RANDOMIZED)

        self.elevators_combo.options_field_name = "layout_configuration_elevators"
        self.elevators_combo.currentIndexChanged.connect(functools.partial(_update_options_by_value,
                                                                           self._options,
                                                                           self.elevators_combo))

    # Sky Temple Key
    def setup_sky_temple_elements(self):
        self.skytemple_combo.setItemData(0, LayoutSkyTempleKeyMode.ALL_BOSSES)
        self.skytemple_combo.setItemData(1, LayoutSkyTempleKeyMode.ALL_GUARDIANS)
        self.skytemple_combo.setItemData(2, int)

        self.skytemple_combo.options_field_name = "layout_configuration_sky_temple_keys"
        self.skytemple_combo.currentIndexChanged.connect(self._on_sky_temple_key_combo_changed)
        self.skytemple_slider.valueChanged.connect(self._on_sky_temple_key_combo_slider_changed)

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

    # Starting Area
    def setup_starting_area_elements(self):
        self.startingarea_combo.setItemData(0, StartingLocationConfiguration.SHIP)
        self.startingarea_combo.setItemData(1, StartingLocationConfiguration.RANDOM_SAVE_STATION)
        self.startingarea_combo.setItemData(2, StartingLocationConfiguration.CUSTOM)

        game_description = data_reader.decode_data(default_data.decode_default_prime2(), False)
        self.world_list = game_description.world_list

        for world in sorted(self.world_list.worlds, key=lambda x: x.name):
            self.specific_starting_world_combo.addItem(world.name, userData=world)

        self.specific_starting_world_combo.currentIndexChanged.connect(self._on_select_world)
        self.specific_starting_area_combo.currentIndexChanged.connect(self._on_select_area)
        self.startingarea_combo.currentIndexChanged.connect(self._on_starting_area_configuration_changed)

    def _on_starting_area_configuration_changed(self):
        specific_enabled = self.startingarea_combo.currentData() == StartingLocationConfiguration.CUSTOM
        self.specific_starting_world_combo.setEnabled(specific_enabled)
        self.specific_starting_area_combo.setEnabled(specific_enabled)
        self._on_select_world()
        self._update_starting_location()

    def _on_select_world(self):
        self.specific_starting_area_combo.clear()
        for area in sorted(self.specific_starting_world_combo.currentData().areas, key=lambda x: x.name):
            self.specific_starting_area_combo.addItem(area.name, userData=area)

    def _on_select_area(self):
        if self.specific_starting_area_combo.currentData() is not None:
            self._update_starting_location()

    def _update_starting_location(self):
        if self._has_valid_starting_location():
            with self._options as options:
                options.set_layout_configuration_field(
                    "starting_location",
                    StartingLocation(self.startingarea_combo.currentData(), self.current_starting_area_location))

    @property
    def current_starting_area_location(self) -> Optional[AreaLocation]:
        if self.specific_starting_world_combo.isEnabled():
            return AreaLocation(
                self.specific_starting_world_combo.currentData().world_asset_id,
                self.specific_starting_area_combo.currentData().area_asset_id,
            )
        else:
            return None

    def _has_valid_starting_location(self):
        current_config = self.startingarea_combo.currentData()
        if current_config == StartingLocationConfiguration.CUSTOM:
            return self.specific_starting_area_combo.currentData() is not None
        else:
            return True
