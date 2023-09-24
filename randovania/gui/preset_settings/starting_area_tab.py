from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from randovania.gui.generated.preset_starting_area_ui import Ui_PresetStartingArea
from randovania.gui.lib.node_list_helper import NodeListHelper
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.layout.base.base_configuration import StartingLocationList

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game_description.db.area_identifier import AreaIdentifier
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_description import GameDescription
    from randovania.games.game import RandovaniaGame
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetStartingArea(PresetTab, Ui_PresetStartingArea, NodeListHelper):
    starting_area_quick_fill_default: QtWidgets.QPushButton
    _starting_location_for_region: dict[str, QtWidgets.QCheckBox]
    _starting_location_for_area: dict[AreaIdentifier, QtWidgets.QCheckBox]
    _starting_location_for_node: dict[NodeIdentifier, QtWidgets.QCheckBox]

    _num_quick_fill_buttons: int

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.starting_area_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        (
            self._starting_location_for_region,
            self._starting_location_for_area,
            self._starting_location_for_node,
        ) = self.create_node_list_selection(
            self.starting_locations_contents,
            self.starting_locations_layout,
            StartingLocationList.nodes_list(self.game_description.game),
            self._on_starting_area_check_changed,
        )

        desc = self.startingarea_description.text().format(quick_fill_text=self.quick_fill_description)
        self.startingarea_description.setText(desc)

        self._num_quick_fill_buttons = 0
        self.create_quick_fill_buttons()

    def create_quick_fill_buttons(self):
        self.starting_area_quick_fill_default = self._quick_fill_button(
            "Default", self._starting_location_on_select_default
        )

    def _quick_fill_button(self, text: str, connection: Callable[[PresetStartingArea], None]) -> QtWidgets.QPushButton:
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
        default_name = self.game_description.region_list.correct_area_identifier_name(
            self.game_description.starting_location
        )
        return f"Default: Just {default_name}, the vanilla location."

    def _on_starting_area_check_changed(self, areas, checked: bool):
        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location", editor.configuration.starting_location.ensure_has_locations(areas, checked)
            )

    def _starting_location_on_select_default(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location",
                editor.configuration.starting_location.with_elements(
                    [self.game_description.starting_location],
                    self.game_enum,
                ),
            )

    def on_preset_changed(self, preset: Preset):
        self.update_node_list(
            preset.configuration.starting_location.locations,
            False,
            self._starting_location_for_region,
            self._starting_location_for_area,
            self._starting_location_for_node,
        )


class PresetMetroidStartingArea(PresetStartingArea):
    starting_area_quick_fill_save_station: QtWidgets.QPushButton

    def create_quick_fill_buttons(self):
        super().create_quick_fill_buttons()
        self.starting_area_quick_fill_save_station = self._quick_fill_button(
            "Save Station",
            self._starting_location_on_select_save_station,
        )

    def _save_station_nodes(self):
        return [
            node.identifier
            for node in self.game_description.region_list.iterate_nodes()
            if node.name == "Save Station" and node.valid_starting_location
        ]

    def _starting_location_on_select_save_station(self):
        save_stations = self._save_station_nodes()

        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location", editor.configuration.starting_location.with_elements(save_stations, self.game_enum)
            )

    @property
    def quick_fill_description(self) -> str:
        return super().quick_fill_description + "<br/>Save Stations: All areas with Save Stations."
