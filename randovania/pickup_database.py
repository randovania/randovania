from typing import Dict, List, Tuple

import re

from randovania.game_description import ResourceInfo, ResourceDatabase, ResourceType

ResourceGain = List[Tuple[ResourceInfo, int]]

pickup_name_to_resource = {}  # type: Dict[str, List[Tuple[ResourceInfo, int]]]

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


def pickup_name_to_resource_gain(name: str,
                                 database: ResourceDatabase) -> ResourceGain:
    infos = database.get_by_type(ResourceType.ITEM)

    result = []
    if name not in percent_less_items:
        result.append((database.get_by_type_and_index(ResourceType.ITEM, 47),
                       1))

    if name in direct_name:
        for info in infos:
            if info.long_name == name:
                return result + [(info, direct_name[name])]
        raise ValueError("Pickup '{}' not found in database.".format(name))
    else:
        for pattern, values in custom_mapping.items():
            if re.match(pattern, name):
                starting_size = len(result)
                for info in infos:
                    if info.long_name in values:
                        result.append((info, values[info.long_name]))
                if len(result) - starting_size != len(values):
                    raise ValueError(
                        "Pattern '{}' (matched by '{}') have resource not found in database. Found {}".
                        format(pattern, name, result))
                return result

    raise ValueError("'{}' is unknown by pickup_database".format(name))
