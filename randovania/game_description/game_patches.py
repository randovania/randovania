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
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.hint import Hint
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
    dock_connection: dict[NodeIdentifier, NodeIdentifier]
    dock_weakness: dict[NodeIdentifier, DockWeakness]
    weaknesses_to_shuffle: set[NodeIdentifier]
    starting_equipment: StartingEquipment
    starting_location: NodeIdentifier
    hints: dict[NodeIdentifier, Hint]
    custom_patcher_data: list
    game_specific: dict

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
            dock_weakness={},
            weaknesses_to_shuffle=set(),
            starting_equipment=[],
            starting_location=game.starting_location,
            hints={},
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
            current = self.game.get_resource_database_view().create_resource_collection()

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
        connections = self.dock_connection.copy()

        for source, target in assignment:
            connections[source.identifier] = target.identifier

        return dataclasses.replace(
            self,
            dock_connection=connections,
        )

    def get_dock_connection_for(self, node: DockNode) -> NodeIdentifier:
        return self.dock_connection.get(node.identifier, node.default_connection)

    def all_dock_connections_identifiers(self) -> Iterator[tuple[NodeIdentifier, NodeIdentifier]]:
        return iter(self.dock_connection.items())

    def all_dock_connections(self, view: GameDatabaseView) -> Iterator[tuple[DockNode, Node]]:
        for source, target in self.dock_connection.items():
            yield view.typed_node_by_identifier(source, DockNode), view.node_by_identifier(target)

    # Dock Weakness
    def assign_dock_weakness(self, weaknesses: Iterable[tuple[DockNode, DockWeakness]]) -> GamePatches:
        new_weakness = self.dock_weakness.copy()

        for node, weakness in weaknesses:
            new_weakness[node.identifier] = weakness

        return dataclasses.replace(self, dock_weakness=new_weakness)

    def assign_weaknesses_to_shuffle(self, weaknesses: Iterable[tuple[DockNode, bool]]) -> GamePatches:
        new_to_shuffle = self.weaknesses_to_shuffle.copy()

        for node, shuffle in weaknesses:
            if shuffle:
                new_to_shuffle.add(node.identifier)
            elif node.identifier in new_to_shuffle:
                new_to_shuffle.remove(node.identifier)

        return dataclasses.replace(self, weaknesses_to_shuffle=new_to_shuffle)

    def assign_game_specific(self, game_specific: dict) -> GamePatches:
        return dataclasses.replace(self, game_specific=game_specific)

    def get_dock_weakness_for(self, node: DockNode) -> DockWeakness:
        return self.dock_weakness.get(node.identifier, node.default_dock_weakness)

    def has_default_weakness(self, node: DockNode) -> bool:
        return self.get_dock_weakness_for(node) == node.default_dock_weakness

    def should_shuffle_weakness(self, node: DockNode) -> bool:
        return node.identifier in self.weaknesses_to_shuffle

    def all_dock_weaknesses(self, game_view: GameDatabaseView) -> Iterator[DockWeaknessAssociation]:
        for _, _, node in game_view.iterate_nodes_of_type(DockNode):
            weakness = self.dock_weakness.get(node.identifier)
            if weakness is not None:
                yield node, weakness

    def all_weaknesses_to_shuffle(self, game_view: GameDatabaseView) -> Iterator[DockNode]:
        for _, _, node in game_view.iterate_nodes_of_type(DockNode):
            if node.identifier in self.weaknesses_to_shuffle:
                yield node

    def starting_resources(self) -> ResourceCollection:
        if isinstance(self.starting_equipment, ResourceCollection):
            return self.starting_equipment.duplicate()
        else:
            result = self.game.get_resource_database_view().create_resource_collection()
            for it in self.starting_equipment:
                result.add_resource_gain(it.resource_gain(result))
            return result
