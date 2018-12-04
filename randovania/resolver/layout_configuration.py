from enum import Enum
from typing import NamedTuple, List, Optional, Set


class LayoutTrickLevel(Enum):
    NO_TRICKS = "no-tricks"
    TRIVIAL = "trivial"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    HYPERMODE = "hypermode"
    MINIMAL_RESTRICTIONS = "minimal-restrictions"


class LayoutMode(Enum):
    STANDARD = "standard"
    MAJOR_ITEMS = "major-items"


class LayoutRandomizedFlag(Enum):
    VANILLA = "vanilla"
    RANDOMIZED = "randomized"


class LayoutEnabledFlag(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class LayoutDifficulty(Enum):
    NORMAL = "normal"


class LayoutConfiguration(NamedTuple):
    trick_level: LayoutTrickLevel
    sky_temple_keys: LayoutRandomizedFlag
    item_loss: LayoutEnabledFlag
    elevators: LayoutRandomizedFlag
    pickup_quantities: dict

    def quantity_for_pickup(self, pickup_name: str) -> Optional[int]:
        return self.pickup_quantities.get(pickup_name)

    @property
    def pickups_with_configured_quantity(self) -> Set[str]:
        return set(self.pickup_quantities.keys())

    @property
    def as_json(self) -> dict:
        return {
            "game": "mp2-echoes",
            "trick_level": self.trick_level.value,
            "sky_temple_keys": self.sky_temple_keys.value,
            "item_loss": self.item_loss.value,
            "elevators": self.elevators.value,
            "pickup_quantities": self.pickup_quantities,
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
