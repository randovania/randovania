import copy
import re
from collections import defaultdict
from typing import NamedTuple, List, Dict, TextIO, Optional

from randovania.games.prime import claris_random, binary_data
from randovania.resolver.game_patches import GamePatches

RANDOMIZER_VERSION = "3.2"


class Elevator:
    world_number: int
    area_number: int
    world_asset_id: int
    area_asset_id: int
    instance_id: int
    destination_world: int
    destination_area: int
    connected_elevator: "Elevator"

    def __init__(self, world_number, area_number, world_id, area_id, instance_id, destination_world, destination_area):
        self.world_number = world_number
        self.area_number = area_number
        self.world_asset_id = world_id
        self.area_asset_id = area_id
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
    Elevator(1, 9, 1006255871, 2918020398, 589851, 2252328306, 2556480432),
    Elevator(1, 24, 1006255871, 1660916974, 1572998, 1119434212, 1473133138),
    Elevator(1, 30, 1006255871, 2889020216, 1966093, 1039999561, 1868895730),
    Elevator(1, 32, 1006255871, 1287880522, 2097251, 2252328306, 2399252740),
    Elevator(1, 51, 1006255871, 3455543403, 3342446, 464164546, 3528156989),
    Elevator(1, 54, 1006255871, 1345979968, 3538975, 2252328306, 408633584),
    Elevator(2, 0, 2252328306, 408633584, 152, 1006255871, 1345979968),
    Elevator(2, 6, 2252328306, 2556480432, 393260, 1006255871, 2918020398),
    Elevator(2, 8, 2252328306, 2399252740, 524321, 1006255871, 1287880522),
    Elevator(3, 0, 1119434212, 1473133138, 122, 1006255871, 1660916974),
    Elevator(3, 19, 1119434212, 2806956034, 1245307, 1039999561, 3479543630),
    Elevator(3, 45, 1119434212, 3331021649, 2949235, 464164546, 900285955),
    Elevator(4, 0, 1039999561, 1868895730, 129, 1006255871, 2889020216),
    Elevator(4, 33, 1039999561, 3479543630, 2162826, 1119434212, 2806956034),
    Elevator(4, 69, 1039999561, 3205424168, 4522032, 464164546, 3145160350),
    Elevator(5, 0, 464164546, 3528156989, 38, 1006255871, 3455543403),
    Elevator(5, 19, 464164546, 900285955, 1245332, 1119434212, 3331021649),
    Elevator(5, 25, 464164546, 3145160350, 1638535, 1039999561, 3205424168),
]


def try_randomize_elevators(randomizer: claris_random.Random) -> Optional[List[Elevator]]:
    elevator_database: List[Elevator] = copy.deepcopy(echoes_elevators)

    elevator_list = copy.copy(elevator_database)
    elevators_by_world: Dict[int, List[Elevator]] = defaultdict(list)
    for elevator in elevator_list:
        elevators_by_world[elevator.world_number].append(elevator)

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

        elevators_by_world[source_elevator.world_number].remove(source_elevator)
        elevators_by_world[target_elevator.world_number].remove(target_elevator)
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
                if celevator2.world_number == celevator1.world_number or celevator2.area_asset_id == celevator1.destination_area:
                    celevator_list1.append(celevator2)
                    list3.remove(celevator2)
                else:
                    index += 1
        if celevator_list1:
            celevator_list3 = celevator_list1
        else:
            # Randomization failed
            return None

    return elevator_database


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


def _add_hyphens(s, rest):
    if len(s) % 2 == rest:
        s += " "
    return s + (" -" * 15)


class RandomizerLog(NamedTuple):
    version: str
    seed: int
    excluded_pickups: List[int]
    pickup_mapping: List[int]
    elevators: List[Elevator]

    def write(self, output_file: TextIO):
        output_file.write("Randomizer V{}\n".format(self.version))
        if self.seed:
            output_file.write("Seed: {}\n".format(self.seed))
        if self.excluded_pickups:
            output_file.write("Excluded pickups: {}\n".format(
                " ".join(str(pickup) for pickup in self.excluded_pickups)))
        else:
            output_file.write("Generated from a provided pickup list\n")

        pickups = binary_data.decode_default_prime2()["resource_database"]["pickups"]
        for original_index, new_index in enumerate(self.pickup_mapping):
            entry = pickups[original_index]
            output_file.write("{:.20} {:.29} {}\n".format(
                _add_hyphens(entry["world"], 1),
                _add_hyphens(entry["room"], 0),
                pickups[new_index]["item"] if new_index is not None else "Nothing"
            ))

        if self.elevators:
            print("\nElevators:")
            for elevator in self.elevators:
                print("{} <> {}".format(elevator_id_to_name[elevator.instance_id],
                                        elevator_id_to_name[elevator.connected_elevator.instance_id]))


class InvalidLogFileException(Exception):
    def __init__(self, logfile, reason):
        super().__init__("File '{}' is not a valid Randomizer log: {}".format(
            logfile, reason))


def extract_with_regexp(logfile, f, regex, invalid_reason):
    match = re.match(regex, f.readline().strip())
    if match:
        return match.group(1)
    else:
        raise InvalidLogFileException(logfile, invalid_reason)


def parse_log(logfile: str) -> RandomizerLog:
    echoes_data = binary_data.decode_default_prime2()
    name_to_index = {
        pickup["item"]: index
        for index, pickup in enumerate(echoes_data["resource_database"]["pickups"])
    }

    with open(logfile) as f:
        version = extract_with_regexp(logfile, f, r"Randomizer V(\d+\.\d+)",
                                      "Could not find Randomizer version")
        if version != RANDOMIZER_VERSION:
            raise InvalidLogFileException(
                logfile, "Unexpected version {}, expected {}".format(
                    version, RANDOMIZER_VERSION))

        seed = int(extract_with_regexp(logfile, f, r"^Seed: (\d+)",
                                       "Could not find Seed"))
        excluded_pickups_str = extract_with_regexp(
            logfile, f, r"^Excluded pickups:\s*((?:(?:\d+\s?)*)|None)$",
            "Could not find excluded pickups")

        if excluded_pickups_str == "None":
            excluded_pickups = []
        else:
            excluded_pickups = [int(pickup_str) for pickup_str in excluded_pickups_str.split(" ")]

        pickups: List[int] = []
        for line in f:
            m = re.match(r"^([^-]+)(?:\s-)+([^-]+)(?:\s-)+([^-]+)$", line)
            if m:
                world, room, item = map(str.strip, m.group(1, 2, 3))
                pickups.append(name_to_index[item])
            else:
                break

        elevator_database: List[Elevator] = copy.deepcopy(echoes_elevators)
        elevator_database_by_id: Dict[int, Elevator] = {
            elevator.instance_id: elevator
            for elevator in elevator_database
        }

        elevators: List[Elevator] = []
        if f.readline().strip() == "Elevators:":
            for line in f:
                split = line.strip().split("<>")
                if len(split) == 2:
                    source = elevator_database_by_id[elevator_name_to_id[split[0].strip()]]
                    target = elevator_database_by_id[elevator_name_to_id[split[1].strip()]]
                    source.connected_elevator = target
                    elevators.append(source)
                else:
                    break

        return RandomizerLog(version, seed, excluded_pickups, pickups, elevators)


def generate_log(seed: int,
                 excluded_pickups: List[int],
                 randomize_elevators: bool) -> RandomizerLog:
    """Reference implementation:
    https://github.com/EthanArmbrust/new-prime-seed-generator/blob/master/src/logChecker.cpp#L4458-L4505"""

    echoes_data = binary_data.decode_default_prime2()
    original_size = len(echoes_data["resource_database"]["pickups"])

    randomized_items = [-1] * original_size

    # add all items from originalList to orderedItems in order
    ordered_items = list(range(original_size))

    # fill addedItems with ordered integers
    items_to_add = list(range(original_size))

    # take the excluded items and set them in the randomizedItems list
    for excluded in excluded_pickups:
        randomized_items[excluded] = ordered_items[excluded]

    # remove the excluded items from orderedItems list and the addedItems list
    for i, excluded in enumerate(excluded_pickups):
        ordered_items.pop(excluded - i)
        items_to_add.pop(excluded - i)

    # begin Randomizing
    randomizer = claris_random.Random(seed)
    while ordered_items:
        # grabs a random int between 0 and the size of itemsToAdd
        number = randomizer.next_with_max(len(items_to_add))

        # take the first item from orderedItems and add it to randomizedItems at the "number"th int from itemsToAdd
        randomized_items[items_to_add.pop(number)] = ordered_items.pop(0)

    elevators: List[Elevator] = []
    if randomize_elevators:
        while not elevators:
            elevators = try_randomize_elevators(randomizer)

    return RandomizerLog(RANDOMIZER_VERSION, seed, excluded_pickups, randomized_items, elevators)


def log_with_patches(patches: GamePatches) -> RandomizerLog:
    return RandomizerLog(RANDOMIZER_VERSION, None, None, patches.pickup_mapping, [])
