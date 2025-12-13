"""Classes that describes the raw data of a game db."""

from __future__ import annotations

import collections
import copy
import dataclasses
from typing import TYPE_CHECKING, override

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.hint_node import HintNode, HintNodeKind
from randovania.game_description.db.node import Node, NodeContext
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.game_database_view import GameDatabaseView, ResourceDatabaseView
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.dock import DockType, DockWeakness, DockWeaknessDatabase
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region import Region
    from randovania.game_description.hint_features import HintFeature
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.graph.graph_requirement import GraphRequirementList
    from randovania.resolver.damage_state import DamageState


@dataclasses.dataclass(frozen=True)
class IndexWithReason:
    name: str
    reason: str | None


@dataclasses.dataclass(frozen=True)
class MinimalLogicData:
    items_to_exclude: list[IndexWithReason]
    custom_item_amount: dict[str, int]
    events_to_exclude: list[IndexWithReason]
    description: str


class GameDescription(GameDatabaseView):
    game: RandovaniaGame
    dock_weakness_database: DockWeaknessDatabase
    resource_database: ResourceDatabase
    hint_feature_database: dict[str, HintFeature]

    layers: tuple[str, ...]
    victory_condition: Requirement
    starting_location: NodeIdentifier
    minimal_logic: MinimalLogicData | None
    _dangerous_resources: frozenset[ResourceInfo] | None = None
    region_list: RegionList
    _used_trick_levels: dict[TrickResourceInfo, set[int]] | None = None
    mutable: bool = False

    def __deepcopy__(self, memodict: dict) -> GameDescription:
        new_game = GameDescription(
            game=self.game,
            resource_database=self.resource_database,
            layers=self.layers,
            dock_weakness_database=self.dock_weakness_database,
            hint_feature_database=self.hint_feature_database,
            region_list=copy.deepcopy(self.region_list, memodict),
            victory_condition=self.victory_condition,
            starting_location=self.starting_location,
            minimal_logic=self.minimal_logic,
        )
        new_game._dangerous_resources = self._dangerous_resources
        return new_game

    def __init__(
        self,
        game: RandovaniaGame,
        dock_weakness_database: DockWeaknessDatabase,
        resource_database: ResourceDatabase,
        hint_feature_database: dict[str, HintFeature],
        layers: tuple[str, ...],
        victory_condition: Requirement,
        starting_location: NodeIdentifier,
        minimal_logic: MinimalLogicData | None,
        region_list: RegionList,
        used_trick_levels: dict[TrickResourceInfo, set[int]] | None = None,
    ):
        self.game = game
        self.dock_weakness_database = dock_weakness_database
        self.resource_database = resource_database
        self.hint_feature_database = hint_feature_database

        self.layers = layers
        self.victory_condition = victory_condition
        self.starting_location = starting_location
        self.minimal_logic = minimal_logic
        self.region_list = region_list
        self._used_trick_levels = used_trick_levels

    @property
    def game_enum(self) -> RandovaniaGame:
        # compatibility with WorldGraph
        return self.game

    def create_node_context(self, resources: ResourceCollection) -> NodeContext:
        return NodeContext(
            None,
            resources,
            self.resource_database,
            self.region_list,
        )

    def get_prefilled_docks(self) -> dict[NodeIdentifier, NodeIdentifier]:
        connections: dict[NodeIdentifier, NodeIdentifier] = {}

        teleporter_dock_types = self.dock_weakness_database.all_teleporter_dock_types
        for _, _, source in self.iterate_nodes_of_type(DockNode):
            if source.dock_type in teleporter_dock_types:
                connections[source.identifier] = source.default_connection

        return connections

    def get_used_trick_levels(self, *, ignore_cache: bool = False) -> dict[TrickResourceInfo, set[int]]:
        if self._used_trick_levels is not None and not ignore_cache:
            return self._used_trick_levels

        result = collections.defaultdict(set)
        context = self.create_node_context(self.resource_database.create_resource_collection())

        def process(req: Requirement) -> None:
            for resource_requirement in req.iterate_resource_requirements(context):
                resource = resource_requirement.resource
                if resource.resource_type == ResourceType.TRICK:
                    assert isinstance(resource, TrickResourceInfo)
                    result[resource].add(resource_requirement.amount)

        for dock_weakness in self.dock_weakness_database.all_weaknesses:
            process(dock_weakness.requirement)
            if dock_weakness.lock is not None:
                process(dock_weakness.lock.requirement)

        for area in self.region_list.all_areas:
            for _, _, requirement in area.all_connections:
                process(requirement)

            for node in area.nodes:
                if isinstance(node, DockNode):
                    if node.override_default_open_requirement is not None:
                        process(node.override_default_open_requirement)
                    if node.override_default_lock_requirement is not None:
                        process(node.override_default_lock_requirement)

        self._used_trick_levels = dict(result)
        return result

    def get_mutable(self) -> GameDescription:
        if self.mutable:
            return self
        else:
            result = GameDescription(
                game=self.game,
                resource_database=self.resource_database,
                layers=self.layers,
                dock_weakness_database=self.dock_weakness_database,
                hint_feature_database=self.hint_feature_database,
                region_list=RegionList(
                    [region.duplicate() for region in self.region_list.regions],
                    self.region_list.flatten_to_set_on_patch,
                ),
                victory_condition=self.victory_condition,
                starting_location=self.starting_location,
                minimal_logic=self.minimal_logic,
            )
            result.mutable = True
            return result

    def _has_hint_with_kind(self, kind: HintNodeKind) -> bool:
        return any(node.kind == kind for node in self.region_list.iterate_nodes_of_type(HintNode))

    @property
    def has_random_hints(self) -> bool:
        return self._has_hint_with_kind(HintNodeKind.GENERIC)

    @property
    def has_specific_location_hints(self) -> bool:
        return self._has_hint_with_kind(HintNodeKind.SPECIFIC_LOCATION)

    @property
    def has_specific_pickup_hints(self) -> bool:
        return bool(self.game.hints.specific_pickup_hints) or self._has_hint_with_kind(HintNodeKind.SPECIFIC_PICKUP)

    # Game Database View

    @override
    def get_game_enum(self) -> RandovaniaGame:
        return self.game

    def node_iterator(self) -> Iterator[tuple[Region, Area, Node]]:
        return self.region_list.all_regions_areas_nodes

    @override
    def node_by_identifier(self, identifier: NodeIdentifier) -> Node:
        return self.region_list.node_by_identifier(identifier)

    @override
    def assert_pickup_index_exists(self, index: PickupIndex) -> None:
        self.region_list.node_from_pickup_index(index)

    @override
    def default_starting_location(self) -> NodeIdentifier:
        return self.starting_location

    @override
    def get_dock_types(self) -> list[DockType]:
        return self.dock_weakness_database.dock_types

    @override
    def get_dock_weakness(self, dock_type_name: str, weakness_name: str) -> DockWeakness:
        return self.dock_weakness_database.get_by_weakness(dock_type_name, weakness_name)

    @override
    def get_resource_database_view(self) -> ResourceDatabaseView:
        return self.resource_database

    @override
    def get_pickup_database(self) -> PickupDatabase:
        from randovania.game_description import default_database

        return default_database.pickup_database_for_game(self.game)

    @override
    def get_victory_condition(self) -> Requirement:
        return self.victory_condition

    @override
    def node_from_pickup_index(self, index: PickupIndex) -> PickupNode:
        return self.region_list.node_from_pickup_index(index)

    @override
    def area_from_node(self, node: Node) -> Area:
        return self.region_list.nodes_to_area(node)

    @override
    def pickup_nodes_with_feature(self, feature: HintFeature) -> tuple[PickupNode, ...]:
        """
        Returns an iterable tuple of PickupNodes with the given feature (either directly or in their area)
        """
        return tuple(
            node
            for _, area, node in self.iterate_nodes_of_type(PickupNode)
            if (feature in area.hint_features) or (feature in node.hint_features)
        )

    @override
    def get_configurable_node_requirements(self) -> Mapping[NodeIdentifier, Requirement]:
        return self.region_list.configurable_nodes


def _resources_for_damage(
    resource: ResourceInfo, database: ResourceDatabase, collection: ResourceCollection, damage_state: DamageState
) -> Iterator[ResourceInfo]:
    yield from damage_state.resources_for_health()
    for reduction in database.damage_reductions.get(resource, []):
        if reduction.inventory_item is not None and not collection.has_resource(reduction.inventory_item):
            yield reduction.inventory_item


def calculate_interesting_resources(
    satisfiable_requirements: frozenset[GraphRequirementList],
    context: NodeContext,
    damage_state: DamageState,
) -> frozenset[ResourceInfo]:
    """A resource is considered interesting if it isn't satisfied and it belongs to any satisfiable RequirementList"""

    from randovania.game_description.requirements.requirement_list import RequirementList

    def helper() -> Iterator[ResourceInfo]:
        # For each possible requirement list
        for requirement_list in satisfiable_requirements:
            # If it's not satisfied, there's at least one IndividualRequirement in it that can be collected
            if not requirement_list.satisfied(context.current_resources, damage_state.health_for_damage_requirements()):
                current_energy = damage_state.health_for_damage_requirements()

                for individual in RequirementList.from_graph_requirement_list(requirement_list).values():
                    # Ignore those with the `negate` flag. We can't "uncollect" a resource to satisfy these.
                    # Finally, if it's not satisfied then we're interested in collecting it
                    if not individual.negate and not individual.satisfied(context, current_energy):
                        if individual.is_damage:
                            assert isinstance(individual.resource, SimpleResourceInfo)
                            yield from _resources_for_damage(
                                individual.resource, context.database, context.current_resources, damage_state
                            )
                        else:
                            yield individual.resource
                    elif individual.is_damage and individual.satisfied(context, current_energy):
                        current_energy -= individual.damage(context)

            elif damage_resources := {
                resource for resource in requirement_list.all_resources() if resource.resource_type.is_damage()
            }:
                # This part is here to make sure that resources for damage are considered interesting for cases where
                # damage constraints are combined from multiple nodes. Each requirement in isolation might be satisfied,
                # but when combined, the energy might not be sufficient. The satisfiable requirements are assumed to be
                # unsatisfied.
                for damage_resource in damage_resources:
                    yield from _resources_for_damage(
                        damage_resource, context.database, context.current_resources, damage_state
                    )

    return frozenset(helper())
