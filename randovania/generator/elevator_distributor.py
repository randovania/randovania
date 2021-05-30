import copy
from collections import defaultdict
from random import Random
from typing import List, Dict, Optional, Tuple

from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.game_patches import ElevatorConnection
from randovania.game_description.world.node import TeleporterNode
from randovania.game_description.world.teleporter import Teleporter
from randovania.game_description.world.world_list import WorldList


class ElevatorHelper:
    teleporter: Teleporter
    destination: AreaLocation
    connected_elevator: Optional["ElevatorHelper"]

    def __init__(self, teleporter: Teleporter, destination: AreaLocation):
        self.teleporter = teleporter
        self.destination = destination
        self.connected_elevator = None

    @property
    def world_asset_id(self):
        return self.teleporter.world_asset_id

    @property
    def area_asset_id(self):
        return self.teleporter.area_asset_id

    @property
    def instance_id(self):
        return self.teleporter.instance_id

    def connect_to(self, other: "ElevatorHelper"):
        self.destination = other.teleporter.area_location
        other.destination = self.teleporter.area_location
        self.connected_elevator = other
        other.connected_elevator = self

    @property
    def area_location(self):
        return AreaLocation(self.world_asset_id, self.area_asset_id)


def try_randomize_elevators(rng: Random,
                            echoes_elevators: Tuple[ElevatorHelper, ...],
                            ) -> List[ElevatorHelper]:
    elevator_database: List[ElevatorHelper] = list(echoes_elevators)
    assert len(elevator_database) % 2 == 0

    elevator_list = copy.copy(elevator_database)
    elevators_by_world: Dict[int, List[ElevatorHelper]] = defaultdict(list)
    for elevator in elevator_list:
        elevators_by_world[elevator.world_asset_id].append(elevator)

    while elevator_list:
        source_elevators: List[ElevatorHelper] = max(elevators_by_world.values(), key=len)
        target_elevators: List[ElevatorHelper] = [
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
                if (celevator2.world_asset_id == celevator1.world_asset_id
                        or celevator2.area_asset_id == celevator1.destination.area_asset_id):
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
                                 elevator_database: Tuple[ElevatorHelper, ...],
                                 between_areas: bool
                                 ) -> ElevatorConnection:
    if len(elevator_database) % 2 != 0:
        raise ValueError("Two-way elevator shuffle, but odd number of elevators to shuffle.")
    if between_areas:
        elevator_database = try_randomize_elevators(rng, elevator_database)
    else:
        elevators = list(elevator_database)
        rng.shuffle(elevators)
        while elevators:
            elevators.pop().connect_to(elevators.pop())

    return {
        elevator.teleporter: elevator.connected_elevator.area_location
        for elevator in elevator_database
    }


def one_way_elevator_connections(rng: Random,
                                 elevator_database: Tuple[ElevatorHelper, ...],
                                 target_locations: List[AreaLocation],
                                 replacement: bool,
                                 ) -> ElevatorConnection:
    target_locations.sort()
    rng.shuffle(target_locations)

    def _create_target():
        if replacement:
            return rng.choice(target_locations)
        else:
            return target_locations.pop()

    return {
        elevator.teleporter: _create_target()
        for elevator in elevator_database
    }


def create_elevator_database(world_list: WorldList,
                             all_teleporters: List[Teleporter],
                             ) -> Tuple[ElevatorHelper, ...]:
    """
    Creates a tuple of Elevator objects, exclude those that belongs to one of the areas provided.
    :param world_list:
    :param all_teleporters: Set of teleporters to use
    :return:
    """
    all_helpers = [
        ElevatorHelper(node.teleporter, node.default_connection)

        for world, area, node in world_list.all_worlds_areas_nodes
        if isinstance(node, TeleporterNode)
    ]
    return tuple(
        helper
        for helper in all_helpers
        if helper.teleporter in all_teleporters
    )
