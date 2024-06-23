"""Classes that describes the raw data of a game db."""

from __future__ import annotations

import collections
import copy
import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node import NodeContext
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.requirements.resource_requirement import DamageResourceRequirement
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.dock import DockWeaknessDatabase
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.requirements.requirement_list import RequirementList, SatisfiableRequirements
    from randovania.game_description.requirements.requirement_set import RequirementSet
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGainTuple, ResourceInfo
    from randovania.games.game import RandovaniaGame


def _requirement_dangerous(requirement: Requirement, context: NodeContext) -> Iterator[ResourceInfo]:
    for individual in requirement.iterate_resource_requirements(context):
        if individual.negate:
            yield individual.resource


def _calculate_dangerous_resources_in_db(
    db: DockWeaknessDatabase,
    context: NodeContext,
) -> Iterator[ResourceInfo]:
    for dock_type in db.dock_types:
        for dock_weakness in db.weaknesses[dock_type].values():
            yield from _requirement_dangerous(context.node_provider.open_requirement_for(dock_weakness), context)
            if dock_weakness.lock is not None:
                yield from _requirement_dangerous(context.node_provider.lock_requirement_for(dock_weakness), context)


def _calculate_dangerous_resources_in_areas(context: NodeContext) -> Iterator[ResourceInfo]:
    for area in context.node_provider.all_areas:
        for node in area.nodes:
            for _, requirement in context.node_provider.area_connections_from(node):
                yield from _requirement_dangerous(requirement, context)


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


class GameDescription:
    game: RandovaniaGame
    dock_weakness_database: DockWeaknessDatabase

    resource_database: ResourceDatabase
    layers: tuple[str, ...]
    victory_condition: Requirement
    starting_location: NodeIdentifier
    initial_states: dict[str, ResourceGainTuple]
    minimal_logic: MinimalLogicData | None
    _dangerous_resources: frozenset[ResourceInfo] | None = None
    region_list: RegionList
    _used_trick_levels: dict[TrickResourceInfo, set[int]] | None = None
    mutable: bool = False
    _victory_condition_as_set: RequirementSet | None = None

    def __deepcopy__(self, memodict: dict) -> GameDescription:
        new_game = GameDescription(
            game=self.game,
            resource_database=self.resource_database,
            layers=self.layers,
            dock_weakness_database=self.dock_weakness_database,
            region_list=copy.deepcopy(self.region_list, memodict),
            victory_condition=self.victory_condition,
            starting_location=self.starting_location,
            initial_states=copy.copy(self.initial_states),
            minimal_logic=self.minimal_logic,
        )
        new_game._dangerous_resources = self._dangerous_resources
        return new_game

    def __init__(
        self,
        game: RandovaniaGame,
        dock_weakness_database: DockWeaknessDatabase,
        resource_database: ResourceDatabase,
        layers: tuple[str, ...],
        victory_condition: Requirement,
        starting_location: NodeIdentifier,
        initial_states: dict[str, ResourceGainTuple],
        minimal_logic: MinimalLogicData | None,
        region_list: RegionList,
        used_trick_levels: dict[TrickResourceInfo, set[int]] | None = None,
    ):
        self.game = game
        self.dock_weakness_database = dock_weakness_database

        self.resource_database = resource_database
        self.layers = layers
        self.victory_condition = victory_condition
        self.starting_location = starting_location
        self.initial_states = initial_states
        self.minimal_logic = minimal_logic
        self.region_list = region_list
        self._used_trick_levels = used_trick_levels

    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        # Don't pickle _victory_condition_as_set
        del state["_victory_condition_as_set"]
        return state

    def __setstate__(self, state: dict) -> None:
        self.__dict__.update(state)
        self._victory_condition_as_set = None

    def create_node_context(self, resources: ResourceCollection) -> NodeContext:
        return NodeContext(
            None,
            resources,
            self.resource_database,
            self.region_list,
        )

    def patch_requirements(self, resources: ResourceCollection, damage_multiplier: float) -> None:
        if not self.mutable:
            raise ValueError("self is not mutable")

        context = self.create_node_context(resources)
        self.region_list.patch_requirements(damage_multiplier, context, self.dock_weakness_database)
        self._dangerous_resources = None

    def get_prefilled_docks(self) -> list[int | None]:
        region_list = self.region_list
        dock_connection = [None] * len(region_list.all_nodes)
        connections: list[int | None] = list(dock_connection)
        teleporter_dock_types = self.dock_weakness_database.all_teleporter_dock_types
        for source in region_list.iterate_nodes():
            if isinstance(source, DockNode) and source.dock_type in teleporter_dock_types:
                target = region_list.node_by_identifier(source.default_connection)
                connections[source.node_index] = target.node_index
        return connections

    @property
    def dangerous_resources(self) -> frozenset[ResourceInfo]:
        if self._dangerous_resources is None:
            context = self.create_node_context(ResourceCollection())
            first = _calculate_dangerous_resources_in_areas(context)
            second = _calculate_dangerous_resources_in_db(self.dock_weakness_database, context)
            self._dangerous_resources = frozenset(first) | frozenset(second)

        return self._dangerous_resources

    def get_used_trick_levels(self, *, ignore_cache: bool = False) -> dict[TrickResourceInfo, set[int]]:
        if self._used_trick_levels is not None and not ignore_cache:
            return self._used_trick_levels

        result = collections.defaultdict(set)
        context = self.create_node_context(ResourceCollection())

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
                region_list=RegionList(
                    [region.duplicate() for region in self.region_list.regions],
                    self.region_list.flatten_to_set_on_patch,
                ),
                victory_condition=self.victory_condition,
                starting_location=self.starting_location,
                initial_states=copy.copy(self.initial_states),
                minimal_logic=self.minimal_logic,
            )
            result.mutable = True
            return result

    def victory_condition_as_set(self, context: NodeContext) -> RequirementSet:
        if self._victory_condition_as_set is None:
            self._victory_condition_as_set = self.victory_condition.as_set(context)
        return self._victory_condition_as_set
        # return self.victory_condition.as_set(context)


def _resources_for_damage(
    resource: SimpleResourceInfo, database: ResourceDatabase, collection: ResourceCollection
) -> Iterator[ResourceInfo]:
    yield database.energy_tank
    for reduction in database.damage_reductions.get(resource, []):
        if reduction.inventory_item is not None and not collection.has_resource(reduction.inventory_item):
            yield reduction.inventory_item


def _damage_resource_from_list(requirements: RequirementList) -> SimpleResourceInfo | None:
    for individual in requirements.values():
        if isinstance(individual, DamageResourceRequirement):
            return individual.resource
    return None


def calculate_interesting_resources(
    satisfiable_requirements: SatisfiableRequirements,
    context: NodeContext,
    energy: int,
) -> frozenset[ResourceInfo]:
    """A resource is considered interesting if it isn't satisfied and it belongs to any satisfiable RequirementList"""

    def helper() -> Iterator[ResourceInfo]:
        # For each possible requirement list
        for requirement_list in satisfiable_requirements:
            # If it's not satisfied, there's at least one IndividualRequirement in it that can be collected
            if not requirement_list.satisfied(context, energy):
                current_energy = energy
                for individual in requirement_list.values():
                    # Ignore those with the `negate` flag. We can't "uncollect" a resource to satisfy these.
                    # Finally, if it's not satisfied then we're interested in collecting it
                    if not individual.negate and not individual.satisfied(context, current_energy):
                        if individual.is_damage:
                            assert isinstance(individual.resource, SimpleResourceInfo)
                            yield from _resources_for_damage(
                                individual.resource, context.database, context.current_resources
                            )
                        else:
                            yield individual.resource
                    elif individual.is_damage and individual.satisfied(context, current_energy):
                        current_energy -= individual.damage(context)
            elif damage_resource := _damage_resource_from_list(requirement_list):
                # This part is here to make sure that resources for damage are considered interesting for cases where
                # damage constraints are combined from multiple nodes. Each requirement in isolation might be satisfied,
                # but when combined, the energy might not be sufficient. The satisfiable requirements are assumed to be
                # unsatisfied.
                yield from _resources_for_damage(damage_resource, context.database, context.current_resources)

    return frozenset(helper())
