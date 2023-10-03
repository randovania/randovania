from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.games.game import ProgressiveItemTuples


def tuples() -> ProgressiveItemTuples:
    return [
        ("Progressive Missile", ("Ice Missile", "Seeker Missile")),
        ("Progressive Beam", ("Plasma Beam", "Nova Beam")),
    ]
