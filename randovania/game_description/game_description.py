"""Classes that describes the raw data of a game world."""
import copy
import dataclasses
from typing import Iterator

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_list import SatisfiableRequirements
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGainTuple, ResourceCollection
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.dock import DockWeaknessDatabase
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.teleporter_node import TeleporterNode
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame


def _calculate_dangerous_resources_in_db(
        wl: WorldList,
        db: DockWeaknessDatabase,
        database: ResourceDatabase,
) -> Iterator[ResourceInfo]:
    for dock_type in db.dock_types:
        for dock_weakness in db.weaknesses[dock_type].values():
            yield from wl.open_requirement_for(dock_weakness).as_set(database).dangerous_resources
            if dock_weakness.lock is not None:
                yield from wl.lock_requirement_for(dock_weakness).as_set(database).dangerous_resources


def _calculate_dangerous_resources_in_areas(
        wl: WorldList,
        database: ResourceDatabase,
) -> Iterator[ResourceInfo]:
    for area in wl.all_areas:
        for node in area.nodes:
            for _, requirement in wl.area_connections_from(node):
                yield from requirement.as_set(database).dangerous_resources


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
    starting_location: AreaIdentifier
    initial_states: dict[str, ResourceGainTuple]
    minimal_logic: MinimalLogicData | None
    _dangerous_resources: frozenset[ResourceInfo] | None = None
    world_list: WorldList
    mutable: bool = False

    def __deepcopy__(self, memodict):
        new_game = GameDescription(
            game=self.game,
            resource_database=self.resource_database,
            layers=self.layers,
            dock_weakness_database=self.dock_weakness_database,
            world_list=copy.deepcopy(self.world_list, memodict),
            victory_condition=self.victory_condition,
            starting_location=self.starting_location,
            initial_states=copy.copy(self.initial_states),
            minimal_logic=self.minimal_logic,
        )
        new_game._dangerous_resources = self._dangerous_resources
        return new_game

    def __init__(self,
                 game: RandovaniaGame,
                 dock_weakness_database: DockWeaknessDatabase,

                 resource_database: ResourceDatabase,
                 layers: tuple[str, ...],
                 victory_condition: Requirement,
                 starting_location: AreaIdentifier,
                 initial_states: dict[str, ResourceGainTuple],
                 minimal_logic: MinimalLogicData | None,
                 world_list: WorldList,
                 ):
        self.game = game
        self.dock_weakness_database = dock_weakness_database

        self.resource_database = resource_database
        self.layers = layers
        self.victory_condition = victory_condition
        self.starting_location = starting_location
        self.initial_states = initial_states
        self.minimal_logic = minimal_logic
        self.world_list = world_list

    def patch_requirements(self, resources: ResourceCollection, damage_multiplier: float):
        if not self.mutable:
            raise ValueError("self is not mutable")

        self.world_list.patch_requirements(resources, damage_multiplier, self.resource_database,
                                           self.dock_weakness_database)
        self._dangerous_resources = None

    def get_default_elevator_connection(self) -> dict[NodeIdentifier, AreaIdentifier]:
        return {
            self.world_list.identifier_for_node(node): node.default_connection

            for node in self.world_list.iterate_nodes()
            if isinstance(node, TeleporterNode) and node.editable
        }

    @property
    def dangerous_resources(self) -> frozenset[ResourceInfo]:
        if self._dangerous_resources is None:
            first = _calculate_dangerous_resources_in_areas(self.world_list, self.resource_database)
            second = _calculate_dangerous_resources_in_db(
                self.world_list, self.dock_weakness_database, self.resource_database
            )
            self._dangerous_resources = frozenset(first) | frozenset(second)

        return self._dangerous_resources

    def get_mutable(self) -> "GameDescription":
        if self.mutable:
            return self
        else:
            result = GameDescription(
                game=self.game,
                resource_database=self.resource_database,
                layers=self.layers,
                dock_weakness_database=self.dock_weakness_database,
                world_list=WorldList([
                    world.duplicate()
                    for world in self.world_list.worlds
                ]),
                victory_condition=self.victory_condition,
                starting_location=self.starting_location,
                initial_states=copy.copy(self.initial_states),
                minimal_logic=self.minimal_logic,
            )
            result.mutable = True
            return result


def _resources_for_damage(resource: SimpleResourceInfo, database: ResourceDatabase) -> Iterator[ResourceInfo]:
    yield database.energy_tank
    for reduction in database.damage_reductions.get(resource, []):
        if reduction.inventory_item is not None:
            yield reduction.inventory_item


def calculate_interesting_resources(satisfiable_requirements: SatisfiableRequirements,
                                    resources: ResourceCollection,
                                    energy: int,
                                    database: ResourceDatabase) -> frozenset[ResourceInfo]:
    """A resource is considered interesting if it isn't satisfied and it belongs to any satisfiable RequirementList """

    def helper():
        # For each possible requirement list
        for requirement_list in satisfiable_requirements:
            # If it's not satisfied, there's at least one IndividualRequirement in it that can be collected
            if not requirement_list.satisfied(resources, energy, database):

                for individual in requirement_list.values():
                    # Ignore those with the `negate` flag. We can't "uncollect" a resource to satisfy these.
                    # Finally, if it's not satisfied then we're interested in collecting it
                    if not individual.negate and not individual.satisfied(resources, energy, database):
                        if individual.is_damage:
                            yield from _resources_for_damage(individual.resource, database)
                        else:
                            yield individual.resource

    return frozenset(helper())
