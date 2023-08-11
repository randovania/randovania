from __future__ import annotations

import copy
import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.games.prime2.exporter.patch_data_factory import should_keep_elevator_sounds
from randovania.gui.generated.preset_elevators_prime2_ui import Ui_PresetElevatorsPrime2
from randovania.gui.lib import signal_handling
from randovania.gui.lib.node_list_helper import NodeListHelper
from randovania.gui.preset_settings.preset_transporter_tab import PresetTransporterTab
from randovania.layout.lib.teleporters import (
    TeleporterList,
    TeleporterShuffleMode,
)
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_description import GameDescription
    from randovania.games.common.prime_family.layout.lib.prime_trilogy_teleporters import (
        PrimeTrilogyTeleporterConfiguration,
    )
    from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetElevatorsPrime2(PresetTransporterTab, Ui_PresetElevatorsPrime2, NodeListHelper):
    custom_weights = {
            "Great Temple": 0,
            "Agon Wastes": 1,
            "Torvus Bog": 2,
            "Sanctuary Fortress": 3,
            "Temple Grounds": 5,
        }
    compatible_modes = list(enum_lib.iterate_enum(TeleporterShuffleMode))

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        signal_handling.on_checked(self.skip_final_bosses_check, self._update_require_final_bosses)
        signal_handling.on_checked(self.teleporters_allow_unvisited_names_check, self._update_allow_unvisited_names)

    def setup_ui(self):
        self.setupUi(self)

    @classmethod
    def tab_title(cls) -> str:
        return "Elevators"

    def _create_source_teleporters(self):
        row = 0
        region_list = self.game_description.region_list

        locations = TeleporterList.nodes_list(self.game_enum)
        node_identifiers: dict[NodeIdentifier, Area] = {
            loc: region_list.area_by_area_location(loc.area_location)
            for loc in locations
        }
        checks: dict[NodeIdentifier, QtWidgets.QCheckBox] = {
            loc: self._create_check_for_source_teleporters(loc) for loc in locations
        }
        self._teleporters_source_for_location = copy.copy(checks)
        self._teleporters_source_destination = {}

        for location in sorted(locations,
                               key=lambda loc: (self.custom_weights.get(loc.area_location.region_name, 0),
                                                checks[loc].text())):
            if location not in checks:
                continue

            self.teleporters_source_layout.addWidget(checks.pop(location), row, 1)

            other_locations = [
                node.default_connection
                for node in node_identifiers[location].nodes
                if isinstance(node, DockNode) and node.dock_type in self.teleporter_types
                and region_list.identifier_for_node(node) == location
            ]
            assert len(other_locations) == 1
            teleporters_in_target = [
                region_list.identifier_for_node(node)
                for node in region_list.area_by_area_location(other_locations[0]).nodes
                if isinstance(node, DockNode) and node.dock_type in self.teleporter_types
            ]

            self._teleporters_source_destination[location] = None

            if teleporters_in_target:
                other_loc = teleporters_in_target[0]

                if other_loc in checks:
                    self.teleporters_source_layout.addWidget(checks.pop(other_loc), row, 2)
                    self._teleporters_source_destination[location] = other_loc

            row += 1

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


    def on_preset_changed(self, preset: Preset):
        config: EchoesConfiguration = preset.configuration
        config_elevators: PrimeTrilogyTeleporterConfiguration = config.elevators

        descriptions = [
            "<p>Controls where each elevator connects to.</p>",
            f'<p><span style="font-weight:600;">{config_elevators.mode.long_name}</span>:'
            f' {config_elevators.mode.description}</p>',
        ]
        self.teleporters_description_label.setText("".join(descriptions))

        signal_handling.set_combo_with_value(self.teleporters_combo, config_elevators.mode)
        can_shuffle_source = config_elevators.mode not in (TeleporterShuffleMode.VANILLA,
                                                           TeleporterShuffleMode.ECHOES_SHUFFLED)
        can_shuffle_target = config_elevators.mode not in (TeleporterShuffleMode.VANILLA,
                                                           TeleporterShuffleMode.ECHOES_SHUFFLED,
                                                           TeleporterShuffleMode.TWO_WAY_RANDOMIZED,
                                                           TeleporterShuffleMode.TWO_WAY_UNCHECKED)
        static_nodes = set(config_elevators.static_teleporters.keys())

        for origin, destination in self._teleporters_source_destination.items():
            origin_check = self._teleporters_source_for_location[origin]
            dest_check = self._teleporters_source_for_location.get(destination)

            assert origin_check or dest_check

            is_locked = origin in static_nodes
            if not is_locked and not can_shuffle_target:
                is_locked = (destination in static_nodes) or (origin_check and not dest_check)

            origin_check.setEnabled(can_shuffle_source and not is_locked)
            origin_check.setChecked(origin not in config_elevators.excluded_teleporters.locations and not is_locked)

            origin_check.setToolTip("The destination for this teleporter is locked due to other settings."
                                    if is_locked else "")

            if dest_check is None:
                if not can_shuffle_target:
                    origin_check.setEnabled(False)
                continue

            dest_check.setEnabled(can_shuffle_target and destination not in static_nodes)
            if can_shuffle_target:
                dest_check.setChecked(destination not in config_elevators.excluded_teleporters.locations
                                      and destination not in static_nodes)
            else:
                dest_check.setChecked(origin_check.isChecked())

        sound_bug_warning = False
        sound_bug_warning = not should_keep_elevator_sounds(config)
        self.teleporters_allow_unvisited_names_check.setChecked(config_elevators.allow_unvisited_room_names)
        self.teleporters_help_sound_bug_label.setVisible(sound_bug_warning)
        self.skip_final_bosses_check.setChecked(config_elevators.skip_final_bosses)

        self.teleporters_source_group.setVisible(can_shuffle_source)
        self.teleporters_target_group.setVisible(config_elevators.has_shuffled_target)
        self.teleporters_target_group.setEnabled(config_elevators.has_shuffled_target)
        self.update_node_list(
            config_elevators.excluded_targets.locations,
            True,
            self._teleporters_target_for_region,
            self._teleporters_target_for_area,
            self._teleporters_target_for_node,
        )
