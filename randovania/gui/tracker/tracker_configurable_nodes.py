from __future__ import annotations

import typing
from typing import TYPE_CHECKING, Self, override

from PySide6 import QtCore, QtWidgets

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.graph.graph_requirement import GraphRequirementSet
from randovania.graph.world_graph import WorldGraphNodeConnection
from randovania.gui.tracker.tracker_component import TrackerComponent

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.graph.world_graph import WorldGraph
    from randovania.gui.tracker.tracker_component import TrackerComponentSetup
    from randovania.layout.base.base_configuration import BaseConfiguration


class TrackerConfigurableNodes(TrackerComponent):
    """Lets the user configure nodes whose requirement isn't known until played, such as translator gates."""

    dock_area = QtCore.Qt.DockWidgetArea.LeftDockWidgetArea

    _config_node_to_combo: dict[NodeIdentifier, QtWidgets.QComboBox]

    @classmethod
    @override
    def create_for(cls, setup: TrackerComponentSetup) -> Self | None:
        has_config_nodes = any(True for _ in setup.game_description.region_list.iterate_nodes_of_type(ConfigurableNode))
        if not has_config_nodes:
            return None

        return cls(setup.game_description, setup.graph, setup.configuration)

    def __init__(self, game_description: GameDescription, graph: WorldGraph, configuration: BaseConfiguration) -> None:
        super().__init__()
        self.game_description = game_description
        self.graph = graph
        self.game_configuration = configuration
        self._config_node_to_combo = {}

        config_node_bootstrap = game_description.game.generator.bootstrap.configurable_nodes
        self.setWindowTitle(config_node_bootstrap.category_name)

        self.root_widget = QtWidgets.QScrollArea()
        self.root_widget.setWidgetResizable(True)
        self.setWidget(self.root_widget)

        self.scroll_contents = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QGridLayout(self.scroll_contents)
        self.root_widget.setWidget(self.scroll_contents)

        config_nodes = {
            f"{area.name} ({node.name})": node
            for region, area, node in game_description.region_list.all_regions_areas_nodes
            if isinstance(node, ConfigurableNode)
        }

        for i, (gate_name, gate) in enumerate(sorted(config_nodes.items(), key=lambda it: it[0])):
            node_name = QtWidgets.QLabel(self.scroll_contents)
            node_name.setText(gate_name)
            self.scroll_layout.addWidget(node_name, i, 0)

            combo = QtWidgets.QComboBox(self.scroll_contents)

            options = config_node_bootstrap.get_options(configuration, game_description, gate)
            for name, value in options.items():
                combo.addItem(name, value)
            combo.setEnabled(len(options) > 1)

            combo.currentIndexChanged.connect(self.StateChanged)
            self._config_node_to_combo[gate.identifier] = combo
            self.scroll_layout.addWidget(combo, i, 1)

    # Tracker Component

    @override
    def reset(self) -> None:
        for combo in self._config_node_to_combo.values():
            combo.setCurrentIndex(0)

    @override
    def decode_persisted_state(self, previous_state: dict) -> dict[NodeIdentifier, typing.Any | None] | None:
        config_bootstrap = self.game_description.game.generator.bootstrap.configurable_nodes
        try:
            return {
                NodeIdentifier.from_string(identifier): (
                    config_bootstrap.json_to_config_data(value) if value is not None else None
                )
                for identifier, value in previous_state["configurable_nodes"].items()
            }
        except (KeyError, AttributeError):
            return None

    @override
    def apply_previous_state(self, previous_state: dict[NodeIdentifier, typing.Any | None]) -> None:
        for identifier, requirement in previous_state.items():
            combo = self._config_node_to_combo[identifier]
            for i in range(combo.count()):
                if requirement == combo.itemData(i):
                    combo.setCurrentIndex(i)
                    break

    @override
    def persist_current_state(self) -> dict:
        config_bootstrap = self.game_description.game.generator.bootstrap.configurable_nodes
        return {
            "configurable_nodes": {
                node_id.as_string: config_bootstrap.config_data_to_json(combo.currentData())
                if combo.currentIndex() > 0
                else None
                for node_id, combo in self._config_node_to_combo.items()
            },
        }

    @override
    def update_graph(self) -> None:
        game = self.game_description

        for configurable_node in game.region_list.iterate_nodes_of_type(ConfigurableNode):
            combo = self._config_node_to_combo[configurable_node.identifier]
            node_config: typing.Any | None = combo.currentData()

            if node_config is None:
                requirement = None
            else:
                db_requirement = game.game.generator.bootstrap.configurable_nodes.get_requirement(
                    self.game_configuration,
                    game,
                    node_config,
                )
                requirement = self.graph.converter.convert_db(db_requirement)

            def _get_requirement(
                conn: WorldGraphNodeConnection, requirement: GraphRequirementSet | None = requirement
            ) -> GraphRequirementSet:
                if requirement is None:
                    return GraphRequirementSet.impossible()
                return conn.requirement_without_leaving.copy_then_and_with_set(requirement)

            graph_node = self.graph.original_to_node[configurable_node.node_index]
            graph_node.connections = [
                WorldGraphNodeConnection(
                    conn.target,
                    _get_requirement(conn),
                    conn.requirement_without_leaving,
                    conn.requirement_without_leaving,
                )
                for conn in graph_node.connections
            ]
