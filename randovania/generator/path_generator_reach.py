import collections
import copy
import dataclasses
import math
from typing import Iterator, Optional, Dict, List, Tuple

from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements import RequirementSet, Requirement, ResourceRequirement, RequirementAnd, \
    RequirementList
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.world.node import Node, ResourceNode, EventNode
from randovania.generator.generator_reach import GeneratorReach
from randovania.resolver.state import State


def _extra_requirement_for_node(game: GameDescription, node: Node) -> Optional[Requirement]:
    extra_requirement = None

    if node.is_resource_node:
        resource_node: ResourceNode = node

        node_resource = resource_node.resource()
        if node_resource in game.dangerous_resources:
            extra_requirement = ResourceRequirement(node_resource, 1, False)

    return extra_requirement


@dataclasses.dataclass(frozen=True)
class Path:
    """
    Represents a path taken in the game graph.

    Attributes:
        - cost: How many steps needed an additional set of resources to be taken.
        - nodes: The path itself
        - resources: The resources needed to complete the path, combined with the resources available at the start.
        - damage: The damage taken at the end of the path
        - requirement: The additional item requirements for completing this path
        - timed_events: After taking an EventNode, how many nodes the can still go before finding an use for that event
    """
    cost: int
    nodes: Tuple[Node, ...]
    resources: CurrentResources
    damage: int
    requirement: RequirementList
    timed_events: Dict[SimpleResourceInfo, int]

    @classmethod
    def new_at(cls, state: State) -> "Path":
        return Path(
            cost=0,
            nodes=(state.node,),
            resources=state.resources,
            damage=state.maximum_energy - state.energy,
            requirement=RequirementList([]),
            timed_events={},
        )

    def advance_to(
            self,
            node: Node,
            requirement: RequirementList,
            db: ResourceDatabase,
    ) -> Optional["Path"]:

        events = copy.copy(self.timed_events)

        result = []
        for item in requirement.values():
            if item.resource in events:
                events.pop(item.resource)

            if item.is_damage:
                continue
            elif not item.satisfied(self.resources, 0, db):
                if item.resource.resource_type == ResourceType.ITEM and not item.negate:
                    result.append(item)
                else:
                    return None

        for event, nodes_left in events.items():
            if nodes_left > 0:
                events[event] = nodes_left - 1
            else:
                # No more nodes for this event, abort this line
                return None

        filtered = RequirementList(result)
        damage = requirement.damage(self.resources, db)

        new_cost = self.cost
        if filtered.items - self.requirement.items:
            new_cost += 1

        resources = self.resources
        if filtered.items:
            resources = copy.copy(resources)
            for item in filtered.values():
                resources[item.resource] = max(resources.get(item.resource, 0), item.amount)

        if isinstance(node, EventNode) and resources.get(node.resource(), 0) == 0:
            # TODO: maybe this shouldn't be just EventNode. There's things like PlayerShipNode and Blast Shields.
            if not filtered.items:
                resources = copy.copy(resources)
            events[node.resource()] = 10  # TODO: max distance should depend on the event and be pre-calculated
            resources[node.resource()] = 1

        return Path(
            new_cost,
            self.nodes + (node,),
            resources,
            self.damage + damage,
            self.requirement.union(filtered),
            events,
        )

    def is_worse_or_equivalent_than(self, other: "Path") -> bool:
        """
        Tests if this equivalent to another path in all aspects or worse in at least one.
        """
        return (  # Paths with less cost is always preferable
                # TODO: is it? a higher cost implies into bigger requirement
                self.cost >= other.cost

                # Needing more damage is worse.
                # TODO: handle using healing sources badly (aka: taking a 100 heal when at 50 dmg)
                and self.damage >= other.damage

                # Needing more items is worse, but a different list isn't (aka: set A contains set B?)
                and self.requirement.items >= other.requirement.items

                # Again needing more items is worse. TODO: consider less events worse?
                and all(q >= other.resources.get(r, 0) for r, q in self.resources.items()
                        if r.resource_type == ResourceType.ITEM)

                # Having less time left for an event is worse. But having missing time left means the event was reached,
                # and that's better!
                and all(time <= other.timed_events.get(event, math.inf)
                        if other.resources.get(event, 0) > 0 else False
                        for event, time in self.timed_events.items())

                # All else equal, a path that takes a longer path is worse.
                and len(self.nodes) >= len(other.nodes)
        )

    def pretty_print(self):
        path = " -> ".join(node.name for node in self.nodes)
        print(
            f"> Cost: {self.cost}"
            f"; Dmg: {self.damage}"
            f"; Reqs: {self.requirement}"
            f"; Events: {sorted((k.long_name, t) for k, t in self.timed_events.items())}"
            f"\n* {path}\n")


class PathGeneratorReach(GeneratorReach):
    _state: State
    _game: GameDescription

    def __deepcopy__(self, memodict):
        reach = PathGeneratorReach(
            self._game,
            self._state,
        )
        return reach

    def __init__(self,
                 game: GameDescription,
                 state: State,
                 ):

        self._game = game
        self._state = state
        self._all_paths = None

    @property
    def game(self) -> GameDescription:
        return self._game

    @classmethod
    def reach_from_state(cls,
                         game: GameDescription,
                         initial_state: State,
                         ) -> "GeneratorReach":

        reach = cls(game, initial_state)
        reach._explore()
        return reach

    def _potential_nodes_from(self, node: Node) -> Iterator[Tuple[Node, RequirementSet]]:
        extra_requirement = _extra_requirement_for_node(self._game, node)
        requirement_to_leave = node.requirement_to_leave(self._state.patches, self._state.resources)

        for target_node, requirement in self._game.world_list.potential_nodes_from(node, self.state.patches):
            if target_node is None:
                continue

            if requirement_to_leave != Requirement.trivial():
                requirement = RequirementAnd([requirement, requirement_to_leave])

            if extra_requirement is not None:
                requirement = RequirementAnd([requirement, extra_requirement])

            yield target_node, requirement.as_set(self._state.resource_database)

    def _explore(self):
        db = self._state.resource_database
        first_path = Path.new_at(self._state)

        existing_paths: Dict[Node, List[Path]] = collections.defaultdict(list)
        paths_to_examine = [first_path]

        while paths_to_examine:
            path = paths_to_examine.pop(0)

            existing = existing_paths[path.nodes[-1]]
            if any(path.is_worse_or_equivalent_than(e) for e in existing):
                continue

            worse = [p for p in existing if p.is_worse_or_equivalent_than(path)]
            for p in worse:
                existing.remove(p)
            existing.append(path)
            # path.pretty_print()

            for target_node, requirement in self._potential_nodes_from(path.nodes[-1]):
                for req_list in requirement.alternatives:
                    new_path = path.advance_to(target_node, req_list, db)
                    if new_path is None or len(new_path.nodes) > 15:
                        continue
                    paths_to_examine.append(new_path)

        for node, paths in existing_paths.items():
            print("\n>> {}:".format(self._game.world_list.node_name(node, True)))
            for path in paths:
                # print("; ".join([f"{i}: {path.is_worse_than(p)}" for i, p in enumerate(paths)]))
                path.pretty_print()

        self._all_paths = existing_paths

    @property
    def state(self) -> State:
        return self._state

    def advance_to(self, new_state: State,
                   is_safe: bool = False,
                   ) -> None:
        self._state = new_state
        self._explore()

    def act_on(self, node: ResourceNode) -> None:
        new_state = self.state.act_on_node(node)
        self.advance_to(new_state)

    # Node stuff

    def is_reachable_node(self, node: Node) -> bool:
        return any(
            path.cost == 0
            for path in self._all_paths.get(node, [])
        )

    @property
    def connected_nodes(self) -> Iterator[Node]:
        """
        An iterator of all nodes there's an path from the reach's starting point. Similar to is_reachable_node
        :return:
        """
        for node in self.all_nodes:
            if self.is_reachable_node(node):
                yield node

    @property
    def nodes(self) -> Iterator[Node]:
        raise NotImplementedError()

    @property
    def safe_nodes(self) -> Iterator[Node]:
        raise NotImplementedError()

    def is_safe_node(self, node: Node) -> bool:
        raise NotImplementedError()

    def unreachable_nodes_with_requirements(self) -> Dict[Node, RequirementSet]:
        raise NotImplementedError()
