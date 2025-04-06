from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.game.gui import ProgressiveItemTuples


def tuples() -> ProgressiveItemTuples:
    return [
        ("Progressive Beam", ("Wide Beam", "Plasma Beam", "Wave Beam")),
        ("Progressive Charge Beam", ("Charge Beam", "Diffusion Beam")),
        ("Progressive Missile", ("Super Missile", "Ice Missile")),
        ("Progressive Suit", ("Varia Suit", "Gravity Suit")),
        ("Progressive Bomb", ("Bomb", "Cross Bomb")),
        ("Progressive Spin", ("Spin Boost", "Space Jump")),
    ]
