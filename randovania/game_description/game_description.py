"""Classes that describes the raw data of a game world."""
import copy
from typing import Iterator, FrozenSet, Dict

from randovania.game_description.area import Area
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.dock import DockWeaknessDatabase
from randovania.game_description.node import TeleporterNode
from randovania.game_description.requirements import RequirementSet, SatisfiableRequirements
from randovania.game_description.resources.damage_resource_info import DamageResourceInfo
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGainTuple, CurrentResources
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.world_list import WorldList


def _calculate_dangerous_resources_in_db(db: DockWeaknessDatabase) -> Iterator[SimpleResourceInfo]:
    for list_by_type in db:
        for dock_weakness in list_by_type:
            yield from dock_weakness.requirements.dangerous_resources


def _calculate_dangerous_resources_in_areas(areas: Iterator[Area]) -> Iterator[SimpleResourceInfo]:
    for area in areas:
        for node in area.nodes:
            for connection in area.connections[node].values():
                yield from connection.dangerous_resources


class GameDescription:
    game: int
    game_name: str
    dock_weakness_database: DockWeaknessDatabase

    resource_database: ResourceDatabase
    victory_condition: RequirementSet
    starting_location: AreaLocation
    initial_states: Dict[str, ResourceGainTuple]
    dangerous_resources: FrozenSet[SimpleResourceInfo]
    world_list: WorldList

    def __deepcopy__(self, memodict):
        return GameDescription(
            game=self.game,
            game_name=self.game_name,
            resource_database=self.resource_database,
            dock_weakness_database=self.dock_weakness_database,
            world_list=copy.deepcopy(self.world_list, memodict),
            victory_condition=self.victory_condition,
            starting_location=self.starting_location,
            initial_states=copy.copy(self.initial_states),
        )

    def __init__(self,
                 game: int,
                 game_name: str,
                 dock_weakness_database: DockWeaknessDatabase,

                 resource_database: ResourceDatabase,
                 victory_condition: RequirementSet,
                 starting_location: AreaLocation,
                 initial_states: Dict[str, ResourceGainTuple],
                 world_list: WorldList,
                 ):
        self.game = game
        self.game_name = game_name
        self.dock_weakness_database = dock_weakness_database

        self.resource_database = resource_database
        self.victory_condition = victory_condition
        self.starting_location = starting_location
        self.initial_states = initial_states
        self.world_list = world_list

        # TODO: refresh dangerous_resources during simplify_connections
        self.dangerous_resources = frozenset(
            _calculate_dangerous_resources_in_areas(self.world_list.all_areas)) | frozenset(
            _calculate_dangerous_resources_in_db(self.dock_weakness_database))

    def simplify_connections(self, resources):
        self.world_list.simplify_connections(resources)

    def all_editable_teleporter_nodes(self) -> Iterator[TeleporterNode]:
        energy_controllers = {
            44045108,  # Main Energy Controller
            50083607,  # Agon Energy Controller
            322696632,  # Torvus Energy Controller
            218311274,  # Sanctuary Energy Controller
            1564082177,  # Aerie
            3136899603,  # Aerie Transport Station
        }

        for area in self.world_list.all_areas:
            for node in area.nodes:
                if isinstance(node, TeleporterNode) and area.area_asset_id not in energy_controllers:
                    yield node


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
