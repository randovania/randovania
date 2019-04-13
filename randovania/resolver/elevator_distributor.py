import copy
from collections import defaultdict
from typing import List, Dict

from randovania.game_description.area_location import AreaLocation
from randovania.game_description.echoes_elevator import Elevator, echoes_elevators
from randovania.games.prime import claris_random


def try_randomize_elevators(randomizer: claris_random.Random,
                            ) -> List[Elevator]:
    elevator_database: List[Elevator] = copy.deepcopy(echoes_elevators)

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
        target_elevator = target_elevators[randomizer.next_with_max(len(target_elevators) - 1)]

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
            return try_randomize_elevators(randomizer)

    return elevator_database


def elevator_connections_for_seed_number(seed_number: int,
                                         ) -> Dict[int, AreaLocation]:
    elevator_connection = {}
    for elevator in try_randomize_elevators(claris_random.Random(seed_number)):
        elevator_connection[elevator.instance_id] = AreaLocation(
            elevator.connected_elevator.world_asset_id,
            elevator.connected_elevator.area_asset_id
        )
    return elevator_connection
