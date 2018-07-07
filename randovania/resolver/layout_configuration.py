from enum import Enum
from typing import NamedTuple


class LayoutLogic(Enum):
    NO_GLITCHES = "no-glitches"
    NORMAL = "normal"
    HARD = "hard"


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
    seed_number: int
    logic: LayoutLogic
    mode: LayoutMode
    sky_temple_keys: LayoutRandomizedFlag
    item_loss: LayoutEnabledFlag
    elevators: LayoutRandomizedFlag
    hundo_guaranteed: LayoutEnabledFlag
    difficulty: LayoutDifficulty

    @property
    def as_json(self) -> dict:
        return {
            "game": "mp2-echoes",
            "seed": self.seed_number,
            "logic": self.logic.value,
            "mode": self.mode.value,
            "sky_temple_keys": self.sky_temple_keys.value,
            "item_loss": self.item_loss.value,
            "elevators": self.elevators.value,
            "hundo_guaranteed": self.hundo_guaranteed.value,
            "difficulty": self.difficulty.value,
        }

    @property
    def as_str(self) -> str:
        return "-".join(s.value if hasattr(s, "value") else str(s) for s in self)
