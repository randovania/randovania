from randovania.game_description.resources.resource_type import ResourceType


class PickupIndex:
    _index: int

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.PICKUP_INDEX

    @property
    def long_name(self) -> str:
        return "PickupIndex {}".format(self._index)

    def __init__(self, index: int):
        self._index = index

    def __lt__(self, other: "PickupIndex") -> bool:
        return self._index < other._index

    def __repr__(self):
        return self.long_name

    def __hash__(self):
        return self._index

    def __eq__(self, other):
        return isinstance(other, PickupIndex) and other._index == self._index

    @property
    def index(self) -> int:
        return self._index

    @property
    def is_major_location(self) -> bool:
        return self._index in _MAJOR_LOCATIONS

_MAJOR_LOCATIONS = [
    1,   # Hall of Honored Dead - Seeker Launcher
    4,   # Windchamber Gateway - Energy Tank
    7,   # Grand Windchamber - Sunburst
    9,   # Storage Cavern B - Energy Tank
    11,  # Defiled Shrine - Sky Temple Key 9
    13,  # GFMC Compound - Missile Launcher
    15,  # Accursed Lake - Sky Temple Key 7
    16,  # Fortress Transport Access - Energy Tank
    19,  # Ing Reliquary - Sky Temple Key 8
    21,  # Temple Sanctuary - Energy Transfer Module
    23,  # Main Energy Controller - Violet Translator
    24,  # Main Energy Controller - Light Suit
    25,  # Mining Plaza - Energy Tank
    26,  # Mining Station Access - Energy Tank
    27,  # Mining Station B - Darkburst
    33,  # Mine Shaft - Energy Tank
    37,  # Judgment Pit - Space Jump Boots
    38,  # Agon Temple - Morph Ball Bomb
    39,  # Trial Tunnel - Dark Agon Key 1
    43,  # Dark Agon Temple - Dark Suit
    44,  # Battleground - Dark Agon Key 3
    45,  # Battleground - Sky Temple Key 1
    46,  # Agon Energy Controller - Amber Translator
    50,  # Doomed Entry - Dark Agon Key 2
    52,  # Storage D - Dark Beam
    53,  # Dark Oasis - Sky Temple Key 2
    56,  # Bioenergy Production - Energy Tank
    57,  # Ing Cache 1 - Light Beam
    59,  # Ing Cache 2 - Sonic Boom
    68,  # Poisoned Bog - Sky Temple Key 3
    69,  # Venomous Pond - Dark Torvus Key 3
    70,  # Temple Access - Energy Tank
    71,  # Torvus Plaza - Energy Tank
    74,  # Torvus Temple - Super Missile
    75,  # Dark Torvus Arena - Boost Ball
    76,  # Dark Torvus Arena - Dark Torvus Key 1
    78,  # Meditation Vista - Energy Tank
    79,  # Dark Torvus Temple - Dark Visor
    80,  # Cache B - Energy Tank
    82,  # Torvus Energy Controller - Emerald Translator
    83,  # Undertemple Access - Dark Torvus Key 2
    86,  # Sacrificial Chamber - Grapple Beam
    88,  # Undertemple - Power Bomb
    90,  # Transit Tunnel East - Energy Tank
    91,  # Dungeon - Sky Temple Key 4
    92,  # Hydrochamber Storage - Gravity Boost
    95,  # Reactor Core - Energy Tank
    100, # Culling Chamber - Ing Hive Key 1
    102, # Dynamo Works - Spider Ball
    106, # Hive Dynamo Works - Sky Temple Key 6
    108, # Watch Station Access - Energy Tank
    109, # Aerial Training Site - Ing Hive Key 3
    112, # Vault - Screw Attack
    114, # Hive Gyro Chamber - Ing Hive Key 2
    115, # Hive Temple - Annihilator Beam
    116, # Sanctuary Energy Controller - Cobalt Translator
    117, # Hive Entrance - Sky Temple Key 5
    118, # Aerie - Echo Visor
]