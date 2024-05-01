from __future__ import annotations

import copy
import dataclasses
import typing
from dataclasses import dataclass

from randovania.game_description.assignment import (
    PickupTarget,
)
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType

TeleporterConnection = dict[NodeIdentifier, NodeIdentifier]
StartingEquipment = list[PickupEntry] | ResourceCollection


class IncompatibleStartingEquipment(Exception):
    pass


if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.game_description.assignment import (
        DockWeaknessAssociation,
        PickupTargetAssociation,
    )
    from randovania.game_description.db.dock import DockWeakness
    from randovania.game_description.db.node import Node
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.hint import Hint
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_info import ResourceGain
    from randovania.layout.base.base_configuration import BaseConfiguration


@dataclass(frozen=True, slots=True)
class GamePatches:
    """Determines patches that are made to the game's data."""

    game: GameDescription = dataclasses.field(compare=False)
    player_index: int
    configuration: BaseConfiguration
    pickup_assignment: dict[PickupIndex, PickupTarget]
    dock_connection: list[int | None]
    dock_weakness: list[DockWeakness | None]
    weaknesses_to_shuffle: list[bool]
    starting_equipment: StartingEquipment
    starting_location: NodeIdentifier
    hints: dict[NodeIdentifier, Hint]
    custom_patcher_data: list
    game_specific: dict

    cached_dock_connections_from: list[tuple[tuple[Node, Requirement], ...] | None] = dataclasses.field(
        hash=False, compare=False
    )

    def __post_init__(self) -> None:
        if isinstance(self.starting_equipment, ResourceCollection | list):
            if isinstance(self.starting_equipment, ResourceCollection):
                for resource, _ in self.starting_equipment.as_resource_gain():
                    if resource.resource_type != ResourceType.ITEM:
                        raise ValueError(f"starting_pickups_or_items must have only Items, not {resource}")
        else:
            raise TypeError("starting_pickups_or_items must be a ResourceCollection or list")

    @classmethod
    def create_from_game(
        cls,
        game: GameDescription,
        player_index: int,
        configuration: BaseConfiguration,
    ) -> GamePatches:
        game.region_list.ensure_has_node_cache()
        return GamePatches(
            game,
            player_index,
            configuration,
            pickup_assignment={},
            dock_connection=game.get_prefilled_docks(),
            dock_weakness=[None] * len(game.region_list.all_nodes),
            weaknesses_to_shuffle=[False] * len(game.region_list.all_nodes),
            starting_equipment=[],
            starting_location=game.starting_location,
            hints={},
            cached_dock_connections_from=[None] * len(game.region_list.all_nodes),
            custom_patcher_data=[],
            game_specific={},
        )

    def assign_new_pickups(self, assignments: Iterable[PickupTargetAssociation]) -> GamePatches:
        new_pickup_assignment = copy.copy(self.pickup_assignment)

        for index, pickup in assignments:
            assert index not in new_pickup_assignment
            assert self.game.region_list.node_from_pickup_index(index) is not None
            new_pickup_assignment[index] = pickup

        return dataclasses.replace(self, pickup_assignment=new_pickup_assignment)

    def assign_own_pickups(self, assignments: Iterable[tuple[PickupIndex, PickupEntry]]) -> GamePatches:
        return self.assign_new_pickups(
            (index, PickupTarget(pickup, self.player_index)) for index, pickup in assignments
        )

    def assign_starting_location(self, location: NodeIdentifier) -> GamePatches:
        return dataclasses.replace(self, starting_location=location)

    def assign_custom_starting_items(self, new_resources: ResourceGain) -> GamePatches:
        if isinstance(self.starting_equipment, ResourceCollection):
            current = self.starting_equipment.duplicate()
        elif self.starting_equipment:
            raise IncompatibleStartingEquipment("GamePatches already has starting pickups")
        else:
            current = ResourceCollection.with_database(self.game.resource_database)

        current.add_resource_gain(new_resources)
        return dataclasses.replace(self, starting_equipment=current)

    def assign_extra_starting_pickups(self, new_pickups: Iterable[PickupEntry]) -> GamePatches:
        if not isinstance(self.starting_equipment, list):
            raise IncompatibleStartingEquipment("GamePatches already has starting items")

        current = list(self.starting_equipment)
        current.extend(new_pickups)
        return dataclasses.replace(self, starting_equipment=current)

    def assign_hint(self, identifier: NodeIdentifier, hint: Hint) -> GamePatches:
        current = copy.copy(self.hints)
        current[identifier] = hint
        return dataclasses.replace(self, hints=current)

    # Dock Connection
    def assign_dock_connections(self, assignment: Iterable[tuple[DockNode, Node]]) -> GamePatches:
        connections = list(self.dock_connection)
        cached_dock_connections = list(self.cached_dock_connections_from)

        for source, target in assignment:
            connections[source.node_index] = target.node_index
            cached_dock_connections[source.node_index] = None
            # TODO: maybe this should set the other side too?

        return dataclasses.replace(
            self, dock_connection=connections, cached_dock_connections_from=cached_dock_connections
        )

    def get_dock_connection_for(self, node: DockNode) -> Node:
        target_index = self.dock_connection[node.node_index]
        if target_index is None:
            target_index = node.cache_default_connection
            if target_index is None:
                target_index = self.game.region_list.node_by_identifier(node.default_connection).node_index
                object.__setattr__(node, "cache_default_connection", target_index)

        result = self.game.region_list.all_nodes[target_index]
        assert result is not None
        return result

    def all_dock_connections(self) -> Iterator[tuple[DockNode, Node]]:
        nodes = self.game.region_list.all_nodes
        for index, target in enumerate(self.dock_connection):
            if target is not None:
                node = nodes[index]
                other = nodes[target]
                assert isinstance(node, DockNode)
                assert other is not None
                yield node, other

    # Dock Weakness
    def assign_dock_weakness(self, weaknesses: Iterable[tuple[DockNode, DockWeakness]]) -> GamePatches:
        new_weakness = list(self.dock_weakness)
        cached_dock_connections = list(self.cached_dock_connections_from)

        for node, weakness in weaknesses:
            new_weakness[node.node_index] = weakness
            cached_dock_connections[node.node_index] = None
            cached_dock_connections[self.get_dock_connection_for(node).node_index] = None

        return dataclasses.replace(
            self, dock_weakness=new_weakness, cached_dock_connections_from=cached_dock_connections
        )

    def assign_weaknesses_to_shuffle(self, weaknesses: Iterable[tuple[DockNode, bool]]) -> GamePatches:
        new_to_shuffle = list(self.weaknesses_to_shuffle)

        for node, shuffle in weaknesses:
            new_to_shuffle[node.node_index] = shuffle

        return dataclasses.replace(self, weaknesses_to_shuffle=new_to_shuffle)

    def assign_game_specific(self, game_specific: dict) -> GamePatches:
        return dataclasses.replace(self, game_specific=game_specific)

    def get_dock_weakness_for(self, node: DockNode) -> DockWeakness:
        return self.dock_weakness[node.node_index] or node.default_dock_weakness

    def has_default_weakness(self, node: DockNode) -> bool:
        if self.dock_weakness[node.node_index] is None:
            return True

        return self.dock_weakness[node.node_index] == node.default_dock_weakness

    def should_shuffle_weakness(self, node: DockNode) -> bool:
        return self.weaknesses_to_shuffle[node.node_index]

    def all_dock_weaknesses(self) -> Iterator[DockWeaknessAssociation]:
        nodes = self.game.region_list.all_nodes
        for index, weakness in enumerate(self.dock_weakness):
            if weakness is not None:
                node = nodes[index]
                assert isinstance(node, DockNode)
                yield node, weakness

    def all_weaknesses_to_shuffle(self) -> Iterator[DockNode]:
        nodes = self.game.region_list.all_nodes
        for index, shuffle in enumerate(self.weaknesses_to_shuffle):
            if shuffle:
                node = nodes[index]
                assert isinstance(node, DockNode)
                yield node

    def starting_resources(self) -> ResourceCollection:
        if isinstance(self.starting_equipment, ResourceCollection):
            return self.starting_equipment.duplicate()
        else:
            result = ResourceCollection.with_database(self.game.resource_database)
            for it in self.starting_equipment:
                result.add_resource_gain(it.resource_gain(result))
            return result

    # Cache things
    def get_cached_dock_connections_from(self, node: DockNode) -> tuple[tuple[Node, Requirement], ...] | None:
        return self.cached_dock_connections_from[node.node_index]

    def set_cached_dock_connections_from(self, node: DockNode, cache: tuple[tuple[Node, Requirement], ...]) -> None:
        self.cached_dock_connections_from[node.node_index] = cache
