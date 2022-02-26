import copy
import dataclasses
import functools
from typing import Dict, Optional

from PySide6 import QtWidgets, QtCore

from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.teleporter_node import TeleporterNode
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.game import RandovaniaGame
from randovania.gui.generated.preset_elevators_ui import Ui_PresetElevators
from randovania.gui.lib import common_qt_lib, signal_handling
from randovania.gui.lib.area_list_helper import AreaListHelper
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.lib.teleporters import TeleporterShuffleMode, TeleporterTargetList, TeleporterList, \
    TeleporterConfiguration
from randovania.layout.preset import Preset
from randovania.lib import enum_lib
from randovania.patching.prime import elevators


class PresetElevators(PresetTab, Ui_PresetElevators, AreaListHelper):
    _elevator_source_for_location: Dict[NodeIdentifier, QtWidgets.QCheckBox]
    _elevator_source_destination: Dict[NodeIdentifier, Optional[NodeIdentifier]]
    _elevator_target_for_world: dict[str, QtWidgets.QCheckBox]
    _elevator_target_for_area: dict[AreaIdentifier, QtWidgets.QCheckBox]

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
        elif self.game_enum != RandovaniaGame.METROID_PRIME_ECHOES:
            self.skip_final_bosses_check.setVisible(False)
            self.skip_final_bosses_label.setVisible(False)

        elif self.game_enum == RandovaniaGame.METROID_PRIME_CORRUPTION:
            self.elevators_description_label.setText(
                self.elevators_description_label.text().replace("elevator", "teleporter")
            )

    @classmethod
    def tab_title(cls) -> str:
        return "Elevators"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    @property
    def game_enum(self):
        return self.game_description.game

    def _create_check_for_source_elevator(self, location: NodeIdentifier):
        name = elevators.get_elevator_or_area_name(self.game_enum, self.game_description.world_list,
                                                   location.area_location, True)

        check = QtWidgets.QCheckBox(self.elevators_source_group)
        check.setText(name)
        check.area_location = location
        signal_handling.on_checked(check, functools.partial(self._on_elevator_source_check_changed, location))
        return check

    def _create_source_elevators(self):
        row = 0
        world_list = self.game_description.world_list

        custom_weights = {}
        if self.game_enum == RandovaniaGame.METROID_PRIME_ECHOES:
            custom_weights = {
                "Great Temple": 0,  # Great Temple
                "Agon Wastes": 1,  # Agon Wastes
                "Torvus Bog": 2,  # Torvus Bog
                "Sanctuary Fortress": 3,  # Sanctuary Fortress
                "Temple Grounds": 5,  # Temple Grounds
            }
        locations = TeleporterList.areas_list(self.game_enum)
        areas: Dict[NodeIdentifier, Area] = {
            loc: world_list.area_by_area_location(loc.area_location)
            for loc in locations
        }
        checks: Dict[NodeIdentifier, QtWidgets.QCheckBox] = {
            loc: self._create_check_for_source_elevator(loc) for loc in locations
        }
        self._elevator_source_for_location = copy.copy(checks)
        self._elevator_source_destination = {}

        for location in sorted(locations,
                               key=lambda loc: (custom_weights.get(loc.area_location.world_name, 0),
                                                checks[loc].text())):
            if location not in checks:
                continue

            self.elevators_source_layout.addWidget(checks.pop(location), row, 1)

            other_locations = [
                node.default_connection
                for node in areas[location].nodes
                if isinstance(node, TeleporterNode) and world_list.identifier_for_node(node) == location
            ]
            assert len(other_locations) == 1
            teleporters_in_target = [
                world_list.identifier_for_node(node)
                for node in world_list.area_by_area_location(other_locations[0]).nodes
                if isinstance(node, TeleporterNode)
            ]

            self._elevator_source_destination[location] = None

            if teleporters_in_target:
                other_loc = teleporters_in_target[0]

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

    def _on_elevator_source_check_changed(self, location: NodeIdentifier, checked: bool):
        with self._editor as editor:
            config = editor.layout_configuration_elevators
            editor.layout_configuration_elevators = dataclasses.replace(
                config,
                excluded_teleporters=config.excluded_teleporters.ensure_has_location(location, not checked),
            )

    def _on_elevator_target_check_changed(self, world_areas: list[AreaIdentifier], checked: bool):
        with self._editor as editor:
            config = editor.layout_configuration_elevators
            editor.layout_configuration_elevators = dataclasses.replace(
                config,
                excluded_targets=config.excluded_targets.ensure_has_locations(world_areas, not checked),
            )

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        config_elevators: TeleporterConfiguration = config.elevators

        common_qt_lib.set_combo_with_value(self.elevators_combo, config_elevators.mode)
        can_shuffle_target = config_elevators.mode not in (TeleporterShuffleMode.VANILLA,
                                                           TeleporterShuffleMode.TWO_WAY_RANDOMIZED,
                                                           TeleporterShuffleMode.TWO_WAY_UNCHECKED)
        static_areas = set(
            teleporter
            for teleporter in config_elevators.static_teleporters.keys()
        )

        for origin, destination in self._elevator_source_destination.items():
            origin_check = self._elevator_source_for_location[origin]
            dest_check = self._elevator_source_for_location.get(destination)

            assert origin_check or dest_check

            is_locked = origin in static_areas
            if not is_locked and not can_shuffle_target:
                is_locked = (destination in static_areas) or (origin_check and not dest_check)

            origin_check.setEnabled(not config_elevators.is_vanilla and not is_locked)
            origin_check.setChecked(origin not in config_elevators.excluded_teleporters.locations and not is_locked)

            origin_check.setToolTip("The destination for this teleporter is locked due to other settings."
                                    if is_locked else "")

            if dest_check is None:
                if not can_shuffle_target:
                    origin_check.setEnabled(False)
                continue

            dest_check.setEnabled(can_shuffle_target and destination not in static_areas)
            if can_shuffle_target:
                dest_check.setChecked(destination not in config_elevators.excluded_teleporters.locations
                                      and destination not in static_areas)
            else:
                dest_check.setChecked(origin_check.isChecked())

        self.elevators_target_group.setEnabled(config_elevators.has_shuffled_target)
        self.skip_final_bosses_check.setChecked(config_elevators.skip_final_bosses)
        self.elevators_allow_unvisited_names_check.setChecked(config_elevators.allow_unvisited_room_names)
        self.update_area_list(
            config_elevators.excluded_targets.locations,
            True,
            self._elevator_target_for_world,
            self._elevator_target_for_area,
        )
