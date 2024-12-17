from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from randovania.game.gui import ProgressiveItemTuples


def tuples() -> ProgressiveItemTuples:
    return [
        ("Progressive Polar Star", ("Polar Star", "Spur")),
        ("Progressive Booster", ("Booster 0.8", "Booster 2.0")),
        ("Progressive Missile Launcher", ("Missile Launcher", "Super Missile Launcher")),
    ]
