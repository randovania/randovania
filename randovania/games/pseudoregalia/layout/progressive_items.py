from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.game.gui import ProgressiveItemTuples


def tuples() -> ProgressiveItemTuples:
    return [
        ("Progressive Dream Breaker", ("Dream Breaker", "Strikebreak", "Soul Cutter")),
        ("Progressive Slide", ("Slide", "Solar Wind")),
    ]
