from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.game.gui import ProgressiveItemTuples


def tuples() -> ProgressiveItemTuples:
    return [
        ("Progressive Suit", ("Varia Suit", "Gravity Suit")),
        ("Progressive Jump", ("Hi-Jump Boots", "Space Jump")),
    ]
