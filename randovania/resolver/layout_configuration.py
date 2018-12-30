from dataclasses import dataclass
from enum import Enum
from typing import List, Dict

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataClass
from randovania.game_description.resources import PickupEntry
from randovania.games.prime import default_data
from randovania.resolver.pickup_quantities import PickupQuantities


class LayoutTrickLevel(BitPackEnum, Enum):
    NO_TRICKS = "no-tricks"
    TRIVIAL = "trivial"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    HYPERMODE = "hypermode"
    MINIMAL_RESTRICTIONS = "minimal-restrictions"


class LayoutMode(BitPackEnum, Enum):
    STANDARD = "standard"
    MAJOR_ITEMS = "major-items"


class LayoutSkyTempleKeyMode(BitPackEnum, Enum):
    VANILLA = "vanilla"
    ALL_BOSSES = "all-bosses"
    ALL_GUARDIANS = "all-guardians"
    FULLY_RANDOM = "fully-random"


class LayoutRandomizedFlag(BitPackEnum, Enum):
    VANILLA = "vanilla"
    RANDOMIZED = "randomized"


class LayoutEnabledFlag(BitPackEnum, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class LayoutDifficulty(BitPackEnum, Enum):
    NORMAL = "normal"


@dataclass(frozen=True)
class LayoutConfiguration(BitPackDataClass):
    trick_level: LayoutTrickLevel
    sky_temple_keys: LayoutSkyTempleKeyMode
    item_loss: LayoutEnabledFlag
    elevators: LayoutRandomizedFlag
    pickup_quantities: PickupQuantities

    def quantity_for_pickup(self, pickup: PickupEntry) -> int:
        return self.pickup_quantities.get(pickup)

    @property
    def game_data(self) -> dict:
        return default_data.decode_default_prime2()

    @property
    def as_json(self) -> dict:
        return {
            "game": "mp2-echoes",
            "trick_level": self.trick_level.value,
            "sky_temple_keys": self.sky_temple_keys.value,
            "item_loss": self.item_loss.value,
            "elevators": self.elevators.value,
            "pickup_quantities": self.pickup_quantities.as_json,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutConfiguration":
        return cls.from_params(
            trick_level=LayoutTrickLevel(json_dict["trick_level"]),
            sky_temple_keys=LayoutSkyTempleKeyMode(json_dict["sky_temple_keys"]),
            item_loss=LayoutEnabledFlag(json_dict["item_loss"]),
            elevators=LayoutRandomizedFlag(json_dict["elevators"]),
            pickup_quantities=json_dict["pickup_quantities"],
        )

    @classmethod
    def from_params(cls,
                    trick_level: LayoutTrickLevel,
                    sky_temple_keys: LayoutSkyTempleKeyMode,
                    item_loss: LayoutEnabledFlag,
                    elevators: LayoutRandomizedFlag,
                    pickup_quantities: Dict[str, int],
                    ) -> "LayoutConfiguration":

        return LayoutConfiguration(
            trick_level=trick_level,
            sky_temple_keys=sky_temple_keys,
            item_loss=item_loss,
            elevators=elevators,
            pickup_quantities=PickupQuantities.from_params(pickup_quantities)
        )

    @classmethod
    def default(cls) -> "LayoutConfiguration":
        return cls.from_params(
            trick_level=LayoutTrickLevel.NO_TRICKS,
            sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
            item_loss=LayoutEnabledFlag.ENABLED,
            elevators=LayoutRandomizedFlag.VANILLA,
            pickup_quantities={}
        )
