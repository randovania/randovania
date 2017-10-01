from typing import List, Dict

from randovania import log_parser

echoes_ing_cache_locations = [
    "Battleground",
    "Dark Oasis",
    "Poisoned Bog",
    "Dungeon",
    "Hive Entrance",
    "Hive Dynamo Works",
    "Accursed Lake",
    "Ing Reliquary",
    "Defiled Shrine",
]

sky_temple_grounds = [
    # "Base Access",
    "War Ritual Grounds",
    # "Abandoned Base",
    # "Portal Site",
    # "Shrine Access",
    "Plain of Dark Workship",
    "Defiled Shrine",
    # "Gateway Access",
    # "Ing Windchamber",
    # "Lake Access",
    # "Sky Temple Gateway",
    "Accursed Lake",
    "Profane Path",
    # "Phazon Pit",
    "Phazon Grounds",
    # "Reliquary Access",
    # "Reliquary Grounds",
    "Ing Reliquary",
]

dark_torvus_bog = [

]


def items_in_caches(item_entries: List[log_parser.ItemEntry]) -> Dict[str, str]:
    items = {}
    for entry in item_entries:
        if entry.room in echoes_ing_cache_locations:
            items[entry.room] = entry.item
            # Battleground appears twice in the entries list
            # But since we want the second entry, this code is fine
    return items


def echoes(log: log_parser.RandomizerLog):
    items = items_in_caches(log.item_entries)

    impossible = False
    has_dark_visor = any(map(lambda x: x == "Dark Visor", items.values()))
    has_screw_attack = any(map(lambda x: x == "Screw Attack", items.values()))
    has_temple_key = any(map(lambda x: x.startswith("Sky Temple Key"), items.values()))

    if has_dark_visor:
        print("Dark Visor locked inside Ing Cache!")
        if has_screw_attack:
            print("Screw Attack also inside Ing Cache.")
            impossible = True
        if has_temple_key:
            print("At least one Sky Temple Key also inside Ing Cache")
            impossible = True

    if impossible:
        print("!! This seed is impossible.")
