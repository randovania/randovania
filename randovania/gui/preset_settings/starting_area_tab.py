from typing import Callable

from PySide6 import QtWidgets, QtCore

from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.games.game import RandovaniaGame
from randovania.gui.generated.preset_starting_area_ui import Ui_PresetStartingArea
from randovania.gui.lib.area_list_helper import AreaListHelper
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.base_configuration import StartingLocationList
from randovania.layout.preset import Preset


class PresetStartingArea(PresetTab, Ui_PresetStartingArea, AreaListHelper):
    _starting_location_for_world: dict[str, QtWidgets.QCheckBox]
    _starting_location_for_area: dict[AreaIdentifier, QtWidgets.QCheckBox]

    _num_quick_fill_buttons: int

    def __init__(self, editor: PresetEditor, game: GameDescription):
        super().__init__(editor)
        self.setupUi(self)
        self.game_description = game

        self.starting_area_layout.setAlignment(QtCore.Qt.AlignTop)

        self._starting_location_for_world, self._starting_location_for_area = self.create_area_list_selection(
            self.starting_locations_contents,
            self.starting_locations_layout,
            StartingLocationList.areas_list(self.game_description.game),
            self._on_starting_area_check_changed,
        )

        desc = self.startingarea_description.text().format(quick_fill_text=self.quick_fill_description)
        self.startingarea_description.setText(desc)

        self._num_quick_fill_buttons = 0
        self.create_quick_fill_buttons()

    def create_quick_fill_buttons(self):
        self.starting_area_quick_fill_default = self._quick_fill_button("Default",
                                                                        self._starting_location_on_select_default)

    def _quick_fill_button(self, text: str,
                           connection: Callable[["PresetStartingArea"], None]) -> QtWidgets.QPushButton:
        self._num_quick_fill_buttons += 1
        button = QtWidgets.QPushButton(text)
        self.starting_area_quick_fill_layout.addWidget(button)
        button.clicked.connect(connection)
        return button

    @classmethod
    def tab_title(cls) -> str:
        return "Starting Area"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    @property
    def game_enum(self) -> RandovaniaGame:
        return self.game_description.game

    @property
    def quick_fill_description(self) -> str:
        default_name = self.game_description.world_list.correct_area_identifier_name(
            self.game_description.starting_location)
        return f"Default: Just {default_name}, the vanilla location."

    def _on_starting_area_check_changed(self, world_areas, checked: bool):
        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location",
                editor.configuration.starting_location.ensure_has_locations(world_areas, checked)
            )

    def _starting_location_on_select_default(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location",
                editor.configuration.starting_location.with_elements(
                    [self.game_description.starting_location],
                    self.game_enum,
                )
            )

    def on_preset_changed(self, preset: Preset):
        self.update_area_list(
            preset.configuration.starting_location.locations,
            False,
            self._starting_location_for_world,
            self._starting_location_for_area,
        )


class PresetMetroidStartingArea(PresetStartingArea):
    def create_quick_fill_buttons(self):
        super().create_quick_fill_buttons()
        self.starting_area_quick_fill_save_station = self._quick_fill_button("Save Station",
                                                                             self._starting_location_on_select_save_station)

    def _starting_location_on_select_save_station(self):
        world_list = self.game_description.world_list
        save_stations = [world_list.node_to_area_location(node)
                         for node in world_list.iterate_nodes() if node.name == "Save Station"]

        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location",
                editor.configuration.starting_location.with_elements(save_stations, self.game_enum)
            )

    @property
    def quick_fill_description(self) -> str:
        return super().quick_fill_description + "<br/>Save Stations: All areas with Save Stations."
