import copy
from collections import defaultdict
from random import Random
from typing import List, Dict, Optional

from randovania.game_description.area_location import AreaLocation


class Int32:
    def __init__(self, value):
        # Wrap value into [-2**31, 2**31-1]
        self.value = (value + 2 ** 31) % 2 ** 32 - 2 ** 31

    def __int__(self):
        return self.value

    def __add__(self, other):
        return Int32(self.value + other.value)

    def __sub__(self, other):
        return Int32(self.value - other.value)


MBIG = Int32(0x7fffffff)
MSEED = Int32(0x9a4ec86)
MZ = 0


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


def try_randomize_elevators(rng: Random,
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
            return try_randomize_elevators(rng)

    return elevator_database


def elevator_connections_for_seed_number(rng: Random,
                                         ) -> Dict[int, AreaLocation]:
    elevator_connection = {}
    for elevator in try_randomize_elevators(rng):
        elevator_connection[elevator.instance_id] = AreaLocation(
            elevator.connected_elevator.world_asset_id,
            elevator.connected_elevator.area_asset_id
        )
    return elevator_connection


echoes_elevators = [
    Elevator(589851, 1006255871, 2918020398, 2252328306, 2556480432),
    Elevator(1572998, 1006255871, 1660916974, 1119434212, 1473133138),
    Elevator(1966093, 1006255871, 2889020216, 1039999561, 1868895730),
    Elevator(2097251, 1006255871, 1287880522, 2252328306, 2399252740),
    Elevator(3342446, 1006255871, 3455543403, 464164546, 3528156989),
    Elevator(3538975, 1006255871, 1345979968, 2252328306, 408633584),
    Elevator(152, 2252328306, 408633584, 1006255871, 1345979968),
    Elevator(393260, 2252328306, 2556480432, 1006255871, 2918020398),
    Elevator(524321, 2252328306, 2399252740, 1006255871, 1287880522),
    Elevator(122, 1119434212, 1473133138, 1006255871, 1660916974),
    Elevator(1245307, 1119434212, 2806956034, 1039999561, 3479543630),
    Elevator(2949235, 1119434212, 3331021649, 464164546, 900285955),
    Elevator(129, 1039999561, 1868895730, 1006255871, 2889020216),
    Elevator(2162826, 1039999561, 3479543630, 1119434212, 2806956034),
    Elevator(4522032, 1039999561, 3205424168, 464164546, 3145160350),
    Elevator(38, 464164546, 3528156989, 1006255871, 3455543403),
    Elevator(1245332, 464164546, 900285955, 1119434212, 3331021649),
    Elevator(1638535, 464164546, 3145160350, 1039999561, 3205424168),
]
