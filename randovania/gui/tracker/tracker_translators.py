from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6 import QtWidgets

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.world.configurable_node import ConfigurableNode
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.layout import translator_configuration
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.gui.tracker.tracker_component import TrackerComponent

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.generator.filler.runner import PlayerPool
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.state import State


class TrackerTranslatorsWidget(TrackerComponent):
    _translator_gate_to_combo: dict[NodeIdentifier, QtWidgets.QComboBox]

    @classmethod
    def create_for(cls, player_pool: PlayerPool, configuration: BaseConfiguration,
                   ) -> TrackerTranslatorsWidget | None:
        if configuration.game != RandovaniaGame.METROID_PRIME_ECHOES:
            return None
        assert isinstance(configuration, EchoesConfiguration)
        return cls(player_pool.game, configuration)

    def __init__(self, game_description: GameDescription, configuration: EchoesConfiguration):
        super().__init__()
        self.game_description = game_description
        self.game_configuration = configuration

        self.setWindowTitle("Translators")

        self.root_widget = QtWidgets.QScrollArea()
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)
        self.root_widget.setWidgetResizable(True)
        self.setWidget(self.root_widget)

        self.scroll_contents = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QGridLayout(self.scroll_contents)
        self.root_widget.setWidget(self.scroll_contents)

        region_list = game_description.region_list
        self._translator_gate_to_combo = {}

        gates = {
            f"{area.name} ({node.name})": node.identifier
            for region, area, node in region_list.all_regions_areas_nodes
            if isinstance(node, ConfigurableNode)
        }
        translator_requirement = configuration.translator_configuration.translator_requirement

        for i, (gate_name, gate) in enumerate(sorted(gates.items(), key=lambda it: it[0])):
            node_name = QtWidgets.QLabel(self.scroll_contents)
            node_name.setText(gate_name)
            self.scroll_layout.addWidget(node_name, i, 0)

            combo = QtWidgets.QComboBox(self.scroll_contents)
            gate_requirement = translator_requirement[gate]

            if gate_requirement in (LayoutTranslatorRequirement.RANDOM,
                                    LayoutTranslatorRequirement.RANDOM_WITH_REMOVED):
                combo.addItem("Undefined", None)
                for translator in translator_configuration.ITEM_NAMES.keys():
                    combo.addItem(translator.long_name, translator)
            else:
                combo.addItem(gate_requirement.long_name, gate_requirement)
                combo.setEnabled(False)

            # combo.currentIndexChanged.connect(self.update_locations_tree_for_reachable_nodes)
            self._translator_gate_to_combo[gate] = combo
            self.scroll_layout.addWidget(combo, i, 1)

    def reset(self):
        for elevator in self._translator_gate_to_combo.values():
            elevator.setCurrentIndex(0)

    def decode_persisted_state(self, previous_state: dict) -> Any | None:
        try:
            return {
                NodeIdentifier.from_string(identifier): (LayoutTranslatorRequirement(item)
                                                         if item is not None
                                                         else None)
                for identifier, item in previous_state["configurable_nodes"].items()
            }
        except (KeyError, AttributeError):
            return None

    def apply_previous_state(self, configurable_nodes: dict[NodeIdentifier, LayoutTranslatorRequirement | None],
                             ) -> None:

        for identifier, requirement in configurable_nodes.items():
            combo = self._translator_gate_to_combo[identifier]
            for i in range(combo.count()):
                if requirement == combo.itemData(i):
                    combo.setCurrentIndex(i)
                    break

    def persist_current_state(self) -> dict:
        return {
            "configurable_nodes": {
                gate.as_string: combo.currentData().value if combo.currentIndex() > 0 else None
                for gate, combo in self._translator_gate_to_combo.items()
            },
        }

    def fill_into_state(self, state: State) -> State | None:
        for gate, item in self._translator_gate_to_combo.items():
            scan_visor = self.game_description.resource_database.get_item("Scan")

            requirement: LayoutTranslatorRequirement | None = item.currentData()
            if requirement is None:
                translator_req = Requirement.impossible()
            else:
                translator = self.game_description.resource_database.get_item(requirement.item_name)
                translator_req = ResourceRequirement.simple(translator)

            state.patches.configurable_nodes[gate] = RequirementAnd([
                ResourceRequirement.simple(scan_visor),
                translator_req,
            ])
        return state
