import dataclasses
import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Set, Iterator, Dict


class BitPackEnum:
    @classmethod
    def bit_pack_format(cls: Enum) -> str:
        return "u{}".format(math.ceil(math.log2(len(cls.__members__))))

    def bit_pack_arguments(self) -> Iterator[int]:
        cls: Enum = self.__class__
        yield list(cls.__members__.values()).index(self)


class BitPackDataClass:
    @classmethod
    def bit_pack_format(cls) -> str:
        return "".join(
            field.type.bit_pack_format()
            for field in dataclasses.fields(cls)
        )

    def bit_pack_arguments(self) -> Iterator[int]:
        for field in dataclasses.fields(self):
            yield from getattr(self, field.name).bit_pack_arguments()


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


class PickupQuantities:
    pickup_quantities: Dict[str, int]

    def __init__(self, pickup_quantities: Dict[str, int]):
        self.pickup_quantities = pickup_quantities

    @classmethod
    def bit_pack_format(cls) -> str:
        return ""

    def bit_pack_arguments(self) -> Iterator[int]:
        yield from ()

    def __eq__(self, other):
        return isinstance(other, PickupQuantities) and self.pickup_quantities == other.pickup_quantities


@dataclass(frozen=True)
class LayoutConfiguration(BitPackDataClass):
    trick_level: LayoutTrickLevel
    sky_temple_keys: LayoutRandomizedFlag
    item_loss: LayoutEnabledFlag
    elevators: LayoutRandomizedFlag
    pickup_quantities: PickupQuantities

    def __init__(self,
                 trick_level: LayoutTrickLevel,
                 sky_temple_keys: LayoutRandomizedFlag,
                 item_loss: LayoutEnabledFlag,
                 elevators: LayoutRandomizedFlag,
                 pickup_quantities: Dict[str, int],
                 ):
        object.__setattr__(self, "trick_level", trick_level)
        object.__setattr__(self, "sky_temple_keys", sky_temple_keys)
        object.__setattr__(self, "item_loss", item_loss)
        object.__setattr__(self, "elevators", elevators)
        object.__setattr__(self, "pickup_quantities", PickupQuantities(pickup_quantities))

    def quantity_for_pickup(self, pickup_name: str) -> Optional[int]:
        return self.pickup_quantities.pickup_quantities.get(pickup_name)

    @property
    def pickups_with_configured_quantity(self) -> Set[str]:
        return set(self.pickup_quantities.pickup_quantities.keys())

    @property
    def as_json(self) -> dict:
        return {
            "game": "mp2-echoes",
            "trick_level": self.trick_level.value,
            "sky_temple_keys": self.sky_temple_keys.value,
            "item_loss": self.item_loss.value,
            "elevators": self.elevators.value,
            "pickup_quantities": self.pickup_quantities.pickup_quantities,
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
        return LayoutConfiguration(
            trick_level=LayoutTrickLevel(json_dict["trick_level"]),
            sky_temple_keys=LayoutRandomizedFlag(json_dict["sky_temple_keys"]),
            item_loss=LayoutEnabledFlag(json_dict["item_loss"]),
            elevators=LayoutRandomizedFlag(json_dict["elevators"]),
            pickup_quantities=json_dict["pickup_quantities"],
        )
