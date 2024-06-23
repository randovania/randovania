from __future__ import annotations

import copy
import dataclasses
from typing import TYPE_CHECKING

import randovania
from randovania.game_description.db.dock_node import DockNode
from randovania.games.prime2.exporter.patch_data_factory import (
    should_keep_elevator_sounds,
)
from randovania.games.prime2.gui.generated.preset_teleporters_prime2_ui import (
    Ui_PresetTeleportersPrime2,
)
from randovania.gui.lib import signal_handling
from randovania.gui.lib.node_list_helper import NodeListHelper
from randovania.gui.preset_settings.preset_teleporter_tab import PresetTeleporterTab
from randovania.layout.lib.teleporters import (
    TeleporterList,
    TeleporterShuffleMode,
)

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


class PresetTeleportersPrime2(PresetTeleporterTab, Ui_PresetTeleportersPrime2, NodeListHelper):
    custom_weights = {
        "Great Temple": 0,
        "Agon Wastes": 1,
        "Torvus Bog": 2,
        "Sanctuary Fortress": 3,
        "Temple Grounds": 5,
    }
    teleporter_mode_to_description = {
        TeleporterShuffleMode.VANILLA: "All elevators are connected to where they do in the original game.",
        TeleporterShuffleMode.TWO_WAY_RANDOMIZED: (
            "After taking an elevator, the elevator in the room you are in will bring you back to where you were. "
            "An elevator will never connect to another in the same region. "
            "This is the only setting that guarantees all regions are reachable."
        ),
        TeleporterShuffleMode.TWO_WAY_UNCHECKED: (
            "after taking an elevator, the elevator in the room you are in will bring you back to where you were."
        ),
        TeleporterShuffleMode.ONE_WAY_TELEPORTER: (
            "All elevators bring you to an elevator room, but going backwards can go somewhere else. "
            "All rooms are used as a destination exactly once, causing all elevators to be separated into loops."
        ),
        TeleporterShuffleMode.ONE_WAY_TELEPORTER_REPLACEMENT: (
            "All elevators bring you to an elevator room, but going backwards can go somewhere else. "
            "Rooms can be used as a destination multiple times, causing elevators which you can possibly"
            " not come back to."
        ),
        TeleporterShuffleMode.ONE_WAY_ANYTHING: "Elevators are connected to any room from the game.",
        TeleporterShuffleMode.ECHOES_SHUFFLED: (
            "Keeps Temple Grounds in place, shuffling the locations of all other regions with each other."
            f'<p><img src="{randovania.get_data_path()}/gui_assets/echoes_elevator_map.png" width=450/></p>'
        ),
    }

    def __init__(
        self,
        editor: PresetEditor,
        game_description: GameDescription,
        window_manager: WindowManager,
    ):
        super().__init__(editor, game_description, window_manager)
        signal_handling.on_checked(self.skip_final_bosses_check, self._update_require_final_bosses)
        signal_handling.on_checked(
            self.teleporters_allow_unvisited_names_check,
            self._update_allow_unvisited_names,
        )

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
            loc: region_list.area_by_area_location(loc.area_identifier) for loc in locations
        }
        checks: dict[NodeIdentifier, QtWidgets.QCheckBox] = {
            loc: self._create_check_for_source_teleporters(loc) for loc in locations
        }
        self._teleporters_source_for_location = copy.copy(checks)
        self._teleporters_source_destination = {}

        for location in sorted(
            locations,
            key=lambda loc: (
                self.custom_weights.get(loc.area_identifier.region, 0),
                checks[loc].text(),
            ),
        ):
            if location not in checks:
                continue

            self.teleporters_source_layout.addWidget(checks.pop(location), row, 1)

            other_locations = [
                node.default_connection
                for node in node_identifiers[location].nodes
                if isinstance(node, DockNode)
                and node.dock_type in self.teleporter_types
                and node.identifier == location
            ]
            assert len(other_locations) == 1
            teleporters_in_target = [
                node.identifier
                for node in region_list.area_by_area_location(other_locations[0].area_identifier).nodes
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
            editor.layout_configuration_teleporters = dataclasses.replace(
                editor.layout_configuration_teleporters,
                skip_final_bosses=checked,
            )

    def _update_allow_unvisited_names(self, checked: bool):
        with self._editor as editor:
            editor.layout_configuration_teleporters = dataclasses.replace(
                editor.layout_configuration_teleporters,
                allow_unvisited_room_names=checked,
            )

    def on_preset_changed(self, preset: Preset):
        config: EchoesConfiguration = preset.configuration
        config_teleporters: PrimeTrilogyTeleporterConfiguration = config.teleporters

        descriptions = [
            "<p>Controls where each elevator connects to.</p>",
            f" {self.teleporter_mode_to_description[config_teleporters.mode]}</p>",
        ]
        self.teleporters_description_label.setText("".join(descriptions))

        signal_handling.set_combo_with_value(self.teleporters_combo, config_teleporters.mode)
        can_shuffle_source = config_teleporters.mode not in (
            TeleporterShuffleMode.VANILLA,
            TeleporterShuffleMode.ECHOES_SHUFFLED,
        )
        can_shuffle_target = config_teleporters.mode not in (
            TeleporterShuffleMode.VANILLA,
            TeleporterShuffleMode.ECHOES_SHUFFLED,
            TeleporterShuffleMode.TWO_WAY_RANDOMIZED,
            TeleporterShuffleMode.TWO_WAY_UNCHECKED,
        )
        static_nodes = set(config_teleporters.static_teleporters.keys())

        for origin, destination in self._teleporters_source_destination.items():
            origin_check = self._teleporters_source_for_location[origin]
            dest_check = self._teleporters_source_for_location.get(destination)

            assert origin_check or dest_check

            is_locked = origin in static_nodes
            if not is_locked and not can_shuffle_target:
                is_locked = (destination in static_nodes) or (origin_check and not dest_check)

            origin_check.setEnabled(can_shuffle_source and not is_locked)
            origin_check.setChecked(origin not in config_teleporters.excluded_teleporters.locations and not is_locked)

            origin_check.setToolTip(
                "The destination for this teleporter is locked due to other settings." if is_locked else ""
            )

            if dest_check is None:
                if not can_shuffle_target:
                    origin_check.setEnabled(False)
                continue

            dest_check.setEnabled(can_shuffle_target and destination not in static_nodes)
            if can_shuffle_target:
                dest_check.setChecked(
                    destination not in config_teleporters.excluded_teleporters.locations
                    and destination not in static_nodes
                )
            else:
                dest_check.setChecked(origin_check.isChecked())

        sound_bug_warning = False
        sound_bug_warning = not should_keep_elevator_sounds(config)
        self.teleporters_allow_unvisited_names_check.setChecked(config_teleporters.allow_unvisited_room_names)
        self.teleporters_help_sound_bug_label.setVisible(sound_bug_warning)
        self.skip_final_bosses_check.setChecked(config_teleporters.skip_final_bosses)

        self.teleporters_source_group.setVisible(can_shuffle_source)
        self.teleporters_target_group.setVisible(config_teleporters.has_shuffled_target)
        self.teleporters_target_group.setEnabled(config_teleporters.has_shuffled_target)
        self.update_node_list(
            config_teleporters.excluded_targets.locations,
            True,
            self._teleporters_target_for_region,
            self._teleporters_target_for_area,
            self._teleporters_target_for_node,
        )
