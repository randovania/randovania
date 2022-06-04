import collections
import copy
import dataclasses
import math
from collections.abc import Iterator
from typing import Optional

from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.world.event_node import EventNode
from randovania.game_description.world.node import Node, NodeContext
from randovania.game_description.world.resource_node import ResourceNode
from randovania.generator.generator_reach import GeneratorReach
from randovania.resolver.state import State

# Output of this module is a mapping
# from
#   resources
# to
#   tuple[ safe nodes, reachable nodes ]


PATH_GENERATOR_DEBUG = True
_empty_list = RequirementList([])


def _extra_requirement_for_node(game: GameDescription, node: Node, context: NodeContext) -> Requirement | None:
    extra_requirement = None

    if node.is_resource_node:
        assert isinstance(node, ResourceNode)
        resource_node: ResourceNode = node

        node_resource = resource_node.resource(context)
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
        - nodes_left: How many nodes can still be navigated after the cost became non-zero.
    """
    cost: int
    nodes: tuple[Node, ...]
    resources: ResourceCollection
    damage: int
    requirement: RequirementList
    timed_events: dict[SimpleResourceInfo, int]
    nodes_left: int

    @classmethod
    def new_at(cls, state: State) -> "Path":
        return Path(
            cost=0,
            nodes=(state.node,),
            resources=state.resources,
            damage=state.maximum_energy - state.energy,
            requirement=RequirementList([]),
            timed_events={},
            nodes_left=15,
        )

    def advance_to(
            self,
            node: Node,
            requirement: RequirementList,
            context: NodeContext,
    ) -> Optional["Path"]:

        events = copy.copy(self.timed_events)

        result = []
        for item in requirement.values():
            if item.resource in events:
                events.pop(item.resource)

            if item.is_damage:
                continue
            elif not item.satisfied(self.resources, 0, context.database):
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
        damage = requirement.damage(self.resources, context.database)

        new_cost = self.cost
        if filtered.has_items_not_in(self.requirement):
            new_cost += 1

        resources = self.resources
        if filtered != _empty_list:
            resources = resources.duplicate()
            for item in filtered.values():
                resources.set_resource(item.resource, max(resources[item.resource], item.amount))

        if isinstance(node, EventNode) and not resources.has_resource(node_resource := node.resource(context)):
            # TODO: maybe this shouldn't be just EventNode. There's things like PlayerShipNode and Blast Shields.
            if filtered == _empty_list:
                resources = copy.copy(resources)
            events[node_resource] = 10  # TODO: max distance should depend on the event and be pre-calculated
            resources.set_resource(node_resource, 1)

        nodes_left = self.nodes_left
        if self.cost > 0:
            nodes_left -= 1
        if nodes_left < 0:
            return None

        return Path(
            new_cost,
            self.nodes + (node,),
            resources,
            self.damage + damage,
            self.requirement.union(filtered),
            events,
            nodes_left,
        )

    def is_worse_or_equivalent_than(self, other: "Path") -> bool:
        """
        Tests if this equivalent to another path in all aspects or worse in at least one.
        """
        # Paths with less cost is always preferable
        # TODO: is it? a higher cost implies into bigger requirement
        worse_cost = self.cost >= other.cost

        # Needing more damage is worse.
        # TODO: handle using healing sources badly (aka: taking a 100 heal when at 50 dmg)
        worse_damage = self.damage >= other.damage

        # Needing more items is worse, but a different list isn't (aka: set A contains set B?)
        worse_requirement = self.requirement.contains(other.requirement)

        # Again needing more items is worse. TODO: consider less events worse?
        worse_resources = all(q >= other.resources[r] for r, q in self.resources.as_resource_gain()
                              if r.resource_type == ResourceType.ITEM)

        # Having less time left for an event is worse. But having missing time left means the event was reached,
        # and that's better!
        worse_time = all(time <= other.timed_events.get(event, math.inf)
                         if other.resources.has_resource(event) else False
                         for event, time in self.timed_events.items())

        # Having less nodes left is worse
        worse_nodes_left = self.nodes_left <= other.nodes_left

        # All else equal, a path that takes a longer path is worse.
        worse_nodes = len(self.nodes) >= len(other.nodes)

        return (worse_cost and worse_damage and worse_requirement and worse_resources
                and worse_time and worse_nodes_left and worse_nodes)

    def pretty_print(self):
        path = " -> ".join(node.name for node in self.nodes)
        print(
            f"> Cost: {self.cost}"
            f"; Dmg: {self.damage}"
            f"; Reqs: {self.requirement}"
            f"; Events: {sorted((k.long_name, t) for k, t in self.timed_events.items())}"
            f"; Left: {self.nodes_left}"
            f"\n* {path}\n")


class PathGeneratorReach(GeneratorReach):
    _state: State
    _game: GameDescription
    _all_paths: dict[Node, list[Path]]
    _safe_nodes: set[Node]

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
        self._all_paths = {}
        self._safe_nodes = set()

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

    def _potential_nodes_from(self, node: Node) -> Iterator[tuple[Node, RequirementSet]]:
        context = self.node_context()
        # extra_requirement = _extra_requirement_for_node(self._game, node, context)
        requirement_to_leave = node.requirement_to_leave(context)

        for target_node, requirement in self._game.world_list.potential_nodes_from(node, context):
            if target_node is None:
                continue

            if requirement_to_leave != Requirement.trivial():
                requirement = RequirementAnd([requirement, requirement_to_leave])

            # if extra_requirement is not None:
            #     requirement = RequirementAnd([requirement, extra_requirement])

            yield target_node, requirement.as_set(self._state.resource_database)

    def _explore(self):
        context = self.node_context()
        first_path = Path.new_at(self._state)

        existing_paths: dict[Node, list[Path]] = collections.defaultdict(list)
        paths_to_examine = [first_path]
        safe_nodes = {self._state.node}

        while paths_to_examine:
            path: Path = paths_to_examine.pop(0)

            existing = existing_paths[path.nodes[-1]]
            if any(path.is_worse_or_equivalent_than(e) for e in existing):
                continue

            worse = [p for p in existing if p.is_worse_or_equivalent_than(path)]
            for p in worse:
                existing.remove(p)

            existing.append(path)
            if path.cost == 0 and path.nodes[-1] in safe_nodes:
                safe_nodes.union(path.nodes)

            for target_node, requirement in self._potential_nodes_from(path.nodes[-1]):
                for req_list in requirement.alternatives:
                    new_path = path.advance_to(target_node, req_list, context)
                    if new_path is None:
                        continue
                    paths_to_examine.append(new_path)

        if PATH_GENERATOR_DEBUG:
            print(">>>>>>>>>>>>>>>>>>>>>>> explore!")
            for node, paths in existing_paths.items():
                print("\n>> {}. Cost min {}, max {}, {}".format(
                    self._game.world_list.node_name(node, True),
                    min(path.cost for path in paths),
                    max(path.cost for path in paths),
                    len(paths),
                ))
                # for path in paths:
                #     # print("; ".join([f"{i}: {path.is_worse_than(p)}" for i, p in enumerate(paths)]))
                #     path.pretty_print()

        self._all_paths = existing_paths
        self._safe_nodes = safe_nodes

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
        def resource_check(path: Path) -> bool:
            if path.resources == self._state.resources:
                return True

            if len(path.timed_events) <= 1:
                resources = path.resources.duplicate()
                for e in path.timed_events.keys():
                    resources.remove_resource(e)
                return resources == self._state.resources

            return False

        return any(
            path.cost == 0 and resource_check(path)
            for path in self._all_paths.get(node, [])
        )

    @property
    def all_nodes(self) -> tuple[Node | None, ...]:
        return self.game.world_list.all_nodes

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
        for node in self.all_nodes:
            if any(path.cost == 0 for path in self._all_paths.get(node, [])):
                yield node

    @property
    def safe_nodes(self) -> Iterator[Node]:
        for node in self.all_nodes:
            if self.is_safe_node(node):
                yield node

    def is_safe_node(self, node: Node) -> bool:
        return node in self._safe_nodes

    def unsatisfied_requirement_list(self) -> Iterator[RequirementSet]:
        for node in self.all_nodes:
            for path in self._all_paths.get(node, []):
                if path.cost == 1:
                    yield path.requirement
