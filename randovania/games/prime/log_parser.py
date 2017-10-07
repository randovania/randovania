import re
import typing

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
        # TODO: lose items when reaching the item loss spot
        # "Boost Ball": 1,
        # "Spider Ball": 1,
        "Morph Ball Bomb": 1,
        # "Space Jump Boots": 1,
        "Missile": 5,
    },
}


class RandomizerLog(typing.NamedTuple):
    version: str
    seed: str
    excluded_pickups: str
    pickup_database: PickupDatabase


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

        seed = extract_with_regexp(logfile, f, r"^Seed: (\d+)$",
                                   "Could not find Seed")
        excluded_pickups = extract_with_regexp(
            logfile, f, r"^Excluded pickups: (\d+)$",
            "Could not find excluded pickups")

        pickups = []
        for line in f:
            m = re.match(r"^([^-]+)(?:\s-)+([^-]+)(?:\s-)+([^-]+)$", line)
            if m:
                pickups.append(PickupEntry(*map(str.strip, m.group(1, 2, 3))))

        database = PickupDatabase(percent_less_items, direct_name, custom_mapping, pickups)
        return RandomizerLog(version, seed, excluded_pickups, database)
