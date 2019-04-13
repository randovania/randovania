from typing import Dict, Optional

RANDOMIZER_VERSION = "3.2"


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

elevator_name_to_id: Dict[str, int] = {
    "Temple Grounds - Temple Transport C": 589851,
    "Temple Grounds - Transport to Agon Wastes": 1572998,
    "Temple Grounds - Transport to Torvus Bog": 1966093,
    "Temple Grounds - Temple Transport B": 2097251,
    "Temple Grounds - Transport to Sanctuary Fortress": 3342446,
    "Temple Grounds - Temple Transport A": 3538975,
    "Great Temple - Temple Transport A": 152,
    "Great Temple - Temple Transport C": 393260,
    "Great Temple - Temple Transport B": 524321,
    "Agon Wastes - Transport to Temple Grounds": 122,
    "Agon Wastes - Transport to Torvus Bog": 1245307,
    "Agon Wastes - Transport to Sanctuary Fortress": 2949235,
    "Torvus Bog - Transport to Temple Grounds": 129,
    "Torvus Bog - Transport to Agon Wastes": 2162826,
    "Torvus Bog - Transport to Sanctuary Fortress": 4522032,
    "Sanctuary Fortress - Transport to Temple Grounds": 38,
    "Sanctuary Fortress - Transport to Agon Wastes": 1245332,
    "Sanctuary Fortress - Transport to Torvus Bog": 1638535,
}

elevator_id_to_name = {
    elevator_id: name
    for name, elevator_id in elevator_name_to_id.items()
}
