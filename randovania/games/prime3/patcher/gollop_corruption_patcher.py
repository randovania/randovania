import hashlib
from typing import List

from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_info import CurrentResources

LAYOUT_LETTERS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ(){}[]<>=,.!#^-+?"
ITEM_NAME_TO_INDEX = {
    "Power Beam": 0,
    "Plasma Beam": 1,
    "Nova Beam": 2,
    "Charge Beam": 3,

    "Missile Launcher": 1000,
    "Ice Missile": 5,
    "Seeker Missile": 6,

    "Grapple Lasso": 7,
    "Grapple Swing": 8,
    "Grapple Voltage": 9,

    "Combat Visor": 11,
    "Scan Visor": 12,
    "Command Visor": 13,
    "X-Ray Visor": 14,

    "Space Jump Boots": 15,
    "Screw Attack": 16,

    "Hazard Shield": 17,
    "Energy Tank": 20,

    "Morph Ball": 32,
    "Morph Ball Bombs": 10,
    "Boost Ball": 33,
    "Spider Ball": 34,
    "CannonBall": 48,

    "Hypermode": 35,
    "Hyper Missile": 37,
    "Hyper Ball": 38,
    "Hyper Grapple": 39,

    "Ship Grapple": 44,
    "Ship Missile": 1001,
    "Missile Expansion": 4,
    "Ship Missile Expansion": 45
}
LETTER_TO_ITEM_MAPPING = {
    "0": ["Power Beam"],
    "1": ["Plasma Beam"],
    "2": ["Nova Beam"],
    "3": ["Charge Beam"],
    "4": ["Missile Expansion"],
    "5": ["Ice Missile"],
    "6": ["Seeker Missile"],
    "7": ["Grapple Lasso"],
    "8": ["Grapple Swing"],
    "9": ["Grapple Voltage"],
    "a": ["Morph Ball Bombs"],
    "b": ["Combat Visor"],
    "c": ["Scan Visor"],
    "d": ["Command Visor"],
    "e": ["X-Ray Visor"],
    "f": ["Space Jump Boots"],
    "g": ["Screw Attack"],
    "h": ["Hazard Shield"],
    # "i": ["Energy"],
    # "j": ["HyperModeEnergy"],
    "k": ["Energy Tank"],
    # "l": ["ItemPercentage"],
    # "m": ["Fuses"],
    "n": ["Energy Cell 1"],
    "o": ["Energy Cell 2"],
    "p": ["Energy Cell 3"],
    "q": ["Energy Cell 4"],
    "r": ["Energy Cell 5"],
    "s": ["Energy Cell 6"],
    "t": ["Energy Cell 7"],
    "u": ["Energy Cell 8"],
    "v": ["Energy Cell 9"],
    "w": ["Morph Ball"],
    "x": ["Boost Ball"],
    "y": ["Spider Ball"],
    "z": ["Hypermode"],
    # "A": ["HyperModeBeam"],
    "B": ["Hyper Missile"],
    "C": ["Hyper Ball"],
    "D": ["Hyper Grapple"],
    # "E": ["HyperModePermanent"],
    # "F": ["HyperModePhaaze"],
    # "G": ["HyperModeOriginal"],
    "H": ["Ship Grapple"],
    "I": ["Ship Missile Expansion"],
    # "J": ["FaceCorruptionLevel"],
    # "K": ["PhazonBall"],
    "L": ["CannonBall"],
    # "M": ["ActivateMorphballBoost"],
    # "N": ["HyperShot"],
    # "O": ["CommandVisorJammed"],
    # "P": ["Stat_Enemies_Killed"],
    # "Q": ["Stat_ShotsFired"],
    # "R": ["Stat_DamageReceived"],
    # "S": ["Stat_DataSaves"],
    # "T": ["Stat_HypermodeUses"],
    # "U": ["Stat_CommandoKills"],
    # "V": ["Stat_TinCanHighScore"],
    # "W": ["Stat_TinCanCurrentScore"],
    "X": ["Missile Expansion"] * 2,
    "Y": ["Missile Expansion"] * 3,
    "Z": ["Missile Expansion"] * 4,
    "(": ["Missile Expansion"] * 5,
    ")": ["Missile Expansion"] * 6,
    "{": ["Progressive Missile"],
    "}": ["Progressive Beam"],
    "[": ["Energy Tank", "Energy Tank"],
    "]": ["Energy Tank", "Energy Tank", "Energy Tank"],
    "<": ["Ship Missile Expansion", "Ship Missile Expansion"],
    ">": ["Missile Expansion", "Energy Tank"],
    "=": ["Energy Tank", "Missile Expansion"],
    ",": ["Missile Expansion", "Energy Tank", "Missile Expansion"],
    ".": ["Missile Expansion", "Ship Missile Expansion"],
    "!": ["Ship Missile Expansion", "Missile Expansion"],
    "#": ["Missile Launcher"],
    "^": ["Ship Missile"],
    "-": ["Ship Missile Expansion", "Energy Tank"],
    "+": ["Energy Tank", "Ship Missile Expansion"],
    "?": ["Missile Expansion", "Ship Missile Expansion", "Missile Expansion"],
}
ITEM_NAME_TO_LETTER_MAPPING = {
    items[0]: letter
    for letter, items in LETTER_TO_ITEM_MAPPING.items()
    if len(items) == 1
}

STARTING_ITEMS_ORDER = [
    "EnergyAmount",
    "EnergyCapacity",
    "EnergyTankAmount",
    "EnergyTankCapacity",
    "FusesAmount",
    "FusesCapacity",
    "PlayerInventoryItemAmount",
    "PlayerInventoryItemCapacity",
    "PowerBeam",
    "PlasmaBeam",
    "NovaBeam",
    "ChargeUpgrade",
    "MissileAmount",
    "MissileCapacity",
    "IceMissile",
    "Seekers",
    "GrappleBeamPull",
    "GrappleBeamSwing",
    "GrappleBeamVoltage",
    "Bomb",
    "ScanVisor",
    "CommandVisor",
    "XRayVisor",
    "MorphBall",
    "BoostBall",
    "SpiderBall",
    "DoubleJump",
    "SuitType",
    "ScrewAttack",
    "HyperModeTank",
    "HyperModeBeam",
    "HyperModeGrapple",
    "HyperModeMissile",
    "HyperModeBall",
    "HyperModePermanent",
    "HyperModePhaaze",
    "HyperModeOriginal",
    "HyperModeCharge",
    "ShipMissileAmount",
    "ShipMissileCapacity",
    "ShipGrapple",
]
STARTING_ITEMS_NAME_ALIAS = {
    "EnergyAmount": "Energy",
    "EnergyCapacity": "Energy",
    "EnergyTankAmount": "EnergyTank",
    "EnergyTankCapacity": "EnergyTank",
    "FusesAmount": "Fuses",
    "FusesCapacity": "Fuses",
    "MissileAmount": "Missile",
    "MissileCapacity": "Missile",
    "ShipMissileAmount": "ShipMissile",
    "ShipMissileCapacity": "ShipMissile",
}
_TWO_BYTE_VALUES = {STARTING_ITEMS_ORDER.index("MissileAmount"), STARTING_ITEMS_ORDER.index("MissileCapacity")}


def layout_string_for_items(item_names: List[str]) -> str:
    letters = [LAYOUT_LETTERS[0]] * 2
    for item in item_names:
        letters.append(ITEM_NAME_TO_LETTER_MAPPING[item])

    result = "".join(letters)
    sha = hashlib.sha256(result.encode("ascii"))
    result += sha.hexdigest()[:5]

    return result


def starting_location_for(location: AreaLocation) -> str:
    return f"custom {location.world_asset_id:x} {location.area_asset_id:x}"


def starting_items_for(resources: CurrentResources, hypermode_original: int) -> str:
    capacity_by_short_name = {
        item.short_name: capacity
        for item, capacity in resources.items()
        if isinstance(item, ItemResourceInfo)
    }
    capacity_by_short_name["HyperModeOriginal"] = hypermode_original

    result_values = [
        capacity_by_short_name.get(STARTING_ITEMS_NAME_ALIAS.get(item, item), 0)
        for item in STARTING_ITEMS_ORDER
    ]
    return "custom " + "".join([
        "{:02x}".format(value) if index in _TWO_BYTE_VALUES else "{:x}".format(value)
        for index, value in enumerate(result_values)
    ])
