from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass(frozen=True)
class GameWebInfo:
    what_can_randomize: Iterable[str] = ()
    """What can be randomized?"""

    need_to_play: Iterable[str] = ()
    """What do you need to play?"""
