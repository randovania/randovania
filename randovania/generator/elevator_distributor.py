import copy
from collections import defaultdict
from random import Random
from typing import List, Dict, Optional, Tuple, AbstractSet

from randovania.game_description.area_location import AreaLocation
from randovania.game_description.node import TeleporterNode
from randovania.game_description.world_list import WorldList


class Elevator:
    instance_id: int
    world_asset_id: int
    area_asset_id: int
    destination_world: int
    destination_area: int
    connected_elevator: Optional["Elevator"]

    def __init__(self, instance_id: int, world_asset_id: int, area_asset_id: int, destination_world: int,
                 destination_area: int):
        self.world_asset_id = world_asset_id
        self.area_asset_id = area_asset_id
        self.instance_id = instance_id
        self.destination_world = destination_world
        self.destination_area = destination_area
        self.connected_elevator = None

    def connect_to(self, other: "Elevator"):
        self.destination_world = other.world_asset_id
        self.destination_area = other.area_asset_id
        other.destination_world = self.world_asset_id
        other.destination_area = self.area_asset_id
        self.connected_elevator = other
        other.connected_elevator = self

    @property
    def area_location(self):
        return AreaLocation(self.world_asset_id, self.area_asset_id)


def try_randomize_elevators(rng: Random,
                            echoes_elevators: Tuple[Elevator, ...],
                            ) -> List[Elevator]:
    elevator_database: List[Elevator] = list(echoes_elevators)

    elevator_list = copy.copy(elevator_database)
    elevators_by_world: Dict[int, List[Elevator]] = defaultdict(list)
    for elevator in elevator_list:
        elevators_by_world[elevator.world_asset_id].append(elevator)

    while elevator_list:
        source_elevators: List[Elevator] = max(elevators_by_world.values(), key=len)
        target_elevators: List[Elevator] = [
            elevator
            for elevator in elevator_list
            if elevator not in source_elevators
        ]
        source_elevator = source_elevators[0]
        target_elevator = rng.choice(target_elevators)

        source_elevator.connect_to(target_elevator)

        elevators_by_world[source_elevator.world_asset_id].remove(source_elevator)
        elevators_by_world[target_elevator.world_asset_id].remove(target_elevator)
        elevator_list.remove(source_elevator)
        elevator_list.remove(target_elevator)

    # TODO
    list3 = copy.copy(elevator_database)
    celevator_list3 = [list3[0]]
    while list3:
        celevator_list1 = []
        for celevator1 in celevator_list3:
            index = 0
            while index < len(list3):
                celevator2 = list3[index]
                if celevator2.world_asset_id == celevator1.world_asset_id or celevator2.area_asset_id == celevator1.destination_area:
                    celevator_list1.append(celevator2)
                    list3.remove(celevator2)
                else:
                    index += 1
        if celevator_list1:
            celevator_list3 = celevator_list1
        else:
            # Randomization failed
            return try_randomize_elevators(rng, echoes_elevators)

    return elevator_database


def two_way_elevator_connections(rng: Random,
                                 elevator_database: Tuple[Elevator, ...],
                                 between_areas: bool
                                 ) -> Dict[int, AreaLocation]:
    if between_areas:
        elevator_database = try_randomize_elevators(rng, elevator_database)
    else:
        assert len(elevator_database) % 2 == 0
        elevators = list(elevator_database)
        rng.shuffle(elevators)
        while elevators:
            elevators.pop().connect_to(elevators.pop())

    return {
        elevator.instance_id: elevator.connected_elevator.area_location
        for elevator in elevator_database
    }


def one_way_elevator_connections(rng: Random,
                                 elevator_database: Tuple[Elevator, ...],
                                 world_list: WorldList,
                                 elevator_target: bool
                                 ) -> Dict[int, AreaLocation]:
    if elevator_target:
        target_locations = [elevator.area_location for elevator in elevator_database]
    else:
        target_locations = [
            AreaLocation(world.world_asset_id, area.area_asset_id)
            for world in world_list.worlds
            for area in world.areas
        ]

    rng.shuffle(target_locations)

    return {
        elevator.instance_id: target_locations.pop()
        for elevator in elevator_database
    }


def create_elevator_database(world_list: WorldList,
                             areas_to_not_change: AbstractSet[int],
                             ) -> Tuple[Elevator, ...]:
    """
    Creates a tuple of Elevator objects, exclude those that belongs to one of the areas provided.
    :param world_list:
    :param areas_to_not_change: Set of asset_id of Areas whose teleporters are to be ignored
    :return:
    """
    return tuple(
        Elevator(node.teleporter_instance_id,
                 world.world_asset_id,
                 area.area_asset_id,
                 node.default_connection.world_asset_id,
                 node.default_connection.area_asset_id)

        for world, area, node in world_list.all_worlds_areas_nodes
        if isinstance(node, TeleporterNode) and node.editable and area.area_asset_id not in areas_to_not_change
    )
