from typing import Optional, List

_pickups = [
    {
        "world": "Temple Grounds",
        "room": "Hive Chamber A",
        "item": "Missile Expansion"
    },
    {
        "world": "Temple Grounds",
        "room": "Hall of Honored Dead",
        "item": "Seeker Launcher"
    },
    {
        "world": "Temple Grounds",
        "room": "Hive Chamber B",
        "item": "Missile Expansion"
    },
    {
        "world": "Temple Grounds",
        "room": "War Ritual Grounds",
        "item": "Missile Expansion"
    },
    {
        "world": "Temple Grounds",
        "room": "Windchamber Gateway",
        "item": "Energy Tank"
    },
    {
        "world": "Temple Grounds",
        "room": "Transport to Agon Wastes",
        "item": "Missile Expansion"
    },
    {
        "world": "Temple Grounds",
        "room": "Temple Assembly Site",
        "item": "Missile Expansion"
    },
    {
        "world": "Temple Grounds",
        "room": "Grand Windchamber",
        "item": "Sunburst"
    },
    {
        "world": "Temple Grounds",
        "room": "Dynamo Chamber",
        "item": "Power Bomb Expansion"
    },
    {
        "world": "Temple Grounds",
        "room": "Storage Cavern B",
        "item": "Energy Tank"
    },
    {
        "world": "Temple Grounds",
        "room": "Plain of Dark Worship",
        "item": "Missile Expansion"
    },
    {
        "world": "Temple Grounds",
        "room": "Defiled Shrine",
        "item": "Sky Temple Key 8"
    },
    {
        "world": "Temple Grounds",
        "room": "Communication Area",
        "item": "Missile Expansion"
    },
    {
        "world": "Temple Grounds",
        "room": "GFMC Compound",
        "item": "Missile Launcher"
    },
    {
        "world": "Temple Grounds",
        "room": "GFMC Compound",
        "item": "Missile Expansion"
    },
    {
        "world": "Temple Grounds",
        "room": "Accursed Lake",
        "item": "Sky Temple Key 9"
    },
    {
        "world": "Temple Grounds",
        "room": "Fortress Transport Access",
        "item": "Energy Tank"
    },
    {
        "world": "Temple Grounds",
        "room": "Profane Path",
        "item": "Beam Ammo Expansion"
    },
    {
        "world": "Temple Grounds",
        "room": "Phazon Grounds",
        "item": "Missile Expansion"
    },
    {
        "world": "Temple Grounds",
        "room": "Ing Reliquary",
        "item": "Sky Temple Key 7"
    },
    {
        "world": "Great Temple",
        "room": "Transport A Access",
        "item": "Missile Expansion"
    },
    {
        "world": "Great Temple",
        "room": "Temple Sanctuary",
        "item": "Energy Transfer Module"
    },
    {
        "world": "Great Temple",
        "room": "Transport B Access",
        "item": "Missile Expansion"
    },
    {
        "world": "Great Temple",
        "room": "Main Energy Controller",
        "item": "Violet Translator"
    },
    {
        "world": "Great Temple",
        "room": "Main Energy Controller",
        "item": "Light Suit"
    },
    {
        "world": "Agon Wastes",
        "room": "Mining Plaza",
        "item": "Energy Tank"
    },
    {
        "world": "Agon Wastes",
        "room": "Mining Station Access",
        "item": "Energy Tank"
    },
    {
        "world": "Agon Wastes",
        "room": "Mining Station B",
        "item": "Darkburst"
    },
    {
        "world": "Agon Wastes",
        "room": "Transport Center",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Mining Station A",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Ing Cache 4",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Junction Site",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Storage A",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Mine Shaft",
        "item": "Energy Tank"
    },
    {
        "world": "Agon Wastes",
        "room": "Crossroads",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Sand Cache",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Portal Access A",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Judgment Pit",
        "item": "Space Jump Boots"
    },
    {
        "world": "Agon Wastes",
        "room": "Agon Temple",
        "item": "Morph Ball Bomb"
    },
    {
        "world": "Agon Wastes",
        "room": "Trial Tunnel",
        "item": "Dark Agon Key 1"
    },
    {
        "world": "Agon Wastes",
        "room": "Central Mining Station",
        "item": "Beam Ammo Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Warrior's Walk",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Sandcanyon",
        "item": "Power Bomb Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Dark Agon Temple",
        "item": "Dark Suit"
    },
    {
        "world": "Agon Wastes",
        "room": "Battleground",
        "item": "Dark Agon Key 3"
    },
    {
        "world": "Agon Wastes",
        "room": "Battleground",
        "item": "Sky Temple Key 1"
    },
    {
        "world": "Agon Wastes",
        "room": "Agon Energy Controller",
        "item": "Amber Translator"
    },
    {
        "world": "Agon Wastes",
        "room": "Ventilation Area A",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Command Center",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Main Reactor",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Doomed Entry",
        "item": "Dark Agon Key 2"
    },
    {
        "world": "Agon Wastes",
        "room": "Sand Processing",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Storage D",
        "item": "Dark Beam"
    },
    {
        "world": "Agon Wastes",
        "room": "Dark Oasis",
        "item": "Sky Temple Key 2"
    },
    {
        "world": "Agon Wastes",
        "room": "Storage B",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Feeding Pit",
        "item": "Power Bomb Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Bioenergy Production",
        "item": "Energy Tank"
    },
    {
        "world": "Agon Wastes",
        "room": "Ing Cache 1",
        "item": "Light Beam"
    },
    {
        "world": "Agon Wastes",
        "room": "Storage C",
        "item": "Missile Expansion"
    },
    {
        "world": "Agon Wastes",
        "room": "Ing Cache 2",
        "item": "Sonic Boom"
    },
    {
        "world": "Torvus Bog",
        "room": "Torvus Lagoon",
        "item": "Missile Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Portal Chamber",
        "item": "Missile Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Path of Roots",
        "item": "Missile Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Forgotten Bridge",
        "item": "Missile Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Great Bridge",
        "item": "Power Bomb Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Cache A",
        "item": "Beam Ammo Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Plaza Access",
        "item": "Missile Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Abandoned Worksite",
        "item": "Missile Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Poisoned Bog",
        "item": "Sky Temple Key 3"
    },
    {
        "world": "Torvus Bog",
        "room": "Venomous Pond",
        "item": "Dark Torvus Key 3"
    },
    {
        "world": "Torvus Bog",
        "room": "Temple Access",
        "item": "Energy Tank"
    },
    {
        "world": "Torvus Bog",
        "room": "Torvus Plaza",
        "item": "Energy Tank"
    },
    {
        "world": "Torvus Bog",
        "room": "Putrid Alcove",
        "item": "Power Bomb Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Torvus Grove",
        "item": "Missile Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Torvus Temple",
        "item": "Super Missile"
    },
    {
        "world": "Torvus Bog",
        "room": "Dark Torvus Arena",
        "item": "Boost Ball"
    },
    {
        "world": "Torvus Bog",
        "room": "Dark Torvus Arena",
        "item": "Dark Torvus Key 1"
    },
    {
        "world": "Torvus Bog",
        "room": "Underground Tunnel",
        "item": "Missile Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Meditation Vista",
        "item": "Energy Tank"
    },
    {
        "world": "Torvus Bog",
        "room": "Dark Torvus Temple",
        "item": "Dark Visor"
    },
    {
        "world": "Torvus Bog",
        "room": "Cache B",
        "item": "Energy Tank"
    },
    {
        "world": "Torvus Bog",
        "room": "Hydrodynamo Station",
        "item": "Missile Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Torvus Energy Controller",
        "item": "Emerald Translator"
    },
    {
        "world": "Torvus Bog",
        "room": "Undertemple Access",
        "item": "Dark Torvus Key 2"
    },
    {
        "world": "Torvus Bog",
        "room": "Gathering Hall",
        "item": "Missile Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Training Chamber",
        "item": "Missile Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Sacrificial Chamber",
        "item": "Grapple Beam"
    },
    {
        "world": "Torvus Bog",
        "room": "Undertemple",
        "item": "Missile Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Undertemple",
        "item": "Power Bomb"
    },
    {
        "world": "Torvus Bog",
        "room": "Transit Tunnel South",
        "item": "Missile Expansion"
    },
    {
        "world": "Torvus Bog",
        "room": "Transit Tunnel East",
        "item": "Energy Tank"
    },
    {
        "world": "Torvus Bog",
        "room": "Dungeon",
        "item": "Sky Temple Key 4"
    },
    {
        "world": "Torvus Bog",
        "room": "Hydrochamber Storage",
        "item": "Gravity Boost"
    },
    {
        "world": "Torvus Bog",
        "room": "Undertransit One",
        "item": "Missile Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Sanctuary Entrance",
        "item": "Power Bomb Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Reactor Core",
        "item": "Energy Tank"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Transit Station",
        "item": "Power Bomb Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Sanctuary Map Station",
        "item": "Missile Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Hall of Combat Mastery",
        "item": "Missile Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Main Research",
        "item": "Missile Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Culling Chamber",
        "item": "Ing Hive Key 1"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Central Area Transport West",
        "item": "Missile Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Dynamo Works",
        "item": "Spider Ball"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Dynamo Works",
        "item": "Missile Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Hazing Cliff",
        "item": "Missile Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Watch Station",
        "item": "Beam Ammo Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Hive Dynamo Works",
        "item": "Sky Temple Key 6"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Sentinel's Path",
        "item": "Missile Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Watch Station Access",
        "item": "Energy Tank"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Aerial Training Site",
        "item": "Ing Hive Key 3"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Aerial Training Site",
        "item": "Missile Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Main Gyro Chamber",
        "item": "Power Bomb Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Vault",
        "item": "Screw Attack"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Temple Access",
        "item": "Missile Expansion"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Hive Gyro Chamber",
        "item": "Ing Hive Key 2"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Hive Temple",
        "item": "Annihilator Beam"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Sanctuary Energy Controller",
        "item": "Cobalt Translator"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Hive Entrance",
        "item": "Sky Temple Key 5"
    },
    {
        "world": "Sanctuary Fortress",
        "room": "Aerie",
        "item": "Echo Visor"
    }
]
_useless_pickup = "Energy Transfer Module"


def get_index_by_pickup_name(name: str) -> int:
    for i, pickup in enumerate(_pickups):
        if pickup["item"] == name:
            return i
    raise RuntimeError("Unknown pickup name: {}".format(name))


def create_empty_index_array() -> List[int]:
    return [get_index_by_pickup_name(_useless_pickup)] * len(_pickups)
