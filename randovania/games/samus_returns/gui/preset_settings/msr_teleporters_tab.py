from __future__ import annotations

import copy
import typing
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.games.samus_returns.gui.generated.preset_teleporters_msr_ui import (
    Ui_PresetTeleportersMSR,
)
from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
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

    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetTeleportersMSR(PresetTeleporterTab, Ui_PresetTeleportersMSR, NodeListHelper):
    teleporter_mode_to_description = {
        TeleporterShuffleMode.VANILLA: "All elevators are connected to where they do in the original game.",
        TeleporterShuffleMode.TWO_WAY_RANDOMIZED: (
            "After taking a elevator, the elevator in the room you are in will bring you back to where you were. "
            "An elevator will never connect to another in the same region. "
            "This is the only non-vanilla setting which guarantees that all regions are reachable."
        ),
        TeleporterShuffleMode.TWO_WAY_UNCHECKED: (
            "After taking an elevator, the elevator in the room you are in will bring you back to where you were."
        ),
        TeleporterShuffleMode.ONE_WAY_TELEPORTER: (
            "All elevators bring you to an elevator room, but going backwards can go somewhere else. "
            "All rooms are used as a destination exactly once, causing all elevators to be separated into loops."
        ),
        TeleporterShuffleMode.ONE_WAY_TELEPORTER_REPLACEMENT: (
            "All elevators bring you to an elevator room, but going backwards can go somewhere else. "
            "Rooms can be used as a destination multiple times, causing elevator which you can possibly"
            " not come back to."
        ),
    }

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager) -> None:
        super().__init__(editor, game_description, window_manager)
        self.teleporters_line.setVisible(self.teleporters_combo.currentData() != TeleporterShuffleMode.VANILLA)

    def setup_ui(self) -> None:
        self.setupUi(self)

    def _update_teleporter_mode(self) -> None:
        super()._update_teleporter_mode()
        self.teleporters_line.setVisible(self.teleporters_combo.currentData() != TeleporterShuffleMode.VANILLA)

    @classmethod
    def tab_title(cls) -> str:
        return "Elevators"

    def _create_source_teleporters(self) -> None:
        row = 0
        region_list = self.game_description.region_list

        locations = TeleporterList.nodes_list(self.game_enum)
        checks: dict[NodeIdentifier, QtWidgets.QCheckBox] = {
            loc: self._create_check_for_source_teleporters(loc) for loc in locations
        }

        self._teleporters_source_for_location = copy.copy(checks)
        self._teleporters_source_destination: dict[NodeIdentifier, NodeIdentifier | None] = {}

        for location in sorted(locations, key=lambda loc: (0, checks[loc].text())):
            if location not in checks:
                continue

            self.teleporters_source_layout.addWidget(checks.pop(location), row, 1)

            teleporter_in_target = typing.cast(DockNode, region_list.node_by_identifier(location)).default_connection

            self._teleporters_source_destination[location] = None

            if teleporter_in_target:
                other_loc = teleporter_in_target

                if other_loc in checks:
                    self.teleporters_source_layout.addWidget(checks.pop(other_loc), row, 2)
                    self._teleporters_source_destination[location] = other_loc

            row += 1

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, MSRConfiguration)
        config_teleporters: TeleporterConfiguration = config.teleporters

        descriptions = [
            "<p>Controls where each elevator connects to.</p>",
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
            dest_check = self._teleporters_source_for_location.get(destination) if destination is not None else None

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
