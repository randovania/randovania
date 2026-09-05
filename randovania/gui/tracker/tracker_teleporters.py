from __future__ import annotations

import collections
from typing import TYPE_CHECKING, Self, override

from PySide6 import QtCore, QtWidgets

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.common import elevators
from randovania.gui.tracker.tracker_component import TrackerComponent
from randovania.layout.lib.teleporters import TeleporterConfiguration, TeleporterShuffleMode

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.graph.state import State
    from randovania.gui.tracker.tracker_component import TrackerComponentSetup


class TrackerTeleporters(TrackerComponent):
    """Lets the user say where each shuffled teleporter leads to."""

    dock_area = QtCore.Qt.DockWidgetArea.LeftDockWidgetArea

    _teleporter_id_to_combo: dict[NodeIdentifier, QtWidgets.QComboBox]

    @classmethod
    @override
    def create_for(cls, setup: TrackerComponentSetup) -> Self | None:
        if not hasattr(setup.configuration, "teleporters"):
            return None

        teleporters_config = getattr(setup.configuration, "teleporters")
        assert isinstance(teleporters_config, TeleporterConfiguration)

        return cls(setup.game_description, teleporters_config)

    def __init__(self, game_description: GameDescription, teleporters_config: TeleporterConfiguration) -> None:
        super().__init__()
        self.game_description = game_description
        self._teleporter_id_to_combo = {}

        self.setWindowTitle("Teleporters")

        self.root_widget = QtWidgets.QScrollArea()
        self.root_widget.setWidgetResizable(True)
        self.setWidget(self.root_widget)

        self.scroll_contents = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_contents)
        self.root_widget.setWidget(self.scroll_contents)

        region_list = game_description.region_list
        nodes_by_region: dict[str, list[DockNode]] = collections.defaultdict(list)

        targets = {}
        teleporter_dock_types = game_description.dock_type_database.all_teleporter_dock_types
        for region, area, node in region_list.all_regions_areas_nodes:
            if isinstance(node, DockNode) and node.dock_type in teleporter_dock_types:
                nodes_by_region[region.name].append(node)
                targets[elevators.get_elevator_or_area_name(node, True)] = node.identifier

        if teleporters_config.mode == TeleporterShuffleMode.ONE_WAY_ANYTHING:
            targets = {}
            for region in region_list.regions:
                for area in region.areas:
                    if area.has_start_node():
                        targets[f"{region.name} - {area.name}"] = area.get_start_nodes()[0].identifier

        combo_targets = sorted(targets.items(), key=lambda it: it[0])

        for region_name in sorted(nodes_by_region.keys()):
            nodes = nodes_by_region[region_name]
            nodes_locations = [node.identifier for node in nodes]
            nodes_names = [
                elevators.get_elevator_or_area_name(game_description.node_by_identifier(location), False)
                for location in nodes_locations
            ]

            group = QtWidgets.QGroupBox(self.scroll_contents)
            group.setTitle(region_name)
            self.scroll_layout.addWidget(group)
            layout = QtWidgets.QGridLayout(group)

            for i, (node, location, name) in enumerate(
                sorted(zip(nodes, nodes_locations, nodes_names), key=lambda it: it[2])
            ):
                node_name = QtWidgets.QLabel(group)
                node_name.setText(name)
                node_name.setWordWrap(True)
                node_name.setMinimumWidth(75)
                layout.addWidget(node_name, i, 0)

                combo = QtWidgets.QComboBox(group)
                if teleporters_config.is_vanilla:
                    combo.addItem("Vanilla", node.default_connection)
                    combo.setEnabled(False)
                else:
                    combo.addItem("Undefined", None)
                    for target_name, connection in combo_targets:
                        combo.addItem(target_name, connection)

                combo.setMinimumContentsLength(11)
                combo.currentIndexChanged.connect(self.StateChanged)
                self._teleporter_id_to_combo[node.identifier] = combo
                layout.addWidget(combo, i, 1)

        self.scroll_layout.addStretch()

    # Tracker Component

    @override
    def reset(self) -> None:
        for combo in self._teleporter_id_to_combo.values():
            combo.setCurrentIndex(0)

    @override
    def decode_persisted_state(self, previous_state: dict) -> dict[NodeIdentifier, NodeIdentifier | None] | None:
        try:
            teleporters: dict[NodeIdentifier, NodeIdentifier | None] = {
                NodeIdentifier.from_json(item["teleporter"]): (
                    NodeIdentifier.from_json(item["data"]) if item["data"] is not None else None
                )
                for item in previous_state["teleporters"]
            }
            for teleporter, node_location in teleporters.items():
                if teleporter not in self._teleporter_id_to_combo:
                    return None
                if node_location is not None:
                    # check if destination exists
                    self.game_description.region_list.node_by_identifier(node_location)
        except (KeyError, AttributeError):
            return None

        return teleporters

    @override
    def apply_previous_state(self, previous_state: dict[NodeIdentifier, NodeIdentifier | None]) -> None:
        for teleporter, node_location in previous_state.items():
            combo = self._teleporter_id_to_combo[teleporter]
            if node_location is None:
                combo.setCurrentIndex(0)
                continue
            for i in range(combo.count()):
                if node_location == combo.itemData(i):
                    combo.setCurrentIndex(i)
                    break

    @override
    def persist_current_state(self) -> dict:
        return {
            "teleporters": [
                {
                    "teleporter": teleporter.as_json,
                    "data": combo.currentData().as_json if combo.currentIndex() > 0 else None,
                }
                for teleporter, combo in self._teleporter_id_to_combo.items()
            ],
        }

    @override
    def fill_into_state(self, state: State) -> None:
        region_list = self.game_description.region_list

        state.patches = state.patches.assign_dock_connections(
            (
                region_list.typed_node_by_identifier(teleporter, DockNode),
                # TODO If there is no `default_node` anymore, what would be the replacement?
                region_list.node_by_identifier(combo.currentData()),
            )
            for teleporter, combo in self._teleporter_id_to_combo.items()
            if combo.currentData() is not None
        )
