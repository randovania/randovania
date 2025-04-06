from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.game.gui import ProgressiveItemTuples


def tuples() -> ProgressiveItemTuples:
    return [
        ("Progressive Suit", ("Dark Suit", "Light Suit")),
        ("Progressive Grapple", ("Grapple Beam", "Screw Attack")),
    ]
