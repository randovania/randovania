from __future__ import annotations

import typing
from typing import TYPE_CHECKING, Self

from randovania.game_description.db.resource_node import ResourceNode

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node import Node, NodeContext
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.requirements.requirement_set import RequirementSet
    from randovania.generator.filler.filler_configuration import FillerConfiguration
    from randovania.resolver.state import State


class GeneratorReach:
    @classmethod
    def reach_from_state(
        cls,
        game: GameDescription,
        initial_state: State,
        filler_config: FillerConfiguration,
    ) -> Self:
        raise NotImplementedError

    # Game related methods

    @property
    def game(self) -> GameDescription:
        raise NotImplementedError

    def victory_condition_satisfied(self) -> bool:
        context = self.state.node_context()
        return self.game.victory_condition_as_set(context).satisfied(context, self.state.health_for_damage_requirements)

    @property
    def iterate_nodes(self) -> Iterator[Node]:
        yield from self.game.region_list.iterate_nodes()

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

    def act_on(self, node: ResourceNode) -> None:
        raise NotImplementedError

    def node_context(self) -> NodeContext:
        return self.state.node_context()

    # Node stuff

    def is_reachable_node(self, node: Node) -> bool:
        raise NotImplementedError

    @property
    def connected_nodes(self) -> Iterator[Node]:
        """
        An iterator of all nodes there's an path from the reach's starting point. Similar to is_reachable_node
        :return:
        """
        raise NotImplementedError

    @property
    def nodes(self) -> Iterator[Node]:
        raise NotImplementedError

    @property
    def safe_nodes(self) -> Iterator[Node]:
        raise NotImplementedError

    @property
    def safe_uncollected_resource_nodes(self) -> Iterator[Node]:
        context = self.node_context()
        for node in self.safe_nodes:
            if node.is_resource_node:
                res = typing.cast(ResourceNode, node)
                if res.should_collect(context) and res.requirement_to_collect().satisfied(
                    context, self.state.health_for_damage_requirements
                ):
                    yield res

    def is_safe_node(self, node: Node) -> bool:
        raise NotImplementedError

    def unreachable_nodes_with_requirements(self) -> dict[Node, RequirementSet]:
        raise NotImplementedError

    @property
    def filler_config(self) -> FillerConfiguration:
        raise NotImplementedError
