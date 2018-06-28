from enum import Enum
from typing import NamedTuple, Tuple


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


class SolverPath(NamedTuple):
    node_name: str
    previous_nodes: Tuple[str, ...]


class LayoutDescription(NamedTuple):
    seed_number: int
    logic: LayoutLogic
    mode: LayoutMode
    sky_temple_keys: LayoutRandomizedFlag
    item_loss: LayoutEnabledFlag
    elevators: LayoutRandomizedFlag
    hundo_guaranteed: LayoutEnabledFlag
    difficulty: LayoutDifficulty
    version: str
    pickup_mapping: Tuple[int, ...]
    solver_path: Tuple[SolverPath, ...]
