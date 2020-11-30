"""Classes that describes the raw data of a game world."""
import copy
from typing import Iterator, FrozenSet, Dict, Optional

from randovania.game_description.area import Area
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.dock import DockWeaknessDatabase
from randovania.game_description.echoes_game_specific import EchoesGameSpecific
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import TeleporterNode
from randovania.game_description.requirements import SatisfiableRequirements, Requirement
from randovania.game_description.resources.damage_resource_info import DamageResourceInfo
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGainTuple, CurrentResources
from randovania.game_description.world_list import WorldList
from randovania.games.game import RandovaniaGame


def _calculate_dangerous_resources_in_db(db: DockWeaknessDatabase) -> Iterator[ResourceInfo]:
    for list_by_type in db:
        for dock_weakness in list_by_type:
            yield from dock_weakness.requirement.as_set.dangerous_resources


def _calculate_dangerous_resources_in_areas(areas: Iterator[Area]) -> Iterator[ResourceInfo]:
    for area in areas:
        for node in area.nodes:
            for requirement in area.connections[node].values():
                yield from requirement.as_set.dangerous_resources


class GameDescription:
    game: RandovaniaGame
    dock_weakness_database: DockWeaknessDatabase

    resource_database: ResourceDatabase
    game_specific: EchoesGameSpecific
    victory_condition: Requirement
    starting_location: AreaLocation
    initial_states: Dict[str, ResourceGainTuple]
    _dangerous_resources: Optional[FrozenSet[ResourceInfo]] = None
    world_list: WorldList

    def __deepcopy__(self, memodict):
        new_game = GameDescription(
            game=self.game,
            resource_database=self.resource_database,
            game_specific=self.game_specific,
            dock_weakness_database=self.dock_weakness_database,
            world_list=copy.deepcopy(self.world_list, memodict),
            victory_condition=self.victory_condition,
            starting_location=self.starting_location,
            initial_states=copy.copy(self.initial_states),
        )
        new_game._dangerous_resources = self._dangerous_resources
        return new_game

    def __init__(self,
                 game: RandovaniaGame,
                 dock_weakness_database: DockWeaknessDatabase,

                 resource_database: ResourceDatabase,
                 game_specific: EchoesGameSpecific,
                 victory_condition: Requirement,
                 starting_location: AreaLocation,
                 initial_states: Dict[str, ResourceGainTuple],
                 world_list: WorldList,
                 ):
        self.game = game
        self.dock_weakness_database = dock_weakness_database

        self.resource_database = resource_database
        self.game_specific = game_specific
        self.victory_condition = victory_condition
        self.starting_location = starting_location
        self.initial_states = initial_states
        self.world_list = world_list

    def patch_requirements(self, resources, damage_multiplier: float):
        self.world_list.patch_requirements(resources, damage_multiplier)
        self._dangerous_resources = None

    def create_game_patches(self) -> GamePatches:
        elevator_connection = {
            node.teleporter_instance_id: node.default_connection

            for node in self.world_list.all_nodes
            if isinstance(node, TeleporterNode) and node.editable
        }

        return GamePatches(None, {}, elevator_connection, {}, {}, {}, {}, self.starting_location, {},
                           game_specific=self.game_specific)

    @property
    def dangerous_resources(self) -> FrozenSet[ResourceInfo]:
        if self._dangerous_resources is None:
            self._dangerous_resources = frozenset(
                _calculate_dangerous_resources_in_areas(self.world_list.all_areas)) | frozenset(
                _calculate_dangerous_resources_in_db(self.dock_weakness_database))
        return self._dangerous_resources


def _resources_for_damage(resource: DamageResourceInfo, database: ResourceDatabase) -> Iterator[ResourceInfo]:
    yield database.energy_tank
    yield from (reduction.inventory_item for reduction in resource.reductions)


def calculate_interesting_resources(satisfiable_requirements: SatisfiableRequirements,
                                    resources: CurrentResources,
                                    energy: int,
                                    database: ResourceDatabase) -> FrozenSet[ResourceInfo]:
    """A resource is considered interesting if it isn't satisfied and it belongs to any satisfiable RequirementList """

    def helper():
        # For each possible requirement list
        for requirement_list in satisfiable_requirements:
            # If it's not satisfied, there's at least one IndividualRequirement in it that can be collected
            if not requirement_list.satisfied(resources, energy):

                for individual in requirement_list.values():
                    # Ignore those with the `negate` flag. We can't "uncollect" a resource to satisfy these.
                    # Finally, if it's not satisfied then we're interested in collecting it
                    if not individual.negate and not individual.satisfied(resources, energy):
                        if isinstance(individual.resource, DamageResourceInfo):
                            yield from _resources_for_damage(individual.resource, database)
                        else:
                            yield individual.resource

    return frozenset(helper())
