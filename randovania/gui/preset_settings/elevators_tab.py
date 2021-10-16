import copy
import dataclasses
import functools
from typing import Dict, Optional

from PySide2 import QtWidgets, QtCore

from randovania.game_description.world.area import Area
from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.node import TeleporterNode
from randovania.game_description.world.teleporter import Teleporter
from randovania.games.game import RandovaniaGame
from randovania.games.prime import elevators
from randovania.gui.generated.preset_elevators_ui import Ui_PresetElevators
from randovania.gui.lib import common_qt_lib, signal_handling
from randovania.gui.lib.area_list_helper import AreaListHelper
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset
from randovania.layout.lib.teleporters import TeleporterShuffleMode, TeleporterTargetList, TeleporterList
from randovania.lib import enum_lib


class PresetElevators(PresetTab, Ui_PresetElevators, AreaListHelper):
    _elevator_source_for_location: Dict[Teleporter, QtWidgets.QCheckBox]
    _elevator_source_destination: Dict[Teleporter, Optional[Teleporter]]
    _elevator_target_for_world: Dict[str, QtWidgets.QCheckBox]
    _elevator_target_for_area: Dict[int, QtWidgets.QCheckBox]

    def __init__(self, editor: PresetEditor, game: GameDescription):
        super().__init__(editor)
        self.setupUi(self)
        self.game_description = game

        self.elevator_layout.setAlignment(QtCore.Qt.AlignTop)

        for value in enum_lib.iterate_enum(TeleporterShuffleMode):
            self.elevators_combo.addItem(value.long_name, value)
        self.elevators_combo.currentIndexChanged.connect(self._update_elevator_mode)
        signal_handling.on_checked(self.skip_final_bosses_check, self._update_require_final_bosses)
        signal_handling.on_checked(self.elevators_allow_unvisited_names_check, self._update_allow_unvisited_names)

        # Elevator Source
        self._create_source_elevators()

        # Elevator Target
        self._elevator_target_for_world, self._elevator_target_for_area = self.create_area_list_selection(
            self.elevators_target_group,
            self.elevators_target_layout,
            TeleporterTargetList.areas_list(self.game_enum),
            self._on_elevator_target_check_changed,
        )

        if self.game_enum != RandovaniaGame.METROID_PRIME_ECHOES:
            self.elevators_help_sound_bug_label.setVisible(False)
            self.elevators_allow_unvisited_names_check.setVisible(False)
            self.elevators_line_3.setVisible(False)
            self.elevators_help_list_label.setVisible(False)

        if self.game_enum == RandovaniaGame.METROID_PRIME:
            self.skip_final_bosses_check.setText("Go directly to credits from Artifact Temple")
            self.skip_final_bosses_label.setText("""<html><head/><body>
            <p>Change the teleport in Artifact Temple to go directly to the credits, skipping the final bosses.</p>
            <p>This changes the requirements to <span style=" font-weight:600;">not need the final bosses</span>,
            turning certain items optional such as Plasma Beam.</p></body></html>
            """)

        elif self.game_enum == RandovaniaGame.METROID_PRIME_CORRUPTION:
            self.elevators_description_label.setText(
                self.elevators_description_label.text().replace("elevator", "teleporter")
            )

    @property
    def uses_patches_tab(self) -> bool:
        return True

    @property
    def tab_title(self):
        if self.game_enum == RandovaniaGame.METROID_PRIME_CORRUPTION:
            return "Teleporters"
        return self.windowTitle()

    @property
    def game_enum(self):
        return self.game_description.game

    def _create_check_for_source_elevator(self, location: Teleporter):
        name = elevators.get_elevator_or_area_name(self.game_enum, self.game_description.world_list, location.area_location, False)

        check = QtWidgets.QCheckBox(self.elevators_source_group)
        check.setText(name)
        check.area_location = location
        signal_handling.on_checked(check, functools.partial(self._on_elevator_source_check_changed, location))
        return check

    def _create_source_elevators(self):
        row = 0

        custom_weights = {}
        if self.game_enum == RandovaniaGame.METROID_PRIME_ECHOES:
            custom_weights = {
                2252328306: 0,  # Great Temple
                1119434212: 1,  # Agon Wastes
                1039999561: 2,  # Torvus Bog
                464164546: 3,  # Sanctuary Fortress
                1006255871: 5,  # Temple Grounds
            }
        locations = TeleporterList.areas_list(self.game_enum)
        areas: Dict[Teleporter, Area] = {
            loc: self.game_description.world_list.area_by_area_location(loc.area_location)
            for loc in locations
        }
        checks: Dict[Teleporter, QtWidgets.QCheckBox] = {
            loc: self._create_check_for_source_elevator(loc) for loc in locations
        }
        self._elevator_source_for_location = copy.copy(checks)
        self._elevator_source_destination = {}

        for location in sorted(locations,
                               key=lambda loc: (custom_weights.get(loc.world_asset_id, 0),
                                                checks[loc].text())):
            if location not in checks:
                continue

            self.elevators_source_layout.addWidget(checks.pop(location), row, 1)

            other_locations = [
                node.default_connection
                for node in areas[location].nodes
                if isinstance(node, TeleporterNode) and node.teleporter == location
            ]
            assert len(other_locations) == 1
            teleporters_in_target = [
                node.teleporter
                for node in self.game_description.world_list.area_by_area_location(other_locations[0]).nodes
                if isinstance(node, TeleporterNode)
            ]
            assert teleporters_in_target
            other_loc = teleporters_in_target[0]

            self._elevator_source_destination[location] = None

            if other_loc in checks:
                self.elevators_source_layout.addWidget(checks.pop(other_loc), row, 2)
                self._elevator_source_destination[location] = other_loc

            row += 1

    def _update_elevator_mode(self):
        with self._editor as editor:
            editor.layout_configuration_elevators = dataclasses.replace(
                editor.layout_configuration_elevators,
                mode=self.elevators_combo.currentData(),
            )

    def _update_require_final_bosses(self, checked: bool):
        with self._editor as editor:
            editor.layout_configuration_elevators = dataclasses.replace(
                editor.layout_configuration_elevators,
                skip_final_bosses=checked,
            )

    def _update_allow_unvisited_names(self, checked: bool):
        with self._editor as editor:
            editor.layout_configuration_elevators = dataclasses.replace(
                editor.layout_configuration_elevators,
                allow_unvisited_room_names=checked,
            )

    def _on_elevator_source_check_changed(self, location: Teleporter, checked: bool):
        with self._editor as editor:
            config = editor.layout_configuration_elevators
            editor.layout_configuration_elevators = dataclasses.replace(
                config,
                excluded_teleporters=config.excluded_teleporters.ensure_has_location(location, not checked),
            )

    def _on_elevator_target_check_changed(self, world_areas, checked: bool):
        with self._editor as editor:
            config = editor.layout_configuration_elevators
            editor.layout_configuration_elevators = dataclasses.replace(
                config,
                excluded_targets=config.excluded_targets.ensure_has_locations(world_areas, not checked),
            )

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration

        common_qt_lib.set_combo_with_value(self.elevators_combo, config.elevators.mode)
        can_shuffle_target = config.elevators.mode not in (TeleporterShuffleMode.VANILLA,
                                                           TeleporterShuffleMode.TWO_WAY_RANDOMIZED,
                                                           TeleporterShuffleMode.TWO_WAY_UNCHECKED)
        static_areas = set(
            teleporter
            for teleporter in config.elevators.static_teleporters.keys()
        )

        for origin, destination in self._elevator_source_destination.items():
            origin_check = self._elevator_source_for_location[origin]
            dest_check = self._elevator_source_for_location.get(destination)

            is_locked = origin in static_areas
            if not can_shuffle_target:
                is_locked = is_locked or destination in static_areas

            origin_check.setEnabled(not config.elevators.is_vanilla and not is_locked)
            origin_check.setChecked(origin not in config.elevators.excluded_teleporters.locations and not is_locked)

            origin_check.setToolTip("The destination for this teleporter is locked due to other settings."
                                    if is_locked else "")

            if dest_check is None:
                if not can_shuffle_target:
                    origin_check.setEnabled(False)
                continue

            dest_check.setEnabled(can_shuffle_target and destination not in static_areas)
            if can_shuffle_target:
                dest_check.setChecked(destination not in config.elevators.excluded_teleporters.locations
                                      and destination not in static_areas)
            else:
                dest_check.setChecked(origin_check.isChecked())

        self.elevators_target_group.setEnabled(config.elevators.has_shuffled_target)
        self.skip_final_bosses_check.setChecked(config.elevators.skip_final_bosses)
        self.elevators_allow_unvisited_names_check.setChecked(config.elevators.allow_unvisited_room_names)
        self.update_area_list(
            config.elevators.excluded_targets.locations,
            True,
            self._elevator_target_for_world,
            self._elevator_target_for_area,
        )
