from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.games.dread.gui.generated.preset_teleporters_dread_ui import (
    Ui_PresetTeleportersDread,
)
from randovania.gui.lib import signal_handling
from randovania.gui.lib.node_list_helper import NodeListHelper
from randovania.gui.preset_settings.preset_teleporter_tab import PresetTeleporterTab
from randovania.layout.lib.teleporters import (
    TeleporterConfiguration,
    TeleporterList,
    TeleporterShuffleMode,
)

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.games.dread.layout.dread_configuration import DreadConfiguration
    from randovania.layout.preset import Preset


class PresetTeleportersDread(PresetTeleporterTab, Ui_PresetTeleportersDread, NodeListHelper):
    teleporter_mode_to_description = {
        TeleporterShuffleMode.VANILLA: "All transporters are connected to where they do in the original game.",
        TeleporterShuffleMode.TWO_WAY_RANDOMIZED: (
            "After taking a transporter, the transporter in the room you are in will bring you back to where you were. "
            "An transporter will never connect to another in the same region. "
            "This is the only setting that guarantees all regions are reachable."
        ),
        TeleporterShuffleMode.TWO_WAY_UNCHECKED: (
            "After taking an transporter, the transporter in the room you are in"
            " will bring you back to where you were."
        ),
        TeleporterShuffleMode.ONE_WAY_TELEPORTER: (
            "All transporters bring you to an elevator room, but going backwards can go somewhere else. "
            "All rooms are used as a destination exactly once, causing all transporters to be separated into loops."
        ),
        TeleporterShuffleMode.ONE_WAY_TELEPORTER_REPLACEMENT: (
            "All transporters bring you to an elevator room, but going backwards can go somewhere else. "
            "Rooms can be used as a destination multiple times, causing transporter which you can possibly"
            " not come back to."
        ),
    }

    def setup_ui(self):
        self.setupUi(self)

    @classmethod
    def tab_title(cls) -> str:
        return "Transporters"

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

        for location in sorted(locations, key=lambda loc: (0, checks[loc].text())):
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

    def on_preset_changed(self, preset: Preset):
        config: DreadConfiguration = preset.configuration
        config_teleporters: TeleporterConfiguration = config.teleporters

        descriptions = [
            "<p>Controls where each transporter connects to.</p>",
            f" {self.teleporter_mode_to_description[config_teleporters.mode]}</p>",
        ]
        self.teleporters_description_label.setText("".join(descriptions))

        signal_handling.set_combo_with_value(self.teleporters_combo, config_teleporters.mode)
        can_shuffle_source = config_teleporters.mode not in (TeleporterShuffleMode.VANILLA,)
        can_shuffle_target = config_teleporters.mode not in (
            TeleporterShuffleMode.VANILLA,
            TeleporterShuffleMode.TWO_WAY_RANDOMIZED,
            TeleporterShuffleMode.TWO_WAY_UNCHECKED,
        )

        for origin, destination in self._teleporters_source_destination.items():
            origin_check = self._teleporters_source_for_location[origin]
            dest_check = self._teleporters_source_for_location.get(destination)

            assert origin_check or dest_check

            origin_check.setEnabled(can_shuffle_source)
            origin_check.setChecked(origin not in config_teleporters.excluded_teleporters.locations)

            if dest_check is None:
                if not can_shuffle_target:
                    origin_check.setEnabled(False)
                continue

            dest_check.setEnabled(can_shuffle_target)
            if can_shuffle_target:
                dest_check.setChecked(destination not in config_teleporters.excluded_teleporters.locations)
            else:
                dest_check.setChecked(origin_check.isChecked())

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
