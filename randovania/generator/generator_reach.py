from __future__ import annotations

from typing import TYPE_CHECKING, Self

from randovania.game_description.game_description import GameDescription

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node import NodeContext, NodeIndex
    from randovania.game_description.db.resource_node import ResourceNode
    from randovania.game_description.requirements.requirement_set import RequirementSet
    from randovania.generator.filler.filler_configuration import FillerConfiguration
    from randovania.graph.state import GraphOrClassicNode, State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode


class GeneratorReach:
    @classmethod
    def reach_from_state(
        cls,
        game: GameDescription | WorldGraph,
        initial_state: State,
        filler_config: FillerConfiguration,
    ) -> Self:
        raise NotImplementedError

    # Game related methods

    @property
    def game(self) -> GameDescription | WorldGraph:
        raise NotImplementedError

    def victory_condition_satisfied(self) -> bool:
        context = self.state.node_context()
        return self.game.victory_condition_as_set(context).satisfied(context, self.state.health_for_damage_requirements)

    @property
    def iterate_nodes(self) -> Iterator[GraphOrClassicNode]:
        if isinstance(self.game, GameDescription):
            return self.game.region_list.iterate_nodes()
        else:
            return iter(self.game.nodes)

    # ASDF

    @property
    def state(self) -> State:
        raise NotImplementedError

    def advance_to(
        self,
        new_state: State,
        is_safe: bool = False,
    ) -> None:
        raise NotImplementedError

    def act_on(self, node: ResourceNode | WorldGraphNode) -> None:
        raise NotImplementedError

    def node_context(self) -> NodeContext:
        return self.state.node_context()

    # Node stuff

    def is_reachable_node(self, node: GraphOrClassicNode) -> bool:
        raise NotImplementedError

    @property
    def connected_nodes(self) -> Iterator[GraphOrClassicNode]:
        """
        An iterator of all nodes there's an path from the reach's starting point. Similar to is_reachable_node
        :return:
        """
        raise NotImplementedError

    @property
    def nodes(self) -> Iterator[GraphOrClassicNode]:
        raise NotImplementedError

    @property
    def safe_nodes(self) -> Iterator[GraphOrClassicNode]:
        raise NotImplementedError

    @property
    def safe_nodes_index_set(self) -> set[int]:
        return {node.node_index for node in self.safe_nodes}

    def is_safe_node(self, node: GraphOrClassicNode) -> bool:
        raise NotImplementedError

    def unreachable_nodes_with_requirements(self) -> dict[NodeIndex, RequirementSet]:
        raise NotImplementedError

    @property
    def filler_config(self) -> FillerConfiguration:
        raise NotImplementedError

    def set_of_reachable_node_indices(self) -> set[int]:
        raise NotImplementedError
