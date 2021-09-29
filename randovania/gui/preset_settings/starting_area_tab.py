from typing import Dict

from PySide2 import QtWidgets, QtCore

from randovania.game_description.game_description import GameDescription
from randovania.games.game import RandovaniaGame
from randovania.gui.generated.preset_starting_area_ui import Ui_PresetStartingArea
from randovania.gui.lib.area_list_helper import AreaListHelper
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.base_configuration import StartingLocationList
from randovania.layout.preset import Preset


class PresetStartingArea(PresetTab, Ui_PresetStartingArea, AreaListHelper):

    _starting_location_for_world: Dict[str, QtWidgets.QCheckBox]
    _starting_location_for_area: Dict[int, QtWidgets.QCheckBox]

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
        self.starting_area_quick_fill_ship.clicked.connect(self._starting_location_on_select_ship)
        self.starting_area_quick_fill_save_station.clicked.connect(self._starting_location_on_select_save_station)

    @property
    def uses_patches_tab(self) -> bool:
        return True

    @property
    def game_enum(self) -> RandovaniaGame:
        return self.game_description.game

    def _on_starting_area_check_changed(self, world_areas, checked: bool):
        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location",
                editor.configuration.starting_location.ensure_has_locations(world_areas, checked)
            )

    def _starting_location_on_select_ship(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location",
                editor.configuration.starting_location.with_elements(
                    [self.game_description.starting_location],
                    self.game_enum,
                )
            )

    def _starting_location_on_select_save_station(self):
        world_list = self.game_description.world_list
        save_stations = [world_list.node_to_area_location(node)
                         for node in world_list.all_nodes if node.name == "Save Station"]

        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location",
                editor.configuration.starting_location.with_elements(save_stations, self.game_enum)
            )

    def on_preset_changed(self, preset: Preset):
        self.update_area_list(
            preset.configuration.starting_location.locations,
            False,
            self._starting_location_for_world,
            self._starting_location_for_area,
        )
