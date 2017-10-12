import os
import re
from typing import NamedTuple, List, Dict, TextIO

from randovania import get_data_path
from randovania.games.prime import random
from randovania.resolver.game_description import PickupEntry, PickupDatabase

RANDOMIZER_VERSION = "3.2"

percent_less_items = {
    "Dark Agon Key 1",
    "Dark Agon Key 2",
    "Dark Agon Key 3",
    "Dark Torvus Key 1",
    "Dark Torvus Key 2",
    "Dark Torvus Key 3",
    "Ing Hive Key 1",
    "Ing Hive Key 2",
    "Ing Hive Key 3",
    "Sky Temple Key 1",
    "Sky Temple Key 2",
    "Sky Temple Key 3",
    "Sky Temple Key 4",
    "Sky Temple Key 5",
    "Sky Temple Key 6",
    "Sky Temple Key 7",
    "Sky Temple Key 8",
    "Sky Temple Key 9",
    "_ItemLossItems",
    "_StartingItems",
}

pickup_importance = {
    "Violet Translator": 2,
    "Amber Translator": 2,
    "Emerald Translator": 1,
    "Cobalt Translator": 1,

    "Dark Beam": 3,
    "Light Beam": 3,
    "Annihilator Beam": 2,

    "Boost Ball": 1,
    "Spider Ball": 1,
    "Morph Ball Bomb": 1,

    "Dark Visor": 2,
    "Echo Visor": 1,

    "Grapple Beam": 1,
    "Gravity Boost": 1,
    "Space Jump Boots": 1,
    "Super Missile": 2,
    "Seeker Launcher": 2,
    "Screw Attack": 3,

    "Dark Suit": 1,
    "Light Suit": 3,
}

direct_name = {
    "Amber Translator": 1,
    "Annihilator Beam": 1,
    "Boost Ball": 1,
    "Cobalt Translator": 1,
    "Dark Agon Key 1": 1,
    "Dark Agon Key 2": 1,
    "Dark Agon Key 3": 1,
    "Dark Suit": 1,
    "Dark Torvus Key 1": 1,
    "Dark Torvus Key 2": 1,
    "Dark Torvus Key 3": 1,
    "Dark Visor": 1,
    "Darkburst": 1,
    "Echo Visor": 1,
    "Emerald Translator": 1,
    "Energy Transfer Module": 1,
    "Grapple Beam": 1,
    "Gravity Boost": 1,
    "Ing Hive Key 1": 1,
    "Ing Hive Key 2": 1,
    "Ing Hive Key 3": 1,
    "Light Suit": 1,
    "Morph Ball Bomb": 1,
    "Power Bomb": 2,
    "Screw Attack": 1,
    "Sky Temple Key 1": 1,
    "Sky Temple Key 2": 1,
    "Sky Temple Key 3": 1,
    "Sky Temple Key 4": 1,
    "Sky Temple Key 5": 1,
    "Sky Temple Key 6": 1,
    "Sky Temple Key 7": 1,
    "Sky Temple Key 8": 1,
    "Sky Temple Key 9": 1,
    "Sonic Boom": 1,
    "Space Jump Boots": 1,
    "Spider Ball": 1,
    "Sunburst": 1,
    "Super Missile": 1,
    "Violet Translator": 1,
}

custom_mapping = {
    "Seeker Launcher": {
        "Seeker Launcher": 1,
        "Missile": 5,
    },
    "Missile Launcher": {
        "Missile": 5,
    },
    "Energy Tank \d+": {
        "Energy Tank": 1
    },
    "Missile Expansion \d+": {
        "Missile": 5
    },
    "Power Bomb Expansion \d+": {
        "Power Bomb": 1
    },
    "Beam Ammo Expansion \d+": {
        "Dark Ammo": 50,
        "Light Ammo": 50,
    },
    "Light Beam": {
        "Light Beam": 1,
        "Light Ammo": 50,
    },
    "Dark Beam": {
        "Dark Beam": 1,
        "Dark Ammo": 50,
    },
    "_StartingItems": {
        "Power Beam": 1,
        "Combat Visor": 1,
        "Scan Visor": 1,
        "Varia Suit": 1,
        "Morph Ball": 1,
        "Charge Beam": 1,
    },
    "_ItemLossItems": {
        "Boost Ball": 1,
        "Spider Ball": 1,
        "Morph Ball Bomb": 1,
        "Space Jump Boots": 1,
        "Missile": 5,
    },
}


class ElevatorData(NamedTuple):
    instance_id: int
    world_asset_id: int
    area_asset_id: int


room_name_to_elevator_instance_id: Dict[str, ElevatorData] = {
    "Temple Grounds - Temple Transport C": ElevatorData(589851, 1006255871, 2918020398),
    "Temple Grounds - Transport to Agon Wastes": ElevatorData(1572998, 1006255871, 1660916974),
    "Temple Grounds - Transport to Torvus Bog": ElevatorData(1966093, 1006255871, 2889020216),
    "Temple Grounds - Temple Transport B": ElevatorData(2097251, 1006255871, 1287880522),
    "Temple Grounds - Transport to Sanctuary Fortress": ElevatorData(3342446, 1006255871, 3455543403),
    "Temple Grounds - Temple Transport A": ElevatorData(3538975, 1006255871, 1345979968),
    "Great Temple - Temple Transport A": ElevatorData(152, 2252328306, 408633584),
    "Great Temple - Temple Transport C": ElevatorData(393260, 2252328306, 2556480432),
    "Great Temple - Temple Transport B": ElevatorData(524321, 2252328306, 2399252740),
    "Agon Wastes - Transport to Temple Grounds": ElevatorData(122, 1119434212, 1473133138),
    "Agon Wastes - Transport to Torvus Bog": ElevatorData(1245307, 1119434212, 2806956034),
    "Agon Wastes - Transport to Sanctuary Fortress": ElevatorData(2949235, 1119434212, 3331021649),
    "Torvus Bog - Transport to Temple Grounds": ElevatorData(129, 1039999561, 1868895730),
    "Torvus Bog - Transport to Agon Wastes": ElevatorData(2162826, 1039999561, 3479543630),
    "Torvus Bog - Transport to Sanctuary Fortress": ElevatorData(4522032, 1039999561, 3205424168),
    "Sanctuary Fortress - Transport to Temple Grounds": ElevatorData(38, 464164546, 3528156989),
    "Sanctuary Fortress - Transport to Agon Wastes": ElevatorData(1245332, 464164546, 900285955),
    "Sanctuary Fortress - Transport to Torvus Bog": ElevatorData(1638535, 464164546, 3145160350),
}


def _add_hyphens(s, rest):
    if len(s) % 2 == rest:
        s += " "
    return s + (" -" * 15)


class RandomizerLog(NamedTuple):
    version: str
    seed: int
    excluded_pickups: List[int]
    pickup_database: PickupDatabase
    elevators: Dict[int, ElevatorData]

    def write(self, output_file: TextIO):
        output_file.write("Randomizer V{}\n".format(self.version))
        output_file.write("Seed: {}\n".format(self.seed))
        output_file.write("Excluded pickups: {}\n".format(
            " ".join(str(pickup) for pickup in self.excluded_pickups)))

        for entry in self.pickup_database.entries:
            output_file.write("{:.20} {:.29} {}\n".format(
                _add_hyphens(entry.world, 1),
                _add_hyphens(entry.room, 0),
                entry.item
            ))


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
            logfile, f, r"^Excluded pickups:\s*((?:\d+\s?)*)$",
            "Could not find excluded pickups")
        if excluded_pickups_str:
            excluded_pickups = [int(pickup_str) for pickup_str in excluded_pickups_str.split(" ")]
        else:
            excluded_pickups = []

        pickups = []
        for line in f:
            m = re.match(r"^([^-]+)(?:\s-)+([^-]+)(?:\s-)+([^-]+)$", line)
            if m:
                pickups.append(PickupEntry(*map(str.strip, m.group(1, 2, 3))))
            else:
                break

        elevators: Dict[int, ElevatorData] = {}
        if f.readline().strip() == "Elevators:":
            for line in f:
                split = line.strip().split("<>")
                if len(split) == 2:
                    target = room_name_to_elevator_instance_id[split[1].strip()]
                    elevators[room_name_to_elevator_instance_id[split[0].strip()].instance_id] = target
                else:
                    break
        database = PickupDatabase(percent_less_items, direct_name, custom_mapping, pickup_importance, pickups)
        return RandomizerLog(version, seed, excluded_pickups, database, elevators)


def generate_log(seed: int, excluded_pickups: List[int]) -> RandomizerLog:
    """Reference implementation:
    https://github.com/EthanArmbrust/new-prime-seed-generator/blob/master/src/logChecker.cpp#L4458-L4505"""
    original_log = parse_log(os.path.join(get_data_path(), "prime2_original_log.txt"))
    original_size = len(original_log.pickup_database.entries)

    randomized_items = [""] * original_size

    # add all items from originalList to orderedItems in order
    ordered_items = [
        entry.item
        for entry in original_log.pickup_database.entries
    ]

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
    randomizer = random.Random(seed)
    while ordered_items:
        # grabs a random int between 0 and the size of itemsToAdd
        number = randomizer.next_with_max(len(items_to_add))

        # take the first item from orderedItems and add it to randomizedItems at the "number"th int from itemsToAdd
        randomized_items[items_to_add.pop(number)] = ordered_items.pop(0)

    pickups = [
        PickupEntry(original_entry.world, original_entry.room, randomized_item)
        for randomized_item, original_entry in zip(randomized_items, original_log.pickup_database.entries)
    ]

    database = PickupDatabase(percent_less_items, direct_name, custom_mapping, pickup_importance, pickups)
    return RandomizerLog(RANDOMIZER_VERSION, seed, excluded_pickups, database, {})
