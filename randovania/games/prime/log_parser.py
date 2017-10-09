import os
import re
from typing import NamedTuple, List, Dict

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


class RandomizerLog(NamedTuple):
    version: str
    seed: int
    excluded_pickups: List[int]
    pickup_database: PickupDatabase
    elevators: Dict[str, str]


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

        seed = int(extract_with_regexp(logfile, f, r"^Seed: (\d+)$",
                                       "Could not find Seed"))
        excluded_pickups_str = extract_with_regexp(
            logfile, f, r"^Excluded pickups:\s+((?:\d+\s?)+)$",
            "Could not find excluded pickups")
        excluded_pickups = [int(pickup_str) for pickup_str in excluded_pickups_str.split(" ")]

        pickups = []
        for line in f:
            m = re.match(r"^([^-]+)(?:\s-)+([^-]+)(?:\s-)+([^-]+)$", line)
            if m:
                pickups.append(PickupEntry(*map(str.strip, m.group(1, 2, 3))))
            else:
                break

        elevators = {}
        if f.readline().strip() == "Elevators:":
            for line in f:
                split = line.strip().split("<>")
                if len(split) == 2:
                    elevators[split[0]] = elevators[split[1]]
                else:
                    break

        database = PickupDatabase(percent_less_items, direct_name, custom_mapping, pickups)
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

    database = PickupDatabase(percent_less_items, direct_name, custom_mapping, pickups)
    return RandomizerLog(RANDOMIZER_VERSION, seed, excluded_pickups, database, {})
