from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataClass
from randovania.game_description.default_database import default_prime2_pickup_database
from randovania.game_description.resources import PickupEntry
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
    sky_temple_keys: LayoutRandomizedFlag
    item_loss: LayoutEnabledFlag
    elevators: LayoutRandomizedFlag
    pickup_quantities: PickupQuantities

    def quantity_for_pickup(self, pickup: PickupEntry) -> Optional[int]:
        return self.pickup_quantities.get(pickup)

    @property
    def as_json(self) -> dict:
        return {
            "game": "mp2-echoes",
            "trick_level": self.trick_level.value,
            "sky_temple_keys": self.sky_temple_keys.value,
            "item_loss": self.item_loss.value,
            "elevators": self.elevators.value,
            "pickup_quantities": {
                pickup.name: quantity
                for pickup, quantity in self.pickup_quantities.items()
            },
        }

    @property
    def as_str(self) -> str:
        strings: List[str] = [self.trick_level.value]

        if self.sky_temple_keys == LayoutRandomizedFlag.VANILLA:
            strings.append("vanilla-sky-temple-keys")

        if self.item_loss == LayoutEnabledFlag.DISABLED:
            strings.append("disabled-item-loss")

        if self.elevators == LayoutRandomizedFlag.RANDOMIZED:
            strings.append("randomized-elevators")

        if self.pickup_quantities:
            strings.append("customized-quantities")

        return "_".join(strings)

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutConfiguration":
        return cls.from_params(
            trick_level=LayoutTrickLevel(json_dict["trick_level"]),
            sky_temple_keys=LayoutRandomizedFlag(json_dict["sky_temple_keys"]),
            item_loss=LayoutEnabledFlag(json_dict["item_loss"]),
            elevators=LayoutRandomizedFlag(json_dict["elevators"]),
            pickup_quantities=json_dict["pickup_quantities"],
        )

    @classmethod
    def from_params(cls,
                    trick_level: LayoutTrickLevel,
                    sky_temple_keys: LayoutRandomizedFlag,
                    item_loss: LayoutEnabledFlag,
                    elevators: LayoutRandomizedFlag,
                    pickup_quantities: Dict[str, int],
                    ) -> "LayoutConfiguration":

        pickup_database = default_prime2_pickup_database()

        quantities = {
            pickup: pickup_database.original_quantity_for(pickup)
            for pickup in pickup_database.pickups.values()
        }
        for name, quantity in pickup_quantities.items():
            quantities[pickup_database.pickup_by_name(name)] = quantity

        if sum(quantities.values()) > pickup_database.total_pickup_count:
            raise ValueError(
                "Invalid pickup_quantities. {} along with unmapped original pickups sum to more than {}".format(
                    pickup_quantities, pickup_database.total_pickup_count
                ))

        return LayoutConfiguration(
            trick_level=trick_level,
            sky_temple_keys=sky_temple_keys,
            item_loss=item_loss,
            elevators=elevators,
            pickup_quantities=PickupQuantities(pickup_database, quantities)
        )


