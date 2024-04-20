from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.games.game import ProgressiveItemTuples


def tuples() -> ProgressiveItemTuples:
    return [
        ("Progressive Polar Star", ("Polar Star", "Spur")),
        ("Progressive Booster", ("Booster 0.8", "Booster 2.0")),
        ("Progressive Missile Launcher", ("Missile Launcher", "Super Missile Launcher")),
    ]
